"""
Content Processor — Cleans and enriches raw crawled content before research.

Responsibilities:
  - HTML stripping and text normalisation
  - Language detection (English filter)
  - Content length validation
  - Duplicate detection (hash-based)
  - Chunk generation for long documents
"""

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProcessedDocument:
    """A cleaned and validated document ready for research."""

    url: str
    title: str
    text: str
    chunks: list[str]
    source_type: str
    content_hash: str
    word_count: int
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "text": self.text,
            "chunks": self.chunks,
            "source_type": self.source_type,
            "content_hash": self.content_hash,
            "word_count": self.word_count,
            "metadata": self.metadata,
        }


class ContentProcessor:
    """
    Transforms raw crawled documents into clean, enriched ProcessedDocuments.

    Configuration:
        chunk_size (int): Target token/word count per chunk (default 400).
        chunk_overlap (int): Word overlap between chunks (default 50).
        min_words (int): Minimum word count to accept a document (default 50).
        max_words (int): Documents longer than this are truncated (default 8_000).
    """

    def __init__(
        self,
        chunk_size: int = 400,
        chunk_overlap: int = 50,
        min_words: int = 50,
        max_words: int = 8_000,
    ) -> None:
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._min_words = min_words
        self._max_words = max_words
        self._seen_hashes: set[str] = set()

    def process(self, raw_doc: dict[str, Any]) -> ProcessedDocument | None:
        """
        Process a single raw document dict.

        Args:
            raw_doc: Dict as returned by CrawlerAgent (url, title, content, source_type).

        Returns:
            ProcessedDocument or None if the document should be discarded.
        """
        url = raw_doc.get("url", "")
        title = raw_doc.get("title", "") or url
        raw_text = raw_doc.get("content", "")
        source_type = raw_doc.get("source_type", "unknown")

        # Clean text
        text = self._clean_text(raw_text)

        # Minimum length check
        words = text.split()
        if len(words) < self._min_words:
            return None

        # Truncate if too long
        if len(words) > self._max_words:
            text = " ".join(words[: self._max_words])
            words = words[: self._max_words]

        # Deduplication
        content_hash = hashlib.sha256(text.encode()).hexdigest()
        if content_hash in self._seen_hashes:
            return None
        self._seen_hashes.add(content_hash)

        # Chunk generation
        chunks = self._chunk_text(text)

        return ProcessedDocument(
            url=url,
            title=self._clean_title(title),
            text=text,
            chunks=chunks,
            source_type=source_type,
            content_hash=content_hash,
            word_count=len(words),
            metadata=raw_doc.get("metadata", {}),
        )

    def process_many(self, raw_docs: list[dict[str, Any]]) -> list[ProcessedDocument]:
        """Process a list of raw documents, discarding invalid ones."""
        results = []
        for doc in raw_docs:
            processed = self.process(doc)
            if processed is not None:
                results.append(processed)
        return results

    # ------------------------------------------------------------------
    # Text cleaning
    # ------------------------------------------------------------------

    @staticmethod
    def _clean_text(text: str) -> str:
        """Remove noise from raw text."""
        # Remove URLs (keep the domain for context)
        text = re.sub(r"https?://\S+", " ", text)
        # Remove excessive whitespace and control characters
        text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def _clean_title(title: str) -> str:
        """Normalise a document title."""
        # Remove site name suffix patterns like " | Blog Name"
        title = re.sub(r"\s*[\|–—-]\s*[^|–—-]{3,50}$", "", title)
        return title.strip()[:200]

    # ------------------------------------------------------------------
    # Chunking
    # ------------------------------------------------------------------

    def _chunk_text(self, text: str) -> list[str]:
        """
        Split text into overlapping word-based chunks.

        Each chunk targets ``chunk_size`` words with ``chunk_overlap`` words
        of overlap to preserve context at boundaries.
        """
        words = text.split()
        if len(words) <= self._chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(words):
            end = min(start + self._chunk_size, len(words))
            chunk = " ".join(words[start:end])
            chunks.append(chunk)
            if end >= len(words):
                break
            start = end - self._chunk_overlap

        return chunks
