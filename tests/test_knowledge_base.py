"""
Unit tests for the KnowledgeBase and KnowledgeEntry classes.
"""

import tempfile
from pathlib import Path

import pytest

from src.knowledge.knowledge_base import KnowledgeBase, KnowledgeEntry
from src.knowledge.knowledge_base import EvaluationRunRecord


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def kb(tmp_path):
    """Create a fresh KnowledgeBase backed by a temp SQLite file."""
    db_path = str(tmp_path / "test_kb.db")
    kb = KnowledgeBase(db_path=db_path)
    kb.initialize()
    yield kb
    kb.close()


def _make_entry(**kwargs) -> KnowledgeEntry:
    defaults = {
        "title": "Test Entry",
        "content": "This is test content about AI architectures.",
        "namespace": "general",
        "content_type": "blog",
        "source_url": "https://example.com",
        "source_name": "Example Blog",
        "confidence": 0.8,
    }
    defaults.update(kwargs)
    return KnowledgeEntry(**defaults)


# ---------------------------------------------------------------------------
# KnowledgeEntry tests
# ---------------------------------------------------------------------------

class TestKnowledgeEntry:
    def test_entry_has_auto_generated_id(self):
        e1 = KnowledgeEntry(title="A", content="B")
        e2 = KnowledgeEntry(title="A", content="B")
        assert e1.entry_id != e2.entry_id

    def test_to_dict_contains_all_fields(self):
        entry = _make_entry()
        d = entry.to_dict()
        for key in ("entry_id", "title", "content", "namespace", "content_type",
                    "source_url", "source_name", "confidence", "created_at", "updated_at"):
            assert key in d, f"Missing key: {key}"

    def test_from_finding_creates_entry(self):
        finding = {
            "title": "FAISS Overview",
            "summary": "FAISS is fast similarity search",
            "namespace": "tools",
            "content_type": "blog",
            "source_url": "https://faiss.ai",
            "source_name": "FAISS Docs",
            "confidence": 0.9,
            "concepts": ["Similarity Search"],
            "tools_mentioned": ["faiss"],
            "people_mentioned": [],
        }
        entry = KnowledgeEntry.from_finding(finding)
        assert entry.title == "FAISS Overview"
        assert entry.namespace == "tools"
        assert entry.confidence == 0.9
        assert "faiss" in entry.metadata.get("tools_mentioned", [])

    def test_from_finding_handles_missing_fields(self):
        entry = KnowledgeEntry.from_finding({"title": "Minimal"})
        assert entry.title == "Minimal"
        assert entry.namespace == "general"


# ---------------------------------------------------------------------------
# KnowledgeBase CRUD tests
# ---------------------------------------------------------------------------

class TestKnowledgeBaseCRUD:
    def test_store_and_retrieve(self, kb):
        entry = _make_entry(title="Stored Entry")
        entry_id = kb.store(entry)
        retrieved = kb.get(entry_id)
        assert retrieved is not None
        assert retrieved.title == "Stored Entry"

    def test_get_nonexistent_returns_none(self, kb):
        assert kb.get("nonexistent-id") is None

    def test_delete_existing(self, kb):
        entry = _make_entry()
        entry_id = kb.store(entry)
        assert kb.delete(entry_id) is True
        assert kb.get(entry_id) is None

    def test_delete_nonexistent_returns_false(self, kb):
        assert kb.delete("fake-id") is False

    def test_store_many(self, kb):
        entries = [_make_entry(title=f"Entry {i}") for i in range(5)]
        count = kb.store_many(entries)
        assert count == 5
        assert kb.count() == 5

    def test_count_total(self, kb):
        assert kb.count() == 0
        kb.store(_make_entry())
        kb.store(_make_entry())
        assert kb.count() == 2

    def test_count_by_namespace(self, kb):
        kb.store(_make_entry(namespace="tools"))
        kb.store(_make_entry(namespace="tools"))
        kb.store(_make_entry(namespace="frameworks"))
        assert kb.count(namespace="tools") == 2
        assert kb.count(namespace="frameworks") == 1

    def test_store_overwrites_on_same_id(self, kb):
        entry = _make_entry(title="Original")
        kb.store(entry)
        entry.title = "Updated"
        kb.store(entry)
        retrieved = kb.get(entry.entry_id)
        assert retrieved is not None
        assert retrieved.title == "Updated"
        assert kb.count() == 1  # Still only 1 entry


# ---------------------------------------------------------------------------
# KnowledgeBase search tests
# ---------------------------------------------------------------------------

