"""Reproduce the frozen dev/test experiment for the 3626 corpus."""
import argparse
import hashlib
import json
import logging
from collections import Counter
from datetime import datetime
from importlib.metadata import version
from pathlib import Path
from statistics import median
from time import perf_counter

from .chunking import MAX_SIZE, OVERLAP, SIZE, by_paragraph, fixed_size
from .embeddings import DIMENSIONS, MODEL, MODEL_FILE, load_embedder
from .evaluation import evaluate_query, summarize
from .ingestion import load_pdf
from .store import VectorStore

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
PRIVATE = ROOT / ".local"
COLLECTIONS = {"A": "fixed", "B": "structured", "C": "structured"}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def text_digest(path):
    # read_text normalizes CRLF and LF before hashing the experiment inputs.
    return hashlib.sha256(path.read_text(encoding="utf-8-sig").encode("utf-8")).hexdigest()


def validate_benchmark(path, pages):
    by_page = {page.page: page for page in pages}
    rows = read_json(path)
    if len({row["id"] for row in rows}) != len(rows):
        raise ValueError("Benchmark question IDs must be unique")
    counts = Counter(row["split"] for row in rows)
    filters = Counter(row["split"] for row in rows if row.get("filter"))
    if set(counts) != {"dev", "test"} or counts["dev"] < 15 or counts["test"] < 5:
        raise ValueError("Benchmark needs at least 15 dev and 5 test questions")
    if filters.total() < 3 or not filters["test"]:
        raise ValueError("Benchmark needs 3 filter questions and one in test")
    for row in rows:
        references = [row, *row.get("alternatives", [])]
        evidence = []
        for reference in references:
            page = by_page[reference["gold_page"]]
            start, end = reference["evidence_start"], reference["evidence_end"]
            quote = page.text[start:end]
            if (not 0 <= start < end <= len(page.text) or reference["gold_source_id"] != page.document_id
                    or hashlib.sha256(quote.encode()).hexdigest() != reference["evidence_sha256"]):
                raise ValueError(f"Invalid gold evidence for {row['id']}")
            if row.get("filter") and not any(
                left <= start < right and label == row["filter"]["chapter"]
                for left, right, label, _ in page.metadata["sections"]
            ):
                raise ValueError(f"Filter does not match source for {row['id']}")
            evidence.append({**reference, "evidence_quote": quote})
        row["evidence"] = evidence
    return rows


def build_index(store, embedder, groups):
    stats = {}
    for strategy, chunks in groups.items():
        name = COLLECTIONS[strategy]
        inputs = ["passage: " + chunk.text for chunk in chunks]
        started = perf_counter()
        vectors = [vector.tolist() for vector in embedder.embed(inputs, batch_size=16)]
        points = store.replace(name, chunks, vectors)
        elapsed = perf_counter() - started
        before = store.count(name)
        store.upsert(name, points)
        after = store.count(name)
        if before != after or after != len(chunks):
            raise RuntimeError(f"Duplicate/missing points in {name}: {before} -> {after}")
        lengths = [len(chunk.text) for chunk in chunks]
        stats[strategy] = {
            "chunks": len(chunks), "characters": sum(lengths),
            "min": min(lengths), "median": median(lengths), "max": max(lengths),
            "ingest_seconds": round(elapsed, 4), "api_cost_usd": 0,
            "count_before_reload": before, "count_after_reload": after,
        }
        logging.info("Ingested %s points in %s", after, name)
    stats["C"] = {**stats["B"], "shared_collection": "structured"}
    return stats


def review_samples(pages, groups):
    samples = []
    for page in pages[:10]:
        anchor = len(page.text) // 2
        for strategy, chunks in groups.items():
            candidate = min(
                (chunk for chunk in chunks if chunk.page == page.page
                 and chunk.metadata["start"] <= anchor < chunk.metadata["end"]),
                key=lambda chunk: (abs((chunk.metadata["start"] + chunk.metadata["end"]) / 2 - anchor),
                                   chunk.metadata["start"]),
            )
            samples.append({"strategy": strategy, "page": page.page, "anchor": anchor,
                            "chunk_id": candidate.chunk_id, "text": candidate.text})
    write_json(PRIVATE / "coherence_samples.json", samples)


