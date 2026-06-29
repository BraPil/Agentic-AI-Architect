"""Tests for P6 outcome capture slice 2: outcome-driven retrieval re-ranking.

Pure functions over in-memory dicts — no network, no API keys, no ChromaDB. One
integration test seeds a real (tmp_path) RecommendationOutcomeStore to prove the
end-to-end signal → re-rank lift deterministically, since the live eval harness
scores a different retrieval rail and cannot measure this one.
"""

import pytest

from src.learning.outcome_weighting import (
    MIN_EVIDENCE_DEFAULT,
    NEUTRAL,
    _normalize,
    gated_multipliers,
    hit_multiplier,
    rerank_by_outcomes,
)
from src.learning.outcomes import MULT_MAX, MULT_MIN, RecommendationOutcomeStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hit(post_id: str, score: float, author: str = "", persona_id: str = "",
         tools: str = "") -> dict:
    return {
        "post_id": post_id,
        "document": f"doc {post_id}",
        "score": score,
        "metadata": {"author": author, "persona_id": persona_id, "mentioned_tools": tools},
    }


def _signal(recommended: int, multiplier: float) -> dict:
    return {"recommended": recommended, "worked": recommended, "success_rate": 1.0,
            "weight_multiplier": multiplier}


# ---------------------------------------------------------------------------
# Normalization / matching
# ---------------------------------------------------------------------------

def test_normalize_collapses_display_name_and_slug_to_same_key():
    assert _normalize("Andrej Karpathy") == _normalize("andrej-karpathy")
    assert _normalize("Andrej Karpathy") == "andrejkarpathy"
    assert _normalize("") == ""
    assert _normalize(None) == ""


# ---------------------------------------------------------------------------
# Minimum-evidence gate
# ---------------------------------------------------------------------------

def test_gate_excludes_entities_below_threshold():
    signal = {
        "Andrej Karpathy": _signal(MIN_EVIDENCE_DEFAULT, 1.4),       # exactly at gate
        "Lilian Weng": _signal(MIN_EVIDENCE_DEFAULT - 1, 1.4),       # one short
    }
    gated = gated_multipliers(signal, MIN_EVIDENCE_DEFAULT)
    assert "andrejkarpathy" in gated
    assert "lilianweng" not in gated


def test_gate_handles_empty_and_malformed_sections():
    assert gated_multipliers(None, MIN_EVIDENCE_DEFAULT) == {}
    assert gated_multipliers({}, MIN_EVIDENCE_DEFAULT) == {}
    assert gated_multipliers({"x": "not-a-dict"}, MIN_EVIDENCE_DEFAULT) == {}
    assert gated_multipliers({"x": {"recommended": 9}}, MIN_EVIDENCE_DEFAULT) == {}  # no mult


# ---------------------------------------------------------------------------
# hit_multiplier
# ---------------------------------------------------------------------------

def test_hit_multiplier_is_neutral_with_no_matching_entity():
    h = _hit("p1", 0.8, author="Nobody Special")
    assert hit_multiplier(h, {"andrejkarpathy": 1.4}, {}) == NEUTRAL


def test_hit_multiplier_matches_author_then_falls_back_to_slug():
    pm = {"andrejkarpathy": 1.4}
    by_author = _hit("p1", 0.8, author="Andrej Karpathy")
    by_slug = _hit("p2", 0.8, persona_id="andrej-karpathy")
    assert hit_multiplier(by_author, pm, {}) == 1.4
    assert hit_multiplier(by_slug, pm, {}) == 1.4


def test_hit_multiplier_averages_persona_and_tools_and_stays_bounded():
    pm = {"andrejkarpathy": 1.5}
    tm = {"pytorch": 0.5}
    h = _hit("p1", 0.8, author="Andrej Karpathy", tools="PyTorch, Python")
    # mean(1.5, 0.5) = 1.0, and the result never escapes the per-entity bounds.
    mult = hit_multiplier(h, pm, tm)
    assert mult == pytest.approx(1.0)
    assert MULT_MIN <= mult <= MULT_MAX


def test_hit_multiplier_counts_each_matched_tool_once():
    tm = {"pytorch": 1.4}
    h = _hit("p1", 0.8, tools="PyTorch, pytorch, py-torch")
    # All three normalize to the same key — counted once, so mult == the tool mult.
    assert hit_multiplier(h, {}, tm) == pytest.approx(1.4)


