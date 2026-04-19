"""
Blog ingest pipeline — fetches posts from RSS/Atom feeds and indexes them
into the ChromaDB persona store alongside LinkedIn, YouTube, and GitHub content.

Supported sources (configured in BLOG_REGISTRY below):
  - Simon Willison's Weblog (simonwillison.net)
  - Lil'Log — Lilian Weng (lilianweng.github.io)

Flow:
  Feed URL → parse RSS/Atom → strip HTML → Claude Haiku extraction → ChromaDB
"""

import hashlib
import html
import logging
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_REQUEST_DELAY = 1.5
_MAX_CONTENT_CHARS = 8000   # chars sent to Claude for extraction
_MAX_DOC_CHARS = 6000       # chars stored in ChromaDB document

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

BLOG_REGISTRY: dict[str, dict] = {
    "simon_willison": {
        "persona_id": "simon_willison",
        "author": "Simon Willison",
        "author_url": "https://simonwillison.net",
        "feed_url": "https://simonwillison.net/atom/everything/",
        "feed_type": "atom",
        "max_posts": 30,
    },
    "lilian_weng": {
        "persona_id": "lilian_weng",
        "author": "Lilian Weng",
        "author_url": "https://lilianweng.github.io",
        "feed_url": "https://lilianweng.github.io/index.xml",
        "feed_type": "rss",
        "max_posts": 30,
    },
}


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class BlogPost:
    post_id: str
    persona_id: str
    author: str
    author_url: str
    post_url: str
    title: str
    text: str
    published_at: str
    post_type: str = "blog_post"
    image_count: int = 0


@dataclass
class BlogIngestResult:
    persona_id: str
    author: str
    total_fetched: int = 0
    added: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Feed parsing
# ---------------------------------------------------------------------------

_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "content": "http://purl.org/rss/1.0/modules/content/",
}


def _strip_html(raw: str) -> str:
    """Remove HTML tags and decode entities."""
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    raw = re.sub(r"\s{2,}", " ", raw)
    return raw.strip()


