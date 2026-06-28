#!/usr/bin/env python3
"""
CLI for the learning-loop promotion gate — the headless / scriptable second surface
alongside the MCP tools. Same PromotionGate underneath.

Usage:
  # List experimental artifacts awaiting review (highest confidence first)
  python3 scripts/promote_learnings.py --list
  python3 scripts/promote_learnings.py --list --min-confidence 0.8

  # Promote / reject / demote a specific artifact
  python3 scripts/promote_learnings.py --promote la-abc123 --by brandt
  python3 scripts/promote_learnings.py --reject la-abc123 --reason "off-topic"
  python3 scripts/promote_learnings.py --demote la-abc123 --reason "contradicted later"

  # Calibration: preview what a confidence-threshold auto-promotion policy would do
  python3 scripts/promote_learnings.py --dry-run --min-confidence 0.85
"""

import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger("promote_learnings")

_REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_REPO_ROOT))


def _gate():
    from src.api.mcp_server import _get_store  # noqa: PLC0415
    from src.learning.promotion import PromotionGate  # noqa: PLC0415
    return PromotionGate(_get_store()._collection)


def main() -> None:
    parser = argparse.ArgumentParser(description="Learning-loop promotion gate (CLI)")
    parser.add_argument("--list", action="store_true", help="List experimental candidates")
    parser.add_argument("--promote", metavar="ID", help="Promote an artifact to grounded")
    parser.add_argument("--reject", metavar="ID", help="Reject (remove) an experimental artifact")
    parser.add_argument("--demote", metavar="ID", help="Demote a grounded artifact to experimental")
    parser.add_argument("--by", default="brandt", help="Actor for the audit trail")
    parser.add_argument("--reason", default="", help="Reason (for reject/demote)")
    parser.add_argument("--min-confidence", type=float, default=0.0,
                        help="Confidence filter for --list / --dry-run")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview which candidates a confidence policy would promote")
    args = parser.parse_args()

    gate = _gate()

    if args.dry_run:
        candidates = gate.list_candidates(min_confidence=args.min_confidence)
        logger.info("Dry run: %d artifact(s) at confidence >= %.2f would be eligible:",
                    len(candidates), args.min_confidence)
        for c in candidates:
            logger.info("  [%.2f] %s — %s", c.confidence, c.artifact_id, c.title[:70])
        return

    if args.list:
        candidates = gate.list_candidates(min_confidence=args.min_confidence)
        logger.info("%d experimental artifact(s) awaiting review:", len(candidates))
        for c in candidates:
            logger.info("  [%.2f] %s — %s", c.confidence, c.artifact_id, c.title[:70])
            if c.topics:
                logger.info("        topics: %s", ", ".join(c.topics))
        return

    if args.promote:
        r = gate.promote(args.promote, args.by)
    elif args.reject:
        r = gate.reject(args.reject, args.by, args.reason)
    elif args.demote:
        r = gate.demote(args.demote, args.by, args.reason)
    else:
        parser.print_help()
        return

    status = "OK" if r.ok else "FAILED"
    logger.info("%s: %s %s — %s", status, r.action, r.artifact_id, r.reason)
    if not r.ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
