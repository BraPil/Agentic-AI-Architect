"""
YouTube Transcript Ingest Pipeline — fetches transcripts from public YouTube videos.

Flow:
    VideoTarget list → TranscriptFetcher → clean → raw artifact write → KnowledgeBase seed

Fetch strategy (in priority order):
  1. youtube-transcript-api with optional proxy config (fastest, no subprocess)
  2. yt-dlp with optional cookies.txt (handles IP blocks via browser session)

For Codespace / cloud environments YouTube will block direct requests.
See scripts/fetch_youtube_transcripts.py for the CLI wrapper with cookie/proxy guidance.

Optional dependencies:
  youtube-transcript-api>=0.6.0   (pip install youtube-transcript-api)
  yt-dlp                          (pip install yt-dlp)
"""

import json
import logging
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_REQUEST_DELAY = 2.0   # seconds between fetches
_MAX_KB_CHARS = 10_000  # KB entry cap; raw file has full transcript


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class VideoTarget:
    """A YouTube video to ingest."""

    video_id: str
    persona_id: str
    title: str = ""
    published_at: str = ""
    url: str = ""

    def __post_init__(self) -> None:
        if not self.url:
            self.url = f"https://www.youtube.com/watch?v={self.video_id}"

    @classmethod
    def from_url(cls, url: str, persona_id: str, title: str = "", published_at: str = "") -> "VideoTarget":
        vid = _extract_video_id(url)
        return cls(video_id=vid, persona_id=persona_id, title=title, published_at=published_at, url=url)


@dataclass
class TranscriptIngestResult:
    """Result of ingesting one YouTube video transcript."""

    video_id: str
    persona_id: str
    title: str = ""
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
            "title": self.title,
            "success": self.success,
            "raw_path": self.raw_path,
            "transcript_chars": self.transcript_chars,
            "segment_count": self.segment_count,
            "error": self.error,
            "ingested_at": self.ingested_at.isoformat(),
        }


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def _extract_video_id(url: str) -> str:
    """Extract YouTube video ID from various URL formats."""
    for pat in (r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", r"(?:embed/)([A-Za-z0-9_-]{11})"):
        m = re.search(pat, url)
        if m:
            return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url):
        return url
    raise ValueError(f"Cannot extract video ID from: {url}")


def _segments_to_text(segments: list[dict]) -> str:
    return " ".join(seg.get("text", "").strip() for seg in segments if seg.get("text", "").strip())


def _json3_to_text(raw: str) -> str:
    """Convert YouTube json3 subtitle format to plain text."""
    data = json.loads(raw)
    words = []
    for event in data.get("events", []):
        for seg in event.get("segs", []):
            word = seg.get("utf8", "").strip()
            if word and word != "\n":
                words.append(word)
    text = " ".join(words)
    # Remove immediate duplicate phrases (auto-caption artifact)
    text = re.sub(r"(\b.{10,40}\b) \1", r"\1", text)
    return text.strip()


def _vtt_to_text(vtt: str) -> str:
    """Strip VTT timestamps and deduplicate repeated lines."""
    lines, seen = [], set()
    for line in vtt.splitlines():
        line = re.sub(r"<[^>]+>", "", line.strip())
        line = re.sub(r"^\d+$", "", line).strip()
        if line and "-->" not in line and not line.startswith("WEBVTT") and line not in seen:
            seen.add(line)
            lines.append(line)
    return " ".join(lines)


def _clean_transcript(raw: str) -> str:
    """Remove noise patterns common to auto-generated captions."""
    cleaned = re.sub(r"\[[\w\s]+\]", "", raw)   # [Music], [Applause], etc.
    cleaned = re.sub(r" {2,}", " ", cleaned)
    return cleaned.strip()


# ---------------------------------------------------------------------------
# Fetchers
# ---------------------------------------------------------------------------

