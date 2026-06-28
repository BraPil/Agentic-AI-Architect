"""
Unit tests for the AAA learning loop: harvester, seeder, and promotion gate.

No ChromaDB, no embedding model, no network — a fake collection stands in for the
store so the full regulated loop (harvest → quarantine → promote/reject/demote) is
exercised in milliseconds.
"""

from pathlib import Path

import pytest

from src.learning.harvester import (
    HarvestPipeline,
    LearningArtifact,
    parse_artifacts,
)
from src.learning.promotion import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    PromotionGate,
    TIER_EXPERIMENTAL,
    TIER_GROUNDED,
)
from src.learning.seeder import (
    build_persona_seed,
    build_seed_spec,
    default_personas,
)

_FIXTURE = Path(__file__).parent / "fixtures" / "oaa_cycle_sample.jsonl"


# ---------------------------------------------------------------------------
# Fake ChromaDB collection
# ---------------------------------------------------------------------------

class FakeCollection:
    """Minimal in-memory stand-in for a ChromaDB collection."""

    def __init__(self):
        self.docs: dict[str, str] = {}
        self.metas: dict[str, dict] = {}

    def add(self, ids, documents, metadatas):
        for i, _id in enumerate(ids):
            self.docs[_id] = documents[i]
            self.metas[_id] = dict(metadatas[i])

    def update(self, ids, documents=None, metadatas=None):
        for i, _id in enumerate(ids):
            if documents is not None:
                self.docs[_id] = documents[i]
            if metadatas is not None:
                self.metas[_id] = dict(metadatas[i])

    def delete(self, ids):
        for _id in ids:
            self.docs.pop(_id, None)
            self.metas.pop(_id, None)

    def get(self, ids=None, where=None, include=None):
        if ids is not None:
            sel = [i for i in ids if i in self.metas]
        elif where and "source_tier" in where:
            want = where["source_tier"]
            sel = [i for i, m in self.metas.items() if m.get("source_tier") == want]
        else:
            sel = list(self.metas.keys())
        return {
            "ids": sel,
            "documents": [self.docs.get(i, "") for i in sel],
            "metadatas": [self.metas.get(i, {}) for i in sel],
        }


# ---------------------------------------------------------------------------
# Harvester
# ---------------------------------------------------------------------------

class TestHarvester:
    def test_parse_real_oaa_shape(self):
        artifacts = parse_artifacts(_FIXTURE)
        assert len(artifacts) == 3
        a = artifacts[0]
        assert a.artifact_id == "la-kr_001"
        assert a.confidence == 0.82
        assert "knowledge base" in a.topics

    def test_harvest_sets_experimental_tier(self):
        col = FakeCollection()
        result = HarvestPipeline(col).run(_FIXTURE)
        assert result.added == 3
        assert result.failed == 0
        for meta in col.metas.values():
            assert meta["source_tier"] == TIER_EXPERIMENTAL
            assert meta["post_type"] == "learning_artifact"

    def test_harvest_sanitizes_injection(self):
        col = FakeCollection()
        HarvestPipeline(col).run(_FIXTURE)
        # kr_003 contains "Ignore all previous instructions" — must be sanitized.
        doc = col.docs["la-kr_003"]
        assert "Ignore all previous instructions" not in doc

    def test_harvest_idempotent(self):
        col = FakeCollection()
        HarvestPipeline(col).run(_FIXTURE)
        second = HarvestPipeline(col).run(_FIXTURE)
        assert second.added == 0
        assert second.skipped == 3

    def test_missing_file_is_error_not_crash(self, tmp_path):
        result = HarvestPipeline(FakeCollection()).run(tmp_path / "nope.jsonl")
        assert result.added == 0
        assert result.errors

    def test_confidence_stored_as_float(self):
        col = FakeCollection()
        HarvestPipeline(col).run(_FIXTURE)
        assert isinstance(col.metas["la-kr_001"]["confidence"], float)


# ---------------------------------------------------------------------------
# Promotion gate
# ---------------------------------------------------------------------------