def _fetch_feed(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "AAA-BlogIngest/1.0 (+https://github.com/BraPil/Agentic-AI-Architect)"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read()


def _parse_atom(data: bytes, config: dict, max_posts: int) -> list[BlogPost]:
    root = ET.fromstring(data)
    ns = "http://www.w3.org/2005/Atom"
    posts = []
    for entry in root.findall(f"{{{ns}}}entry")[:max_posts]:
        title_el = entry.find(f"{{{ns}}}title")
        title = title_el.text or "" if title_el is not None else ""

        link_el = entry.find(f"{{{ns}}}link[@rel='alternate']")
        if link_el is None:
            link_el = entry.find(f"{{{ns}}}link")
        url = link_el.get("href", "") if link_el is not None else ""

        pub_el = entry.find(f"{{{ns}}}published") or entry.find(f"{{{ns}}}updated")
        published = pub_el.text or "" if pub_el is not None else ""

        summary_el = entry.find(f"{{{ns}}}summary")
        content_el = entry.find(f"{{{ns}}}content")
        raw = ""
        if content_el is not None and content_el.text:
            raw = content_el.text
        elif summary_el is not None and summary_el.text:
            raw = summary_el.text
        text = _strip_html(raw)

        post_id = f"blog-{config['persona_id']}-{hashlib.md5(url.encode()).hexdigest()[:12]}"
        posts.append(BlogPost(
            post_id=post_id,
            persona_id=config["persona_id"],
            author=config["author"],
            author_url=config["author_url"],
            post_url=url,
            title=title,
            text=text,
            published_at=published[:10] if published else "",
        ))
    return posts


def _parse_rss(data: bytes, config: dict, max_posts: int) -> list[BlogPost]:
    root = ET.fromstring(data)
    posts = []
    for item in root.findall(".//item")[:max_posts]:
        title_el = item.find("title")
        title = title_el.text or "" if title_el is not None else ""

        link_el = item.find("link")
        url = link_el.text or "" if link_el is not None else ""

        pub_el = item.find("pubDate")
        published = pub_el.text or "" if pub_el is not None else ""
        # Normalize: "Thu, 01 May 2025 00:00:00 +0000" → "2025-05-01"
        try:
            from email.utils import parsedate_to_datetime
            published = parsedate_to_datetime(published).date().isoformat()
        except Exception:
            published = published[:10] if published else ""

        # Prefer content:encoded over description
        content_el = item.find("content:encoded", _NS)
        desc_el = item.find("description")
        raw = ""
        if content_el is not None and content_el.text:
            raw = content_el.text
        elif desc_el is not None and desc_el.text:
            raw = desc_el.text
        text = _strip_html(raw)

        post_id = f"blog-{config['persona_id']}-{hashlib.md5(url.encode()).hexdigest()[:12]}"
        posts.append(BlogPost(
            post_id=post_id,
            persona_id=config["persona_id"],
            author=config["author"],
            author_url=config["author_url"],
            post_url=url,
            title=title,
            text=text,
            published_at=published,
        ))
    return posts


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

_EXTRACTION_PROMPT = """\
You are ingesting a blog post by {author} into a structured AI architecture knowledge base.

Extract a ResearchSource object. Only include what you can directly infer from the text.

Return ONLY valid JSON:
{{
  "directClaims": [],      // Specific factual or technical claims — precise and quotable
  "inferredBeliefs": [],   // Beliefs/stances inferable from framing and word choice
  "mentionedTools": [],    // Every tool, library, framework, platform mentioned by name
  "topics": [],            // Topic tags (e.g. "agentic-ai", "RAG", "evaluation", "memory")
  "voiceSignals": [],      // 2-4 adjectives describing tone (e.g. "analytical", "practical")
  "summary": ""            // 2-3 sentence summary of the post's key insight
}}

AUTHOR: {author}
TITLE: {title}
PUBLISHED: {published}

TEXT:
{text}

Return only the JSON object. No markdown."""


def _extract(client, post: BlogPost) -> dict | None:
    prompt = _EXTRACTION_PROMPT.format(
        author=post.author,
        title=post.title,
        published=post.published_at or "unknown",
        text=post.text[:_MAX_CONTENT_CHARS],
    )
    try:
        import json  # noqa: PLC0415
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Extraction failed for %s: %s", post.post_url, exc)
        return None


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class BlogIngestPipeline:
    """
    Fetches blog posts from RSS/Atom feeds and indexes them into ChromaDB.

    Usage::

        pipeline = BlogIngestPipeline(anthropic_api_key="sk-ant-...")
        results = pipeline.run(["simon_willison", "lilian_weng"])
    """

    def __init__(
        self,
        anthropic_api_key: str | None = None,
        raw_dir: str = "data/wiki/raw",
        request_delay: float = _REQUEST_DELAY,
    ) -> None:
        self._raw_dir = Path(raw_dir)
        self._delay = request_delay
        self._client = None
        if anthropic_api_key:
            try:
                import anthropic  # noqa: PLC0415
                self._client = anthropic.Anthropic(api_key=anthropic_api_key)
            except ImportError:
                logger.warning("anthropic not installed — running without extraction")

    def run(self, persona_ids: list[str] | None = None) -> list[BlogIngestResult]:
        from src.pipeline.linkedin_persona_store import LinkedInPersonaStore, PostRecord, persona_slug  # noqa: PLC0415

        store = LinkedInPersonaStore()
        store.initialize()
        existing = store.get_existing_ids()

        targets = persona_ids or list(BLOG_REGISTRY)
        results = []

        for pid in targets:
            config = BLOG_REGISTRY.get(pid)
            if not config:
                logger.warning("Unknown blog persona: %s", pid)
                continue

            result = BlogIngestResult(persona_id=pid, author=config["author"])
            logger.info("Fetching feed for %s…", config["author"])

            try:
                data = _fetch_feed(config["feed_url"])
            except Exception as exc:  # noqa: BLE001
                result.errors.append(f"Feed fetch failed: {exc}")
                results.append(result)
                continue

            if config["feed_type"] == "atom":
                posts = _parse_atom(data, config, config.get("max_posts", 20))
            else:
                posts = _parse_rss(data, config, config.get("max_posts", 20))

            result.total_fetched = len(posts)
            logger.info("  %d posts parsed", len(posts))

            persona_dir = self._raw_dir / pid
            persona_dir.mkdir(parents=True, exist_ok=True)

            for i, post in enumerate(posts):
                if post.post_id in existing:
                    result.skipped += 1
                    continue

                if i > 0:
                    time.sleep(self._delay)

                # Claude extraction
                extracted: dict = {}
                if self._client and post.text:
                    extracted = _extract(self._client, post) or {}

                # Write raw artifact
                safe_title = re.sub(r"[^\w\-]", "_", post.title)[:60]
                raw_path = persona_dir / f"blog_{post.published_at}_{safe_title}.md"
                raw_content = (
                    f"# {post.title}\n"
                    f"url: {post.post_url}\n"
                    f"author: {post.author}\n"
                    f"published_at: {post.published_at}\n"
                    f"persona_id: {post.persona_id}\n\n---\n\n"
                    f"{post.text[:_MAX_DOC_CHARS]}\n"
                )
                raw_path.write_text(raw_content, encoding="utf-8")

                # Index into ChromaDB
                try:
                    record = PostRecord(
                        post_id=post.post_id,
                        persona_id=persona_slug(post.author),
                        author=post.author,
                        author_url=post.author_url,
                        post_url=post.post_url,
                        text=f"{post.title}\n\n{post.text}"[:_MAX_DOC_CHARS],
                        timestamp=post.published_at,
                        post_type="blog_post",
                        image_count=0,
                        image_descriptions=[],
                        reactor_persona_id="brandtpileggi",
                        scraped_at=datetime.now(timezone.utc).isoformat(),
                        direct_claims=extracted.get("directClaims", []),
                        inferred_beliefs=extracted.get("inferredBeliefs", []),
                        mentioned_tools=extracted.get("mentionedTools", []),
                        topics=extracted.get("topics", []),
                        voice_signals=extracted.get("voiceSignals", []),
                        summary=extracted.get("summary", post.title),
                        confidence=0.9,
                    )
                    added = store.ingest(record)
                    if added:
                        result.added += 1
                        existing.add(post.post_id)
                        claims = len(extracted.get("directClaims", []))
                        tools = len(extracted.get("mentionedTools", []))
                        logger.info(
                            "  [%d/%d] %s — %d claims, %d tools",
                            i + 1, len(posts), post.title[:60], claims, tools,
                        )
                    else:
                        result.skipped += 1
                except Exception as exc:  # noqa: BLE001
                    result.failed += 1
                    result.errors.append(f"{post.post_id}: {exc}")
                    logger.warning("  Failed to index %s: %s", post.post_id, exc)

            results.append(result)

        return results
