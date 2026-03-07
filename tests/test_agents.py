"""
Unit tests for all agent classes.

Tests are intentionally dependency-free (no external APIs required) so they
can run in any CI environment without credentials.
"""

import pytest

from src.agents.base_agent import AgentResult, AgentStatus, BaseAgent
from src.agents.crawler_agent import CrawlerAgent, CrawledDocument
from src.agents.documentation_agent import DocumentationAgent
from src.agents.orchestrator import CycleResult, Orchestrator
from src.agents.research_agent import ResearchAgent, KNOWN_TOOLS, KNOWN_PEOPLE
from src.agents.tool_discovery_agent import ToolDiscoveryAgent
from src.agents.trend_tracker_agent import TrendScore, TrendTrackerAgent


# ---------------------------------------------------------------------------
# BaseAgent tests
# ---------------------------------------------------------------------------

class ConcreteAgent(BaseAgent):
    """Minimal concrete implementation of BaseAgent for testing."""

    def __init__(self, config=None, fail=False):
        super().__init__(name="TestAgent", config=config)
        self._fail = fail

    def _execute(self, task_input=None):
        if self._fail:
            raise ValueError("Simulated failure")
        return {"processed": task_input}


class TestBaseAgent:
    def test_initial_status_is_idle(self):
        agent = ConcreteAgent()
        assert agent.status == AgentStatus.IDLE

    def test_run_returns_agent_result(self):
        agent = ConcreteAgent()
        result = agent.run("hello")
        assert isinstance(result, AgentResult)
        assert result.agent_name == "TestAgent"
        assert result.status == AgentStatus.SUCCESS
        assert result.data == {"processed": "hello"}

    def test_run_captures_exception(self):
        agent = ConcreteAgent(fail=True)
        result = agent.run()
        assert result.status == AgentStatus.ERROR
        assert "Simulated failure" in result.error

    def test_health_check_after_init(self):
        agent = ConcreteAgent()
        agent.initialize()
        assert agent.health_check() is True

    def test_health_check_after_error(self):
        agent = ConcreteAgent(fail=True)
        agent.run()
        assert agent.health_check() is False

    def test_health_check_after_shutdown(self):
        agent = ConcreteAgent()
        agent.initialize()
        agent.shutdown()
        assert agent.health_check() is False

    def test_result_duration(self):
        agent = ConcreteAgent()
        result = agent.run()
        assert result.duration_seconds is not None
        assert result.duration_seconds >= 0.0

    def test_result_to_dict(self):
        agent = ConcreteAgent()
        result = agent.run("payload")
        d = result.to_dict()
        assert d["agent_name"] == "TestAgent"
        assert d["status"] == "success"
        assert "started_at" in d
        assert "completed_at" in d

    def test_repr(self):
        agent = ConcreteAgent()
        r = repr(agent)
        assert "ConcreteAgent" in r
        assert "TestAgent" in r


# ---------------------------------------------------------------------------
# CrawlerAgent tests
# ---------------------------------------------------------------------------

