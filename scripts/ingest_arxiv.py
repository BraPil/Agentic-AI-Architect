#!/usr/bin/env python3
"""
Ingest arXiv paper abstracts into the ChromaDB persona store.

Runs curated queries across agentic AI, RAG, memory, evaluation, and related topics.
No API key required for fetching; ANTHROPIC_API_KEY enables Claude extraction.

Usage:
  ANTHROPIC_API_KEY=sk-ant-... python3 scripts/ingest_arxiv.py
  python3 scripts/ingest_arxiv.py --no-extract
  python3 scripts/ingest_arxiv.py --max-per-query 5
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline.arxiv_ingest import ARXIV_QUERIES, ArxivIngestPipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest arXiv abstracts into ChromaDB")
    parser.add_argument("--no-extract", action="store_true", help="Skip Claude extraction")
    parser.add_argument("--max-per-query", type=int, default=10,
                        help="Max results per query (default: 10)")
    parser.add_argument("--raw-dir", default="data/wiki/raw")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    use_extraction = not args.no_extract and bool(api_key)

    if not use_extraction and not args.no_extract:
        print("ANTHROPIC_API_KEY not set — running in text-only mode.\n")

    queries = [{**q, "max_results": args.max_per_query} for q in ARXIV_QUERIES]

    pipeline = ArxivIngestPipeline(
        anthropic_api_key=api_key if use_extraction else None,
        raw_dir=args.raw_dir,
        queries=queries,
    )

    print(f"Running {len(queries)} arXiv queries (max {args.max_per_query} results each)…\n")
    results = pipeline.run()

    print(f"\n── Summary {'─' * 40}")
    total_added = 0
    for r in results:
        print(f"  [{r.added:>2} added, {r.skipped:>2} skip]  {r.query[:60]}")
        total_added += r.added

    print(f"\n  Total new papers indexed: {total_added}")

    if total_added > 0:
        print("\nUpdating ChromaDB snapshot…")
        import subprocess  # noqa: PLC0415
        subprocess.run(
            [sys.executable, "scripts/export_chromadb_snapshot.py"],
            check=False,
        )


if __name__ == "__main__":
    main()
