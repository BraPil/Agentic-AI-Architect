"""
Crawler Agent — Web crawling and data discovery.

Scours configured sources for new AI architecture content:
  - arXiv papers (cs.AI, cs.LG, cs.CL)
  - GitHub trending repositories (ai, llm, rag, mcp, agents topics)
  - Hacker News (AI-related stories)
  - Official blogs: Anthropic, OpenAI, LangChain, LlamaIndex, HuggingFace
  - Reddit (r/MachineLearning, r/LocalLLaMA, r/artificial)

Rate limiting and robots.txt compliance are enforced by default.
"""

import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class CrawledDocument:
    """Represents a single crawled piece of content."""

    url: str
    title: str
    content: str
    source_type: str  # paper | blog | github | forum | docs
    crawled_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def content_hash(self) -> str:
        """SHA-256 of the content — used for deduplication."""
        return hashlib.sha256(self.content.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "content": self.content,
            "source_type": self.source_type,
            "crawled_at": self.crawled_at.isoformat(),
            "content_hash": self.content_hash,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Default source configuration
# ---------------------------------------------------------------------------

DEFAULT_SOURCES: list[dict[str, Any]] = [
    # arXiv RSS feeds (AI/ML categories)
    {"url": "https://rss.arxiv.org/rss/cs.AI", "type": "paper", "name": "arXiv cs.AI"},
    {"url": "https://rss.arxiv.org/rss/cs.LG", "type": "paper", "name": "arXiv cs.LG"},
    {"url": "https://rss.arxiv.org/rss/cs.CL", "type": "paper", "name": "arXiv cs.CL"},
    # GitHub trending (via unofficial JSON API wrapper concept)
    {"url": "https://github.com/trending?spoken_language_code=en", "type": "github", "name": "GitHub Trending"},
    # Hacker News Algolia API — AI stories
    {
        "url": "https://hn.algolia.com/api/v1/search?query=LLM+agents&tags=story&hitsPerPage=20",
        "type": "forum",
        "name": "Hacker News AI",
    },
    {
        "url": "https://hn.algolia.com/api/v1/search?query=MCP+model+context&tags=story&hitsPerPage=20",
        "type": "forum",
        "name": "Hacker News MCP",
    },
    # Official blogs
    {"url": "https://www.anthropic.com/news", "type": "blog", "name": "Anthropic Blog"},
    {"url": "https://openai.com/blog", "type": "blog", "name": "OpenAI Blog"},
    {"url": "https://blog.langchain.dev", "type": "blog", "name": "LangChain Blog"},
    {"url": "https://www.llamaindex.ai/blog", "type": "blog", "name": "LlamaIndex Blog"},
    {"url": "https://huggingface.co/blog", "type": "blog", "name": "HuggingFace Blog"},
    {"url": "https://mistral.ai/news", "type": "blog", "name": "Mistral Blog"},
]


# ---------------------------------------------------------------------------
# CrawlerAgent
# ---------------------------------------------------------------------------

class CrawlerAgent(BaseAgent):
    """
    Fetches content from configured sources and returns :class:`CrawledDocument`
    instances for downstream processing.

    Configuration keys (``config`` dict):
        sources (list[dict]): Override the default source list.
        user_agent (str): HTTP User-Agent header sent with every request.
        request_timeout (int): Per-request timeout in seconds (default 15).
        rate_limit_seconds (float): Minimum gap between requests (default 1.0).
        max_content_length (int): Truncate content beyond this many chars (default 50_000).
        respect_robots_txt (bool): Enforce robots.txt rules (default True).
    """

    DEFAULT_USER_AGENT = (
        "AgenticAIArchitect/1.0 (research crawler; "
        "https://github.com/BraPil/Agentic-AI-Architect)"
    )

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(name="CrawlerAgent", config=config)
        self._sources: list[dict[str, Any]] = self.config.get("sources", DEFAULT_SOURCES)
        self._user_agent: str = self.config.get("user_agent", self.DEFAULT_USER_AGENT)
        self._request_timeout: int = self.config.get("request_timeout", 15)
        self._rate_limit: float = self.config.get("rate_limit_seconds", 1.0)
        self._max_content_length: int = self.config.get("max_content_length", 50_000)
        self._respect_robots: bool = self.config.get("respect_robots_txt", True)
        self._session: requests.Session | None = None
        self._robots_cache: dict[str, RobotFileParser] = {}
        self._seen_hashes: set[str] = set()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        super().initialize()
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": self._user_agent})
        self.logger.info("CrawlerAgent initialized with %d sources", len(self._sources))

    def shutdown(self) -> None:
        if self._session:
            self._session.close()
            self._session = None
        super().shutdown()

    # ------------------------------------------------------------------
    # Core execution
    # ------------------------------------------------------------------

    def _execute(self, task_input: Any = None) -> list[dict[str, Any]]:
        """Crawl all configured sources and return a list of document dicts."""
        sources: list[dict[str, Any]] = task_input if isinstance(task_input, list) else self._sources
        documents: list[dict[str, Any]] = []

        for source in sources:
            url = source.get("url", "")
            source_type = source.get("type", "unknown")
            source_name = source.get("name", url)

            if not url:
                continue

            if self._respect_robots and not self._is_allowed(url):
                self.logger.warning("robots.txt disallows crawling: %s", url)
                continue

            try:
                doc = self._fetch_url(url, source_type, source_name)
                if doc and not self._is_duplicate(doc):
                    self._seen_hashes.add(doc.content_hash)
                    documents.append(doc.to_dict())
                    self.logger.debug("Crawled: %s (%d chars)", url, len(doc.content))
            except Exception as exc:  # noqa: BLE001
                self.logger.warning("Failed to crawl %s: %s", url, exc)

            time.sleep(self._rate_limit)

        self.logger.info("CrawlerAgent finished: %d documents collected", len(documents))
        return documents

    # ------------------------------------------------------------------
    # Fetching helpers
    # ------------------------------------------------------------------

    def _fetch_url(self, url: str, source_type: str, source_name: str) -> CrawledDocument | None:
        """Fetch a single URL and return a :class:`CrawledDocument`."""
        assert self._session is not None, "CrawlerAgent not initialized"

        response = self._session.get(url, timeout=self._request_timeout)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")

        if "json" in content_type:
            content = self._extract_from_json(response.json(), source_type)
            title = source_name
        else:
            content, title = self._extract_from_html(response.text, url)

        content = content[: self._max_content_length]

        if not content.strip():
            return None

        return CrawledDocument(
            url=url,
            title=title or source_name,
            content=content,
            source_type=source_type,
            metadata={
                "source_name": source_name,
                "content_type": content_type,
                "status_code": response.status_code,
            },
        )

    def _extract_from_html(self, html: str, url: str) -> tuple[str, str]:
        """Best-effort HTML → plain text extraction without BeautifulSoup dependency."""
        import re  # noqa: PLC0415

        # Strip script and style blocks
        html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.DOTALL | re.IGNORECASE)
        # Extract title
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else url
        # Strip all remaining tags
        text = re.sub(r"<[^>]+>", " ", html)
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text, title

    def _extract_from_json(self, data: Any, source_type: str) -> str:
        """Extract readable text from known JSON API shapes (HN Algolia, etc.)."""
        if isinstance(data, dict):
            # Hacker News Algolia
            if "hits" in data:
                pieces = []
                for hit in data["hits"]:
                    title = hit.get("title", "")
                    story_text = hit.get("story_text") or hit.get("comment_text") or ""
                    url = hit.get("url", "")
                    if title:
                        pieces.append(f"# {title}\n{url}\n{story_text}")
                return "\n\n".join(pieces)
        return str(data)

    # ------------------------------------------------------------------
    # robots.txt compliance
    # ------------------------------------------------------------------

    def _is_allowed(self, url: str) -> bool:
        """Check robots.txt for the given URL. Returns True if crawling is allowed."""
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"

        if base not in self._robots_cache:
            rp = RobotFileParser()
            rp.set_url(f"{base}/robots.txt")
            try:
                rp.read()
            except Exception:  # noqa: BLE001
                # If robots.txt is unreachable, assume allowed
                rp.allow_all = True
            self._robots_cache[base] = rp

        return self._robots_cache[base].can_fetch(self._user_agent, url)

    # ------------------------------------------------------------------
    # Deduplication
    # ------------------------------------------------------------------

    def _is_duplicate(self, doc: CrawledDocument) -> bool:
        return doc.content_hash in self._seen_hashes
