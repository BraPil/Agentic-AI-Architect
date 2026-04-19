"""
arXiv ingest pipeline — fetches AI/ML paper abstracts via the arXiv API
and indexes them into the ChromaDB persona store as a "research" persona.

Uses the arXiv Atom API (no key required). Fetches abstracts only (not full PDFs).

Curated search queries target: agentic AI, LLM architecture, RAG, evaluation,
memory systems, multi-agent systems, and tool use.
"""

import hashlib
import logging
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_ARXIV_API = "https://export.arxiv.org/api/query"
_REQUEST_DELAY = 3.0   # arXiv asks for 3s between requests
_ATOM_NS = "http://www.w3.org/2005/Atom"
_ARXIV_NS = "http://arxiv.org/schemas/atom"

# Curated queries covering the core AAA knowledge domains
ARXIV_QUERIES: list[dict] = [
    {"query": "agentic AI multi-agent systems LLM", "max_results": 10},
    {"query": "retrieval augmented generation RAG architecture", "max_results": 10},
    {"query": "LLM agent memory tool use", "max_results": 10},
    {"query": "LLM evaluation benchmark reasoning", "max_results": 8},
    {"query": "code generation LLM software engineering agents", "max_results": 8},
    {"query": "chain of thought reasoning language models", "max_results": 8},
    {"query": "LLM fine-tuning RLHF alignment", "max_results": 6},
]


@dataclass
class ArxivPaper:
    paper_id: str
    arxiv_id: str
    title: str
    authors: list[str]
    abstract: str
    published_at: str
    url: str
    categories: list[str] = field(default_factory=list)


@dataclass
class ArxivIngestResult:
    query: str
    fetched: int = 0
    added: int = 0
    skipped: int = 0
    failed: int = 0


# ---------------------------------------------------------------------------
# Feed fetching
# ---------------------------------------------------------------------------

