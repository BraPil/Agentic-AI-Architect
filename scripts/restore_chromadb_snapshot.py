#!/usr/bin/env python3
"""
Restore the ChromaDB persona store from a JSON snapshot.

Embeddings are recomputed on restore using the same all-MiniLM-L6-v2 model.
Already-indexed IDs are skipped, so restore is safe to run incrementally.

Usage:
  python3 scripts/restore_chromadb_snapshot.py
  python3 scripts/restore_chromadb_snapshot.py --snapshot data/wiki/schema/chromadb_snapshot.json
  python3 scripts/restore_chromadb_snapshot.py --dry-run
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

DEFAULT_SNAPSHOT = Path("data/wiki/schema/chromadb_snapshot.json")
BATCH_SIZE = 50  # ChromaDB performs best with batched adds


def main() -> None:
    parser = argparse.ArgumentParser(description="Restore ChromaDB from JSON snapshot")
    parser.add_argument("--snapshot", default=str(DEFAULT_SNAPSHOT), help="Snapshot file path")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be restored, don't write")
    args = parser.parse_args()

    snapshot_path = Path(args.snapshot)
    if not snapshot_path.exists():
        print(f"ERROR: snapshot not found at {snapshot_path}")
        sys.exit(1)

    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    items = snapshot.get("items", [])
    print(f"Snapshot: {snapshot.get('count', len(items))} items, exported {snapshot.get('exported_at', 'unknown')}")

    if args.dry_run:
        print(f"DRY RUN — would restore {len(items)} items")
        for item in items[:5]:
            meta = item.get("metadata", {})
            print(f"  {item['id']:<35}  {meta.get('author', '')[:30]}  ({meta.get('post_type', '')})")
        if len(items) > 5:
            print(f"  … and {len(items) - 5} more")
        return

    from src.pipeline.linkedin_persona_store import LinkedInPersonaStore
    store = LinkedInPersonaStore()
    store.initialize()

    existing = store.get_existing_ids()
    to_add = [item for item in items if item["id"] not in existing]
    print(f"Already indexed: {len(existing)}  |  To restore: {len(to_add)}  |  Skipping: {len(items) - len(to_add)}")

    if not to_add:
        print("Nothing to restore — collection is already complete.")
        return

    added = 0
    for i in range(0, len(to_add), BATCH_SIZE):
        batch = to_add[i:i + BATCH_SIZE]
        store._collection.add(
            ids=[item["id"] for item in batch],
            documents=[item["document"] for item in batch],
            metadatas=[item["metadata"] for item in batch],
        )
        added += len(batch)
        print(f"  Restored {added}/{len(to_add)}…")

    print(f"\nDone. Collection now has {store.count} items.")


if __name__ == "__main__":
    main()
