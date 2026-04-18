"""
YouTube Transcript Ingest Pipeline — fetches transcripts from public YouTube videos.

Flow:
    VideoTarget list → TranscriptFetcher → clean/chunk → raw artifact write → KnowledgeBase seed

Requires: youtube-transcript-api>=0.6.0 (optional dependency).
Falls back gracefully if the library is not installed.

No API key required for publicly available auto-generated or manual captions.
"""

import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_REQUEST_DELAY = 2.0  # seconds between transcript fetches
_MAX_KB_CHARS = 10_000  # KB entry content cap; raw file has full transcript


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class VideoTarget:
    """A YouTube video to ingest."""

    video_id: str
    persona_id: str
    title_hint: str = ""
    url: str = ""

    def __post_init__(self) -> None:
        if not self.url:
            self.url = f"https://www.youtube.com/watch?v={self.video_id}"

    @classmethod
    def from_url(cls, url: str, persona_id: str, title_hint: str = "") -> "VideoTarget":
        vid = _extract_video_id(url)
        return cls(video_id=vid, persona_id=persona_id, title_hint=title_hint, url=url)


@dataclass
class TranscriptIngestResult:
    """Result of ingesting one YouTube video transcript."""

    video_id: str
    persona_id: str
    title_hint: str = ""
    success: bool = False
    raw_path: str = ""
    transcript_chars: int = 0
    segment_count: int = 0
    error: str = ""
    ingested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "video_id": self.video_id,
            "persona_id": self.persona_id,
            "title_hint": self.title_hint,
            "success": self.success,
            "raw_path": self.raw_path,
            "transcript_chars": self.transcript_chars,
            "segment_count": self.segment_count,
            "error": self.error,
            "ingested_at": self.ingested_at.isoformat(),
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_video_id(url: str) -> str:
    """Extract YouTube video ID from various URL formats."""
    patterns = [
        r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})",
        r"(?:embed/)([A-Za-z0-9_-]{11})",
    ]
    for pat in patterns:
        m = re.search(pat, url)
        if m:
            return m.group(1)
    # Assume the input is already a bare video ID
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url):
        return url
    raise ValueError(f"Cannot extract video ID from: {url}")


def _segments_to_text(segments: list[dict]) -> str:
    """Convert transcript segment list to a clean readable string."""
    parts = []
    for seg in segments:
        text = seg.get("text", "").strip()
        if text:
            parts.append(text)
    return " ".join(parts)


def _clean_transcript(raw: str) -> str:
    """Remove common transcript noise patterns."""
    # Remove [Music], [Applause], etc.
    cleaned = re.sub(r"\[[\w\s]+\]", "", raw)
    # Collapse multiple spaces
    cleaned = re.sub(r" {2,}", " ", cleaned)
    return cleaned.strip()


# ---------------------------------------------------------------------------
# Fetcher
# ---------------------------------------------------------------------------

