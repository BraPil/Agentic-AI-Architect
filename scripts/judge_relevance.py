#!/usr/bin/env python3
"""
LLM-judged graded relevance — build a fine-grained relevance label set for the ranking eval.

The label-free heuristic oracle (author/tool/topic signal-counting) is coarse: with hybrid ON
the rank-aware eval saturates (MRR = hit@1 = 1.0), so it can no longer tell a strong reranker
from a weak one. This script produces *graded* judgments (0..3) per (question, document) with
an LLM judge, persisted to `data/wiki/schema/relevance_judgments.json`. The eval then scores
nDCG against those grades, restoring discriminating power.

Judging pool: for each search question, the union of what hybrid OFF and hybrid ON surface in
their top-N — so every ordering being compared is judged on the same fixed document set.

Grading rubric (0..3):
  3 — directly and substantially answers the question
  2 — clearly relevant; covers part of the question or strong related context
  1 — tangentially related; mentions the topic but doesn't address the question
  0 — irrelevant

Requires ANTHROPIC_API_KEY. All document text is passed through sanitize_text() before the
prompt (prompt-injection firewall — these are external documents). Re-runs are incremental:
existing judgments are kept unless --overwrite.

Usage:
  python3 scripts/judge_relevance.py                 # judge all search questions
  python3 scripts/judge_relevance.py --question eval-005
  python3 scripts/judge_relevance.py --pool-n 20 --overwrite
  python3 scripts/judge_relevance.py --dry-run        # show pool sizes, no LLM calls
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.helpers import sanitize_text  # noqa: E402

GROUND_TRUTH_PATH = Path("data/wiki/schema/eval_ground_truth.json")
JUDGMENTS_PATH = Path("data/wiki/schema/relevance_judgments.json")
JUDGE_MODEL = "claude-haiku-4-5-20251001"

RUBRIC = (
    "Grade each document's relevance to the QUESTION on a 0-3 scale:\n"
    "  3 = directly and substantially answers the question\n"
    "  2 = clearly relevant; covers part of the question or strong related context\n"
    "  1 = tangentially related; mentions the topic but doesn't address the question\n"
    "  0 = irrelevant\n"
)


def _build_pool(search_knowledge, question: dict, pool_n: int) -> list[dict]:
    """Union of hybrid-OFF and hybrid-ON top-N results for a question, deduped by post_id."""
    persona = question.get("expected_persona") or ""
    pool: dict[str, dict] = {}
    for flag in ("0", "1"):
        os.environ["AAA_HYBRID_RANKING"] = flag
        raw = json.loads(search_knowledge(question["question"], persona=persona, n_results=pool_n))
        for r in raw.get("results", []):
            pool.setdefault(r["post_id"], r)
    return list(pool.values())


def _grade_pool(client, question: dict, pool: list[dict]) -> dict[str, int]:
    """Ask the LLM judge to grade every document in the pool. Returns {post_id: grade}."""
    docs_block = []
    for i, r in enumerate(pool):
        snippet = sanitize_text(r.get("snippet", ""))[:400]
        docs_block.append(f'[{i}] post_id="{r["post_id"]}" author="{r.get("author","")}"\n{snippet}')
    prompt = (
        f"{RUBRIC}\n"
        f"QUESTION: {sanitize_text(question['question'])}\n\n"
        f"DOCUMENTS:\n" + "\n\n".join(docs_block) + "\n\n"
        "Return ONLY a JSON object mapping each post_id to its integer grade, e.g. "
        '{"li-123": 3, "li-456": 1}. No prose.'
    )
    msg = client.messages.create(
        model=JUDGE_MODEL, max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = msg.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    grades = json.loads(raw)
    # Coerce to ints in [0,3]; keep only known post_ids.
    valid = {r["post_id"] for r in pool}
    return {pid: max(0, min(3, int(g))) for pid, g in grades.items() if pid in valid}


def main() -> None:
    parser = argparse.ArgumentParser(description="LLM-judged graded relevance for the ranking eval")
    parser.add_argument("--question", help="Judge a single question id")
    parser.add_argument("--pool-n", type=int, default=20, help="Top-N per ranker in the pool")
    parser.add_argument("--overwrite", action="store_true", help="Re-judge existing questions")
    parser.add_argument("--dry-run", action="store_true", help="Show pool sizes, no LLM calls")
    args = parser.parse_args()

    ground_truth = json.loads(GROUND_TRUTH_PATH.read_text())
    questions = [q for q in ground_truth["questions"] if q.get("type", "search") == "search"]
    if args.question:
        questions = [q for q in questions if q["id"] == args.question]

    existing = {}
    if JUDGMENTS_PATH.exists():
        existing = json.loads(JUDGMENTS_PATH.read_text()).get("judgments", {})

    from src.api.mcp_server import _get_anthropic, search_knowledge  # noqa: PLC0415
    client = None if args.dry_run else _get_anthropic()
    if not args.dry_run and client is None:
        print("ERROR: ANTHROPIC_API_KEY not set — cannot judge.")
        sys.exit(1)

    judgments = dict(existing)
    try:
        for q in questions:
            if q["id"] in existing and not args.overwrite and not args.dry_run:
                print(f"  [skip] {q['id']} (already judged; --overwrite to redo)")
                continue
            pool = _build_pool(search_knowledge, q, args.pool_n)
            if args.dry_run:
                print(f"  {q['id']}: pool {len(pool)} docs")
                continue
            graded = _grade_pool(client, q, pool)
            judgments[q["id"]] = graded
            dist = {g: sum(1 for v in graded.values() if v == g) for g in (3, 2, 1, 0)}
            print(f"  [judged] {q['id']}: {len(graded)} docs  grade dist {dist}")
    finally:
        os.environ.pop("AAA_HYBRID_RANKING", None)  # leave env as we found it

    if args.dry_run:
        return

    JUDGMENTS_PATH.write_text(json.dumps({
        "schema_version": "1.0",
        "description": "LLM-judged graded relevance (0-3) per (question_id, post_id). "
                       "Built by scripts/judge_relevance.py.",
        "judge_model": JUDGE_MODEL,
        "judgments": judgments,
    }, indent=2, ensure_ascii=False) + "\n")
    print(f"\nWrote {len(judgments)} judged question(s) → {JUDGMENTS_PATH}")


if __name__ == "__main__":
    main()