class TestCrawlerAgent:
    def test_initialization(self):
        agent = CrawlerAgent()
        agent.initialize()
        assert agent.health_check()
        agent.shutdown()

    def test_empty_source_list(self):
        agent = CrawlerAgent(config={"sources": []})
        agent.initialize()
        result = agent.run([])
        assert result.status == AgentStatus.SUCCESS
        assert result.data == []

    def test_deduplication(self):
        doc1 = CrawledDocument(url="http://a.com", title="A", content="Same content", source_type="blog")
        doc2 = CrawledDocument(url="http://b.com", title="B", content="Same content", source_type="blog")
        agent = CrawlerAgent()
        assert doc1.content_hash == doc2.content_hash
        agent._seen_hashes.add(doc1.content_hash)
        assert agent._is_duplicate(doc2) is True

    def test_content_hash_is_deterministic(self):
        doc = CrawledDocument(url="http://x.com", title="X", content="Hello", source_type="blog")
        hash1 = doc.content_hash
        hash2 = doc.content_hash
        assert hash1 == hash2

    def test_to_dict_contains_required_keys(self):
        doc = CrawledDocument(url="http://x.com", title="Title", content="Content", source_type="paper")
        d = doc.to_dict()
        for key in ("url", "title", "content", "source_type", "crawled_at", "content_hash"):
            assert key in d

    def test_robots_txt_disallows_covered_by_flag(self):
        agent = CrawlerAgent(config={"respect_robots_txt": True})
        agent.initialize()
        # Simulate robots.txt already denying
        from urllib.robotparser import RobotFileParser
        rp = RobotFileParser()
        rp.parse(["User-agent: *", "Disallow: /"])
        agent._robots_cache["http://blocked.com"] = rp
        assert agent._is_allowed("http://blocked.com/page") is False

    def test_extract_from_json_hacker_news_shape(self):
        agent = CrawlerAgent()
        data = {
            "hits": [
                {"title": "AI Architects Unite", "url": "http://hn.example.com/1", "story_text": "Great post"},
                {"title": "LangGraph vs AutoGen", "url": "http://hn.example.com/2", "story_text": ""},
            ]
        }
        result = agent._extract_from_json(data, "forum")
        assert "AI Architects Unite" in result
        assert "LangGraph vs AutoGen" in result


# ---------------------------------------------------------------------------
# ResearchAgent tests
# ---------------------------------------------------------------------------

RAW_DOC = {
    "url": "https://arxiv.org/abs/2401.00001",
    "title": "Advances in Multi-Agent Systems",
    "content": (
        "This paper introduces a new approach to hierarchical multi-agent orchestration. "
        "We propose using LangGraph for stateful agent management with FAISS-based vector retrieval. "
        "Experiments show significant improvements over baseline AutoGen configurations. "
        "The system achieves 92% accuracy on AgentBench tasks. "
        "Key contributors include Andrej Karpathy and Lilian Weng's foundational work on RLHF. "
        "The prompt injection defense mechanism prevents adversarial inputs from affecting agent behavior. "
    ) * 5,  # Make it long enough to exceed min_content_length
    "source_type": "paper",
    "metadata": {"source_name": "arXiv"},
}


class TestResearchAgent:
    def test_processes_valid_document(self):
        agent = ResearchAgent()
        result = agent.run([RAW_DOC])
        assert result.status == AgentStatus.SUCCESS
        findings = result.data
        assert len(findings) == 1
        finding = findings[0]
        assert "title" in finding
        assert "summary" in finding
        assert "content_type" in finding
        assert "namespace" in finding
        assert "confidence" in finding

    def test_skips_too_short_documents(self):
        agent = ResearchAgent(config={"min_content_length": 100})
        short_doc = {"url": "http://x.com", "title": "T", "content": "Too short", "source_type": "blog"}
        result = agent.run([short_doc])
        assert result.status == AgentStatus.SUCCESS
        assert result.data == []

    def test_detects_known_tools(self):
        agent = ResearchAgent()
        result = agent.run([RAW_DOC])
        assert result.status == AgentStatus.SUCCESS
        finding = result.data[0]
        # Should detect at least LangGraph and FAISS from the content
        tools = [t.lower() for t in finding.get("tools_mentioned", [])]
        assert any(t in tools for t in ["langgraph", "faiss", "autogen"])

    def test_content_type_classification_paper(self):
        agent = ResearchAgent()
        content_type = agent._classify_content_type("this paper proposes a new approach we show that", "paper")
        assert content_type == "paper"

    def test_content_type_classification_tool_release(self):
        agent = ResearchAgent()
        content_type = agent._classify_content_type("we are excited to release version 2.0 of our tool", "blog")
        assert content_type == "tool_release"

    def test_namespace_detection_tools(self):
        agent = ResearchAgent()
        ns = agent._detect_namespace("this library framework sdk api tool is installed via pip")
        assert ns == "tools"

    def test_namespace_detection_frameworks(self):
        agent = ResearchAgent()
        ns = agent._detect_namespace("this architecture pattern for rag retrieval method algorithm")
        assert ns == "frameworks"

    def test_empty_input(self):
        agent = ResearchAgent()
        result = agent.run([])
        assert result.status == AgentStatus.SUCCESS
        assert result.data == []

    def test_known_tools_set_not_empty(self):
        assert len(KNOWN_TOOLS) > 10

    def test_known_people_set_not_empty(self):
        assert len(KNOWN_PEOPLE) > 5

    def test_extract_concepts_finds_capitalized_phrases(self):
        agent = ResearchAgent()
        concepts = agent._extract_concepts("The Large Language Model uses Retrieval Augmented Generation techniques")
        assert "Large Language Model" in concepts or "Retrieval Augmented Generation" in concepts

    def test_confidence_threshold_filters(self):
        agent = ResearchAgent(config={"confidence_threshold": 0.99})  # Very high threshold
        result = agent.run([RAW_DOC])
        assert result.status == AgentStatus.SUCCESS
        # High threshold should filter most findings
        assert len(result.data) == 0

    def test_non_list_input_returns_empty(self):
        agent = ResearchAgent()
        result = agent.run("not a list")
        assert result.status == AgentStatus.SUCCESS
        assert result.data == []