class TestKnowledgeBaseSearch:
    def _populate(self, kb):
        entries = [
            _make_entry(title="FAISS Vector Search", content="FAISS enables fast similarity search", namespace="tools", content_type="docs"),
            _make_entry(title="RAG Architecture", content="Retrieval Augmented Generation patterns", namespace="frameworks", content_type="blog"),
            _make_entry(title="GPT-4 Overview", content="GPT-4 is a large language model", namespace="tools", content_type="blog"),
            _make_entry(title="LangGraph Guide", content="LangGraph provides stateful agent orchestration", namespace="tools", confidence=0.95),
            _make_entry(title="XGBoost Tutorial", content="XGBoost for tabular data classification", namespace="frameworks", confidence=0.6),
        ]
        kb.store_many(entries)
        return entries

    def test_search_by_keyword(self, kb):
        self._populate(kb)
        results = kb.search(query="FAISS")
        assert len(results) >= 1
        assert any("FAISS" in r.title for r in results)

    def test_search_case_insensitive(self, kb):
        self._populate(kb)
        results_upper = kb.search(query="FAISS")
        results_lower = kb.search(query="faiss")
        # Both should find the FAISS entry
        assert len(results_upper) == len(results_lower)

    def test_search_matches_multi_term_partial_query(self, kb):
        self._populate(kb)
        results = kb.search(query="LangGraph orchestration")
        assert any("LangGraph" in result.title for result in results)

    def test_search_by_namespace(self, kb):
        self._populate(kb)
        results = kb.search(namespace="frameworks")
        assert all(r.namespace == "frameworks" for r in results)

    def test_search_by_content_type(self, kb):
        self._populate(kb)
        results = kb.search(content_type="docs")
        assert all(r.content_type == "docs" for r in results)

    def test_search_min_confidence(self, kb):
        self._populate(kb)
        results = kb.search(min_confidence=0.9)
        assert all(r.confidence >= 0.9 for r in results)

    def test_search_limit(self, kb):
        self._populate(kb)
        results = kb.search(limit=2)
        assert len(results) <= 2

    def test_search_empty_query_returns_all(self, kb):
        self._populate(kb)
        results = kb.search(limit=100)
        assert len(results) == 5

    def test_search_no_matches_returns_empty(self, kb):
        self._populate(kb)
        results = kb.search(query="ZZZNOMATCH999")
        assert results == []

    def test_get_namespaces(self, kb):
        self._populate(kb)
        namespaces = kb.get_namespaces()
        assert "tools" in namespaces
        assert "frameworks" in namespaces

    def test_results_sorted_by_confidence_desc(self, kb):
        self._populate(kb)
        results = kb.search(namespace="frameworks")
        confidences = [r.confidence for r in results]
        assert confidences == sorted(confidences, reverse=True)


# ---------------------------------------------------------------------------
# KnowledgeBase repr test
# ---------------------------------------------------------------------------

class TestKnowledgeBaseRepr:
    def test_repr_includes_path_and_count(self, kb):
        kb.store(_make_entry())
        r = repr(kb)
        assert "KnowledgeBase" in r
        assert "entries=1" in r


class TestKnowledgeBaseEvaluationRuns:
    def test_store_and_list_evaluation_runs(self, kb):
        record = EvaluationRunRecord(
            run_type="query-set",
            average_normalized_score=0.82,
            verdict_summary='{"strong": 2, "partial": 0, "weak": 0}',
            payload={"result_count": 2},
        )

        run_id = kb.store_evaluation_run(record)
        records = kb.list_evaluation_runs(limit=5)

        assert run_id == record.run_id
        assert len(records) == 1
        assert records[0].run_id == run_id
        assert records[0].payload["result_count"] == 2

    def test_list_evaluation_runs_filters_by_type(self, kb):
        kb.store_evaluation_run(
            EvaluationRunRecord(
                run_type="query",
                query="LangGraph",
                question_id="stack-current-enterprise",
                average_normalized_score=0.6,
                verdict_summary="partial",
                payload={"verdict": "partial"},
            )
        )
        kb.store_evaluation_run(
            EvaluationRunRecord(
                run_type="query-set",
                average_normalized_score=0.8,
                verdict_summary='{"strong": 1}',
                payload={"result_count": 1},
            )
        )

        records = kb.list_evaluation_runs(limit=10, run_type="query")

        assert len(records) == 1
        assert records[0].run_type == "query"

    def test_derive_learned_weight_profile_from_recent_runs(self, kb):
        kb.store_evaluation_run(
            EvaluationRunRecord(
                run_type="query",
                average_normalized_score=0.92,
                verdict_summary="strong",
                payload={
                    "normalized_score": 0.92,
                    "answer": {
                        "segment": "enterprise",
                        "recommendation": {"retrieval_sources": ["framework_matrix"]},
                    },
                },
            )
        )
        kb.store_evaluation_run(
            EvaluationRunRecord(
                run_type="query",
                average_normalized_score=0.45,
                verdict_summary="weak",
                payload={
                    "normalized_score": 0.45,
                    "answer": {
                        "segment": "startup",
                        "recommendation": {"retrieval_sources": ["tool_registry"]},
                    },
                },
            )
        )

        profile = kb.derive_learned_weight_profile(limit=10)

        assert profile.sample_count == 2
        assert profile.source_multipliers["framework_matrix"] > 1.0
        assert profile.source_multipliers["tool_registry"] < 1.0
        assert profile.segment_source_multipliers["enterprise"]["framework_matrix"] > 1.0
