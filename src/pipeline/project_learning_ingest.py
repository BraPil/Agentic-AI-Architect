"""
Project Learning Ingest — indexes AAA's own decision, discovery, and lesson logs
into ChromaDB so they appear alongside external knowledge in search results.

This closes the feedback loop: lessons learned from building real systems with AAA
become searchable knowledge that informs future recommendations.

Sources:
  docs/decision-log.md      → learning_type: decision
  docs/discovery-log.md     → learning_type: discovery
  docs/lessons-learned-log.md → learning_type: lesson

All entries land in the same `linkedin_reactions` ChromaDB collection with:
  persona_id:    aaa_project
  post_type:     project_learning
  learning_type: decision | discovery | lesson
  author:        Agentic AI Architect

Flow:
  Parse markdown table → build document string → stable MD5 ID → ChromaDB upsert
"""

import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[2]

_LEARNING_SOURCES = {
    "decision": _REPO_ROOT / "docs" / "decision-log.md",
    "discovery": _REPO_ROOT / "docs" / "discovery-log.md",
    "lesson": _REPO_ROOT / "docs" / "lessons-learned-log.md",
}

# Tools and topics mentioned frequently in project work — used for keyword tagging
_KNOWN_TOOLS = [
    "ChromaDB", "SQLite", "FastAPI", "MCP", "Claude", "Haiku", "Sonnet",
    "FAISS", "Pinecone", "LangChain", "LangGraph", "Archon", "FastMCP",
    "GitHub Actions", "APScheduler", "Pydantic", "pytest", "yt-dlp",
    "sentence-transformers", "all-MiniLM-L6-v2", "PostgreSQL", "pgvector",
    "ExMorbus", "Mouseion", "MoltBook", "DGX Spark",
]

_KNOWN_TOPICS = [
    "evaluation", "knowledge base", "agent", "orchestration", "ingest",
    "deduplication", "ChromaDB", "vector search", "semantic search",
    "prompt injection", "sanitization", "rate limiting", "webhook",
    "schema versioning", "REST API", "MCP", "persona", "LinkedIn",
    "YouTube", "blog", "arXiv", "embeddings", "architecture",
    "ExMorbus", "Mouseion", "shared substrate", "hardware", "inference",
    "evaluation harness", "source weighting", "learning loop",
]


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class LearningEntry:
    """A single row from a project log file, ready for ChromaDB."""

    entry_id: str
    learning_type: str          # decision | discovery | lesson
    date: str
    title: str                  # the primary content column (decision / discovery / lesson)
    context: str                # second column (rationale / why_it_matters / trigger)
    action: str                 # third column (references / follow_up / preventive_action)
    status: str = ""            # present only for decisions
    mentioned_tools: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)

    def to_document(self) -> str:
        """Build the indexable string for embedding."""
        type_label = self.learning_type.upper().replace("_", " ")
        parts = [f"{type_label}: {self.title}"]
        if self.status:
            parts[0] += f" [{self.status}]"
        if self.context:
            label = {
                "decision": "Rationale",
                "discovery": "Why it matters",
                "lesson": "What triggered it",
            }.get(self.learning_type, "Context")
            parts.append(f"{label}: {self.context}")
        if self.action:
            label = {
                "decision": "References",
                "discovery": "Follow-up",
                "lesson": "Preventive action",
            }.get(self.learning_type, "Action")
            parts.append(f"{label}: {self.action}")
        if self.mentioned_tools:
            parts.append(f"Tools: {', '.join(self.mentioned_tools)}")
        if self.topics:
            parts.append(f"Topics: {', '.join(self.topics)}")
        return "\n\n".join(p for p in parts if p)

    def to_metadata(self) -> dict:
        return {
            "persona_id": "aaa_project",
            "author": "Agentic AI Architect",
            "post_type": "project_learning",
            "learning_type": self.learning_type,
            "timestamp": self.date,
            "status": self.status,
            "title": self.title[:200],
            "mentioned_tools": ", ".join(self.mentioned_tools),
            "topics": ", ".join(self.topics),
            "summary": self.title[:300],
            "post_url": "",
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        }


# ---------------------------------------------------------------------------
# Markdown table parser
# ---------------------------------------------------------------------------

