"""
GitHub Ingest Pipeline — fetches README and top-level structure from public repos.

Flow:
    RepoTarget list → GitHubReadmeFetcher → raw artifact write → KnowledgeBase seed

No API key required for public repos. Uses raw.githubusercontent.com for README fetch.
Rate-limited to respect GitHub's anonymous limits.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_RAW_BASE = "https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
_DEFAULT_BRANCHES = ("main", "master")
_README_CANDIDATES = ("README.md", "readme.md", "README.rst", "README.txt", "README")
_REQUEST_DELAY = 1.5  # seconds between requests (anonymous GitHub rate limit)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class RepoTarget:
    """A GitHub repository to ingest."""

    owner: str
    repo: str
    persona_id: str
    foundational: bool = False
    why: str = ""
    url: str = ""

    @classmethod
    def from_registry_entry(cls, entry: dict[str, Any], persona_id: str) -> "RepoTarget":
        raw_url = entry.get("url", "")
        parts = raw_url.rstrip("/").split("/")
        owner = parts[-2] if len(parts) >= 2 else ""
        repo = parts[-1] if parts else ""
        return cls(
            owner=owner,
            repo=repo,
            persona_id=persona_id,
            foundational=entry.get("foundational", False),
            why=entry.get("why", ""),
            url=raw_url,
        )


@dataclass
class RepoIngestResult:
    """Result of ingesting one GitHub repository."""

    owner: str
    repo: str
    persona_id: str
    success: bool = False
    raw_path: str = ""
    readme_chars: int = 0
    error: str = ""
    ingested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "owner": self.owner,
            "repo": self.repo,
            "persona_id": self.persona_id,
            "success": self.success,
            "raw_path": self.raw_path,
            "readme_chars": self.readme_chars,
            "error": self.error,
            "ingested_at": self.ingested_at.isoformat(),
        }


# ---------------------------------------------------------------------------
# Fetcher
# ---------------------------------------------------------------------------

class GitHubReadmeFetcher:
    """
    Fetches README content from public GitHub repositories.

    No API key required. Falls back across branch names and README filename
    variants. Sanitizes content before returning.
    """

    def __init__(self) -> None:
        try:
            import requests
            self._requests = requests
        except ImportError:
            self._requests = None

    def fetch(self, owner: str, repo: str) -> str | None:
        """Return README content string, or None if not found."""
        if self._requests is None:
            logger.error("requests library not available")
            return None

        for branch in _DEFAULT_BRANCHES:
            for filename in _README_CANDIDATES:
                url = _RAW_BASE.format(owner=owner, repo=repo, branch=branch, path=filename)
                try:
                    resp = self._requests.get(url, timeout=15)
                    if resp.status_code == 200:
                        logger.info("Fetched %s/%s README from %s", owner, repo, url)
                        return resp.text
                except Exception as exc:  # noqa: BLE001
                    logger.debug("Request error for %s: %s", url, exc)
        logger.warning("No README found for %s/%s", owner, repo)
        return None


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class GitHubIngestPipeline:
    """
    Ingests GitHub repository READMEs and seeds them into the wiki raw layer
    and optionally into the KnowledgeBase.

    Usage::

        from src.pipeline.github_ingest import GitHubIngestPipeline, RepoTarget
        from src.knowledge.knowledge_base import KnowledgeBase

        kb = KnowledgeBase(); kb.initialize()
        pipeline = GitHubIngestPipeline(raw_dir="data/wiki/raw", kb=kb)
        results = pipeline.run(targets)
    """

    def __init__(
        self,
        raw_dir: str = "data/wiki/raw",
        kb: Any = None,
        request_delay: float = _REQUEST_DELAY,
    ) -> None:
        self._raw_dir = Path(raw_dir)
        self._kb = kb
        self._fetcher = GitHubReadmeFetcher()
        self._delay = request_delay

    def run(self, targets: list[RepoTarget]) -> list[RepoIngestResult]:
        """Ingest all targets; return one result per target."""
        results: list[RepoIngestResult] = []
        for i, target in enumerate(targets):
            if i > 0:
                time.sleep(self._delay)
            result = self._ingest_one(target)
            results.append(result)
            status = "OK" if result.success else f"FAIL: {result.error}"
            logger.info("[%d/%d] %s/%s — %s", i + 1, len(targets), target.owner, target.repo, status)
        return results

    def _ingest_one(self, target: RepoTarget) -> RepoIngestResult:
        result = RepoIngestResult(owner=target.owner, repo=target.repo, persona_id=target.persona_id)

        readme = self._fetcher.fetch(target.owner, target.repo)
        if readme is None:
            result.error = "README not found"
            return result

        # Write raw artifact
        persona_dir = self._raw_dir / target.persona_id
        persona_dir.mkdir(parents=True, exist_ok=True)
        raw_path = persona_dir / f"github_{target.owner}_{target.repo}_readme.md"
        raw_path.write_text(readme, encoding="utf-8")
        result.raw_path = str(raw_path)
        result.readme_chars = len(readme)

        # Seed into KnowledgeBase if provided
        if self._kb is not None:
            self._seed_kb(target, readme)

        result.success = True
        return result

    def _seed_kb(self, target: RepoTarget, readme: str) -> None:
        from ..knowledge.knowledge_base import KnowledgeEntry
        from ..utils.helpers import sanitize_text

        safe_content = sanitize_text(readme)
        # Truncate to 8000 chars for the KB entry; raw file has the full text
        content_excerpt = safe_content[:8000]

        namespace = "tools" if not target.foundational else "education"
        entry = KnowledgeEntry(
            title=f"GitHub: {target.owner}/{target.repo}",
            content=content_excerpt,
            namespace=namespace,
            content_type="github_readme",
            source_url=target.url or f"https://github.com/{target.owner}/{target.repo}",
            source_name=f"github_{target.owner}_{target.repo}",
            confidence=0.9,
            metadata={
                "persona_id": target.persona_id,
                "foundational": target.foundational,
                "why": target.why,
                "full_chars": len(readme),
            },
        )
        try:
            self._kb.store(entry)
            logger.info("Seeded KB: %s", entry.title)
        except Exception as exc:  # noqa: BLE001
            logger.warning("KB seed failed for %s/%s: %s", target.owner, target.repo, exc)
