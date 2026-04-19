#!/usr/bin/env python3
"""
Run the AAA MCP evaluation suite against the ground-truth question set.

For each question:
  1. Calls search_knowledge() to retrieve relevant items
  2. Scores results against expected persona, topics, tools, and relevance threshold
  3. Outputs a pass/fail report with per-question details and an overall score

Usage:
  python3 scripts/run_eval.py
  python3 scripts/run_eval.py --question eval-001
  python3 scripts/run_eval.py --output data/wiki/schema/eval_results.json
  python3 scripts/run_eval.py --verbose
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

GROUND_TRUTH_PATH = Path("data/wiki/schema/eval_ground_truth.json")
DEFAULT_OUTPUT = Path("data/wiki/schema/eval_results.json")
N_RESULTS = 8


def score_question(question: dict, search_results: dict) -> dict:
    """Score search results against a ground-truth question."""
    results = search_results.get("results", [])
    total_results = search_results.get("total_results", 0)

    checks = {}

    # 1. Got any results?
    checks["has_results"] = total_results > 0

    # 2. Top result meets minimum relevance threshold
    min_score = question.get("min_relevance_score", 0.35)
    top_score = results[0]["relevance_score"] if results else 0.0
    checks["relevance_threshold"] = top_score >= min_score

    # 3. Required author cited?
    must_cite = question.get("must_cite_author")
    if must_cite:
        cited_authors = [r.get("author", "").lower() for r in results]
        checks["author_cited"] = any(must_cite.lower() in a for a in cited_authors)
    else:
        checks["author_cited"] = None  # not applicable

    # 4. Expected tools appear in top results?
    expected_tools = [t.lower() for t in question.get("expected_tools", [])]
    if expected_tools:
        all_tools: list[str] = []
        for r in results:
            all_tools.extend(t.lower() for t in r.get("mentioned_tools", []))
        all_tools_str = " ".join(all_tools)
        found_tools = [t for t in expected_tools if t in all_tools_str]
        checks["tools_found"] = len(found_tools) == len(expected_tools)
        checks["tools_detail"] = {"expected": expected_tools, "found": found_tools}
    else:
        checks["tools_found"] = None

    # 5. Expected topics appear in top results (any match)?
    expected_topics = [t.lower() for t in question.get("expected_topics", [])]
    if expected_topics:
        all_topics_text = " ".join(
            " ".join(r.get("topics", [])) + " " + r.get("snippet", "").lower()
            for r in results
        ).lower()
        found_topics = [t for t in expected_topics if t in all_topics_text]
        checks["topics_found"] = len(found_topics) >= max(1, len(expected_topics) // 2)
        checks["topics_detail"] = {"expected": expected_topics, "found": found_topics}
    else:
        checks["topics_found"] = None

    # Calculate score: count applicable passing checks
    applicable = [v for v in [
        checks["has_results"],
        checks["relevance_threshold"],
        checks.get("author_cited"),
        checks.get("tools_found"),
        checks.get("topics_found"),
    ] if v is not None]

    score = sum(1 for v in applicable if v) / len(applicable) if applicable else 0.0
    passed = score >= 0.6  # pass if 60%+ of applicable checks pass

    return {
        "question_id": question["id"],
        "question": question["question"],
        "passed": passed,
        "score": round(score, 3),
        "top_relevance": round(top_score, 4),
        "result_count": total_results,
        "checks": checks,
        "top_results": [
            {"author": r.get("author"), "post_type": r.get("post_type"),
             "relevance": r.get("relevance_score"), "snippet": r.get("snippet", "")[:120]}
            for r in results[:3]
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AAA MCP evaluation suite")
    parser.add_argument("--question", help="Run a single question by ID (e.g. eval-001)")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if not GROUND_TRUTH_PATH.exists():
        print(f"ERROR: Ground truth not found at {GROUND_TRUTH_PATH}")
        sys.exit(1)

    ground_truth = json.loads(GROUND_TRUTH_PATH.read_text())
    questions = ground_truth["questions"]

    if args.question:
        questions = [q for q in questions if q["id"] == args.question]
        if not questions:
            print(f"ERROR: Question '{args.question}' not found")
            sys.exit(1)

    from src.api.mcp_server import search_knowledge  # noqa: PLC0415

    print(f"Running {len(questions)} evaluation questions…\n")

    eval_results = []
    passed = failed = 0

    for q in questions:
        raw = json.loads(search_knowledge(q["question"], n_results=N_RESULTS))
        result = score_question(q, raw)
        eval_results.append(result)

        status = "PASS" if result["passed"] else "FAIL"
        score_pct = f"{result['score']*100:.0f}%"
        print(f"  [{status}] {score_pct:>4}  {q['id']}  {q['question'][:65]}")

        if args.verbose:
            for r in result["top_results"]:
                print(f"          {r['relevance']:.3f}  {r['author']} ({r['post_type']})")
                print(f"          {r['snippet'][:100]}")
            print()

        if result["passed"]:
            passed += 1
        else:
            failed += 1

    overall_score = passed / len(questions) if questions else 0.0
    print(f"\n── Results {'─' * 40}")
    print(f"  Passed:  {passed}/{len(questions)} ({overall_score*100:.0f}%)")
    print(f"  Failed:  {failed}")
    print(f"  Avg relevance score: {sum(r['top_relevance'] for r in eval_results)/len(eval_results):.4f}")

    if not args.question:
        print("\nFailed questions:")
        for r in eval_results:
            if not r["passed"]:
                print(f"  {r['question_id']}: {r['question'][:70]}")
                missing = [k for k, v in r["checks"].items()
                           if v is False and k not in ("tools_detail", "topics_detail")]
                print(f"    Failed checks: {missing}")

    # Write output
    output = {
        "schema_version": "1.0",
        "run_at": datetime.now(timezone.utc).isoformat(),
        "total_questions": len(questions),
        "passed": passed,
        "failed": failed,
        "overall_score": round(overall_score, 4),
        "avg_top_relevance": round(
            sum(r["top_relevance"] for r in eval_results) / len(eval_results), 4
        ),
        "results": eval_results,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\nResults written → {out_path}")


if __name__ == "__main__":
    main()
