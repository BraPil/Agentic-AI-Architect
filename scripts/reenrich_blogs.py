#!/usr/bin/env python3
"""
Re-enrich blog posts that were indexed without Claude extraction.

Identifies ChromaDB entries where mentioned_tools is empty (indicating text-only
ingest), deletes them, and re-ingests with full Claude Haiku extraction.

Only targets blog_post entries — LinkedIn/YouTube/GitHub content is unaffected.

Usage:
  ANTHROPIC_API_KEY=sk-ant-... python3 scripts/reenrich_blogs.py
  python3 scripts/reenrich_blogs.py --dry-run   # show what would be re-enriched
  python3 scripts/reenrich_blogs.py --persona chip_huyen  # single author
"""

import argparse
import logging
import os
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("reenrich_blogs")

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline.blog_ingest import BLOG_REGISTRY, BlogIngestPipeline
from src.pipeline.linkedin_persona_store import LinkedInPersonaStore


def find_unenriched_blog_posts(store: LinkedInPersonaStore, persona_filter: str | None = None) -> list[dict]:
    """Return blog_post entries with empty topics field (unenriched by Claude)."""
    result = store._collection.get(
        where={"post_type": "blog_post"},
        include=["metadatas"],
    )
    unenriched = []
    for pid, meta in zip(result["ids"], result["metadatas"]):
        # topics is populated by Claude extraction; empty means text-only ingest
        topics = meta.get("topics", "").strip()
        if topics:
            continue  # already enriched
        if persona_filter and meta.get("persona_id") != persona_filter:
            continue
        unenriched.append({"post_id": pid, "persona_id": meta.get("persona_id"), "metadata": meta})
    return unenriched


def delete_entries(store: LinkedInPersonaStore, post_ids: list[str]) -> None:
    """Delete entries from ChromaDB by ID so they can be re-ingested."""
    if post_ids:
        store._collection.delete(ids=post_ids)
        logger.info("Deleted %d unenriched entries from ChromaDB", len(post_ids))


def main() -> None:
    parser = argparse.ArgumentParser(description="Re-enrich unenriched blog posts with Claude extraction")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be re-enriched without making changes")
    parser.add_argument("--persona", help="Restrict to a single blog persona (e.g. chip_huyen)")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key and not args.dry_run:
        logger.error("ANTHROPIC_API_KEY not set. Set it or use --dry-run.")
        sys.exit(1)

    store = LinkedInPersonaStore()
    store.initialize()

    unenriched = find_unenriched_blog_posts(store, args.persona)

    if not unenriched:
        logger.info("No unenriched blog posts found — nothing to do.")
        return

    by_persona: dict[str, list[str]] = {}
    for entry in unenriched:
        pid = entry["persona_id"]
        by_persona.setdefault(pid, []).append(entry["post_id"])

    print(f"\nFound {len(unenriched)} unenriched blog posts:")
    for pid, ids in sorted(by_persona.items(), key=lambda x: -len(x[1])):
        reg_key = next((k for k, v in BLOG_REGISTRY.items() if v["persona_id"] == pid), pid)
        author = BLOG_REGISTRY.get(reg_key, {}).get("author", pid)
        print(f"  {author:<30} {len(ids):>3} posts")

    if args.dry_run:
        print("\n[DRY RUN] No changes made.")
        return

    print()
    target_personas = list(by_persona.keys())
    if args.persona:
        target_personas = [p for p in target_personas if p == args.persona]

    # Map persona_id → registry key
    pid_to_regkey: dict[str, str] = {v["persona_id"]: k for k, v in BLOG_REGISTRY.items()}

    for persona_id in target_personas:
        reg_key = pid_to_regkey.get(persona_id)
        if not reg_key:
            logger.warning("No BLOG_REGISTRY entry for persona_id=%s — skipping", persona_id)
            continue

        post_ids_to_delete = by_persona[persona_id]
        logger.info(
            "Re-enriching %s (%d posts)…",
            BLOG_REGISTRY[reg_key]["author"], len(post_ids_to_delete),
        )

        # Delete unenriched entries
        delete_entries(store, post_ids_to_delete)
        # Clear existing_ids cache in the store won't be called again;
        # the blog pipeline fetches its own existing set from ChromaDB
        # so deleted IDs will be treated as new and re-ingested.

    # Re-ingest with extraction
    pipeline = BlogIngestPipeline(anthropic_api_key=api_key)
    target_reg_keys = [pid_to_regkey[p] for p in target_personas if p in pid_to_regkey]
    results = pipeline.run(target_reg_keys)

    print(f"\n── Re-enrichment Results {'─' * 30}")
    total_added = 0
    for r in results:
        print(f"  {r.author:<30}  {r.added} re-enriched, {r.skipped} skipped, {r.failed} failed")
        for err in r.errors[:3]:
            print(f"    ERROR: {err[:100]}")
        total_added += r.added

    print(f"\n  Total re-enriched: {total_added}")

    if total_added > 0:
        print("\nExporting updated ChromaDB snapshot…")
        import subprocess  # noqa: PLC0415
        subprocess.run(
            [sys.executable, "scripts/export_chromadb_snapshot.py"],
            check=False,
        )


if __name__ == "__main__":
    main()
