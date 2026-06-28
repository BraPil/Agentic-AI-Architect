#!/usr/bin/env python3
"""
Ingest project learning logs into ChromaDB.

Parses docs/decision-log.md, docs/discovery-log.md, and docs/lessons-learned-log.md
and indexes all entries into the linkedin_reactions ChromaDB collection so they appear
in search_knowledge and get_architecture_recommendation results alongside external content.

This closes the feedback loop: lessons learned from building real systems are searchable
and inform future architectural recommendations.

Usage:
  python3 scripts/ingest_project_learnings.py          # ingest all three logs
  python3 scripts/ingest_project_learnings.py --dry-run  # parse only, no writes
  python3 scripts/ingest_project_learnings.py --type decision  # one log only
"""

import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ingest_project_learnings")

_REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_REPO_ROOT))


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest project learning logs into ChromaDB")
    parser.add_argument(
        "--type",
        choices=["decision", "discovery", "lesson", "all"],
        default="all",
        help="Which log to ingest (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and report only — no ChromaDB writes",
    )
    args = parser.parse_args()

    from src.pipeline.project_learning_ingest import (  # noqa: PLC0415
        ProjectLearningIngestPipeline,
        _LEARNING_SOURCES,
        _parse_decisions,
        _parse_discoveries,
        _parse_lessons,
    )

    if args.dry_run:
        logger.info("DRY RUN — parsing only, no ChromaDB writes")
        parsers = {
            "decision": (_LEARNING_SOURCES["decision"], _parse_decisions),
            "discovery": (_LEARNING_SOURCES["discovery"], _parse_discoveries),
            "lesson": (_LEARNING_SOURCES["lesson"], _parse_lessons),
        }
        total = 0
        for learning_type, (path, parse_fn) in parsers.items():
            if args.type != "all" and args.type != learning_type:
                continue
            if not path.exists():
                logger.warning("Not found: %s", path)
                continue
            entries = parse_fn(path)
            logger.info(
                "%-10s: %d entries parsed from %s", learning_type, len(entries), path.name
            )
            for e in entries[:3]:
                logger.info("  [%s] %s", e.date, e.title[:80])
            if len(entries) > 3:
                logger.info("  ... and %d more", len(entries) - 3)
            total += len(entries)
        logger.info("Total: %d entries would be ingested", total)
        return

    pipeline = ProjectLearningIngestPipeline()
    results = pipeline.run()

    total_added = 0
    total_skipped = 0
    total_failed = 0
    for r in results:
        if args.type != "all" and args.type != r.learning_type:
            continue
        logger.info(
            "%-10s: %d added, %d updated/skipped, %d failed",
            r.learning_type, r.added, r.skipped, r.failed,
        )
        for err in r.errors:
            logger.warning("  Error: %s", err)
        total_added += r.added
        total_skipped += r.skipped
        total_failed += r.failed

    logger.info(
        "Done. Total: %d new, %d updated/skipped, %d failed",
        total_added, total_skipped, total_failed,
    )

    if total_added > 0:
        logger.info(
            "Run export_chromadb_snapshot.py to commit the updated snapshot to git."
        )


if __name__ == "__main__":
    main()