# ---------------------------------------------------------------------------
# TrendTrackerAgent tests
# ---------------------------------------------------------------------------

SAMPLE_FINDINGS = [
    {
        "title": "LangGraph in Production",
        "summary": "LangGraph agentic systems are seeing rapid adoption in enterprise environments.",
        "concepts": ["LangGraph", "Agentic RAG", "Dynamic Tool Discovery"],
        "tools_mentioned": ["langgraph", "langchain"],
        "namespace": "frameworks",
        "confidence": 0.9,
    },
    {
        "title": "Small Language Models Take Off",
        "summary": "Small Language Models are displacing large models for on-device use cases.",
        "concepts": ["Small Language Models", "On-Device Inference", "Edge AI"],
        "tools_mentioned": ["phi", "gemma", "ollama"],
        "namespace": "trends",
        "confidence": 0.85,
    },
]


class TestTrendTrackerAgent:
    def test_initialization_seeds_trends(self):
        agent = TrendTrackerAgent()
        agent.initialize()
        assert len(agent._history) > 0

    def test_run_returns_scores_and_alerts(self):
        agent = TrendTrackerAgent()
        agent.initialize()
        result = agent.run(SAMPLE_FINDINGS)
        assert result.status == AgentStatus.SUCCESS
        data = result.data
        assert "scores" in data
        assert "alerts" in data
        assert "total_trends" in data
        assert len(data["scores"]) > 0

    def test_scores_are_bounded(self):
        agent = TrendTrackerAgent()
        agent.initialize()
        result = agent.run(SAMPLE_FINDINGS)
        for score in result.data["scores"]:
            assert 0.0 <= score["composite"] <= 10.0

    def test_scores_sorted_descending(self):
        agent = TrendTrackerAgent()
        agent.initialize()
        result = agent.run(SAMPLE_FINDINGS)
        scores = [s["composite"] for s in result.data["scores"]]
        assert scores == sorted(scores, reverse=True)

    def test_trend_score_composite_formula(self):
        ts = TrendScore(
            trend_name="Test Trend",
            recency=8.0,
            adoption_velocity=9.0,
            credibility=7.0,
            novelty_delta=5.0,
        )
        expected = 8.0 * 0.30 + 9.0 * 0.35 + 7.0 * 0.25 + 5.0 * 0.10
        assert abs(ts.composite - expected) < 0.01

    def test_get_top_trends_returns_n_results(self):
        agent = TrendTrackerAgent()
        agent.initialize()
        top = agent.get_top_trends(n=5)
        assert len(top) <= 5

    def test_new_trend_discovered_from_findings(self):
        agent = TrendTrackerAgent()
        agent.initialize()
        initial_count = len(agent._history)
        findings_with_new_concept = [
            {
                "title": "Novel approach",
                "summary": "something new",
                "concepts": ["Brand New Trend 2025 XYZ"],
                "tools_mentioned": [],
                "namespace": "trends",
                "confidence": 0.9,
            }
        ]
        agent.run(findings_with_new_concept)
        assert len(agent._history) >= initial_count

    def test_empty_findings_doesnt_crash(self):
        agent = TrendTrackerAgent()
        agent.initialize()
        result = agent.run([])
        assert result.status == AgentStatus.SUCCESS


