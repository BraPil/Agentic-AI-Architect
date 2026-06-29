"""Tests for the P6 recommendation-outcome capture store.

No network, no API keys, no real ChromaDB — the store is pure JSONL over tmp_path.
"""

import json

import pytest

from src.learning.outcomes import (
    MULT_MAX,
    MULT_MIN,
    OutcomeRecord,
    RecommendationOutcomeStore,
    compute_recommendation_id,
)


@pytest.fixture
def store(tmp_path):
    return RecommendationOutcomeStore(ledger_path=tmp_path / "outcomes.jsonl")


# ---------------------------------------------------------------------------
# ID
# ---------------------------------------------------------------------------

def test_recommendation_id_is_stable_and_prefixed():
    a = compute_recommendation_id("design agent memory", "2026-06-29T00:00:00+00:00")
    b = compute_recommendation_id("design agent memory", "2026-06-29T00:00:00+00:00")
    assert a == b
    assert a.startswith("rec-")


def test_recommendation_id_varies_by_timestamp():
    a = compute_recommendation_id("q", "2026-06-29T00:00:00+00:00")
    b = compute_recommendation_id("q", "2026-06-29T00:00:01+00:00")
    assert a != b


# ---------------------------------------------------------------------------
# Record + retrieve
# ---------------------------------------------------------------------------

def test_record_recommendation_then_outcome_roundtrip(store):
    store.record_recommendation(
        "rec-1", "How to design memory?",
        personas_cited=["lilian-weng"], tools=["chromadb"], confidence="high",
    )
    rec = store.get("rec-1")
    assert rec is not None and not rec.has_outcome

    out = store.record_outcome("rec-1", adopted=True, worked=True,
                               outcome_score=0.9, notes="shipped", recorded_by="brandt")
    assert out.has_outcome and out.success
    assert out.adopted is True and out.worked is True
    assert out.outcome_score == 0.9
    assert store.get("rec-1").success is True


def test_outcome_for_unknown_id_raises(store):
    with pytest.raises(ValueError):
        store.record_outcome("rec-missing", adopted=True)


def test_outcome_score_is_clamped(store):
    store.record_recommendation("rec-2", "q")
    assert store.record_outcome("rec-2", adopted=True, outcome_score=5.0).outcome_score == 1.0
    assert store.record_outcome("rec-2", adopted=True, outcome_score=-3.0).outcome_score == 0.0


def test_last_outcome_wins(store):
    store.record_recommendation("rec-3", "q")
    store.record_outcome("rec-3", adopted=True, worked=True)
    store.record_outcome("rec-3", adopted=True, worked=False, notes="regressed later")
    rec = store.get("rec-3")
    assert rec.worked is False and rec.notes == "regressed later"
    assert rec.success is False


def test_adopted_but_not_worked_is_not_success(store):
    store.record_recommendation("rec-4", "q", personas_cited=["p"])
    rec = store.record_outcome("rec-4", adopted=True, worked=False)
    assert rec.adopted is True and rec.success is False


# ---------------------------------------------------------------------------
# Pending + aggregate
# ---------------------------------------------------------------------------

def test_pending_lists_only_outcomeless_recommendations(store):
    store.record_recommendation("rec-a", "qa")
    store.record_recommendation("rec-b", "qb")
    store.record_outcome("rec-a", adopted=True, worked=True)
    pending_ids = {r.recommendation_id for r in store.pending()}
    assert pending_ids == {"rec-b"}


def test_aggregate_rates_and_persona_signal(store):
    # Two recs citing weng; one works, one doesn't. One rec citing huyen that works.
    store.record_recommendation("r1", "q1", personas_cited=["weng"], tools=["faiss"])
    store.record_recommendation("r2", "q2", personas_cited=["weng"])
    store.record_recommendation("r3", "q3", personas_cited=["huyen"])
    store.record_outcome("r1", adopted=True, worked=True, outcome_score=0.8)
    store.record_outcome("r2", adopted=True, worked=False, outcome_score=0.2)
    store.record_outcome("r3", adopted=True, worked=True)  # huyen: a clean success

    agg = store.aggregate()
    assert agg["total_recommendations"] == 3
    assert agg["outcomes_recorded"] == 3
    assert agg["pending_outcomes"] == 0
    assert agg["adoption_rate"] == 1.0
    assert agg["success_rate"] == round(2 / 3, 4)
    assert agg["mean_outcome_score"] == round((0.8 + 0.2) / 2, 4)  # r3 has no score

    weng = agg["persona_signal"]["weng"]
    assert weng["recommended"] == 2 and weng["worked"] == 1
    assert weng["success_rate"] == 0.5
    # weng's multiplier (1 of 2) should sit below huyen's (1 of 1).
    huyen = agg["persona_signal"]["huyen"]
    assert MULT_MIN <= weng["weight_multiplier"] <= MULT_MAX
    assert huyen["weight_multiplier"] > weng["weight_multiplier"]


def test_aggregate_empty_store_is_safe(store):
    agg = store.aggregate()
    assert agg["outcomes_recorded"] == 0
    assert agg["adoption_rate"] is None
    assert agg["persona_signal"] == {}


def test_multiplier_neutral_with_no_data():
    # Laplace prior: zero trials → neutral midpoint of the band.
    store = RecommendationOutcomeStore(ledger_path="/dev/null")
    assert store._laplace_multiplier(0, 0) == round(MULT_MIN + (MULT_MAX - MULT_MIN) * 0.5, 4)


def test_malformed_ledger_lines_are_skipped(tmp_path):
    ledger = tmp_path / "outcomes.jsonl"
    ledger.write_text(
        json.dumps({"event": "recommendation", "recommendation_id": "ok", "ts": "t"}) + "\n"
        + "this is not json\n",
        encoding="utf-8",
    )
    store = RecommendationOutcomeStore(ledger_path=ledger)
    assert store.get("ok") is not None


def test_outcome_record_to_dict_shape():
    rec = OutcomeRecord(recommendation_id="x")
    d = rec.to_dict()
    assert d["recommendation_id"] == "x"
    assert d["has_outcome"] is False
    assert d["success"] is None


# ---------------------------------------------------------------------------
# MCP-server integration glue (recommendation event stamping)
# ---------------------------------------------------------------------------

def test_record_recommendation_event_stamps_and_logs(tmp_path, monkeypatch):
    import src.api.mcp_server as srv

    ledger = tmp_path / "outcomes.jsonl"
    monkeypatch.setattr(srv, "_OUTCOME_LEDGER", ledger)
    synthesis = {"personas_cited": ["weng"], "relevant_tools": ["chromadb"],
                 "confidence": "high"}

    rec_id = srv._record_recommendation_event("design memory", "2026-06-29T00:00:00+00:00",
                                              synthesis)
    assert rec_id.startswith("rec-")

    stored = RecommendationOutcomeStore(ledger).get(rec_id)
    assert stored is not None
    assert stored.personas_cited == ["weng"]
    assert stored.tools == ["chromadb"]
    assert stored.confidence == "high"
    # And an outcome can be tied back to the stamped id.
    out = RecommendationOutcomeStore(ledger).record_outcome(rec_id, adopted=True, worked=True)
    assert out.success is True
