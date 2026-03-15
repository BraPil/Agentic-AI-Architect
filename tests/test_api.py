"""Unit tests for the minimal REST API surface."""

from pathlib import Path
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from src.api.rest import create_app
from src.knowledge.knowledge_base import EvaluationRunRecord, KnowledgeBase, KnowledgeEntry


class StubOrchestrator:
    """Small orchestrator stub used to keep API tests deterministic."""

    def __init__(self) -> None:
        self._agents_initialized = True

    def initialize(self) -> None:
        self._agents_initialized = True

    def shutdown(self) -> None:
        return None

    def health_check(self) -> dict[str, bool]:
        return {
            "CrawlerAgent": True,
            "ResearchAgent": True,
            "TrendTrackerAgent": True,
            "ToolDiscoveryAgent": True,
            "DocumentationAgent": True,
        }

    def query_trends(self, top_n: int = 10) -> list[dict[str, object]]:
        return [{"trend_name": "agent workflows", "composite": 0.91}][:top_n]

    def query_tools(
        self,
        category: str | None = None,
        top_n: int = 10,
    ) -> list[dict[str, object]]:
        tools = [
            {"tool_name": "FastAPI", "category": "framework"},
            {"tool_name": "pgvector", "category": "database"},
        ]
        if category:
            tools = [tool for tool in tools if tool["category"] == category]
        return tools[:top_n]


def _make_client(tmp_path: Path) -> TestClient:
    kb = KnowledgeBase(str(tmp_path / "test_api.db"))
    kb.initialize()
    kb.store(
        KnowledgeEntry(
            title="LangGraph for durable workflows",
            content="LangGraph provides graph-based orchestration for agent systems.",
            namespace="tools",
            content_type="article",
            source_url="https://example.com/langgraph",
            source_name="Test Source",
            confidence=0.9,
        )
    )
    kb.store(
        KnowledgeEntry(
            title="LangChain orchestration overview",
            content="LangChain remains relevant, but LangGraph is replacing it for many agent cases.",
            namespace="frameworks",
            content_type="analysis",
            source_url="https://example.com/langchain",
            source_name="Framework Notes",
            confidence=0.6,
        )
    )
    app = create_app(orchestrator=StubOrchestrator(), knowledge_base=kb)
    return TestClient(app)


def _make_empty_client(tmp_path: Path) -> TestClient:
    kb = KnowledgeBase(str(tmp_path / "test_api_empty.db"))
    kb.initialize()
    app = create_app(orchestrator=StubOrchestrator(), knowledge_base=kb)
    return TestClient(app)


