"""
Knowledge Base — SQLite-backed structured storage for all knowledge entries.

Schema:
  knowledge_entries:
    - id            TEXT PRIMARY KEY (UUID)
    - namespace     TEXT  (education | frameworks | trends | tools | general)
    - title         TEXT
    - content       TEXT
    - content_type  TEXT
    - source_url    TEXT
    - source_name   TEXT
    - confidence    REAL
    - created_at    TEXT  (ISO 8601)
    - updated_at    TEXT  (ISO 8601)
    - metadata      TEXT  (JSON string)
"""

import json
import logging
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Default database path
DEFAULT_DB_PATH = "data/knowledge_base.db"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class KnowledgeEntry:
    """A single entry in the knowledge base."""

    title: str
    content: str
    namespace: str = "general"
    content_type: str = "unknown"
    source_url: str = ""
    source_name: str = ""
    confidence: float = 0.8
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "title": self.title,
            "content": self.content,
            "namespace": self.namespace,
            "content_type": self.content_type,
            "source_url": self.source_url,
            "source_name": self.source_name,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_row(cls, row: tuple) -> "KnowledgeEntry":
        """Reconstruct a KnowledgeEntry from a database row tuple."""
        (entry_id, namespace, title, content, content_type,
         source_url, source_name, confidence, created_at, updated_at, metadata_json) = row
        return cls(
            entry_id=entry_id,
            namespace=namespace,
            title=title,
            content=content,
            content_type=content_type,
            source_url=source_url or "",
            source_name=source_name or "",
            confidence=confidence,
            created_at=datetime.fromisoformat(created_at),
            updated_at=datetime.fromisoformat(updated_at),
            metadata=json.loads(metadata_json) if metadata_json else {},
        )

    @classmethod
    def from_finding(cls, finding: dict[str, Any]) -> "KnowledgeEntry":
        """Create a KnowledgeEntry from a ResearchFinding dict."""
        return cls(
            title=finding.get("title", ""),
            content=finding.get("summary", ""),
            namespace=finding.get("namespace", "general"),
            content_type=finding.get("content_type", "unknown"),
            source_url=finding.get("source_url", ""),
            source_name=finding.get("source_name", ""),
            confidence=finding.get("confidence", 0.8),
            metadata={
                "concepts": finding.get("concepts", []),
                "tools_mentioned": finding.get("tools_mentioned", []),
                "people_mentioned": finding.get("people_mentioned", []),
            },
        )


# ---------------------------------------------------------------------------
# KnowledgeBase
# ---------------------------------------------------------------------------