def _parse_table_rows(text: str) -> list[list[str]]:
    """Extract data rows from a markdown pipe table, skipping header and separator."""
    rows: list[list[str]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        # Skip separator rows (contain only dashes, pipes, spaces)
        if re.match(r"^\|[-| :]+\|$", line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and not all(c.replace("-", "").replace(" ", "") == "" for c in cells):
            rows.append(cells)
    return rows


def _extract_tags(text: str, candidates: list[str]) -> list[str]:
    """Case-insensitive substring match for known tools/topics in a block of text."""
    found: list[str] = []
    lower = text.lower()
    for candidate in candidates:
        if candidate.lower() in lower:
            found.append(candidate)
    return found


def _stable_id(learning_type: str, date: str, title: str) -> str:
    """Deterministic ID: pl-{md5(type:date:title_first_120)}."""
    key = f"{learning_type}:{date}:{title[:120]}"
    return "pl-" + hashlib.md5(key.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Per-file parsers
# ---------------------------------------------------------------------------

def _parse_decisions(path: Path) -> list[LearningEntry]:
    """
    Table columns: Date | Decision | Status | Rationale | Primary References
    """
    text = path.read_text(encoding="utf-8")
    rows = _parse_table_rows(text)
    entries: list[LearningEntry] = []
    header_seen = False
    for row in rows:
        if not header_seen:
            # First row is the header — skip it
            header_seen = True
            continue
        if len(row) < 4:
            continue
        date, decision, status, rationale = row[0], row[1], row[2], row[3]
        refs = row[4] if len(row) > 4 else ""
        combined = f"{decision} {rationale} {refs}"
        entry = LearningEntry(
            entry_id=_stable_id("decision", date, decision),
            learning_type="decision",
            date=date,
            title=decision,
            context=rationale,
            action=refs,
            status=status,
            mentioned_tools=_extract_tags(combined, _KNOWN_TOOLS),
            topics=_extract_tags(combined, _KNOWN_TOPICS),
        )
        entries.append(entry)
    return entries


def _parse_discoveries(path: Path) -> list[LearningEntry]:
    """
    Table columns: Date | Discovery | Why It Matters | Evidence / Source | Follow-Up
    """
    text = path.read_text(encoding="utf-8")
    rows = _parse_table_rows(text)
    entries: list[LearningEntry] = []
    header_seen = False
    for row in rows:
        if not header_seen:
            header_seen = True
            continue
        if len(row) < 3:
            continue
        date, discovery, why = row[0], row[1], row[2]
        follow_up = row[4] if len(row) > 4 else (row[3] if len(row) > 3 else "")
        combined = f"{discovery} {why} {follow_up}"
        entry = LearningEntry(
            entry_id=_stable_id("discovery", date, discovery),
            learning_type="discovery",
            date=date,
            title=discovery,
            context=why,
            action=follow_up,
            mentioned_tools=_extract_tags(combined, _KNOWN_TOOLS),
            topics=_extract_tags(combined, _KNOWN_TOPICS),
        )
        entries.append(entry)
    return entries


def _parse_lessons(path: Path) -> list[LearningEntry]:
    """
    Table columns: Date | Lesson | What Triggered It | Preventive Action
    """
    text = path.read_text(encoding="utf-8")
    rows = _parse_table_rows(text)
    entries: list[LearningEntry] = []
    header_seen = False
    for row in rows:
        if not header_seen:
            header_seen = True
            continue
        if len(row) < 3:
            continue
        date, lesson, trigger = row[0], row[1], row[2]
        action = row[3] if len(row) > 3 else ""
        combined = f"{lesson} {trigger} {action}"
        entry = LearningEntry(
            entry_id=_stable_id("lesson", date, lesson),
            learning_type="lesson",
            date=date,
            title=lesson,
            context=trigger,
            action=action,
            mentioned_tools=_extract_tags(combined, _KNOWN_TOOLS),
            topics=_extract_tags(combined, _KNOWN_TOPICS),
        )
        entries.append(entry)
    return entries


# ---------------------------------------------------------------------------
# Ingest result
# ---------------------------------------------------------------------------

@dataclass
class LearningIngestResult:
    learning_type: str
    added: int
    skipped: int
    failed: int
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class ProjectLearningIngestPipeline:
    """
    Parses the three project log files and writes entries to ChromaDB.

    Configuration keys (all optional):
        store_path (str | Path): ChromaDB directory. Default: data/linkedin_store
    """

    def __init__(self, store_path: str | Path | None = None) -> None:
        from src.pipeline.linkedin_persona_store import STORE_PATH  # noqa: PLC0415
        self._store_path = Path(store_path) if store_path else STORE_PATH

    def _get_store(self):
        from src.pipeline.linkedin_persona_store import LinkedInPersonaStore  # noqa: PLC0415
        store = LinkedInPersonaStore(store_path=self._store_path)
        store.initialize()
        return store

    def run(self) -> list[LearningIngestResult]:
        """Parse all three log files and upsert to ChromaDB. Returns per-type results."""
        store = self._get_store()
        existing_ids = store.get_existing_ids()
        results: list[LearningIngestResult] = []

        parsers = {
            "decision": (_LEARNING_SOURCES["decision"], _parse_decisions),
            "discovery": (_LEARNING_SOURCES["discovery"], _parse_discoveries),
            "lesson": (_LEARNING_SOURCES["lesson"], _parse_lessons),
        }

        for learning_type, (path, parse_fn) in parsers.items():
            result = LearningIngestResult(learning_type=learning_type,
                                          added=0, skipped=0, failed=0)
            if not path.exists():
                logger.warning("Log file not found: %s — skipping", path)
                result.errors.append(f"File not found: {path}")
                results.append(result)
                continue

            try:
                entries = parse_fn(path)
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to parse %s: %s", path.name, exc)
                result.errors.append(str(exc))
                results.append(result)
                continue

            logger.info("Parsed %d %s entries from %s", len(entries), learning_type, path.name)

            for entry in entries:
                if entry.entry_id in existing_ids:
                    # Upsert: re-write to pick up edits to existing log entries
                    try:
                        store._collection.update(
                            ids=[entry.entry_id],
                            documents=[entry.to_document()],
                            metadatas=[entry.to_metadata()],
                        )
                        result.skipped += 1
                    except Exception as exc:  # noqa: BLE001
                        logger.debug("Update skipped for %s: %s", entry.entry_id, exc)
                        result.skipped += 1
                else:
                    try:
                        store._collection.add(
                            ids=[entry.entry_id],
                            documents=[entry.to_document()],
                            metadatas=[entry.to_metadata()],
                        )
                        existing_ids.add(entry.entry_id)
                        result.added += 1
                        logger.debug("Added %s: %s", entry.entry_id, entry.title[:60])
                    except Exception as exc:  # noqa: BLE001
                        logger.error("Failed to add %s: %s", entry.entry_id, exc)
                        result.errors.append(f"{entry.entry_id}: {exc}")
                        result.failed += 1

            logger.info(
                "%s: %d added, %d updated/skipped, %d failed",
                learning_type, result.added, result.skipped, result.failed,
            )
            results.append(result)

        return results
