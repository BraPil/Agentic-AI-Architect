"""
Research Agent — Deep research and knowledge synthesis.

Takes raw crawled documents and transforms them into structured knowledge:
  - Content type classification (paper | blog | tool_release | benchmark | opinion)
  - Concept and entity extraction
  - Structured summary generation
  - Source attribution and confidence scoring
  - Storage to the knowledge base

LLM calls use the configured provider; classification falls back to heuristics
when no LLM is available (offline / test mode).
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class ResearchFinding:
    """A structured piece of knowledge extracted from a raw document."""

    title: str
    summary: str
    content_type: str  # paper | blog | tool_release | benchmark | opinion | docs | forum
    concepts: list[str] = field(default_factory=list)
    tools_mentioned: list[str] = field(default_factory=list)
    people_mentioned: list[str] = field(default_factory=list)
    source_url: str = ""
    source_name: str = ""
    confidence: float = 0.8
    namespace: str = "general"  # education | frameworks | trends | tools | general
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "summary": self.summary,
            "content_type": self.content_type,
            "concepts": self.concepts,
            "tools_mentioned": self.tools_mentioned,
            "people_mentioned": self.people_mentioned,
            "source_url": self.source_url,
            "source_name": self.source_name,
            "confidence": self.confidence,
            "namespace": self.namespace,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Known entities for heuristic extraction
# ---------------------------------------------------------------------------

KNOWN_TOOLS = {
    "langchain", "langgraph", "llamaindex", "autogen", "crewai", "dspy",
    "faiss", "pinecone", "weaviate", "qdrant", "chromadb", "pgvector",
    "mlflow", "wandb", "weights & biases", "optuna", "ray", "vllm",
    "firecrawl", "playwright", "openai", "anthropic", "gemini", "mistral",
    "ollama", "huggingface", "transformers", "pydantic", "fastapi",
    "langsmith", "mcp", "semantic kernel", "haystack", "bentoml",
    "modal", "replicate", "groq", "deepseek", "cursor", "devin",
    "swe-agent", "github copilot", "llama", "phi", "gemma",
}

KNOWN_PEOPLE = {
    "andrej karpathy", "yann lecun", "geoffrey hinton", "yoshua bengio",
    "ilya sutskever", "demis hassabis", "dario amodei", "harrison chase",
    "jerry liu", "swyx", "shawn wang", "simon willison", "chip huyen",
    "lilian weng", "andrew ng", "cassie kozyrkov", "carlos guestrin",
    "jim fan", "percy liang", "kanjun qiu",
}

NAMESPACE_KEYWORDS: dict[str, list[str]] = {
    "tools": [
        "library", "framework", "sdk", "api", "package", "tool", "plugin",
        "release", "version", "install", "npm", "pip", "github.com",
    ],
    "frameworks": [
        "architecture", "pattern", "paradigm", "approach", "method",
        "algorithm", "model", "training", "fine-tuning", "rag", "retrieval",
    ],
    "trends": [
        "trend", "adoption", "popular", "emerging", "growing", "startup",
        "enterprise", "industry", "survey", "report", "benchmark",
    ],
    "education": [
        "introduction", "tutorial", "guide", "course", "learn", "beginner",
        "explained", "how to", "understanding", "deep dive",
    ],
}

CONTENT_TYPE_PATTERNS: dict[str, list[str]] = {
    "paper": [r"\barxiv\b", r"\bpaper\b", r"\bpropose\b", r"\bwe show\b", r"\bexperiment"],
    "tool_release": [r"\brelease\b", r"\blaunch\b", r"\bintroduc", r"\bnew version\b", r"\bv\d+\.\d+"],
    "benchmark": [r"\bbenchmark\b", r"\bevaluat", r"\bscore\b", r"\bleaderboard\b", r"\bbaseline"],
    "opinion": [r"\bopinion\b", r"\bthink\b", r"\bbelieve\b", r"\bmy take\b", r"\bperspective"],
    "docs": [r"\bdocumentation\b", r"\bguide\b", r"\btutorial\b", r"\bhow to\b"],
    "forum": [r"\bdiscussion\b", r"\bask hn\b", r"\bcomment\b", r"\bthread\b"],
    "blog": [],  # catch-all
}


# ---------------------------------------------------------------------------
# ResearchAgent
# ---------------------------------------------------------------------------

class ResearchAgent(BaseAgent):
    """
    Converts raw crawled documents into :class:`ResearchFinding` records.

    Configuration keys:
        llm_client: An optional callable ``llm_client(prompt: str) -> str``
                    for LLM-powered extraction. Falls back to heuristics if None.
        min_content_length (int): Skip documents shorter than this (default 100).
        confidence_threshold (float): Discard findings below this score (default 0.3).
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(name="ResearchAgent", config=config)
        self._llm_client = self.config.get("llm_client")
        self._min_content_length: int = self.config.get("min_content_length", 100)
        self._confidence_threshold: float = self.config.get("confidence_threshold", 0.3)

    # ------------------------------------------------------------------
    # Core execution
    # ------------------------------------------------------------------

    def _execute(self, task_input: Any = None) -> list[dict[str, Any]]:
        """Process a list of crawled document dicts; return research findings."""
        raw_docs: list[dict[str, Any]] = task_input if isinstance(task_input, list) else []
        findings: list[dict[str, Any]] = []

        for doc in raw_docs:
            if not isinstance(doc, dict):
                continue
            content = doc.get("content", "")
            if len(content) < self._min_content_length:
                continue

            finding = self._process_document(doc)
            if finding and finding.confidence >= self._confidence_threshold:
                findings.append(finding.to_dict())

        self.logger.info("ResearchAgent produced %d findings from %d documents", len(findings), len(raw_docs))
        return findings

    # ------------------------------------------------------------------
    # Document processing
    # ------------------------------------------------------------------

    def _process_document(self, doc: dict[str, Any]) -> ResearchFinding | None:
        """Extract structured knowledge from a single document."""
        content = doc.get("content", "")
        title = doc.get("title", "")
        url = doc.get("url", "")
        source_name = doc.get("metadata", {}).get("source_name", "")

        if self._llm_client:
            return self._llm_extract(doc)

        return self._heuristic_extract(content, title, url, source_name, doc.get("source_type", "blog"))

    def _heuristic_extract(
        self,
        content: str,
        title: str,
        url: str,
        source_name: str,
        source_type: str,
    ) -> ResearchFinding:
        """Rule-based extraction when no LLM is available."""
        content_lower = content.lower()

        # Classify content type
        content_type = self._classify_content_type(content_lower, source_type)

        # Detect namespace
        namespace = self._detect_namespace(content_lower)

        # Extract concepts (capitalized noun phrases, simple heuristic)
        concepts = self._extract_concepts(content)

        # Extract known tool mentions
        tools = [t for t in KNOWN_TOOLS if t in content_lower]

        # Extract known people mentions
        people = [p for p in KNOWN_PEOPLE if p in content_lower]

        # Simple summary: first 400 chars of clean content
        summary = re.sub(r"\s+", " ", content[:400]).strip()

        # Confidence: higher for longer, more structured content
        confidence = min(1.0, 0.3 + len(content) / 10_000 + 0.1 * len(tools))

        return ResearchFinding(
            title=title or url,
            summary=summary,
            content_type=content_type,
            concepts=concepts[:20],
            tools_mentioned=list(set(tools))[:15],
            people_mentioned=list(set(people))[:10],
            source_url=url,
            source_name=source_name,
            confidence=confidence,
            namespace=namespace,
        )

    def _llm_extract(self, doc: dict[str, Any]) -> ResearchFinding | None:
        """LLM-powered extraction — called only when ``_llm_client`` is configured."""
        assert self._llm_client is not None

        content = doc.get("content", "")[:3000]  # Truncate to stay within context
        title = doc.get("title", "")
        url = doc.get("url", "")

        prompt = f"""You are an AI architecture knowledge extractor.

Analyse the following document and return a JSON object with these fields:
- title: string (document title)
- summary: string (2-3 sentence summary focused on AI architecture insights)
- content_type: one of [paper, blog, tool_release, benchmark, opinion, docs, forum]
- concepts: list of up to 10 AI architecture concepts mentioned
- tools_mentioned: list of AI tools or frameworks named
- people_mentioned: list of people named
- namespace: one of [education, frameworks, trends, tools, general]
- confidence: float 0.0-1.0 (how confident you are in the extraction quality)

Document title: {title}
Document URL: {url}
Document content:
{content}

Return ONLY valid JSON, no other text."""

        try:
            raw = self._llm_client(prompt)
            data = json.loads(raw)
            return ResearchFinding(
                title=data.get("title", title),
                summary=data.get("summary", ""),
                content_type=data.get("content_type", "blog"),
                concepts=data.get("concepts", []),
                tools_mentioned=data.get("tools_mentioned", []),
                people_mentioned=data.get("people_mentioned", []),
                source_url=url,
                source_name=doc.get("metadata", {}).get("source_name", ""),
                confidence=float(data.get("confidence", 0.7)),
                namespace=data.get("namespace", "general"),
            )
        except Exception as exc:  # noqa: BLE001
            self.logger.warning("LLM extraction failed, falling back to heuristics: %s", exc)
            return self._heuristic_extract(
                doc.get("content", ""),
                title,
                url,
                doc.get("metadata", {}).get("source_name", ""),
                doc.get("source_type", "blog"),
            )

    # ------------------------------------------------------------------
    # Classification helpers
    # ------------------------------------------------------------------

    def _classify_content_type(self, content_lower: str, source_type: str) -> str:
        """Return the most likely content type label."""
        for ctype, patterns in CONTENT_TYPE_PATTERNS.items():
            if any(re.search(p, content_lower) for p in patterns):
                return ctype
        # Fall back to source type
        return source_type if source_type in {"paper", "blog", "docs", "forum"} else "blog"

    def _detect_namespace(self, content_lower: str) -> str:
        """Map document content to a knowledge namespace."""
        scores: dict[str, int] = {}
        for ns, keywords in NAMESPACE_KEYWORDS.items():
            scores[ns] = sum(content_lower.count(kw) for kw in keywords)
        if not any(scores.values()):
            return "general"
        return max(scores, key=lambda k: scores[k])

    def _extract_concepts(self, text: str) -> list[str]:
        """Extract capitalised multi-word phrases as candidate concepts."""
        matches = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b", text)
        # Deduplicate while preserving order
        seen: set[str] = set()
        unique = []
        for m in matches:
            if m not in seen:
                seen.add(m)
                unique.append(m)
        return unique
