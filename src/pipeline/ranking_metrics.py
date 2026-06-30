"""
Rank-aware retrieval metrics — measure *ordering* quality, not just pass/fail presence.

The existing eval harness (`scripts/run_eval.py`) is structurally blind to ranking: its
pass-rate is saturated and its "avg relevance" is the mean top-1 *vector* similarity, which
can only fall under any reorder (discovery-log 2026-06-30). So it can detect a catastrophic
regression but cannot tell a better ordering from a worse one — which makes it useless for
judging a reranker (hybrid, cross-encoder, query expansion).

This module supplies the missing instrument: MRR, nDCG@k, precision@k, hit@1 — metrics that
*reward* pulling relevant documents higher.

The relevance oracle is **label-free**: it derives a graded relevance for each returned result
from fields the ground truth already carries (`must_cite_author`, `expected_tools`,
`expected_topics`). A result earns +1 per matched signal (author / tool / topic), giving a
grade in 0..3. No manual per-document judgments are required, so the instrument exists today
and stays in sync with the ground-truth set.

All functions are pure (stdlib only) and operate on already-ranked result lists.
"""

import math

# Default cutoff for @k metrics.
DEFAULT_K = 10


# ---------------------------------------------------------------------------
# Relevance oracle (label-free, from existing ground-truth fields)
# ---------------------------------------------------------------------------

def grade_result(result: dict, question: dict) -> int:
    """
    Graded relevance of one search result against a ground-truth question, in 0..3.

    +1 for each matched signal the question specifies:
      - author: `must_cite_author` appears in the result's author
      - tool:   any `expected_tools` entry appears in the result's `mentioned_tools`
      - topic:  any `expected_topics` entry appears in the result's topics or snippet

    Signals the question does not specify (empty/None) cannot contribute — so a topic-only
    question maxes at grade 1, an author+tool+topic question at grade 3. Relevance is graded
    by *how many* on-target signals a result carries, which is what nDCG needs.
    """
    grade = 0

    author = (result.get("author") or "").lower()
    must_cite = (question.get("must_cite_author") or "").lower()
    if must_cite and (must_cite in author or author in must_cite) and author:
        grade += 1

    expected_tools = [t.lower() for t in (question.get("expected_tools") or [])]
    if expected_tools:
        result_tools = " ".join(t.lower() for t in (result.get("mentioned_tools") or []))
        if any(t in result_tools for t in expected_tools):
            grade += 1

    expected_topics = [t.lower() for t in (question.get("expected_topics") or [])]
    if expected_topics:
        haystack = (
            " ".join(result.get("topics") or []) + " " + (result.get("snippet") or "")
        ).lower()
        if any(t in haystack for t in expected_topics):
            grade += 1

    return grade


def is_relevant(result: dict, question: dict) -> bool:
    """A result is relevant if it carries at least one on-target signal (grade >= 1)."""
    return grade_result(result, question) >= 1


def resolve_gains(results: list[dict], question: dict,
                  judgments: dict | None = None) -> list[int]:
    """
    Graded relevance for each result, preferring **LLM-judged** grades when available.

    `judgments` maps question_id → {post_id: grade 0..3}. For a result whose post_id has a
    judged grade, that grade is used; otherwise we fall back to the label-free heuristic
    `grade_result`. Judged grades are finer (they distinguish "directly answers" from
    "tangential" rather than counting matched signal types), which is what de-saturates the
    eval enough for nDCG to discriminate between rankers.
    """
    q_judg = (judgments or {}).get(question.get("id"), {}) if judgments else {}
    gains = []
    for r in results:
        pid = r.get("post_id")
        if pid in q_judg:
            gains.append(int(q_judg[pid]))
        else:
            gains.append(grade_result(r, question))
    return gains


# ---------------------------------------------------------------------------
# Rank-aware metrics
# ---------------------------------------------------------------------------

def reciprocal_rank(relevances: list[bool]) -> float:
    """1 / (rank of the first relevant result); 0.0 if none are relevant."""
    for i, rel in enumerate(relevances):
        if rel:
            return 1.0 / (i + 1)
    return 0.0


def precision_at_k(relevances: list[bool], k: int = DEFAULT_K) -> float:
    """Fraction of the top-k results that are relevant (denominator is the count present, ≤ k)."""
    if not relevances or k <= 0:
        return 0.0
    top = relevances[:k]
    return sum(1 for r in top if r) / len(top)


def hit_at_k(relevances: list[bool], k: int = 1) -> bool:
    """True if any of the top-k results is relevant."""
    return any(relevances[:k])


def dcg(gains: list[float]) -> float:
    """Discounted cumulative gain with the exponential gain (2^g - 1), standard IR form."""
    return sum((2 ** g - 1) / math.log2(rank + 2) for rank, g in enumerate(gains))


def ndcg_at_k(gains: list[float], k: int = DEFAULT_K) -> float:
    """
    Normalized DCG at cutoff k. `gains` are graded relevances in *ranked* order. Normalized
    against the ideal ordering (gains sorted descending). Returns 0.0 when no gain exists.
    """
    if not gains or k <= 0:
        return 0.0
    actual = dcg(gains[:k])
    ideal = dcg(sorted(gains, reverse=True)[:k])
    return (actual / ideal) if ideal > 0 else 0.0


def score_ranking(results: list[dict], question: dict, k: int = DEFAULT_K,
                  judgments: dict | None = None) -> dict:
    """
    Compute all rank-aware metrics for one question's ranked result list.

    When `judgments` (question_id → {post_id: grade}) is supplied, LLM-judged graded relevance
    is used in preference to the heuristic oracle. Returns a dict with: mrr, ndcg@k, p@5, hit@1,
    n_relevant, n_results, first_relevant_rank, graded (True if any judged grade was used).
    """
    gains = resolve_gains(results, question, judgments)
    rels = [g >= 1 for g in gains]
    q_judg = (judgments or {}).get(question.get("id"), {}) if judgments else {}
    used_judged = any(r.get("post_id") in q_judg for r in results)
    first_rel = next((i + 1 for i, r in enumerate(rels) if r), None)
    return {
        "mrr": round(reciprocal_rank(rels), 4),
        "ndcg_at_k": round(ndcg_at_k(gains, k), 4),
        "precision_at_5": round(precision_at_k(rels, 5), 4),
        "hit_at_1": hit_at_k(rels, 1),
        "n_relevant": sum(rels),
        "n_results": len(results),
        "first_relevant_rank": first_rel,
        "graded": used_judged,
    }
