#!/usr/bin/env python3
"""
Ingest blog posts from registered sources into the ChromaDB persona store.

Registered sources: Simon Willison, Lilian Weng, Chip Huyen, Sebastian Ruder, Eugene Yan.
Add more in BLOG_REGISTRY inside src/pipeline/blog_ingest.py.

Usage:
  ANTHROPIC_API_KEY=sk-ant-... python3 scripts/ingest_blogs.py
  python3 scripts/ingest_blogs.py --no-extract              # text-only, no API key needed
  python3 scripts/ingest_blogs.py --persona chip_huyen      # single source
  python3 scripts/ingest_blogs.py --max-posts 10
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline.blog_ingest import BLOG_REGISTRY, BlogIngestPipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest blog posts into ChromaDB persona store")
    parser.add_argument("--persona", nargs="+", choices=list(BLOG_REGISTRY),
                        default=list(BLOG_REGISTRY), help="Blogs to ingest (default: all)")
    parser.add_argument("--max-posts", type=int, default=30,
                        help="Max posts per blog to fetch (default: 30)")
    parser.add_argument("--no-extract", action="store_true",
                        help="Skip Claude extraction — embed raw text only")
    parser.add_argument("--raw-dir", default="data/wiki/raw")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    use_extraction = not args.no_extract and bool(api_key)

    if not use_extraction and not args.no_extract:
        print("ANTHROPIC_API_KEY not set — running in text-only mode.\n")

    # Override max_posts in registry
    for config in BLOG_REGISTRY.values():
        config["max_posts"] = args.max_posts

    pipeline = BlogIngestPipeline(
        anthropic_api_key=api_key if use_extraction else None,
        raw_dir=args.raw_dir,
    )

    print(f"Ingesting blogs: {', '.join(args.persona)}\n")
    results = pipeline.run(args.persona)

    print(f"\n── Summary {'─' * 40}")
    total_added = 0
    for r in results:
        status = f"{r.added} added, {r.skipped} skipped, {r.failed} failed"
        print(f"  {r.author:<25}  {r.total_fetched:>3} fetched  |  {status}")
        if r.errors:
            for err in r.errors[:3]:
                print(f"    ERROR: {err[:100]}")
        total_added += r.added

    print(f"\n  Total new posts indexed: {total_added}")

    if total_added > 0:
        print("\nUpdating ChromaDB snapshot…")
        import subprocess  # noqa: PLC0415
        subprocess.run(
            [sys.executable, "scripts/export_chromadb_snapshot.py"],
            check=False,
        )


if __name__ == "__main__":
    main()