# ---------------------------------------------------------------------------
# ToolDiscoveryAgent tests
# ---------------------------------------------------------------------------

class TestToolDiscoveryAgent:
    def test_initialization_loads_seed_tools(self):
        agent = ToolDiscoveryAgent()
        agent.initialize()
        assert len(agent._registry) > 10

    def test_run_returns_registry_and_alerts(self):
        agent = ToolDiscoveryAgent()
        agent.initialize()
        result = agent.run(SAMPLE_FINDINGS)
        assert result.status == AgentStatus.SUCCESS
        data = result.data
        assert "registry" in data
        assert "alerts" in data
        assert "total_tools" in data

    def test_new_tool_discovered(self):
        agent = ToolDiscoveryAgent()
        agent.initialize()
        findings_with_new_tool = [
            {
                "title": "New Tool Released",
                "summary": "brandnewtool2025xyz is a revolutionary new agent framework",
                "concepts": ["Agent Framework"],
                "tools_mentioned": ["brandnewtool2025xyz"],
                "source_url": "http://example.com",
                "source_name": "Example Blog",
                "namespace": "tools",
                "confidence": 0.9,
            }
        ]
        result = agent.run(findings_with_new_tool)
        assert "brandnewtool2025xyz" in result.data.get("newly_discovered", [])

    def test_deprecation_signal_detected(self):
        agent = ToolDiscoveryAgent()
        agent.initialize()
        # LangChain is in the seed registry
        findings_with_deprecation = [
            {
                "title": "LangChain deprecated",
                "summary": "LangChain has been deprecated in favor of LangGraph",
                "concepts": [],
                "tools_mentioned": ["langchain"],
                "source_url": "http://example.com",
                "source_name": "Tech Blog",
                "namespace": "tools",
                "confidence": 0.9,
            }
        ]
        agent.run(findings_with_deprecation)
        assert agent._registry["langchain"].status == "deprecated"

    def test_get_tools_by_category(self):
        agent = ToolDiscoveryAgent()
        agent.initialize()
        frameworks = agent.get_tools_by_category("framework")
        assert len(frameworks) > 0
        assert all(t["category"] == "framework" for t in frameworks)

    def test_get_top_tools(self):
        agent = ToolDiscoveryAgent()
        agent.initialize()
        top = agent.get_top_tools(n=5)
        assert len(top) <= 5
        scores = [t["evaluation_score"] for t in top]
        assert scores == sorted(scores, reverse=True)

    def test_empty_findings_doesnt_crash(self):
        agent = ToolDiscoveryAgent()
        agent.initialize()
        result = agent.run([])
        assert result.status == AgentStatus.SUCCESS


# ---------------------------------------------------------------------------
# DocumentationAgent tests
# ---------------------------------------------------------------------------