def _fetch_arxiv(query: str, max_results: int, start: int = 0) -> bytes:
    params = urllib.parse.urlencode({
        "search_query": f"ti:{query} OR abs:{query}",
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "start": start,
        "max_results": max_results,
    })
    url = f"{_ARXIV_API}?{params}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "AAA-ArxivIngest/1.0 (+https://github.com/BraPil/Agentic-AI-Architect)"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read()


def _parse_arxiv_feed(data: bytes) -> list[ArxivPaper]:
    root = ET.fromstring(data)
    papers = []
    for entry in root.findall(f"{{{_ATOM_NS}}}entry"):
        id_el = entry.find(f"{{{_ATOM_NS}}}id")
        raw_id = id_el.text.strip() if id_el is not None and id_el.text else ""
        arxiv_id = raw_id.split("/abs/")[-1].split("v")[0] if "/abs/" in raw_id else raw_id

        title_el = entry.find(f"{{{_ATOM_NS}}}title")
        title = re.sub(r"\s+", " ", title_el.text.strip()) if title_el is not None and title_el.text else ""

        summary_el = entry.find(f"{{{_ATOM_NS}}}summary")
        abstract = re.sub(r"\s+", " ", summary_el.text.strip()) if summary_el is not None and summary_el.text else ""

        pub_el = entry.find(f"{{{_ATOM_NS}}}published")
        published = pub_el.text[:10] if pub_el is not None and pub_el.text else ""

        authors = [
            name_el.text.strip()
            for author in entry.findall(f"{{{_ATOM_NS}}}author")
            if (name_el := author.find(f"{{{_ATOM_NS}}}name")) is not None
            and name_el.text
        ]

        categories = [
            cat.get("term", "")
            for cat in entry.findall(f"{{{_ARXIV_NS}}}primary_category")
        ] + [
            cat.get("term", "")
            for cat in entry.findall(f"{{{_ATOM_NS}}}category")
        ]
        categories = list(dict.fromkeys(c for c in categories if c))

        url = f"https://arxiv.org/abs/{arxiv_id}"
        paper_id = f"arxiv-{hashlib.md5(arxiv_id.encode()).hexdigest()[:12]}"

        papers.append(ArxivPaper(
            paper_id=paper_id,
            arxiv_id=arxiv_id,
            title=title,
            authors=authors,
            abstract=abstract,
            published_at=published,
            url=url,
            categories=categories,
        ))
    return papers


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

_EXTRACTION_PROMPT = """\
You are ingesting an arXiv paper abstract into an AI architecture knowledge base.

Extract a ResearchSource object. Base everything on the abstract text provided.

Return ONLY valid JSON:
{{
  "directClaims": [],      // Specific claims or findings from the abstract — precise and quotable
  "inferredBeliefs": [],   // Assumptions or design philosophies implied by the approach
  "mentionedTools": [],    // Frameworks, benchmarks, models, datasets mentioned by name
  "topics": [],            // Topic tags (e.g. "agentic-ai", "RAG", "evaluation", "memory", "RLHF")
  "voiceSignals": [],      // 2-3 adjectives: tone/style (e.g. "empirical", "theoretical", "applied")
  "summary": ""            // 2 sentence summary of the paper's contribution and finding
}}

TITLE: {title}
AUTHORS: {authors}
PUBLISHED: {published}
CATEGORIES: {categories}

ABSTRACT:
{abstract}

Return only the JSON. No markdown."""


def _extract(client, paper: ArxivPaper) -> dict | None:
    prompt = _EXTRACTION_PROMPT.format(
        title=paper.title,
        authors=", ".join(paper.authors[:5]),
        published=paper.published_at,
        categories=", ".join(paper.categories[:4]),
        abstract=paper.abstract[:4000],
    )
    try:
        import json  # noqa: PLC0415
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=768,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Extraction failed for %s: %s", paper.arxiv_id, exc)
        return None


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class ArxivIngestPipeline:
    """
    Fetches arXiv paper abstracts and indexes them into ChromaDB.

    Papers are attributed to a synthetic "arxiv_research" persona so they
    are discoverable alongside practitioner content but clearly distinguished.

    Usage::

        pipeline = ArxivIngestPipeline(anthropic_api_key="sk-ant-...")
        results = pipeline.run()
    """

    _PERSONA_ID = "arxiv-research"
    _AUTHOR = "arXiv Research"
    _AUTHOR_URL = "https://arxiv.org"

    def __init__(
        self,
        anthropic_api_key: str | None = None,
        raw_dir: str = "data/wiki/raw",
        queries: list[dict] | None = None,
        request_delay: float = _REQUEST_DELAY,
    ) -> None:
        self._raw_dir = Path(raw_dir)
        self._delay = request_delay
        self._queries = queries or ARXIV_QUERIES
        self._client = None
        if anthropic_api_key:
            try:
                import anthropic  # noqa: PLC0415
                self._client = anthropic.Anthropic(api_key=anthropic_api_key)
            except ImportError:
                logger.warning("anthropic not installed")

    def run(self) -> list[ArxivIngestResult]:
        from src.pipeline.linkedin_persona_store import LinkedInPersonaStore, PostRecord, persona_slug  # noqa: PLC0415

        store = LinkedInPersonaStore()
        store.initialize()
        existing = store.get_existing_ids()

        persona_dir = self._raw_dir / self._PERSONA_ID
        persona_dir.mkdir(parents=True, exist_ok=True)

        results = []
        seen_ids: set[str] = set()  # dedup across queries

        for qi, query_cfg in enumerate(self._queries):
            query = query_cfg["query"]
            max_results = query_cfg.get("max_results", 10)

            if qi > 0:
                time.sleep(self._delay)

            result = ArxivIngestResult(query=query)
            logger.info("arXiv query: %s (max %d)", query, max_results)

            try:
                data = _fetch_arxiv(query, max_results)
                papers = _parse_arxiv_feed(data)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Feed failed for query '%s': %s", query, exc)
                results.append(result)
                continue

            result.fetched = len(papers)

            for paper in papers:
                if paper.paper_id in existing or paper.paper_id in seen_ids:
                    result.skipped += 1
                    continue
                seen_ids.add(paper.paper_id)

                time.sleep(0.5)

                # Claude extraction
                extracted: dict = {}
                if self._client:
                    extracted = _extract(self._client, paper) or {}

                # Write raw artifact
                safe_title = re.sub(r"[^\w\-]", "_", paper.title)[:60]
                raw_path = persona_dir / f"arxiv_{paper.published_at}_{safe_title}.md"
                raw_path.write_text(
                    f"# {paper.title}\n"
                    f"arxiv_id: {paper.arxiv_id}\n"
                    f"url: {paper.url}\n"
                    f"authors: {', '.join(paper.authors[:8])}\n"
                    f"published_at: {paper.published_at}\n"
                    f"categories: {', '.join(paper.categories)}\n\n---\n\n"
                    f"{paper.abstract}\n",
                    encoding="utf-8",
                )

                # Build document text for embedding
                author_str = ", ".join(paper.authors[:3])
                if len(paper.authors) > 3:
                    author_str += f" et al."
                document_text = (
                    f"{paper.title}\n\n"
                    f"Authors: {author_str}\n\n"
                    f"{paper.abstract}"
                )

                try:
                    record = PostRecord(
                        post_id=paper.paper_id,
                        persona_id=persona_slug(self._AUTHOR),
                        author=self._AUTHOR,
                        author_url=self._AUTHOR_URL,
                        post_url=paper.url,
                        text=document_text[:6000],
                        timestamp=paper.published_at,
                        post_type="arxiv_abstract",
                        image_count=0,
                        image_descriptions=[],
                        reactor_persona_id="brandtpileggi",
                        scraped_at=datetime.now(timezone.utc).isoformat(),
                        direct_claims=extracted.get("directClaims", []),
                        inferred_beliefs=extracted.get("inferredBeliefs", []),
                        mentioned_tools=extracted.get("mentionedTools", []),
                        topics=extracted.get("topics", []),
                        voice_signals=extracted.get("voiceSignals", []),
                        summary=extracted.get("summary", paper.title),
                        confidence=0.85,
                    )
                    added = store.ingest(record)
                    if added:
                        result.added += 1
                        existing.add(paper.paper_id)
                        logger.info("  + %s", paper.title[:70])
                    else:
                        result.skipped += 1
                except Exception as exc:  # noqa: BLE001
                    result.failed += 1
                    logger.warning("  Failed %s: %s", paper.arxiv_id, exc)

            results.append(result)

        return results