class _APIFetcher:
    """Uses youtube-transcript-api (fast, but blocked from cloud IPs without proxy)."""

    def __init__(self, proxy_url: str | None = None) -> None:
        self._proxy_url = proxy_url
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            kwargs: dict[str, Any] = {}
            if proxy_url:
                try:
                    from youtube_transcript_api.proxies import GenericProxyConfig
                    kwargs["proxy_config"] = GenericProxyConfig(
                        http_url=proxy_url, https_url=proxy_url
                    )
                except ImportError:
                    pass
            self._api = YouTubeTranscriptApi(**kwargs)
            self._available = True
        except ImportError:
            self._available = False

    def fetch(self, video_id: str) -> tuple[str, int] | None:
        """Return (clean_text, segment_count) or None on failure."""
        if not self._available:
            return None
        for lang_codes in (("en",), ("en-US", "en-GB")):
            try:
                fetched = self._api.fetch(video_id, languages=lang_codes)
                segs = [{"text": s.text} for s in fetched]
                text = _clean_transcript(_segments_to_text(segs))
                return text, len(segs)
            except Exception:  # noqa: BLE001
                pass
        try:
            transcript_list = self._api.list(video_id)
            t = next(iter(transcript_list))
            fetched = self._api.fetch(video_id, languages=(t.language_code,))
            segs = [{"text": s.text} for s in fetched]
            text = _clean_transcript(_segments_to_text(segs))
            return text, len(segs)
        except Exception:  # noqa: BLE001
            return None


class _YtDlpFetcher:
    """Uses yt-dlp to download auto-generated subtitles (handles cookies/proxies)."""

    def __init__(self, cookies_path: str | None = None, proxy_url: str | None = None) -> None:
        self._cookies = cookies_path
        self._proxy = proxy_url
        self._available = shutil.which("yt-dlp") is not None

    def fetch(self, video_id: str) -> tuple[str, int] | None:
        """Return (clean_text, 0) or None on failure."""
        if not self._available:
            return None

        with tempfile.TemporaryDirectory() as tmpdir:
            cmd = [
                "yt-dlp",
                "--write-auto-sub", "--sub-lang", "en",
                "-f", "sb3",
                "--skip-download",
                "--sub-format", "json3",
                "--output", f"{tmpdir}/%(id)s",
                "--no-warnings", "--quiet",
            ]
            if self._cookies:
                cmd += ["--cookies", self._cookies]
            if self._proxy:
                cmd += ["--proxy", self._proxy]
            cmd.append(f"https://www.youtube.com/watch?v={video_id}")

            subprocess.run(cmd, capture_output=True, text=True)

            sub_files = list(Path(tmpdir).glob("*.json3")) or list(Path(tmpdir).glob("*.vtt"))
            if not sub_files:
                return None

            raw = sub_files[0].read_text(encoding="utf-8")
            if sub_files[0].suffix == ".json3":
                text = _clean_transcript(_json3_to_text(raw))
            else:
                text = _clean_transcript(_vtt_to_text(raw))
            return text, 0