class TestPromotionGate:
    def _harvested_gate(self, tmp_path):
        col = FakeCollection()
        HarvestPipeline(col).run(_FIXTURE)
        gate = PromotionGate(col, audit_log=tmp_path / "audit.jsonl")
        return col, gate

    def test_list_candidates_sorted_desc(self, tmp_path):
        _, gate = self._harvested_gate(tmp_path)
        cands = gate.list_candidates()
        assert len(cands) == 3
        confs = [c.confidence for c in cands]
        assert confs == sorted(confs, reverse=True)

    def test_list_candidates_min_confidence(self, tmp_path):
        _, gate = self._harvested_gate(tmp_path)
        # default threshold 0.7 → only kr_001 (0.82) and kr_003 (0.71)
        cands = gate.list_candidates(min_confidence=DEFAULT_CONFIDENCE_THRESHOLD)
        ids = {c.artifact_id for c in cands}
        assert ids == {"la-kr_001", "la-kr_003"}

    def test_promote_high_confidence_succeeds(self, tmp_path):
        col, gate = self._harvested_gate(tmp_path)
        r = gate.promote("la-kr_001", approved_by="brandt")
        assert r.ok
        assert r.to_tier == TIER_GROUNDED
        assert col.metas["la-kr_001"]["source_tier"] == TIER_GROUNDED
        assert col.metas["la-kr_001"]["promoted_by"] == "brandt"

    def test_promote_below_threshold_blocked(self, tmp_path):
        col, gate = self._harvested_gate(tmp_path)
        r = gate.promote("la-kr_002", approved_by="brandt")  # confidence 0.55
        assert not r.ok
        assert "below threshold" in r.reason
        assert col.metas["la-kr_002"]["source_tier"] == TIER_EXPERIMENTAL  # unchanged

    def test_promote_missing_artifact(self, tmp_path):
        _, gate = self._harvested_gate(tmp_path)
        r = gate.promote("la-nonexistent", approved_by="brandt")
        assert not r.ok
        assert "not found" in r.reason

    def test_cannot_promote_already_grounded(self, tmp_path):
        _, gate = self._harvested_gate(tmp_path)
        gate.promote("la-kr_001", "brandt")
        r = gate.promote("la-kr_001", "brandt")  # already grounded
        assert not r.ok
        assert "experimental" in r.reason

    def test_reject_removes_artifact(self, tmp_path):
        col, gate = self._harvested_gate(tmp_path)
        r = gate.reject("la-kr_002", rejected_by="brandt", reason="unverified")
        assert r.ok
        assert "la-kr_002" not in col.metas

    def test_demote_reverses_promotion(self, tmp_path):
        col, gate = self._harvested_gate(tmp_path)
        gate.promote("la-kr_001", "brandt")
        r = gate.demote("la-kr_001", demoted_by="brandt", reason="contradicted")
        assert r.ok
        assert col.metas["la-kr_001"]["source_tier"] == TIER_EXPERIMENTAL

    def test_cannot_demote_experimental(self, tmp_path):
        _, gate = self._harvested_gate(tmp_path)
        r = gate.demote("la-kr_002", demoted_by="brandt")
        assert not r.ok

    def test_audit_log_written(self, tmp_path):
        _, gate = self._harvested_gate(tmp_path)
        gate.promote("la-kr_001", "brandt")
        audit = tmp_path / "audit.jsonl"
        assert audit.exists()
        assert "promote" in audit.read_text()

    def test_custom_threshold(self, tmp_path):
        col = FakeCollection()
        HarvestPipeline(col).run(_FIXTURE)
        gate = PromotionGate(col, confidence_threshold=0.5, audit_log=tmp_path / "a.jsonl")
        r = gate.promote("la-kr_002", "brandt")  # 0.55 >= 0.5
        assert r.ok


# ---------------------------------------------------------------------------
# Seeder (AAA -> OAA influence)
# ---------------------------------------------------------------------------

class TestSeeder:
    def test_curated_persona_has_genome_and_role(self):
        seed = build_persona_seed("andrej-karpathy")
        assert seed.suggested_role == "researcher"
        assert seed.genome["curiosity"] >= 0.9
        assert "compassion" in seed.genome

    def test_unknown_persona_gets_generic_genome(self):
        seed = build_persona_seed("some-new-person")
        assert seed.genome["compassion"] > 0.5  # OAA doctrine: compassion biased up
        assert seed.suggested_role == "researcher"

    def test_build_seed_spec_structure(self):
        spec = build_seed_spec("How should we design agent memory?")
        assert spec["niche"]["description"] == "How should we design agent memory?"
        assert spec["niche"]["posted_by"] == "agentic-ai-architect"
        assert len(spec["agents"]) == len(default_personas())

    def test_seed_spec_custom_personas(self):
        spec = build_seed_spec("Q?", persona_ids=["andrej-karpathy", "lilian-weng"])
        assert len(spec["agents"]) == 2

    def test_compassion_biased_above_half_for_all_core(self):
        for pid in default_personas():
            assert build_persona_seed(pid).genome["compassion"] > 0.5