class TestRestApi:
    def test_root_returns_service_metadata(self, tmp_path: Path):
        with _make_client(tmp_path) as client:
            response = client.get("/")

        assert response.status_code == 200
        payload = response.json()
        assert payload["service"] == "Agentic AI Architect API"
        assert payload["docs_url"] == "/docs"

    def test_health_returns_agent_and_knowledge_status(self, tmp_path: Path):
        with _make_client(tmp_path) as client:
            response = client.get("/health")

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "ok"
        assert payload["knowledge_entries"] == 2
        assert payload["agents"]["CrawlerAgent"] is True

    def test_trends_endpoint_returns_items(self, tmp_path: Path):
        with _make_client(tmp_path) as client:
            response = client.get("/trends", params={"top_n": 1})

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 1
        assert payload["items"][0]["trend_name"] == "agent workflows"

    def test_tools_endpoint_filters_by_category(self, tmp_path: Path):
        with _make_client(tmp_path) as client:
            response = client.get("/tools", params={"category": "framework"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 1
        assert payload["items"][0]["tool_name"] == "FastAPI"

    def test_frameworks_endpoint_returns_matrix_rows(self, tmp_path: Path):
        with _make_client(tmp_path) as client:
            response = client.get("/frameworks")

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] > 0
        assert payload["source_path"] == "docs/phase-2-conceptual-frameworks.md"
        assert "Framework" in payload["items"][0]
        assert "2026 Trajectory" in payload["items"][0]

    def test_frameworks_endpoint_filters_by_trajectory(self, tmp_path: Path):
        with _make_client(tmp_path) as client:
            response = client.get("/frameworks", params={"trajectory": "growing fast"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] >= 1
        assert any(row["Framework"] == "LangGraph" for row in payload["items"])

    def test_frameworks_endpoint_filters_by_search(self, tmp_path: Path):
        with _make_client(tmp_path) as client:
            response = client.get("/frameworks", params={"search": "optuna"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 1
        assert payload["items"][0]["Framework"] == "Optuna"

    def test_report_endpoint_returns_phase_markdown(self, tmp_path: Path):
        with _make_client(tmp_path) as client:
            response = client.get("/report/frameworks")

        assert response.status_code == 200
        payload = response.json()
        assert payload["source_path"] == "docs/phase-2-conceptual-frameworks.md"
        assert payload["format"] == "markdown"
        assert payload["title"].startswith("Phase 2: Conceptual Frameworks")
        assert "## 2.11 Framework Maturity Matrix" in payload["content"]

    def test_report_endpoint_rejects_unknown_phase(self, tmp_path: Path):
        with _make_client(tmp_path) as client:
            response = client.get("/report/unknown-phase")

        assert response.status_code == 404
        assert "Unknown phase report" in response.json()["detail"]

    def test_evaluation_set_endpoint_returns_initial_questions(self, tmp_path: Path):
        with _make_client(tmp_path) as client:
            response = client.get("/evaluation-set")

        assert response.status_code == 200
        payload = response.json()
        assert payload["evaluation_set_version"] == "v0"
        assert len(payload["questions"]) == 6
        assert payload["questions"][0]["question_id"] == "arch-slo-enterprise"

    def test_evaluation_set_endpoint_filters_by_question_type(self, tmp_path: Path):
        with _make_client(tmp_path) as client:
            response = client.get(
                "/evaluation-set",
                params={"question_type": "change_watch"},
            )

        assert response.status_code == 200
        payload = response.json()
        assert len(payload["questions"]) == 2
        assert all(question["question_type"] == "change_watch" for question in payload["questions"])

    def test_evaluate_query_endpoint_returns_scored_result(self, tmp_path: Path):
        with _make_client(tmp_path) as client:
            response = client.get(
                "/evaluate/query",
                params={
                    "question_id": "stack-current-enterprise",
                    "q": "LangGraph",
                },
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["question_id"] == "stack-current-enterprise"
        assert payload["answer"]["contract_version"] == "v0"
        assert len(payload["criterion_scores"]) == 5
        assert payload["answer"]["enterprise_overlay"]["enterprise_safe_now"] is True
        assert payload["normalized_score"] > 0
        assert payload["run_id"]

    def test_evaluate_query_endpoint_rejects_unknown_question(self, tmp_path: Path):
        with _make_client(tmp_path) as client:
            response = client.get(
                "/evaluate/query",
                params={"question_id": "missing-question"},
            )

        assert response.status_code == 404
        assert "Unknown evaluation question" in response.json()["detail"]

    def test_evaluate_query_set_endpoint_returns_aggregate_scores(self, tmp_path: Path):
        with _make_client(tmp_path) as client:
            response = client.get(
                "/evaluate/query-set",
                params={"question_type": "change_watch"},
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["result_count"] == 2
        assert len(payload["results"]) == 2
        assert payload["average_normalized_score"] > 0.49
        assert payload["verdict_counts"]["partial"] + payload["verdict_counts"]["strong"] >= 1
        assert payload["run_id"]

    def test_evaluation_history_endpoint_returns_persisted_runs(self, tmp_path: Path):
        with _make_client(tmp_path) as client:
            client.get(
                "/evaluate/query-set",
                params={"question_type": "change_watch"},
            )
            response = client.get("/evaluate/history", params={"run_type": "query-set"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] >= 1
        assert payload["items"][0]["run_type"] == "query-set"

    def test_evaluation_performance_endpoint_returns_summary(self, tmp_path: Path):
        with _make_client(tmp_path) as client:
            client.get(
                "/evaluate/query",
                params={
                    "question_id": "stack-current-enterprise",
                    "q": "LangGraph",
                },
            )
            response = client.get("/evaluate/performance")

        assert response.status_code == 200
        payload = response.json()
        assert payload["total_runs"] >= 1
        assert payload["overall_average_normalized_score"] > 0
        assert payload["by_run_type"][0]["run_type"] == "query"

    def test_evaluate_query_segments_endpoint_compares_segments(self, tmp_path: Path):
        with _make_client(tmp_path) as client:
            response = client.get(
                "/evaluate/query-segments",
                params=[
                    ("question_id", "stack-current-enterprise"),
                    ("q", "LangGraph"),
                    ("segments", "startup"),
                    ("segments", "enterprise"),
                ],
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["result_count"] == 2
        assert payload["best_segment"] in {"startup", "enterprise"}
        assert {result["answer"]["segment"] for result in payload["results"]} == {
            "startup",
            "enterprise",
        }
        assert payload["run_id"]

    def test_query_endpoint_includes_source_weighting_model(self, tmp_path: Path):
        with _make_empty_client(tmp_path) as client:
            response = client.get("/query", params={"q": "LangGraph"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["recommendation"]["source_weighting_model"] == "v2"
        assert payload["enterprise_overlay"]["segment_deltas"]

    def test_query_endpoint_reports_learned_weighting_when_history_exists(self, tmp_path: Path):
        kb = KnowledgeBase(str(tmp_path / "test_api_learned.db"))
        kb.initialize()
        kb.store_evaluation_run(
            EvaluationRunRecord(
                run_type="query",
                average_normalized_score=0.9,
                verdict_summary="strong",
                payload={
                    "normalized_score": 0.9,
                    "answer": {
                        "segment": "enterprise",
                        "recommendation": {"retrieval_sources": ["framework_matrix"]},
                    },
                },
            )
        )
        app = create_app(orchestrator=StubOrchestrator(), knowledge_base=kb)

        with TestClient(app) as client:
            response = client.get("/query", params={"q": "LangGraph", "segment": "enterprise"})

        payload = response.json()
        assert payload["recommendation"]["learned_weighting_active"] is True
        assert payload["recommendation"]["learned_weighting_samples"] >= 1

    def test_query_endpoint_prefers_fresher_matches_when_scores_are_close(self, tmp_path: Path):
        kb = KnowledgeBase(str(tmp_path / "test_api_freshness.db"))
        kb.initialize()
        fresh_entry = KnowledgeEntry(
            title="LangGraph fresh guidance",
            content="LangGraph provides current orchestration guidance for agent systems.",
            namespace="tools",
            content_type="article",
            source_url="https://example.com/fresh-langgraph",
            source_name="Fresh Source",
            confidence=0.86,
        )
        stale_entry = KnowledgeEntry(
            title="LangGraph stale guidance",
            content="LangGraph provides older orchestration guidance for agent systems.",
            namespace="tools",
            content_type="article",
            source_url="https://example.com/stale-langgraph",
            source_name="Stale Source",
            confidence=0.9,
        )
        kb.store(fresh_entry)
        kb.store(stale_entry)
        stale_timestamp = (datetime.now(UTC) - timedelta(days=365)).isoformat()
        assert kb._conn is not None
        kb._conn.execute(
            "UPDATE knowledge_entries SET updated_at = ? WHERE entry_id = ?",
            (stale_timestamp, stale_entry.entry_id),
        )
        kb._conn.commit()
        app = create_app(orchestrator=StubOrchestrator(), knowledge_base=kb)

        with TestClient(app) as client:
            response = client.get(
                "/query",
                params={"q": "LangGraph", "segment": "enterprise", "time_horizon": "now"},
            )

        payload = response.json()
        assert payload["evidence"][0]["title"] == "LangGraph fresh guidance"

    def test_change_watch_query_uses_broad_fallback_signals(self, tmp_path: Path):
        with _make_empty_client(tmp_path) as client:
            response = client.get(
                "/query",
                params={
                    "q": "What are the most recent and impactful changes to the current paradigm?",
                    "question_type": "change_watch",
                },
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["recommendation"]["match_count"] >= 1
        assert payload["recommendation"]["top_paradigm_shifts"]
        assert payload["recommendation"]["why_each_shift_matters"]
        assert payload["recommendation"]["what_remains_stable"]

    def test_query_endpoint_uses_repo_fallbacks_when_kb_is_empty(self, tmp_path: Path):
        with _make_empty_client(tmp_path) as client:
            response = client.get("/query", params={"q": "LangGraph"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["recommendation"]["match_count"] >= 1
        assert payload["recommendation"]["ranking_strategy"] == (
            "keyword-plus-confidence-plus-learned-weighting-plus-freshness-with-fallbacks"
        )
        assert payload["evidence"][0]["evidence_tier"] == "direct"

    def test_query_set_endpoint_rejects_empty_filters(self, tmp_path: Path):
        with _make_client(tmp_path) as client:
            response = client.get(
                "/evaluate/query-set",
                params={"segment": "startup", "question_type": "stack_recommendation"},
            )

        assert response.status_code == 404
        assert "No evaluation questions matched" in response.json()["detail"]

    def test_query_endpoint_returns_contract_payload(self, tmp_path: Path):
        with _make_client(tmp_path) as client:
            response = client.get(
                "/query",
                params={
                    "q": "LangGraph",
                    "response_mode": "both",
                    "question_type": "stack_recommendation",
                    "segment": "enterprise",
                },
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["contract_version"] == "v0"
        assert payload["question_type"] == "stack_recommendation"
        assert payload["summary"].startswith("Retrieved 2 knowledge entries")
        assert payload["enterprise_overlay"]["enterprise_safe_now"] is True
        assert payload["recommendation"]["match_count"] == 2
        assert payload["recommendation"]["ranking_strategy"] == (
            "keyword-plus-confidence-plus-learned-weighting-plus-freshness"
        )
        assert payload["evidence"][0]["title"] == "LangGraph for durable workflows"
        assert payload["evidence"][0]["source_url"] == "https://example.com/langgraph"
        assert payload["rendered_response"] is not None

    def test_query_endpoint_supports_namespace_filter(self, tmp_path: Path):
        with _make_client(tmp_path) as client:
            response = client.get(
                "/query",
                params={
                    "q": "LangGraph",
                    "namespace": "tools",
                },
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["recommendation"]["match_count"] == 1
        assert payload["evidence"][0]["title"] == "LangGraph for durable workflows"

    def test_query_endpoint_returns_low_confidence_for_no_match(self, tmp_path: Path):
        with _make_client(tmp_path) as client:
            response = client.get("/query", params={"q": "nonexistent topic"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["confidence"]["score"] == 0.25
        assert payload["evidence"] == []
        assert payload["confidence"]["gaps"]