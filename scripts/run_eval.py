#!/usr/bin/env python3
"""
Run the AAA MCP evaluation suite against the ground-truth question set.

For each search question:
  1. Calls search_knowledge() to retrieve relevant items
  2. Scores results against expected persona, topics, tools, and relevance threshold

For each synthesis question (--synthesis flag):
  1. Calls get_architecture_recommendation()
  2. Checks recommendation quality, confidence, tools cited, personas cited

Usage:
  python3 scripts/run_eval.py
  python3 scripts/run_eval.py --synthesis          # also run synthesis eval (requires API key)
  python3 scripts/run_eval.py --coverage           # print persona coverage report
  python3 scripts/run_eval.py --question eval-001  # single question
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

CONFIDENCE_RANK = {"high": 3, "medium": 2, "low": 1}


# ---------------------------------------------------------------------------
# Search question scoring
# ---------------------------------------------------------------------------

def score_search_question(question: dict, search_results: dict) -> dict:
    """Score search results against a ground-truth search question."""
    results = search_results.get("results", [])
    total_results = search_results.get("total_results", 0)

    checks = {}

    checks["has_results"] = total_results > 0

    min_score = question.get("min_relevance_score", 0.35)
    top_score = results[0]["relevance_score"] if results else 0.0
    checks["relevance_threshold"] = top_score >= min_score

    must_cite = question.get("must_cite_author")
    if must_cite:
        cited_authors = [r.get("author", "").lower() for r in results]
        checks["author_cited"] = any(must_cite.lower() in a for a in cited_authors)
    else:
        checks["author_cited"] = None

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

    applicable = [v for v in [
        checks["has_results"],
        checks["relevance_threshold"],
        checks.get("author_cited"),
        checks.get("tools_found"),
        checks.get("topics_found"),
    ] if v is not None]

    score = sum(1 for v in applicable if v) / len(applicable) if applicable else 0.0
    passed = score >= 0.6

    return {
        "question_id": question["id"],
        "question": question["question"],
        "type": "search",
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


# ---------------------------------------------------------------------------
# Synthesis question scoring
# ---------------------------------------------------------------------------

def score_synthesis_question(question: dict, synthesis_result: dict) -> dict:
    """Score a get_architecture_recommendation response against ground truth."""
    checks = {}

    recommendation = synthesis_result.get("recommendation", "")
    checks["has_recommendation"] = bool(recommendation and len(recommendation) > 20)

    confidence = synthesis_result.get("confidence", "low")
    min_conf = question.get("min_confidence", "medium")
    checks["confidence_adequate"] = CONFIDENCE_RANK.get(confidence, 0) >= CONFIDENCE_RANK.get(min_conf, 2)

    min_personas = question.get("min_personas_cited", 1)
    personas_cited = synthesis_result.get("personas_cited", [])
    checks["personas_cited"] = len(personas_cited) >= min_personas

    expected_tools = [t.lower() for t in question.get("expected_tools_in_recommendation", [])]
    if expected_tools:
        all_tools_lower = [t.lower() for t in synthesis_result.get("relevant_tools", [])]
        rec_lower = recommendation.lower()
        found = [t for t in expected_tools if any(t in tool for tool in all_tools_lower) or t in rec_lower]
        checks["tools_in_recommendation"] = len(found) == len(expected_tools)
        checks["tools_detail"] = {"expected": expected_tools, "found": found}
    else:
        checks["tools_in_recommendation"] = None

    expected_topics = [t.lower() for t in question.get("expected_topics_in_recommendation", [])]
    if expected_topics:
        rec_lower = recommendation.lower()
        considerations_lower = " ".join(synthesis_result.get("key_considerations", [])).lower()
        search_text = rec_lower + " " + considerations_lower
        found_topics = [t for t in expected_topics if t in search_text]
        checks["topics_in_recommendation"] = len(found_topics) >= max(1, len(expected_topics) // 2)
        checks["topics_detail"] = {"expected": expected_topics, "found": found_topics}
    else:
        checks["topics_in_recommendation"] = None

    applicable = [v for v in [
        checks["has_recommendation"],
        checks["confidence_adequate"],
        checks["personas_cited"],
        checks.get("tools_in_recommendation"),
        checks.get("topics_in_recommendation"),
    ] if v is not None]

    score = sum(1 for v in applicable if v) / len(applicable) if applicable else 0.0
    passed = score >= 0.6

    return {
        "question_id": question["id"],
        "question": question["question"],
        "type": "synthesis",
        "passed": passed,
        "score": round(score, 3),
        "top_relevance": None,
        "confidence": confidence,
        "personas_cited": personas_cited,
        "relevant_tools": synthesis_result.get("relevant_tools", []),
        "recommendation_snippet": recommendation[:200],
        "checks": checks,
    }


# ---------------------------------------------------------------------------
# Persona coverage report
# ---------------------------------------------------------------------------

def print_persona_coverage(store) -> None:
    """Print a table showing item count and content richness per persona."""
    result = store._collection.get(include=["metadatas"])
    metas = result.get("metadatas", [])

    persona_data: dict[str, dict] = {}
    for m in metas:
        pid = m.get("persona_id", "unknown")
        author = m.get("author", pid)
        if pid not in persona_data:
            persona_data[pid] = {
                "persona_id": pid,
                "author": author,
                "count": 0,
                "with_tools": 0,
                "with_claims": 0,
                "post_types": set(),
            }
        persona_data[pid]["count"] += 1
        if m.get("mentioned_tools", "").strip():
            persona_data[pid]["with_tools"] += 1
        summary = m.get("summary", "")
        if summary and len(summary) > 20 and summary != m.get("author", ""):
            persona_data[pid]["with_claims"] += 1
        post_type = m.get("post_type", "")
        if post_type:
            persona_data[pid]["post_types"].add(post_type)

    sorted_personas = sorted(persona_data.values(), key=lambda x: -x["count"])

    print(f"\n── Persona Coverage Report {'─' * 30}")
    print(f"  {'Persona':<35} {'Items':>5}  {'w/Tools':>7}  {'w/Claims':>8}  Types")
    print(f"  {'─'*35}  {'─'*5}  {'─'*7}  {'─'*8}  {'─'*20}")
    for p in sorted_personas:
        types_str = ", ".join(sorted(p["post_types"]))
        enrichment_pct = int(100 * p["with_tools"] / p["count"]) if p["count"] else 0
        flag = " ⚠" if p["count"] < 3 else ""
        print(
            f"  {p['author'][:35]:<35}  {p['count']:>5}  {p['with_tools']:>5} ({enrichment_pct}%)  "
            f"{p['with_claims']:>6}  {types_str[:25]}{flag}"
        )
    thin = sum(1 for p in sorted_personas if p["count"] < 3)
    print(f"\n  Total personas: {len(sorted_personas)}  |  Thin (< 3 items): {thin}")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Run AAA MCP evaluation suite")
    parser.add_argument("--question", help="Run a single question by ID (e.g. eval-001)")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--synthesis", action="store_true",
                        help="Also run synthesis eval questions (requires ANTHROPIC_API_KEY)")
    parser.add_argument("--coverage", action="store_true",
                        help="Print per-persona coverage report")
    args = parser.parse_args()

    if not GROUND_TRUTH_PATH.exists():
        print(f"ERROR: Ground truth not found at {GROUND_TRUTH_PATH}")
        sys.exit(1)

    ground_truth = json.loads(GROUND_TRUTH_PATH.read_text())
    all_questions = ground_truth["questions"]

    from src.api.mcp_server import _get_store, get_architecture_recommendation, search_knowledge  # noqa: PLC0415

    if args.coverage:
        store = _get_store()
        print_persona_coverage(store)

    # Filter question types
    search_questions = [q for q in all_questions if q.get("type", "search") == "search"]
    synthesis_questions = [q for q in all_questions if q.get("type") == "synthesis"]

    if args.question:
        search_questions = [q for q in search_questions if q["id"] == args.question]
        synthesis_questions = [q for q in synthesis_questions if q["id"] == args.question]
        if not search_questions and not synthesis_questions:
            print(f"ERROR: Question '{args.question}' not found")
            sys.exit(1)

    if not args.synthesis:
        synthesis_questions = []

    questions_to_run = search_questions + synthesis_questions
    if not questions_to_run:
        if not args.coverage:
            print("No questions to run. Use --synthesis to include synthesis questions.")
        return

    print(f"Running {len(search_questions)} search + {len(synthesis_questions)} synthesis questions…\n")

    eval_results = []
    passed = failed = 0

    for q in search_questions:
        raw = json.loads(search_knowledge(q["question"], n_results=N_RESULTS))
        result = score_search_question(q, raw)
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

    for q in synthesis_questions:
        raw = json.loads(get_architecture_recommendation(q["question"], n_sources=N_RESULTS))
        result = score_synthesis_question(q, raw)
        eval_results.append(result)

        status = "PASS" if result["passed"] else "FAIL"
        score_pct = f"{result['score']*100:.0f}%"
        conf = result.get("confidence", "?")
        print(f"  [{status}] {score_pct:>4}  {q['id']}  {q['question'][:55]}  [{conf}]")

        if args.verbose:
            print(f"          Personas: {result.get('personas_cited', [])}")
            print(f"          Tools: {result.get('relevant_tools', [])}")
            print(f"          {result.get('recommendation_snippet', '')[:120]}")
            print()

        if result["passed"]:
            passed += 1
        else:
            failed += 1

    total = len(eval_results)
    overall_score = passed / total if total else 0.0
    search_relevances = [r["top_relevance"] for r in eval_results if r.get("top_relevance") is not None]

    print(f"\n── Results {'─' * 40}")
    print(f"  Passed:  {passed}/{total} ({overall_score*100:.0f}%)")
    print(f"  Failed:  {failed}")
    if search_relevances:
        print(f"  Avg search relevance: {sum(search_relevances)/len(search_relevances):.4f}")

    if not args.question:
        failed_results = [r for r in eval_results if not r["passed"]]
        if failed_results:
            print("\nFailed questions:")
            for r in failed_results:
                print(f"  {r['question_id']}: {r['question'][:70]}")
                missing = [k for k, v in r["checks"].items()
                           if v is False and k not in ("tools_detail", "topics_detail")]
                print(f"    Failed checks: {missing}")

    # Write output
    output = {
        "schema_version": "1.1",
        "run_at": datetime.now(timezone.utc).isoformat(),
        "total_questions": total,
        "search_questions": len(search_questions),
        "synthesis_questions": len(synthesis_questions),
        "passed": passed,
        "failed": failed,
        "overall_score": round(overall_score, 4),
        "avg_top_relevance": round(sum(search_relevances) / len(search_relevances), 4) if search_relevances else None,
        "results": eval_results,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\nResults written → {out_path}")


if __name__ == "__main__":
    main()