# ---------------------------------------------------------------------------
# rerank_by_outcomes
# ---------------------------------------------------------------------------

def test_rerank_is_exact_noop_when_nothing_clears_gate():
    hits = [_hit("a", 0.9, author="X"), _hit("b", 0.7, author="Y")]
    below = {"X": _signal(MIN_EVIDENCE_DEFAULT - 1, 1.5)}
    out = rerank_by_outcomes(hits, below, {}, MIN_EVIDENCE_DEFAULT)
    assert [h["post_id"] for h in out] == ["a", "b"]
    # No-op path leaves hits untouched (no injected ranking fields).
    assert "ranking_score" not in out[0]


def test_rerank_promotes_proven_source_above_higher_relevance_hit():
    # 'b' is less semantically relevant but its author is proven; the multiplier
    # should lift it above 'a'.
    hits = [_hit("a", 0.80, author="Unproven"), _hit("b", 0.70, author="Proven")]
    signal = {"Proven": _signal(MIN_EVIDENCE_DEFAULT, MULT_MAX)}  # 0.70 * 1.5 = 1.05 > 0.80
    out = rerank_by_outcomes(hits, signal, {}, MIN_EVIDENCE_DEFAULT)
    assert [h["post_id"] for h in out] == ["b", "a"]
    assert out[0]["outcome_multiplier"] == MULT_MAX
    # Original semantic score is preserved untouched alongside ranking_score.
    assert out[0]["score"] == 0.70
    assert out[0]["ranking_score"] == pytest.approx(0.70 * MULT_MAX)


def test_rerank_demotes_failed_source():
    hits = [_hit("a", 0.80, author="Failed"), _hit("b", 0.75, author="Neutral")]
    signal = {"Failed": _signal(MIN_EVIDENCE_DEFAULT, MULT_MIN)}  # 0.80 * 0.5 = 0.40 < 0.75
    out = rerank_by_outcomes(hits, signal, {}, MIN_EVIDENCE_DEFAULT)
    assert [h["post_id"] for h in out] == ["b", "a"]


def test_rerank_is_stable_for_equal_ranking_scores():
    # Equal base scores, no gated signal applies → input (relevance) order kept.
    hits = [_hit("a", 0.5, author="P"), _hit("b", 0.5, author="Q")]
    signal = {"R": _signal(MIN_EVIDENCE_DEFAULT, MULT_MAX)}  # matches neither hit
    out = rerank_by_outcomes(hits, signal, {}, MIN_EVIDENCE_DEFAULT)
    assert [h["post_id"] for h in out] == ["a", "b"]


# ---------------------------------------------------------------------------
# End-to-end: real store → aggregate → rerank (the "prove lift" demonstration)
# ---------------------------------------------------------------------------

def test_seeded_outcomes_lift_proven_persona_to_top(tmp_path):
    """Deterministic before/after: with 5 adopted-and-worked outcomes citing
    'Andrej Karpathy', his lower-relevance hit moves from rank 3 to rank 1."""
    store = RecommendationOutcomeStore(ledger_path=tmp_path / "outcomes.jsonl")
    for i in range(MIN_EVIDENCE_DEFAULT):
        rid = f"rec-{i}"
        store.record_recommendation(rid, f"problem {i}", personas_cited=["Andrej Karpathy"])
        store.record_outcome(rid, adopted=True, worked=True)

    agg = store.aggregate()
    karpathy = agg["persona_signal"]["Andrej Karpathy"]
    assert karpathy["recommended"] == MIN_EVIDENCE_DEFAULT
    assert karpathy["weight_multiplier"] > NEUTRAL  # 5/5 success pushes above neutral

    hits = [
        _hit("other1", 0.90, author="Someone Else"),
        _hit("other2", 0.85, author="Another Person"),
        _hit("karpathy", 0.80, author="Andrej Karpathy"),
    ]
    before = [h["post_id"] for h in hits]
    after = [h["post_id"] for h in rerank_by_outcomes(
        hits, agg["persona_signal"], agg["tool_signal"], MIN_EVIDENCE_DEFAULT)]

    assert before[-1] == "karpathy"          # was last by raw relevance
    assert after[0] == "karpathy"            # now first after outcome weighting
