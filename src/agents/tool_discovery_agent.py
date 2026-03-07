"""
Tool Discovery Agent — Monitors the AI tools landscape for new releases,
deprecations, and paradigm shifts.

Tracks:
  - GitHub trending repos (AI-relevant topics)
  - PyPI new releases (ai, llm, rag, agent, mcp tags)
  - Version bumps in tracked tools
  - Deprecation signals
  - Breaking change detection in changelogs
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .base_agent import BaseAgent


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class ToolRecord:
    """Represents a discovered or tracked AI tool."""

    name: str
    description: str
    category: str  # framework | vector_db | llm_provider | inference | observability | crawler | other
    url: str
    version: str = "unknown"
    github_stars: int = 0
    language: str = "unknown"
    license: str = "unknown"
    status: str = "active"  # active | deprecated | archived | experimental
    evaluation_score: float = 0.0  # 0–10
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "url": self.url,
            "version": self.version,
            "github_stars": self.github_stars,
            "language": self.language,
            "license": self.license,
            "status": self.status,
            "evaluation_score": self.evaluation_score,
            "last_seen": self.last_seen.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class ToolAlert:
    """Alert for a significant tool event."""

    alert_type: str  # NEW_TOOL | DEPRECATION | MAJOR_RELEASE | BREAKTHROUGH_SCORE
    tool_name: str
    message: str
    url: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "alert_type": self.alert_type,
            "tool_name": self.tool_name,
            "message": self.message,
            "url": self.url,
            "created_at": self.created_at.isoformat(),
        }


# ---------------------------------------------------------------------------
# Pre-seeded tool database
# ---------------------------------------------------------------------------

SEED_TOOLS: list[dict[str, Any]] = [
    # Agentic frameworks
    {"name": "LangGraph", "category": "framework", "url": "https://github.com/langchain-ai/langgraph",
     "description": "Graph-based stateful agent orchestration", "status": "active", "evaluation_score": 9.0},
    {"name": "LangChain", "category": "framework", "url": "https://github.com/langchain-ai/langchain",
     "description": "LLM application framework", "status": "active", "evaluation_score": 7.5},
    {"name": "LlamaIndex", "category": "framework", "url": "https://github.com/run-llama/llama_index",
     "description": "Data framework for LLM applications; best-in-class RAG", "status": "active", "evaluation_score": 9.0},
    {"name": "AutoGen", "category": "framework", "url": "https://github.com/microsoft/autogen",
     "description": "Multi-agent conversation framework from Microsoft", "status": "active", "evaluation_score": 8.5},
    {"name": "CrewAI", "category": "framework", "url": "https://github.com/crewAIInc/crewAI",
     "description": "Role-based multi-agent framework", "status": "active", "evaluation_score": 8.0},
    {"name": "DSPy", "category": "framework", "url": "https://github.com/stanfordnlp/dspy",
     "description": "Programmatic prompt optimization from Stanford", "status": "active", "evaluation_score": 8.2},
    {"name": "Pydantic AI", "category": "framework", "url": "https://github.com/pydantic/pydantic-ai",
     "description": "Type-safe AI agent framework", "status": "experimental", "evaluation_score": 7.5},
    # Vector databases
    {"name": "FAISS", "category": "vector_db", "url": "https://github.com/facebookresearch/faiss",
     "description": "Facebook's fast vector similarity search library", "status": "active", "evaluation_score": 8.5},
    {"name": "Qdrant", "category": "vector_db", "url": "https://github.com/qdrant/qdrant",
     "description": "Rust-based vector database with strong filtering", "status": "active", "evaluation_score": 8.5},
    {"name": "ChromaDB", "category": "vector_db", "url": "https://github.com/chroma-core/chroma",
     "description": "Lightweight embedded vector database", "status": "active", "evaluation_score": 7.8},
    {"name": "Weaviate", "category": "vector_db", "url": "https://github.com/weaviate/weaviate",
     "description": "Open-source vector database with GraphQL", "status": "active", "evaluation_score": 8.2},
    # Observability
    {"name": "LangSmith", "category": "observability", "url": "https://smith.langchain.com",
     "description": "LLM tracing and evaluation platform", "status": "active", "evaluation_score": 8.8},
    {"name": "MLflow", "category": "observability", "url": "https://github.com/mlflow/mlflow",
     "description": "Open-source ML experiment tracking", "status": "active", "evaluation_score": 8.5},
    # Inference
    {"name": "vLLM", "category": "inference", "url": "https://github.com/vllm-project/vllm",
     "description": "Fast LLM serving with PagedAttention", "status": "active", "evaluation_score": 9.2},
    {"name": "Ollama", "category": "inference", "url": "https://github.com/ollama/ollama",
     "description": "Run LLMs locally with one command", "status": "active", "evaluation_score": 9.0},
    {"name": "SGLang", "category": "inference", "url": "https://github.com/sgl-project/sglang",
     "description": "Fast structured generation and serving", "status": "active", "evaluation_score": 8.8},
    # Crawlers
    {"name": "Firecrawl", "category": "crawler", "url": "https://github.com/mendableai/firecrawl",
     "description": "LLM-ready web crawling with Markdown output", "status": "active", "evaluation_score": 8.5},
    {"name": "Playwright", "category": "crawler", "url": "https://github.com/microsoft/playwright-python",
     "description": "Dynamic site browser automation", "status": "active", "evaluation_score": 8.8},
    {"name": "Stagehand", "category": "crawler", "url": "https://github.com/browserbase/stagehand",
     "description": "Playwright + LLM natural language browser control", "status": "experimental", "evaluation_score": 7.5},
]


# ---------------------------------------------------------------------------
# ToolDiscoveryAgent
# ---------------------------------------------------------------------------

DEPRECATION_SIGNALS = [
    "deprecated", "end of life", "eol", "no longer maintained",
    "archived", "sunset", "discontinue", "shutting down",
]

TOOL_CATEGORIES = {
    "framework": ["agent", "orchestrat", "pipeline", "chain", "workflow", "sdk"],
    "vector_db": ["vector", "embedding", "similarity", "ann", "faiss", "pinecone"],
    "llm_provider": ["llm", "language model", "gpt", "claude", "gemini", "llama"],
    "inference": ["serving", "inference", "deploy", "quantiz", "vllm", "gguf"],
    "observability": ["monitor", "trace", "log", "metric", "mlflow", "wandb", "eval"],
    "crawler": ["crawl", "scrape", "browser", "playwright", "fetch"],
}


class ToolDiscoveryAgent(BaseAgent):
    """
    Maintains a registry of AI tools and alerts on significant events.

    Configuration keys:
        new_tool_star_threshold (int): Min stars in first week to trigger alert (default 100).
        breakthrough_score_threshold (float): Evaluation score for breakthrough alert (default 8.5).
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(name="ToolDiscoveryAgent", config=config)
        self._star_threshold: int = self.config.get("new_tool_star_threshold", 100)
        self._breakthrough_threshold: float = self.config.get("breakthrough_score_threshold", 8.5)
        self._registry: dict[str, ToolRecord] = {}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        super().initialize()
        self._load_seed_tools()
        self.logger.info("ToolDiscoveryAgent tracking %d tools", len(self._registry))

    # ------------------------------------------------------------------
    # Core execution
    # ------------------------------------------------------------------

    def _execute(self, task_input: Any = None) -> dict[str, Any]:
        """
        Process research findings for tool mentions; return updated registry and alerts.

        Args:
            task_input: List of ResearchFinding dicts from ResearchAgent.
        """
        findings: list[dict[str, Any]] = task_input if isinstance(task_input, list) else []
        alerts: list[dict[str, Any]] = []
        newly_discovered: list[str] = []

        for finding in findings:
            for tool_name in finding.get("tools_mentioned", []):
                tool_lower = tool_name.lower().strip()
                if not tool_lower:
                    continue

                if tool_lower in self._registry:
                    # Update last_seen
                    self._registry[tool_lower].last_seen = datetime.now(timezone.utc)
                else:
                    # New tool discovered
                    new_tool = ToolRecord(
                        name=tool_name,
                        description=finding.get("summary", "")[:200],
                        category=self._classify_tool(finding),
                        url=finding.get("source_url", ""),
                        status="active",
                    )
                    self._registry[tool_lower] = new_tool
                    newly_discovered.append(tool_name)
                    alerts.append(
                        ToolAlert(
                            alert_type="NEW_TOOL",
                            tool_name=tool_name,
                            message=f"New tool discovered: '{tool_name}' (from {finding.get('source_name', 'unknown')})",
                            url=finding.get("source_url", ""),
                        ).to_dict()
                    )

            # Check for deprecation signals in findings
            summary_lower = finding.get("summary", "").lower()
            for signal in DEPRECATION_SIGNALS:
                if signal in summary_lower:
                    for tool_name in finding.get("tools_mentioned", []):
                        tool_lower = tool_name.lower()
                        if tool_lower in self._registry:
                            self._registry[tool_lower].status = "deprecated"
                            alerts.append(
                                ToolAlert(
                                    alert_type="DEPRECATION",
                                    tool_name=tool_name,
                                    message=f"Deprecation signal detected for '{tool_name}': '{signal}'",
                                    url=finding.get("source_url", ""),
                                ).to_dict()
                            )

        registry_snapshot = [t.to_dict() for t in self._registry.values()]
        registry_snapshot.sort(key=lambda t: t["evaluation_score"], reverse=True)

        return {
            "registry": registry_snapshot,
            "alerts": alerts,
            "newly_discovered": newly_discovered,
            "total_tools": len(self._registry),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _load_seed_tools(self) -> None:
        """Pre-populate the registry with known tools."""
        for t in SEED_TOOLS:
            key = t["name"].lower()
            self._registry[key] = ToolRecord(
                name=t["name"],
                description=t.get("description", ""),
                category=t.get("category", "other"),
                url=t.get("url", ""),
                status=t.get("status", "active"),
                evaluation_score=t.get("evaluation_score", 7.0),
            )

    def _classify_tool(self, finding: dict[str, Any]) -> str:
        """Guess the tool category from finding context."""
        text = (finding.get("summary", "") + " ".join(finding.get("concepts", []))).lower()
        for category, keywords in TOOL_CATEGORIES.items():
            if any(kw in text for kw in keywords):
                return category
        return "other"

    def get_tools_by_category(self, category: str) -> list[dict[str, Any]]:
        """Return all tools in a given category, sorted by evaluation score."""
        tools = [
            t.to_dict()
            for t in self._registry.values()
            if t.category == category
        ]
        return sorted(tools, key=lambda t: t["evaluation_score"], reverse=True)

    def get_top_tools(self, n: int = 10) -> list[dict[str, Any]]:
        """Return the top-n tools by evaluation score."""
        all_tools = [t.to_dict() for t in self._registry.values()]
        return sorted(all_tools, key=lambda t: t["evaluation_score"], reverse=True)[:n]
