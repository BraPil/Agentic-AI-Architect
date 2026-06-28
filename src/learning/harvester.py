"""
Harvester — ingests OAA-emitted KnowledgeRecordV0 artifacts into AAA's ChromaDB
under the quarantined `experimental` provenance tier.

This is the OAA → AAA boundary. OAA runs as its own process (its MoltBook clone)
and writes KnowledgeRecordV0 records to a JSONL file. AAA observes that file and
makes the artifacts *actionable* — searchable only behind an explicit flag, never
surfaced as fact, never counted in trends — until a human promotes them via the
PromotionGate.

KnowledgeRecordV0 shape (from OAA src/mouseion/contracts.py):
    record_id, author_id, content, content_hash, topic_tags, confidence,
    provenance_refs, review_history, created_at_ms, updated_at_ms, schema_version

Flow:
    OAA cycle → artifacts.jsonl → harvest() → ChromaDB (source_tier=experimental)
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.learning.promotion import TIER_EXPERIMENTAL

logger = logging.getLogger(__name__)

_HARVEST_PERSONA = "oaa_agent"      # persona_id bucket for all harvested artifacts
_POST_TYPE = "learning_artifact"


# ---------------------------------------------------------------------------
# Artifact model
# ---------------------------------------------------------------------------

@dataclass
class LearningArtifact:
    """An OAA KnowledgeRecordV0 normalized for AAA's ChromaDB conventions."""

    artifact_id: str
    author_id: str
    content: str
    confidence: float
    topics: list[str] = field(default_factory=list)
    provenance_refs: list[str] = field(default_factory=list)
    created_at: str = ""
    title: str = ""

    @classmethod
    def from_knowledge_record(cls, record: dict[str, Any]) -> "LearningArtifact":
        """Build from a KnowledgeRecordV0 dict (OAA's emitted shape)."""
        from src.utils.helpers import sanitize_text  # noqa: PLC0415

        record_id = record.get("record_id") or record.get("content_hash") or ""
        content = sanitize_text(record.get("content", "") or "")
        created_ms = record.get("created_at_ms")
        created_at = (
            datetime.fromtimestamp(created_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
            if isinstance(created_ms, (int, float)) else
            datetime.now(timezone.utc).strftime("%Y-%m-%d")
        )
        first_line = content.strip().splitlines()[0] if content.strip() else record_id
        return cls(
            artifact_id=f"la-{record_id}",
            author_id=record.get("author_id", "unknown"),
            content=content,
            confidence=float(record.get("confidence", 0.0) or 0.0),
            topics=list(record.get("topic_tags", []) or []),
            provenance_refs=list(record.get("provenance_refs", []) or []),
            created_at=created_at,
            title=first_line[:120],
        )

    def to_document(self) -> str:
        parts = [self.content.strip()]
        if self.topics:
            parts.append(f"Topics: {', '.join(self.topics)}")
        return "\n\n".join(p for p in parts if p)

    def to_metadata(self) -> dict[str, Any]:
        return {
            "persona_id": _HARVEST_PERSONA,
            "author": self.author_id,
            "post_type": _POST_TYPE,
            "source_tier": TIER_EXPERIMENTAL,
            "confidence": self.confidence,
            "timestamp": self.created_at,
            "title": self.title[:200],
            "topics": ", ".join(self.topics),
            "mentioned_tools": "",
            "summary": self.title[:300],
            "provenance_refs": ", ".join(self.provenance_refs),
            "post_url": "",
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        }


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

@dataclass
class HarvestResult:
    added: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def parse_artifacts(jsonl_path: Path) -> list[LearningArtifact]:
    """Parse a JSONL file of KnowledgeRecordV0 records into LearningArtifacts."""
    artifacts: list[LearningArtifact] = []
    for line in Path(jsonl_path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        artifacts.append(LearningArtifact.from_knowledge_record(record))
    return artifacts


class HarvestPipeline:
    """Ingests OAA artifact files into ChromaDB as experimental-tier entries."""

    def __init__(self, collection: Any) -> None:
        # collection is a ChromaDB-style collection (inject a fake in tests).
        self._collection = collection

    def run(self, jsonl_path: Path | str) -> HarvestResult:
        path = Path(jsonl_path)
        result = HarvestResult()
        if not path.exists():
            result.errors.append(f"File not found: {path}")
            return result

        try:
            artifacts = parse_artifacts(path)
        except Exception as exc:  # noqa: BLE001
            result.errors.append(f"Parse error: {exc}")
            return result

        existing = set(self._collection.get(include=[]).get("ids", []))
        for art in artifacts:
            try:
                if art.artifact_id in existing:
                    self._collection.update(
                        ids=[art.artifact_id],
                        documents=[art.to_document()],
                        metadatas=[art.to_metadata()],
                    )
                    result.skipped += 1
                else:
                    self._collection.add(
                        ids=[art.artifact_id],
                        documents=[art.to_document()],
                        metadatas=[art.to_metadata()],
                    )
                    existing.add(art.artifact_id)
                    result.added += 1
            except Exception as exc:  # noqa: BLE001
                result.failed += 1
                result.errors.append(f"{art.artifact_id}: {exc}")

        logger.info("Harvest complete: %d added, %d updated, %d failed",
                    result.added, result.skipped, result.failed)
        return result
