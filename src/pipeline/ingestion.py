"""
Ingestion Pipeline — Orchestrates the flow from raw URLs to knowledge base entries.

Flow:
    URL list → CrawlerAgent → ContentProcessor → ResearchAgent → KnowledgeBase
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from ..agents.crawler_agent import CrawlerAgent
from ..agents.research_agent import ResearchAgent
from ..knowledge.knowledge_base import KnowledgeBase, KnowledgeEntry

logger = logging.getLogger(__name__)


@dataclass
class IngestionResult:
    """Result of an ingestion pipeline run."""

    urls_submitted: int = 0
    documents_crawled: int = 0
    findings_extracted: int = 0
    entries_stored: int = 0
    errors: list[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None

    @property
    def success_rate(self) -> float:
        if self.urls_submitted == 0:
            return 0.0
        return self.entries_stored / self.urls_submitted

    def to_dict(self) -> dict[str, Any]:
        return {
            "urls_submitted": self.urls_submitted,
            "documents_crawled": self.documents_crawled,
            "findings_extracted": self.findings_extracted,
            "entries_stored": self.entries_stored,
            "success_rate": round(self.success_rate, 3),
            "errors": self.errors,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class IngestionPipeline:
    """
    Connects the Crawler, Research, and Knowledge Base components into a
    single end-to-end data ingestion flow.

    Usage::

        kb = KnowledgeBase("data/knowledge_base.db")
        kb.initialize()

        pipeline = IngestionPipeline(knowledge_base=kb)
        pipeline.initialize()

        result = pipeline.ingest_urls(["https://arxiv.org/abs/2401.00001"])
    """

    def __init__(
        self,
        knowledge_base: KnowledgeBase,
        crawler_config: dict[str, Any] | None = None,
        research_config: dict[str, Any] | None = None,
        min_confidence: float = 0.4,
    ) -> None:
        self._kb = knowledge_base
        self._crawler = CrawlerAgent(config=crawler_config)
        self._researcher = ResearchAgent(config=research_config)
        self._min_confidence = min_confidence
        self._initialized = False

    def initialize(self) -> None:
        """Initialize all pipeline components."""
        self._crawler.initialize()
        self._researcher.initialize()
        self._initialized = True
        logger.info("IngestionPipeline initialized")

    def shutdown(self) -> None:
        """Shut down all pipeline components."""
        self._crawler.shutdown()
        self._researcher.shutdown()
        self._initialized = False

    def ingest_urls(self, urls: list[str]) -> IngestionResult:
        """
        Crawl, research, and store knowledge from the given URLs.

        Args:
            urls: List of URLs to process.

        Returns:
            IngestionResult with metrics.
        """
        if not self._initialized:
            self.initialize()

        result = IngestionResult(urls_submitted=len(urls))

        # Build source dicts for the crawler
        sources = [{"url": url, "type": "unknown", "name": url} for url in urls]

        # Step 1: Crawl
        crawl_result = self._crawler.run(task_input=sources)
        if crawl_result.data:
            documents = crawl_result.data
            result.documents_crawled = len(documents)
        else:
            result.errors.append(f"Crawl failed: {crawl_result.error}")
            result.completed_at = datetime.now(timezone.utc)
            return result

        # Step 2: Research
        research_result = self._researcher.run(task_input=documents)
        if research_result.data:
            findings = research_result.data
            result.findings_extracted = len(findings)
        else:
            result.errors.append(f"Research failed: {research_result.error}")
            result.completed_at = datetime.now(timezone.utc)
            return result

        # Step 3: Store in knowledge base
        for finding in findings:
            if finding.get("confidence", 0) < self._min_confidence:
                continue
            try:
                entry = KnowledgeEntry.from_finding(finding)
                self._kb.store(entry)
                result.entries_stored += 1
            except Exception as exc:  # noqa: BLE001
                result.errors.append(f"Storage error: {exc}")

        result.completed_at = datetime.now(timezone.utc)
        logger.info(
            "Ingestion complete: %d URLs → %d docs → %d findings → %d stored",
            result.urls_submitted,
            result.documents_crawled,
            result.findings_extracted,
            result.entries_stored,
        )
        return result

    def ingest_default_sources(self) -> IngestionResult:
        """Run ingestion for all default sources configured in CrawlerAgent."""
        if not self._initialized:
            self.initialize()

        result = IngestionResult()

        # Crawl default sources
        crawl_result = self._crawler.run()
        if crawl_result.data:
            documents = crawl_result.data
            result.documents_crawled = len(documents)
            result.urls_submitted = len(documents)
        else:
            result.errors.append(f"Crawl failed: {crawl_result.error}")
            result.completed_at = datetime.now(timezone.utc)
            return result

        # Research
        research_result = self._researcher.run(task_input=documents)
        if research_result.data:
            findings = research_result.data
            result.findings_extracted = len(findings)
        else:
            result.errors.append(f"Research failed: {research_result.error}")
            result.completed_at = datetime.now(timezone.utc)
            return result

        # Store
        for finding in findings:
            if finding.get("confidence", 0) < self._min_confidence:
                continue
            try:
                entry = KnowledgeEntry.from_finding(finding)
                self._kb.store(entry)
                result.entries_stored += 1
            except Exception as exc:  # noqa: BLE001
                result.errors.append(f"Storage error: {exc}")

        result.completed_at = datetime.now(timezone.utc)
        return result
