"""Match a complete reference span in a single retrieved chunk."""
from collections import defaultdict


def evaluate_query(question, hits):
    for hit in hits:
        hit["evidence_hit"] = any(
            hit["document_id"] == gold["gold_source_id"]
            and hit["page"] == gold["gold_page"]
            and gold["evidence_quote"] in hit["text"]
            for gold in question["evidence"]
        )
    return {
        **question, "hits": hits, "hit1": bool(hits and hits[0]["evidence_hit"]),
        "hit3": any(hit["evidence_hit"] for hit in hits),
    }


def summarize(traces):
    grouped = defaultdict(list)
    for trace in traces:
        grouped[trace["strategy"]].append(trace)
    return {
        strategy: {
            "n": len(rows), "hit1": sum(row["hit1"] for row in rows),
            "hit3": sum(row["hit3"] for row in rows),
        }
        for strategy, rows in grouped.items()
    }

