"""Aggregate the recorded evidence review over the saved, ranked traces."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def main():
    path = RESULTS / "evidence_review.csv"
    with path.open(encoding="utf-8-sig", newline="") as stream:
        review = {}
        for row in csv.DictReader(stream):
            key = (row["split"], row["strategy"], row["id"], int(row["rank"]))
            if key in review:
                raise ValueError(f"Duplicate review row: {key}")
            review[key] = row

    summary = {}
    for split in ("dev", "test"):
        traces = json.loads((RESULTS / f"trace_{split}.json").read_text(encoding="utf-8"))
        summary[split] = {}
        for trace in traces:
            strategy = trace["strategy"]
            flags = []
            for rank, hit in enumerate(trace["hits"], 1):
                key = (split, strategy, trace["id"], rank)
                row = review.pop(key)
                if (row["chunk_id"] != hit["chunk_id"] or int(row["page"]) != hit["page"]
                        or (row["source_id"], row["start"], row["end"]) !=
                        (hit["document_id"], str(hit["start"]), str(hit["end"]))):
                    raise ValueError(f"Review row does not match saved trace: {key}")
                decision = row["decision"]
                if decision not in ("exact", "equivalent", "insufficient"):
                    raise ValueError(f"Invalid decision: {key}")
                if (decision == "exact") != hit["evidence_hit"]:
                    raise ValueError(f"Exact-match label differs from trace: {key}")
                if not row["reason"] or not row["reviewer"]:
                    raise ValueError(f"Missing review information: {key}")
                flags.append(decision in ("exact", "equivalent"))
            counts = summary[split].setdefault(strategy, {"n": 0, "hit1": 0, "hit3": 0})
            counts["n"] += 1
            counts["hit1"] += bool(flags and flags[0])
            counts["hit3"] += any(flags)

    if review:
        raise ValueError(f"Review contains {len(review)} unrecognized hits")
    (RESULTS / "metrics_evidence_review.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
