#!/usr/bin/env python3
"""
Rank-aware retrieval evaluation — measure *ordering* quality (MRR, nDCG@k, P@5, hit@1).

Complements `scripts/run_eval.py`, which scores pass/fail presence checks and is structurally
blind to ranking (saturated pass-rate + a vector-biased "avg relevance" metric). This harness
scores how well relevant documents are *ordered*, so a reranker (hybrid / cross-encoder /
query expansion) can finally be judged.

Relevance is graded label-free from the existing ground-truth fields (must_cite_author /
expected_tools / expected_topics) — see src/pipeline/ranking_metrics.py.

Usage:
  # Score current retrieval ordering over the search ground-truth set
  python3 scripts/eval_ranking.py

  # A/B the hybrid reranker: run with it OFF then ON and compare the aggregate line
  AAA_HYBRID_RANKING=0 python3 scripts/eval_ranking.py --output data/rank_off.json
  AAA_HYBRID_RANKING=1 python3 scripts/eval_ranking.py --output data/rank_on.json

  # Compare two saved runs
  python3 scripts/eval_ranking.py --compare data/rank_off.json data/rank_on.json
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline.ranking_metrics import DEFAULT_K, score_ranking  # noqa: E402

GROUND_TRUTH_PATH = Path("data/wiki/schema/eval_ground_truth.json")
N_RESULTS = 10  # retrieve a deeper list than run_eval (8) so ranking has room to be judged


def _aggregate(per_question: list[dict]) -> dict:
    n = len(per_question) or 1
    return {
        "questions": len(per_question),
        "mean_mrr": round(sum(q["metrics"]["mrr"] for q in per_question) / n, 4),
        "mean_ndcg_at_k": round(sum(q["metrics"]["ndcg_at_k"] for q in per_question) / n, 4),
        "mean_precision_at_5": round(sum(q["metrics"]["precision_at_5"] for q in per_question) / n, 4),
        "hit_at_1_rate": round(sum(1 for q in per_question if q["metrics"]["hit_at_1"]) / n, 4),
    }


def run() -> dict:
    if not GROUND_TRUTH_PATH.exists():
        print(f"ERROR: Ground truth not found at {GROUND_TRUTH_PATH}")
        sys.exit(1)

    ground_truth = json.loads(GROUND_TRUTH_PATH.read_text())
    search_questions = [q for q in ground_truth["questions"] if q.get("type", "search") == "search"]

    from src.api.mcp_server import search_knowledge  # noqa: PLC0415

    hybrid = os.environ.get("AAA_HYBRID_RANKING", "0") == "1"
    print(f"Rank-aware eval — {len(search_questions)} search questions, "
          f"n_results={N_RESULTS}, hybrid={'ON' if hybrid else 'OFF'}\n")

    per_question = []
    for q in search_questions:
        persona_arg = q.get("expected_persona") or ""
        raw = json.loads(search_knowledge(q["question"], persona=persona_arg, n_results=N_RESULTS))
        results = raw.get("results", [])
        metrics = score_ranking(results, q, k=DEFAULT_K)
        per_question.append({"id": q["id"], "question": q["question"], "metrics": metrics})
        fr = metrics["first_relevant_rank"]
        print(f"  {q['id']}  MRR {metrics['mrr']:.3f}  nDCG@{DEFAULT_K} {metrics['ndcg_at_k']:.3f}  "
              f"P@5 {metrics['precision_at_5']:.2f}  hit@1 {int(metrics['hit_at_1'])}  "
              f"first_rel@{fr if fr else '-'}  ({metrics['n_relevant']}/{metrics['n_results']} rel)")

    agg = _aggregate(per_question)
    print("\n── Aggregate ──────────────────────────────────────")
    print(f"  MRR              {agg['mean_mrr']:.4f}")
    print(f"  nDCG@{DEFAULT_K}          {agg['mean_ndcg_at_k']:.4f}")
    print(f"  Precision@5      {agg['mean_precision_at_5']:.4f}")
    print(f"  hit@1 rate       {agg['hit_at_1_rate']:.4f}")
    return {"hybrid": hybrid, "n_results": N_RESULTS, "aggregate": agg, "questions": per_question}


def compare(path_a: str, path_b: str) -> None:
    a = json.loads(Path(path_a).read_text())
    b = json.loads(Path(path_b).read_text())
    ga, gb = a["aggregate"], b["aggregate"]
    label_a = "ON" if a.get("hybrid") else "OFF"
    label_b = "ON" if b.get("hybrid") else "OFF"
    print(f"Comparing  {path_a} (hybrid {label_a})  vs  {path_b} (hybrid {label_b})\n")
    print(f"  {'metric':<16}{label_a:>10}{label_b:>10}{'Δ':>10}")
    for key in ("mean_mrr", "mean_ndcg_at_k", "mean_precision_at_5", "hit_at_1_rate"):
        va, vb = ga[key], gb[key]
        print(f"  {key:<16}{va:>10.4f}{vb:>10.4f}{vb - va:>+10.4f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Rank-aware retrieval evaluation")
    parser.add_argument("--output", help="Write full results JSON to this path")
    parser.add_argument("--compare", nargs=2, metavar=("A", "B"),
                        help="Compare two saved result files and exit")
    args = parser.parse_args()

    if args.compare:
        compare(*args.compare)
        return

    result = run()
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"\nResults written → {args.output}")


if __name__ == "__main__":
    main()
