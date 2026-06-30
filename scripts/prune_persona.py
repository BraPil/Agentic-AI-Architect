#!/usr/bin/env python3
"""
Prune a non-practitioner persona from the store **and bar it from re-entry** — one act.

The standing curation rule is that the store holds only AI/tech practitioners. Removing a
persona from ChromaDB alone is not enough: the next LinkedIn reactions scrape will silently
re-ingest it (this happened April → June 2026). This script does both in one step:

  1. Delete the persona's posts from the persona store.
  2. Add the persona to the curation denylist (data/curation_denylist.json), so
     LinkedInPersonaStore.ingest() refuses to re-add it.

After running, export the snapshot so the deletion persists across restarts:
  python3 scripts/export_chromadb_snapshot.py

Usage:
  # Prune and bar a persona
  python3 scripts/prune_persona.py --persona kyle-faust --reason "job-announcement persona"

  # Bar without deleting (persona not currently in the store, but block future ingest)
  python3 scripts/prune_persona.py --persona kyle-faust --reason "..." --bar-only

  # List currently barred personas
  python3 scripts/prune_persona.py --list

  # Dry run — show what would change, write nothing
  python3 scripts/prune_persona.py --persona kyle-faust --reason "..." --dry-run
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline.curation import DEFAULT_DENYLIST_PATH, PersonaCurationList  # noqa: E402
from src.pipeline.linkedin_persona_store import LinkedInPersonaStore, persona_slug  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Prune and bar a non-practitioner persona.")
    parser.add_argument("--persona", help="Persona ID or display name to prune + bar.")
    parser.add_argument("--reason", default="non-practitioner persona (manual prune)",
                        help="Why this persona is barred — recorded in the denylist audit trail.")
    parser.add_argument("--bar-only", action="store_true",
                        help="Add to denylist without deleting from the store.")
    parser.add_argument("--list", action="store_true", help="List barred personas and exit.")
    parser.add_argument("--dry-run", action="store_true", help="Show changes, write nothing.")
    args = parser.parse_args()

    curation = PersonaCurationList.load()

    if args.list:
        if not len(curation):
            print("No personas are currently barred.")
            return
        print(f"Barred personas ({len(curation)}):")
        for pid in sorted(curation.blocked_ids):
            print(f"  - {pid}")
        return

    if not args.persona:
        parser.error("--persona is required (or use --list)")

    # Accept either a slug or a display name.
    persona_id = args.persona if args.persona == persona_slug(args.persona) else persona_slug(args.persona)
    print(f"Persona: {persona_id}")

    # 1. Delete from the store (unless bar-only).
    deleted = 0
    if not args.bar_only:
        store = LinkedInPersonaStore()
        try:
            store.initialize()
        except ImportError as exc:
            print(f"WARNING: store unavailable ({exc}); falling back to bar-only.")
        else:
            existing = store.get_posts_by_persona(persona_id)
            print(f"  {len(existing)} post(s) currently indexed for this persona.")
            if not args.dry_run:
                deleted = store.prune_persona(persona_id)
                print(f"  Deleted {deleted} post(s) from the store.")
            else:
                print(f"  DRY RUN — would delete {len(existing)} post(s).")

    # 2. Bar from future ingest.
    newly_barred = persona_id not in curation.blocked_ids
    if args.dry_run:
        verb = "would bar" if newly_barred else "already barred"
        print(f"  DRY RUN — {verb}: {persona_id}")
        return

    curation.block(persona_id, reason=args.reason)
    curation.save(DEFAULT_DENYLIST_PATH)
    print(f"  {'Barred' if newly_barred else 'Updated bar for'}: {persona_id}")
    print(f"  Denylist now holds {len(curation)} persona(s) → {DEFAULT_DENYLIST_PATH}")

    if deleted and not args.bar_only:
        print("\nRemember to export the snapshot so the deletion persists:")
        print("  python3 scripts/export_chromadb_snapshot.py")


if __name__ == "__main__":
    main()