def retrieve(store, embedder, questions):
    vectors = [vector.tolist() for vector in embedder.embed(
        ["query: " + row["question"] for row in questions], batch_size=16)]
    traces = []
    for strategy, collection in COLLECTIONS.items():
        for question, vector in zip(questions, vectors, strict=True):
            chapter = question.get("filter", {}).get("chapter") if strategy == "C" else None
            start = perf_counter()
            hits = store.search(collection, vector, chapter)
            traces.append({
                "strategy": strategy, "applied_chapter": chapter,
                "query_ms": round((perf_counter() - start) * 1000, 4),
                **evaluate_query(question, hits),
            })
    return traces


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["dev", "test"])
    parser.add_argument("--pdf", type=Path, default=PRIVATE / "3626-text.pdf")
    parser.add_argument("--model-dir", type=Path, default=PRIVATE / "e5")
    args = parser.parse_args()
    RESULTS.mkdir(exist_ok=True)
    logging.basicConfig(filename=RESULTS / "pipeline.log", encoding="utf-8",
                        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    manifest = read_json(ROOT / "data/manifest.json")
    benchmark = ROOT / "benchmark/questions.json"
    pdf_hash = digest(args.pdf)
    if pdf_hash != manifest["sha256"]:
        raise ValueError("PDF checksum differs from the manifest")
    pages = load_pdf(args.pdf, manifest["source_id"], manifest["source_path_or_url"])
    actual_pages = [{"page": page.page, "characters": len(page.text)} for page in pages]
    if len(pages) < 30 or actual_pages != manifest["pages"]:
        raise ValueError("Extracted corpus differs from the manifest")
    questions = validate_benchmark(benchmark, pages)
    revision = (args.model_dir / "revision.txt").read_text().strip()
    identity = {
        "pdf_sha256": pdf_hash, "benchmark_sha256": text_digest(benchmark),
        "embedding_model": MODEL, "embedding_revision": revision, "dimensions": DIMENSIONS,
        "onnx_sha256": digest(args.model_dir / MODEL_FILE),
        "tokenizer_sha256": digest(args.model_dir / "tokenizer.json"),
        "packages": {package: version(package) for package in
                     ("pymupdf", "qdrant-client", "fastembed", "onnxruntime", "tokenizers", "numpy")},
        "pipeline_sha256": {file.name: text_digest(file)
                            for file in sorted(Path(__file__).parent.glob("*.py"))},
        "cosine_search": "Qdrant local, exact",
    }
    freeze_path = RESULTS / "dev_selection.json"
    if args.stage == "test":
        freeze = read_json(freeze_path)
        if freeze["identity"] != identity:
            raise ValueError("Experiment inputs differ from the frozen dev run")
    logging.info("Starting %s with %d verified pages", args.stage, len(pages))
    embedder = load_embedder(args.model_dir)
    store = VectorStore(PRIVATE / "qdrant")
    try:
        if args.stage == "dev":
            groups = {
                "A": [chunk for page in pages for chunk in fixed_size(page, SIZE, OVERLAP)],
                "B": [chunk for page in pages for chunk in by_paragraph(page, MAX_SIZE)],
            }
            stats = build_index(store, embedder, groups)
            review_samples(pages, groups)
            write_json(RESULTS / "ingest.json", stats)
        else:
            stats = read_json(RESULTS / "ingest.json")
            for strategy in ("A", "B"):
                if store.count(COLLECTIONS[strategy]) != stats[strategy]["chunks"]:
                    raise RuntimeError("Persistent collection count differs from the dev run")
        traces = retrieve(store, embedder, [q for q in questions if q["split"] == args.stage])
    finally:
        store.client.close()
    summary = summarize(traces)
    write_json(PRIVATE / f"trace_{args.stage}_full.json", traces)
    redacted = [
        {**{key: value for key, value in trace.items() if key != "evidence"},
         "hits": [{key: value for key, value in hit.items() if key != "text"} for hit in trace["hits"]]}
        for trace in traces
    ]
    write_json(RESULTS / f"trace_{args.stage}.json", redacted)
    write_json(RESULTS / f"metrics_{args.stage}.json", summary)
    if args.stage == "dev":
        choice = max(COLLECTIONS, key=lambda name: (
            summary[name]["hit3"], summary[name]["hit1"], -stats[name]["chunks"],
            -list(COLLECTIONS).index(name)))
        write_json(freeze_path, {
            "identity": identity, "chosen": choice,
            "frozen_at": datetime.now().astimezone().isoformat(),
            "rule": "Dev Hit@3, then Hit@1, then fewer chunks, then A before B before C",
        })
    logging.info("Completed %s: %s", args.stage, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.exception("Pipeline failed")
        raise
