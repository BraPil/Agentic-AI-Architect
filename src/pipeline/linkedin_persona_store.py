"""
LinkedIn Persona Store — hybrid vector + keyword store for LinkedIn post ingestion.

Organizes posts by author persona. Backed by ChromaDB (local persistent) with
sentence-transformers embeddings. Upgrade path to pgvector: swap the client init.

Features:
  - Incremental sync: skips posts already ingested by ID
  - Semantic search via cosine similarity on all-MiniLM-L6-v2 embeddings
  - Keyword + metadata filtering (persona, post_type, tool mentions)
  - Per-persona retrieval and persona index

Storage layout:
  data/linkedin_store/           ← ChromaDB persistent dir
    chroma.sqlite3               ← ChromaDB index + metadata
  Collection: linkedin_reactions
"""

import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from src.pipeline.curation import PersonaCurationList

logger = logging.getLogger(__name__)

STORE_PATH = Path("data/linkedin_store")
COLLECTION_NAME = "linkedin_reactions"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # 384-dim, fast, no API key needed


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def persona_slug(author: str) -> str:
    """Normalize author name to a stable persona ID: 'Rahul Agarwal' → 'rahul-agarwal'."""
    return re.sub(r"[^a-z0-9]+", "-", (author or "unknown").lower()).strip("-")[:50]


def build_document(text: str, summary: str, image_descriptions: list[str],
                   extracted: dict) -> str:
    """Combine all content into a single indexable string."""
    parts = [text.strip()]
    if summary:
        parts.append(summary)
    if image_descriptions:
        parts.append("Image analysis: " + " | ".join(image_descriptions))
    for key in ("directClaims", "inferredBeliefs", "mentionedTools", "topics"):
        items = extracted.get(key, [])
        if items:
            parts.append(f"{key}: {', '.join(items)}")
    return "\n\n".join(p for p in parts if p).strip()


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class PostRecord:
    """A LinkedIn post ready for storage in the persona store."""

    post_id: str                      # e.g. li-7450530828104880128
    persona_id: str                   # author slug, e.g. rahul-agarwal
    author: str                       # display name
    author_url: str
    post_url: str
    text: str
    timestamp: str
    post_type: str                    # text | image | video | article
    image_count: int
    image_descriptions: list[str]
    reactor_persona_id: str           # who reacted (e.g. brandtpileggi)
    scraped_at: str
    direct_claims: list[str] = field(default_factory=list)
    inferred_beliefs: list[str] = field(default_factory=list)
    mentioned_tools: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    voice_signals: list[str] = field(default_factory=list)
    summary: str = ""
    confidence: float = 0.8


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------