class KnowledgeBase:
    """
    SQLite-backed knowledge store with simple search capabilities.

    Usage::

        kb = KnowledgeBase("data/knowledge_base.db")
        kb.initialize()

        entry = KnowledgeEntry(title="FAISS Overview", content="...", namespace="tools")
        kb.store(entry)

        results = kb.search(query="vector search", namespace="tools", limit=10)
        kb.close()
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """Create the database and schema if they don't exist."""
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create_schema()
        logger.info("KnowledgeBase initialized: %s", self._db_path)

    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def store(self, entry: KnowledgeEntry) -> str:
        """Insert or replace a knowledge entry. Returns the entry_id."""
        assert self._conn is not None, "KnowledgeBase not initialized"
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """
            INSERT OR REPLACE INTO knowledge_entries
              (entry_id, namespace, title, content, content_type, source_url,
               source_name, confidence, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry.entry_id,
                entry.namespace,
                entry.title,
                entry.content,
                entry.content_type,
                entry.source_url,
                entry.source_name,
                entry.confidence,
                entry.created_at.isoformat(),
                now,
                json.dumps(entry.metadata),
            ),
        )
        self._conn.commit()
        return entry.entry_id

    def store_many(self, entries: list[KnowledgeEntry]) -> int:
        """Batch insert entries. Returns count of inserted entries."""
        stored = 0
        for entry in entries:
            self.store(entry)
            stored += 1
        return stored

    def get(self, entry_id: str) -> KnowledgeEntry | None:
        """Retrieve a single entry by ID."""
        assert self._conn is not None, "KnowledgeBase not initialized"
        cursor = self._conn.execute(
            "SELECT * FROM knowledge_entries WHERE entry_id = ?", (entry_id,)
        )
        row = cursor.fetchone()
        return KnowledgeEntry.from_row(tuple(row)) if row else None

    def delete(self, entry_id: str) -> bool:
        """Delete an entry. Returns True if deleted."""
        assert self._conn is not None, "KnowledgeBase not initialized"
        cursor = self._conn.execute(
            "DELETE FROM knowledge_entries WHERE entry_id = ?", (entry_id,)
        )
        self._conn.commit()
        return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        query: str = "",
        namespace: str | None = None,
        content_type: str | None = None,
        min_confidence: float = 0.0,
        limit: int = 20,
        offset: int = 0,
    ) -> list[KnowledgeEntry]:
        """
        Full-text keyword search across title and content.

        Args:
            query: Keywords to search for (case-insensitive LIKE match).
            namespace: Filter to a specific namespace.
            content_type: Filter to a specific content type.
            min_confidence: Minimum confidence score (0.0–1.0).
            limit: Maximum results to return.
            offset: Pagination offset.

        Returns:
            List of matching KnowledgeEntry objects, most-confident first.
        """
        assert self._conn is not None, "KnowledgeBase not initialized"

        clauses: list[str] = ["confidence >= ?"]
        params: list[Any] = [min_confidence]

        if query:
            clauses.append("(title LIKE ? OR content LIKE ?)")
            like = f"%{query}%"
            params.extend([like, like])

        if namespace:
            clauses.append("namespace = ?")
            params.append(namespace)

        if content_type:
            clauses.append("content_type = ?")
            params.append(content_type)

        where_clause = " AND ".join(clauses) if clauses else "1=1"
        sql = f"""
            SELECT entry_id, namespace, title, content, content_type, source_url,
                   source_name, confidence, created_at, updated_at, metadata
            FROM knowledge_entries
            WHERE {where_clause}
            ORDER BY confidence DESC, updated_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        cursor = self._conn.execute(sql, params)
        return [KnowledgeEntry.from_row(tuple(row)) for row in cursor.fetchall()]

    def count(self, namespace: str | None = None) -> int:
        """Return total entry count, optionally filtered by namespace."""
        assert self._conn is not None, "KnowledgeBase not initialized"
        if namespace:
            cursor = self._conn.execute(
                "SELECT COUNT(*) FROM knowledge_entries WHERE namespace = ?", (namespace,)
            )
        else:
            cursor = self._conn.execute("SELECT COUNT(*) FROM knowledge_entries")
        result = cursor.fetchone()
        return result[0] if result else 0

    def get_namespaces(self) -> list[str]:
        """Return distinct namespace values in the knowledge base."""
        assert self._conn is not None, "KnowledgeBase not initialized"
        cursor = self._conn.execute(
            "SELECT DISTINCT namespace FROM knowledge_entries ORDER BY namespace"
        )
        return [row[0] for row in cursor.fetchall()]

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _create_schema(self) -> None:
        assert self._conn is not None
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS knowledge_entries (
                entry_id    TEXT PRIMARY KEY,
                namespace   TEXT NOT NULL DEFAULT 'general',
                title       TEXT NOT NULL,
                content     TEXT NOT NULL,
                content_type TEXT NOT NULL DEFAULT 'unknown',
                source_url  TEXT,
                source_name TEXT,
                confidence  REAL NOT NULL DEFAULT 0.8,
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL,
                metadata    TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_namespace ON knowledge_entries (namespace);
            CREATE INDEX IF NOT EXISTS idx_content_type ON knowledge_entries (content_type);
            CREATE INDEX IF NOT EXISTS idx_confidence ON knowledge_entries (confidence DESC);
            CREATE INDEX IF NOT EXISTS idx_updated_at ON knowledge_entries (updated_at DESC);
        """)
        self._conn.commit()

    def __repr__(self) -> str:
        count = self.count() if self._conn else 0
        return f"KnowledgeBase(path={self._db_path!r}, entries={count})"
