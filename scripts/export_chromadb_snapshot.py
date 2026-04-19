#!/usr/bin/env python3
"""
Export the ChromaDB persona store to a portable JSON snapshot.

The snapshot includes all document text, metadata, and IDs — everything
needed to fully restore the collection from scratch. Embeddings are
intentionally excluded (they are cheap to recompute with all-MiniLM-L6-v2).

Usage:
  python3 scripts/export_chromadb_snapshot.py
  python3 scripts/export_chromadb_snapshot.py --out data/wiki/schema/chromadb_snapshot.json
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

DEFAULT_OUT = Path("data/wiki/schema/chromadb_snapshot.json")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export ChromaDB persona store to JSON")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Output path")
    args = parser.parse_args()

    out_path = Path(args.out)

    from src.pipeline.linkedin_persona_store import LinkedInPersonaStore
    store = LinkedInPersonaStore()
    store.initialize()

    print(f"Exporting {store.count} items from ChromaDB…")

    result = store._collection.get(include=["documents", "metadatas"])
    ids = result["ids"]
    documents = result["documents"]
    metadatas = result["metadatas"]

    items = [
        {"id": id_, "document": doc, "metadata": meta}
        for id_, doc, meta in zip(ids, documents, metadatas)
    ]

    snapshot = {
        "schema_version": "1.0",
        "collection": "linkedin_reactions",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "count": len(items),
        "items": items,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Snapshot written → {out_path}  ({out_path.stat().st_size / 1024:.1f} KB, {len(items)} items)")


if __name__ == "__main__":
    main()