class TranscriptFetcher:
    """
    Two-stage transcript fetcher: youtube-transcript-api → yt-dlp fallback.

    Args:
        cookies_path: Path to a cookies.txt file exported from a logged-in browser.
                      Needed for cloud environments blocked by YouTube.
        proxy_url:    Optional proxy URL (e.g. http://user:pass@host:port).
    """

    def __init__(self, cookies_path: str | None = None, proxy_url: str | None = None) -> None:
        self._api_fetcher = _APIFetcher(proxy_url=proxy_url)
        self._ytdlp_fetcher = _YtDlpFetcher(cookies_path=cookies_path, proxy_url=proxy_url)

    @property
    def available(self) -> bool:
        return self._api_fetcher._available or self._ytdlp_fetcher._available

    def fetch(self, video_id: str) -> tuple[str, int] | None:
        """Return (clean_text, segment_count) or None if both fetchers fail."""
        result = self._api_fetcher.fetch(video_id)
        if result is not None:
            return result
        return self._ytdlp_fetcher.fetch(video_id)


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class YouTubeIngestPipeline:
    """
    Ingests YouTube video transcripts into the wiki raw layer and KnowledgeBase.

    Usage::

        from src.pipeline.youtube_ingest import YouTubeIngestPipeline, VideoTarget

        pipeline = YouTubeIngestPipeline(
            raw_dir="data/wiki/raw",
            cookies_path="scripts/cookies.txt",  # needed in cloud envs
        )
        targets = [VideoTarget("kCc8FmEb1nY", "karpathy", title="Neural Net Zero to Hero")]
        results = pipeline.run(targets)
    """

    def __init__(
        self,
        raw_dir: str = "data/wiki/raw",
        kb: Any = None,
        cookies_path: str | None = None,
        proxy_url: str | None = None,
        request_delay: float = _REQUEST_DELAY,
    ) -> None:
        self._raw_dir = Path(raw_dir)
        self._kb = kb
        self._fetcher = TranscriptFetcher(cookies_path=cookies_path, proxy_url=proxy_url)
        self._delay = request_delay

    def run(self, targets: list[VideoTarget]) -> list[TranscriptIngestResult]:
        if not self._fetcher.available:
            logger.error("No transcript fetcher available. Install youtube-transcript-api or yt-dlp.")
            return [
                TranscriptIngestResult(video_id=t.video_id, persona_id=t.persona_id, title=t.title,
                                       error="no fetcher available")
                for t in targets
            ]

        results: list[TranscriptIngestResult] = []
        for i, target in enumerate(targets):
            if i > 0:
                time.sleep(self._delay)
            # Skip if raw file already exists
            persona_dir = self._raw_dir / target.persona_id
            safe_title = re.sub(r"[^\w\-]", "_", target.title or target.video_id)[:60]
            raw_path = persona_dir / f"youtube_{target.video_id}_{safe_title}.txt"
            if raw_path.exists():
                logger.info("[%d/%d] %s — SKIP (already ingested)", i + 1, len(targets), target.video_id)
                results.append(TranscriptIngestResult(
                    video_id=target.video_id, persona_id=target.persona_id,
                    title=target.title, success=True, raw_path=str(raw_path),
                ))
                continue

            result = self._ingest_one(target, raw_path)
            results.append(result)
            status = "OK" if result.success else f"FAIL: {result.error[:80]}"
            logger.info("[%d/%d] %s (%s) — %s", i + 1, len(targets), target.video_id, target.title, status)
        return results

    def _ingest_one(self, target: VideoTarget, raw_path: Path) -> TranscriptIngestResult:
        result = TranscriptIngestResult(video_id=target.video_id, persona_id=target.persona_id, title=target.title)

        fetched = self._fetcher.fetch(target.video_id)
        if fetched is None:
            result.error = (
                "All fetchers failed. In cloud environments, YouTube blocks requests. "
                "Pass cookies_path= (see scripts/fetch_youtube_transcripts.py for instructions)."
            )
            return result

        clean_text, segment_count = fetched
        result.transcript_chars = len(clean_text)
        result.segment_count = segment_count

        raw_path.parent.mkdir(parents=True, exist_ok=True)
        header = (
            f"# Transcript: {target.title or target.video_id}\n"
            f"video_id: {target.video_id}\n"
            f"url: {target.url}\n"
            f"persona_id: {target.persona_id}\n"
            f"published_at: {target.published_at}\n"
            f"ingested_at: {result.ingested_at.isoformat()}\n"
            f"chars: {result.transcript_chars}\n\n---\n\n"
        )
        raw_path.write_text(header + clean_text, encoding="utf-8")
        result.raw_path = str(raw_path)

        if self._kb is not None:
            self._seed_kb(target, clean_text)

        result.success = True
        return result

    def _seed_kb(self, target: VideoTarget, clean_text: str) -> None:
        from ..knowledge.knowledge_base import KnowledgeEntry
        from ..utils.helpers import sanitize_text

        entry = KnowledgeEntry(
            title=f"YouTube: {target.title or target.video_id}",
            content=sanitize_text(clean_text)[:_MAX_KB_CHARS],
            namespace="education",
            content_type="youtube_transcript",
            source_url=target.url,
            source_name=f"youtube_{target.video_id}",
            confidence=0.85,
            metadata={
                "persona_id": target.persona_id,
                "video_id": target.video_id,
                "published_at": target.published_at,
                "full_chars": len(clean_text),
            },
        )
        try:
            self._kb.store(entry)
        except Exception as exc:  # noqa: BLE001
            logger.warning("KB seed failed for %s: %s", target.video_id, exc)