class LinkedInPersonaStore:
    """
    Hybrid vector + keyword store for LinkedIn posts, organized by author persona.

    Usage:
        store = LinkedInPersonaStore()
        store.initialize()
        existing = store.get_existing_ids()
        store.ingest(record)
        results = store.search("agentic AI frameworks", persona_id="andrej-karpathy")
        personas = store.get_personas()
    """

    def __init__(
        self,
        store_path: str | Path = STORE_PATH,
        curation: PersonaCurationList | None = None,
    ) -> None:
        self._store_path = Path(store_path)
        self._client = None
        self._collection = None
        self._initialized = False
        # Curation guard — bars non-practitioner personas from ingest. Loaded from the
        # default denylist unless one is injected (tests) or disabled via env kill-switch.
        # See src/pipeline/curation.py.
        if curation is not None:
            self._curation: PersonaCurationList = curation
        elif os.environ.get("AAA_PERSONA_CURATION", "1") == "0":
            self._curation = PersonaCurationList()  # inert
        else:
            self._curation = PersonaCurationList.load()

    @property
    def curation(self) -> PersonaCurationList:
        """The persona curation denylist consulted at ingest()."""
        return self._curation

    def initialize(self) -> None:
        """Connect to ChromaDB and get/create the reactions collection."""
        try:
            import chromadb
            from chromadb.utils import embedding_functions  # noqa: PLC0415
        except ImportError:
            raise ImportError(
                "chromadb and sentence-transformers are required.\n"
                "Run: pip install 'chromadb>=0.5.0' 'sentence-transformers>=2.7.0'"
            )

        self._store_path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(self._store_path))

        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"},
        )
        self._initialized = True
        logger.info(
            "LinkedInPersonaStore ready — %d posts indexed at %s",
            self._collection.count(), self._store_path,
        )

    def _check(self) -> None:
        if not self._initialized:
            raise RuntimeError("Call initialize() before using the store.")

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def get_existing_ids(self) -> set[str]:
        """Return all post IDs already indexed — used for incremental sync."""
        self._check()
        return set(self._collection.get(include=[])["ids"])

    def ingest(self, record: PostRecord) -> bool:
        """
        Index a single post. Returns True if added, False if already present.
        Raises on unexpected errors.
        """
        self._check()

        # Curation guard: barred (non-practitioner) personas never re-enter the store,
        # even if a later reactions scrape surfaces them again. Enforced HERE at the store
        # layer so every ingest path inherits the bar. See src/pipeline/curation.py.
        if self._curation.is_blocked(record.persona_id):
            logger.warning(
                "Curation guard blocked persona '%s' (%s) — skipping ingest of %s",
                record.persona_id, record.author, record.post_id,
            )
            return False

        document = build_document(
            record.text, record.summary, record.image_descriptions,
            {
                "directClaims": record.direct_claims,
                "inferredBeliefs": record.inferred_beliefs,
                "mentionedTools": record.mentioned_tools,
                "topics": record.topics,
            },
        )
        if not document.strip():
            logger.warning("Skipping %s — empty document", record.post_id)
            return False

        # ChromaDB metadata must be flat (str/int/float — no lists)
        metadata = {
            "persona_id":         record.persona_id,
            "author":             record.author[:200],
            "author_url":         record.author_url[:500],
            "post_url":           record.post_url[:500],
            "timestamp":          record.timestamp,
            "post_type":          record.post_type,
            "image_count":        record.image_count,
            "reactor_persona_id": record.reactor_persona_id,
            "scraped_at":         record.scraped_at,
            "summary":            record.summary[:500],
            "confidence":         record.confidence,
            "mentioned_tools":    ", ".join(record.mentioned_tools),
            "topics":             ", ".join(record.topics),
            "voice_signals":      ", ".join(record.voice_signals),
            "ingested_at":        datetime.now(timezone.utc).isoformat(),
        }

        try:
            self._collection.add(
                ids=[record.post_id],
                documents=[document],
                metadatas=[metadata],
            )
            return True
        except Exception as e:
            if "already exists" in str(e).lower():
                return False
            raise

    # ------------------------------------------------------------------
    # Read / Search
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        n_results: int = 10,
        persona_id: str | None = None,
        post_type: str | None = None,
        keyword: str | None = None,
        include_experimental: bool = False,
    ) -> list[dict]:
        """
        Hybrid search combining semantic vector similarity with optional filters.

        Args:
            query:      Natural language query for semantic search.
            n_results:  Maximum results to return.
            persona_id: Restrict to a specific author persona slug.
            post_type:  Restrict to text | image | video | article.
            keyword:    Substring that must appear in the document text.
            include_experimental: Include unpromoted agent-generated artifacts
                        (source_tier="experimental"). Default False — these are
                        quarantined and must be promoted before they count as
                        knowledge. Enforced HERE at the store layer so every
                        caller (MCP, grounding, eval) inherits the quarantine.

        Returns:
            List of dicts with keys: post_id, document, metadata, score (0–1).
        """
        self._check()
        total = self._collection.count()
        if total == 0:
            return []

        where: dict | None = None
        filters = {k: v for k, v in [
            ("persona_id", persona_id),
            ("post_type", post_type),
        ] if v}
        if len(filters) == 1:
            where = filters
        elif len(filters) > 1:
            where = {"$and": [{k: v} for k, v in filters.items()]}

        where_doc: dict | None = {"$contains": keyword} if keyword else None

        # Quarantine is enforced by post-filtering (not a $ne where-clause, which in
        # ChromaDB also drops legacy docs that lack the source_tier field entirely).
        # Over-fetch so dropping experimental hits doesn't starve the result set.
        fetch = min(n_results, total) if include_experimental else min(n_results + 15, total)
        results = self._collection.query(
            query_texts=[query],
            n_results=fetch,
            where=where or None,
            where_document=where_doc,
            include=["documents", "metadatas", "distances"],
        )

        hits = [
            {
                "post_id":  results["ids"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score":    round(1.0 - results["distances"][0][i], 4),
            }
            for i in range(len(results["ids"][0]))
        ]
        if not include_experimental:
            hits = [h for h in hits if h["metadata"].get("source_tier") != "experimental"]

        # Hybrid ranking: re-order the candidate pool by a vector+lexical blend before
        # trimming, so exact-term matches the embedding smoothed away can surface. The
        # reported `score` stays the vector similarity; only the order changes.
        # ON by default — justified by the rank-aware eval (scripts/eval_ranking.py):
        # hybrid raised MRR 0.90→1.00, nDCG@10 0.877→0.947, hit@1 0.80→1.00, and rescued
        # the exact-term query from rank 2 to rank 1. Kill-switch: AAA_HYBRID_RANKING=0.
        # See src/pipeline/hybrid_ranking.py and docs/hybrid-ranking-v0.md.
        if os.environ.get("AAA_HYBRID_RANKING", "1") != "0" and len(hits) > 1:
            from src.pipeline.hybrid_ranking import rerank_hits  # noqa: PLC0415
            hits = rerank_hits(query, hits)

        return hits[:n_results]

    def get_personas(self) -> list[dict]:
        """Return all indexed personas sorted by post count."""
        self._check()
        all_meta = self._collection.get(include=["metadatas"])["metadatas"]
        counts: dict[str, dict] = {}
        for m in all_meta:
            pid = m.get("persona_id", "unknown")
            if pid not in counts:
                counts[pid] = {
                    "persona_id": pid,
                    "author": m.get("author", ""),
                    "post_count": 0,
                }
            counts[pid]["post_count"] += 1
        return sorted(counts.values(), key=lambda x: -x["post_count"])

    def get_posts_by_persona(self, persona_id: str, limit: int = 200) -> list[dict]:
        """Return all indexed posts for a given author persona."""
        self._check()
        results = self._collection.get(
            where={"persona_id": persona_id},
            include=["documents", "metadatas"],
            limit=limit,
        )
        return [
            {"post_id": pid, "document": doc, "metadata": meta}
            for pid, doc, meta in zip(
                results["ids"], results["documents"], results["metadatas"]
            )
        ]

    def prune_persona(self, persona_id: str) -> int:
        """
        Remove all indexed posts for a persona. Returns the number of posts deleted.

        This only deletes from the store; pair it with ``self.curation.block(...)`` (see
        ``scripts/prune_persona.py``) so the persona is also barred from future re-ingest.
        """
        self._check()
        ids = self._collection.get(where={"persona_id": persona_id}, include=[])["ids"]
        if ids:
            self._collection.delete(ids=ids)
        return len(ids)

    def print_index_summary(self) -> None:
        """Print a human-readable summary of what's indexed."""
        self._check()
        personas = self.get_personas()
        total = self._collection.count()
        print(f"\n── LinkedIn Persona Store ({'─' * 35})")
        print(f"   Total posts indexed: {total}")
        print(f"   Unique personas:     {len(personas)}")
        print()
        for p in personas:
            print(f"   {p['post_count']:>3}  {p['author'] or p['persona_id']}")
        print()

    @property
    def count(self) -> int:
        self._check()
        return self._collection.count()
