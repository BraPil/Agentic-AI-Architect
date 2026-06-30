"""
Tests for rank-aware retrieval metrics (src/pipeline/ranking_metrics.py).

Pure-function tests — no store, no network. They lock in the property that makes this
instrument worth building: it *rewards* a better ordering (unlike the vector-biased
avg-relevance metric it replaces for ranking work).
"""

import math

from src.pipeline.ranking_metrics import (
    dcg,
    grade_result,
    hit_at_k,
    is_relevant,
    ndcg_at_k,
    precision_at_k,
    reciprocal_rank,
    score_ranking,
)


# ---------------------------------------------------------------------------
# Relevance oracle
# ---------------------------------------------------------------------------

class TestGradeResult:
    def test_author_match(self):
        q = {"must_cite_author": "Cole Medin", "expected_tools": [], "expected_topics": []}
        assert grade_result({"author": "Cole Medin"}, q) == 1

    def test_three_signals_grade_3(self):
        q = {"must_cite_author": "Cole Medin", "expected_tools": ["Claude Code"],
             "expected_topics": ["agentic coding"]}
        r = {"author": "Cole Medin", "mentioned_tools": ["Claude Code"],
             "topics": ["agentic coding"], "snippet": ""}
        assert grade_result(r, q) == 3

    def test_topic_in_snippet_counts(self):
        q = {"must_cite_author": None, "expected_tools": [], "expected_topics": ["memory"]}
        r = {"author": "x", "mentioned_tools": [], "topics": [],
             "snippet": "a discussion of agent MEMORY design"}
        assert grade_result(r, q) == 1

    def test_no_signals_grade_0(self):
        q = {"must_cite_author": "Karpathy", "expected_tools": ["vLLM"],
             "expected_topics": ["rlhf"]}
        r = {"author": "Someone Else", "mentioned_tools": ["LangChain"],
             "topics": ["agents"], "snippet": "unrelated"}
        assert grade_result(r, q) == 0
        assert not is_relevant(r, q)

    def test_unspecified_signals_cannot_contribute(self):
        q = {"must_cite_author": None, "expected_tools": [], "expected_topics": ["rag"]}
        r = {"author": "anyone", "mentioned_tools": ["anything"], "topics": ["rag"], "snippet": ""}
        assert grade_result(r, q) == 1  # only the topic signal is available


# ---------------------------------------------------------------------------
# Rank-aware metrics
# ---------------------------------------------------------------------------

class TestReciprocalRank:
    def test_first_relevant_at_rank_1(self):
        assert reciprocal_rank([True, False, False]) == 1.0

    def test_first_relevant_at_rank_3(self):
        assert reciprocal_rank([False, False, True]) == 1 / 3

    def test_none_relevant(self):
        assert reciprocal_rank([False, False]) == 0.0


class TestPrecisionAtK:
    def test_half_relevant(self):
        assert precision_at_k([True, False, True, False], 4) == 0.5

    def test_denominator_is_count_present(self):
        # only 2 results, k=5 → divide by 2, not 5
        assert precision_at_k([True, True], 5) == 1.0


class TestHitAtK:
    def test_hit_at_1(self):
        assert hit_at_k([True, False], 1)
        assert not hit_at_k([False, True], 1)


class TestNDCG:
    def test_perfect_order_is_1(self):
        assert ndcg_at_k([3, 2, 1, 0], 10) == 1.0

    def test_reversed_order_is_worse(self):
        good = ndcg_at_k([3, 2, 1], 10)
        bad = ndcg_at_k([1, 2, 3], 10)
        assert good == 1.0
        assert bad < good

    def test_rewards_promoting_relevant_doc(self):
        """The headline property: moving a relevant doc up raises nDCG."""
        before = ndcg_at_k([0, 0, 2], 10)   # relevant doc at rank 3
        after = ndcg_at_k([2, 0, 0], 10)    # same doc promoted to rank 1
        assert after > before

    def test_all_zero_is_zero(self):
        assert ndcg_at_k([0, 0, 0], 10) == 0.0

    def test_dcg_matches_manual(self):
        # gains [3, 0] → (2^3-1)/log2(2) + 0 = 7/1 = 7
        assert math.isclose(dcg([3, 0]), 7.0)


class TestScoreRanking:
    def test_full_metric_bundle(self):
        q = {"must_cite_author": "Cole Medin", "expected_tools": ["Claude Code"],
             "expected_topics": ["agentic coding"]}
        results = [
            {"author": "Cole Medin", "mentioned_tools": ["Claude Code"],
             "topics": ["agentic coding"], "snippet": ""},          # grade 3
            {"author": "Other", "mentioned_tools": [], "topics": ["x"], "snippet": "y"},  # 0
        ]
        m = score_ranking(results, q, k=10)
        assert m["hit_at_1"] is True
        assert m["mrr"] == 1.0
        assert m["ndcg_at_k"] == 1.0
        assert m["n_relevant"] == 1
        assert m["first_relevant_rank"] == 1