class TranscriptFetcher:
    """
    Wraps youtube-transcript-api with graceful fallback if not installed.

    Prefers manual English captions, falls back to auto-generated.
    """

    def __init__(self) -> None:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            self._api = YouTubeTranscriptApi()  # v1.x requires an instance
            self._available = True
        except ImportError:
            logger.warning(
                "youtube-transcript-api not installed. "
                "Run: pip install youtube-transcript-api"
            )
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def fetch(self, video_id: str) -> tuple[list[dict], str] | tuple[None, str]:
        """
        Fetch transcript segments for a video.

        Returns:
            (segments, language) on success, (None, error_message) on failure.
        """
        if not self._available:
            return None, "youtube-transcript-api not installed"

        # Prefer manual English, fall back through variants, then any language
        for lang_codes in (("en",), ("en-US", "en-GB")):
            try:
                fetched = self._api.fetch(video_id, languages=lang_codes)
                segments = [{"text": s.text} for s in fetched]
                return segments, "en"
            except Exception:  # noqa: BLE001
                pass
        # Final fallback: let the library pick any available language
        try:
            transcript_list = self._api.list(video_id)
            t = next(iter(transcript_list))
            fetched = self._api.fetch(video_id, languages=(t.language_code,))
            segments = [{"text": s.text} for s in fetched]
            return segments, t.language_code
        except Exception as exc:  # noqa: BLE001
            return None, str(exc)


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class YouTubeIngestPipeline:
    """
    Ingests YouTube video transcripts and seeds them into the wiki raw layer
    and optionally into the KnowledgeBase.

    Usage::

        from src.pipeline.youtube_ingest import YouTubeIngestPipeline, VideoTarget
        from src.knowledge.knowledge_base import KnowledgeBase

        kb = KnowledgeBase(); kb.initialize()
        pipeline = YouTubeIngestPipeline(raw_dir="data/wiki/raw", kb=kb)
        targets = [VideoTarget.from_url("https://youtu.be/...", "karpathy")]
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
        self._fetcher = TranscriptFetcher()
        self._delay = request_delay

    def run(self, targets: list[VideoTarget]) -> list[TranscriptIngestResult]:
        """Ingest all targets; return one result per target."""
        if not self._fetcher.available:
            logger.error("TranscriptFetcher unavailable; install youtube-transcript-api")
            return [
                TranscriptIngestResult(
                    video_id=t.video_id,
                    persona_id=t.persona_id,
                    title_hint=t.title_hint,
                    error="youtube-transcript-api not installed",
                )
                for t in targets
            ]

        results: list[TranscriptIngestResult] = []
        for i, target in enumerate(targets):
            if i > 0:
                time.sleep(self._delay)
            result = self._ingest_one(target)
            results.append(result)
            status = "OK" if result.success else f"FAIL: {result.error}"
            logger.info(
                "[%d/%d] %s (%s) — %s",
                i + 1, len(targets), target.video_id, target.title_hint, status,
            )
        return results

    def _ingest_one(self, target: VideoTarget) -> TranscriptIngestResult:
        result = TranscriptIngestResult(
            video_id=target.video_id,
            persona_id=target.persona_id,
            title_hint=target.title_hint,
        )

        segments, lang_or_error = self._fetcher.fetch(target.video_id)
        if segments is None:
            result.error = lang_or_error
            return result

        raw_text = _segments_to_text(segments)
        clean_text = _clean_transcript(raw_text)
        result.transcript_chars = len(clean_text)
        result.segment_count = len(segments)

        # Write raw artifact
        persona_dir = self._raw_dir / target.persona_id
        persona_dir.mkdir(parents=True, exist_ok=True)
        safe_title = re.sub(r"[^\w\-]", "_", target.title_hint or target.video_id)[:60]
        raw_path = persona_dir / f"youtube_{target.video_id}_{safe_title}.txt"
        header = (
            f"# Transcript: {target.title_hint or target.video_id}\n"
            f"video_id: {target.video_id}\n"
            f"url: {target.url}\n"
            f"persona_id: {target.persona_id}\n"
            f"language: {lang_or_error}\n"
            f"ingested_at: {result.ingested_at.isoformat()}\n"
            f"segments: {result.segment_count}\n"
            f"chars: {result.transcript_chars}\n\n"
            "---\n\n"
        )
        raw_path.write_text(header + clean_text, encoding="utf-8")
        result.raw_path = str(raw_path)

        # Seed into KnowledgeBase if provided
        if self._kb is not None:
            self._seed_kb(target, clean_text, lang_or_error)

        result.success = True
        return result

    def _seed_kb(self, target: VideoTarget, clean_text: str, language: str) -> None:
        from ..knowledge.knowledge_base import KnowledgeEntry
        from ..utils.helpers import sanitize_text

        safe_content = sanitize_text(clean_text)
        content_excerpt = safe_content[:_MAX_KB_CHARS]

        entry = KnowledgeEntry(
            title=f"YouTube Transcript: {target.title_hint or target.video_id}",
            content=content_excerpt,
            namespace="education",
            content_type="youtube_transcript",
            source_url=target.url,
            source_name=f"youtube_{target.video_id}",
            confidence=0.85,
            metadata={
                "persona_id": target.persona_id,
                "video_id": target.video_id,
                "language": language,
                "full_chars": len(clean_text),
            },
        )
        try:
            self._kb.store(entry)
            logger.info("Seeded KB: %s", entry.title)
        except Exception as exc:  # noqa: BLE001
            logger.warning("KB seed failed for %s: %s", target.video_id, exc)
