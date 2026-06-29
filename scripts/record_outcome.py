#!/usr/bin/env python3
"""
Record the real-world outcome of an AAA architecture recommendation (P6 learning loop).

AAA can only learn from outcomes if you report them. Every
get_architecture_recommendation response carries a `recommendation_id`; grade it here.

Usage:
  # Record an outcome
  python3 scripts/record_outcome.py rec-ab12cd34ef567890 --adopted --worked --score 0.9 \
      --notes "Shipped the namespaced memory design; latency held under target."

  # Adopted but it did not work out
  python3 scripts/record_outcome.py rec-... --adopted --no-worked --notes "Hit a scaling wall."

  # Did not adopt
  python3 scripts/record_outcome.py rec-... --no-adopted

  # Show what AAA has learned so far
  python3 scripts/record_outcome.py --summary

  # List recommendations still awaiting an outcome
  python3 scripts/record_outcome.py --pending
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.learning.outcomes import RecommendationOutcomeStore  # noqa: E402

_LEDGER = Path(__file__).parent.parent / "data" / "recommendation_outcomes.jsonl"


def main() -> None:
    parser = argparse.ArgumentParser(description="Record/inspect AAA recommendation outcomes")
    parser.add_argument("recommendation_id", nargs="?", help="The id being graded")
    parser.add_argument("--adopted", action=argparse.BooleanOptionalAction,
                        help="Did you follow the recommendation? (--adopted / --no-adopted)")
    parser.add_argument("--worked", action=argparse.BooleanOptionalAction, default=False,
                        help="If adopted, did it work? (--worked / --no-worked)")
    parser.add_argument("--score", type=float, default=None, help="Optional 0–1 quality rating")
    parser.add_argument("--notes", default="", help="Free-text context")
    parser.add_argument("--by", default="brandt", help="Who is recording this")
    parser.add_argument("--summary", action="store_true", help="Print the learned signal and exit")
    parser.add_argument("--pending", action="store_true", help="List outcome-less recommendations")
    args = parser.parse_args()

    store = RecommendationOutcomeStore(_LEDGER)

    if args.summary:
        print(json.dumps(store.aggregate(), indent=2, ensure_ascii=False))
        return

    if args.pending:
        pending = store.pending()
        print(f"{len(pending)} recommendation(s) awaiting an outcome:")
        for r in pending:
            print(f"  {r.recommendation_id}  [{r.recommended_at[:10]}]  {r.problem_statement[:70]}")
        return

    if not args.recommendation_id:
        parser.error("recommendation_id is required (or use --summary / --pending)")
    if args.adopted is None:
        parser.error("specify --adopted or --no-adopted")

    try:
        record = store.record_outcome(
            args.recommendation_id, adopted=args.adopted, worked=args.worked,
            outcome_score=args.score, notes=args.notes, recorded_by=args.by,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print("Recorded outcome:")
    print(json.dumps(record.to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