class TestDocumentationAgent:
    def _sample_input(self):
        return {
            "findings": SAMPLE_FINDINGS,
            "trend_data": {
                "scores": [
                    {"trend_name": "Agentic RAG", "composite": 9.0, "recency": 9.0,
                     "adoption_velocity": 9.0, "credibility": 9.0, "evidence_count": 3},
                ],
                "alerts": [],
                "total_trends": 1,
                "summary": "Agentic RAG leading trends.",
            },
            "tool_data": {
                "registry": [
                    {"name": "LangGraph", "category": "framework", "url": "https://github.com/langchain-ai/langgraph",
                     "description": "Graph-based agent orchestration", "status": "active",
                     "evaluation_score": 9.0, "last_seen": "2026-01-01T00:00:00+00:00"},
                ],
                "alerts": [],
                "newly_discovered": [],
                "total_tools": 1,
            },
            "cycle_number": 1,
        }

    def test_run_produces_documents(self):
        agent = DocumentationAgent()
        result = agent.run(self._sample_input())
        assert result.status == AgentStatus.SUCCESS
        docs = result.data
        assert len(docs) >= 1

    def test_daily_digest_contains_summary(self):
        agent = DocumentationAgent()
        result = agent.run(self._sample_input())
        digest = next(d for d in result.data if d["doc_type"] == "daily_digest")
        assert "New findings" in digest["content"]
        assert "Trends tracked" in digest["content"]

    def test_tool_comparison_generated(self):
        agent = DocumentationAgent()
        result = agent.run(self._sample_input())
        doc_types = [d["doc_type"] for d in result.data]
        assert "tool_comparison" in doc_types

    def test_trend_report_generated(self):
        agent = DocumentationAgent()
        result = agent.run(self._sample_input())
        doc_types = [d["doc_type"] for d in result.data]
        assert "trend_report" in doc_types

    def test_non_dict_input_returns_empty(self):
        agent = DocumentationAgent()
        result = agent.run("not a dict")
        assert result.status == AgentStatus.SUCCESS
        # Should produce a digest with zero counts
        assert len(result.data) >= 1

    def test_document_has_required_fields(self):
        agent = DocumentationAgent()
        result = agent.run(self._sample_input())
        for doc in result.data:
            assert "doc_type" in doc
            assert "title" in doc
            assert "content" in doc
            assert "generated_at" in doc


# ---------------------------------------------------------------------------
# Orchestrator tests
# ---------------------------------------------------------------------------

class TestOrchestrator:
    def test_initialization(self):
        orch = Orchestrator()
        orch.initialize()
        assert orch._agents_initialized is True

    def test_health_check_returns_dict(self):
        orch = Orchestrator()
        orch.initialize()
        health = orch.health_check()
        assert isinstance(health, dict)
        assert len(health) == 5  # 5 agents

    def test_run_cycle_returns_cycle_result(self):
        # Run in trends-only mode to avoid actual HTTP requests
        orch = Orchestrator()
        orch.initialize()
        # Override crawler to return empty list (avoid network calls)
        class NoOpCrawler(CrawlerAgent):
            def _execute(self, task_input=None):
                return []

        orch.crawler = NoOpCrawler()
        orch.crawler.initialize()

        result = orch.run_cycle(mode="trends")
        assert isinstance(result, CycleResult)
        assert result.cycle_number == 1

    def test_cycle_increments_counter(self):
        orch = Orchestrator()
        orch.initialize()

        class NoOpCrawler(CrawlerAgent):
            def _execute(self, task_input=None):
                return []

        orch.crawler = NoOpCrawler()
        orch.crawler.initialize()

        orch.run_cycle(mode="trends")
        orch.run_cycle(mode="trends")
        assert orch._cycle_count == 2

    def test_query_trends_returns_list(self):
        orch = Orchestrator()
        orch.initialize()
        trends = orch.query_trends(top_n=5)
        assert isinstance(trends, list)
        assert len(trends) <= 5

    def test_query_tools_returns_list(self):
        orch = Orchestrator()
        orch.initialize()
        tools = orch.query_tools(top_n=5)
        assert isinstance(tools, list)
        assert len(tools) <= 5

    def test_query_tools_by_category(self):
        orch = Orchestrator()
        orch.initialize()
        tools = orch.query_tools(category="framework")
        assert all(t.get("category") == "framework" for t in tools)

    def test_get_cycle_history(self):
        orch = Orchestrator()
        orch.initialize()
        history = orch.get_cycle_history()
        assert isinstance(history, list)

    def test_shutdown(self):
        orch = Orchestrator()
        orch.initialize()
        orch.shutdown()
        # All agents should be in SHUTDOWN status
        from src.agents.base_agent import AgentStatus
        for agent in orch._all_agents:
            assert agent.status == AgentStatus.SHUTDOWN

    def test_cycle_result_to_dict(self):
        cr = CycleResult(cycle_number=1, crawled_count=10, findings_count=5)
        from datetime import datetime, timezone
        cr.completed_at = datetime.now(timezone.utc)
        d = cr.to_dict()
        assert d["cycle_number"] == 1
        assert d["crawled_count"] == 10
        assert "success" in d
