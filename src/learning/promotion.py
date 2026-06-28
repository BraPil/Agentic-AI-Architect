"""
PromotionGate — the single load-bearing function that moves an agent-generated
artifact from the quarantined `experimental` tier to the trusted `grounded` tier.

This is the human checkpoint in the echo-chamber firewall. Nothing else is allowed
to change an artifact's tier to `grounded`. Every transition:
  - enforces a confidence threshold,
  - is reversible (demote),
  - writes an append-only audit record.

Configuration keys (PromotionGate.__init__):
    confidence_threshold (float): minimum artifact confidence to allow promotion (default 0.7)
    audit_log (Path): where promotion/rejection/demotion events are recorded

The gate operates on a ChromaDB-style collection object so it stays cheap to test
(inject a fake collection; no embedding model load required).
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TIER_EXPERIMENTAL = "experimental"
TIER_GROUNDED = "grounded"

DEFAULT_CONFIDENCE_THRESHOLD = 0.7
_DEFAULT_AUDIT_LOG = Path("data/learning_promotions.jsonl")


# ---------------------------------------------------------------------------
# Result model
# ---------------------------------------------------------------------------

@dataclass
class PromotionResult:
    """Outcome of a promotion/rejection/demotion attempt."""

    artifact_id: str
    action: str               # promote | reject | demote
    ok: bool
    from_tier: str = ""
    to_tier: str = ""
    confidence: float = 0.0
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Candidate model
# ---------------------------------------------------------------------------

@dataclass
class PromotionCandidate:
    """An experimental artifact awaiting human review."""

    artifact_id: str
    title: str
    confidence: float
    author_id: str
    topics: list[str] = field(default_factory=list)
    snippet: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# The gate
# ---------------------------------------------------------------------------

class PromotionGate:
    """Human-gated promotion of experimental artifacts into the grounded tier."""

    def __init__(
        self,
        collection: Any,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
        audit_log: Path | str = _DEFAULT_AUDIT_LOG,
    ) -> None:
        self._collection = collection
        self._threshold = confidence_threshold
        self._audit_log = Path(audit_log)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def list_candidates(self, min_confidence: float = 0.0) -> list[PromotionCandidate]:
        """Return experimental artifacts awaiting review, highest confidence first."""
        raw = self._collection.get(
            where={"source_tier": TIER_EXPERIMENTAL},
            include=["documents", "metadatas"],
        )
        candidates: list[PromotionCandidate] = []
        for i, art_id in enumerate(raw.get("ids", [])):
            meta = raw["metadatas"][i] if raw.get("metadatas") else {}
            doc = raw["documents"][i] if raw.get("documents") else ""
            conf = float(meta.get("confidence", 0.0) or 0.0)
            if conf < min_confidence:
                continue
            candidates.append(PromotionCandidate(
                artifact_id=art_id,
                title=meta.get("title", "") or doc[:80],
                confidence=conf,
                author_id=meta.get("author", meta.get("persona_id", "unknown")),
                topics=[t.strip() for t in meta.get("topics", "").split(",") if t.strip()],
                snippet=doc[:300],
            ))
        candidates.sort(key=lambda c: c.confidence, reverse=True)
        return candidates

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def promote(self, artifact_id: str, approved_by: str) -> PromotionResult:
        """Promote experimental → grounded. Requires confidence >= threshold."""
        meta = self._get_meta(artifact_id)
        if meta is None:
            return PromotionResult(artifact_id, "promote", False,
                                   reason="artifact not found")

        tier = meta.get("source_tier", "")
        if tier != TIER_EXPERIMENTAL:
            return PromotionResult(artifact_id, "promote", False, from_tier=tier,
                                   reason=f"only experimental artifacts can be promoted (is '{tier}')")

        conf = float(meta.get("confidence", 0.0) or 0.0)
        if conf < self._threshold:
            return PromotionResult(artifact_id, "promote", False,
                                   from_tier=tier, confidence=conf,
                                   reason=f"confidence {conf:.2f} below threshold {self._threshold:.2f}")

        meta["source_tier"] = TIER_GROUNDED
        meta["promoted_by"] = approved_by
        meta["promoted_at"] = datetime.now(timezone.utc).isoformat()
        self._collection.update(ids=[artifact_id], metadatas=[meta])

        result = PromotionResult(artifact_id, "promote", True,
                                 from_tier=TIER_EXPERIMENTAL, to_tier=TIER_GROUNDED,
                                 confidence=conf, reason=f"approved by {approved_by}")
        self._audit(result, approved_by)
        logger.info("Promoted %s to grounded (confidence %.2f, by %s)",
                    artifact_id, conf, approved_by)
        return result

    def reject(self, artifact_id: str, rejected_by: str, reason: str = "") -> PromotionResult:
        """Reject an experimental artifact — removes it from the store."""
        meta = self._get_meta(artifact_id)
        if meta is None:
            return PromotionResult(artifact_id, "reject", False, reason="artifact not found")

        tier = meta.get("source_tier", "")
        if tier != TIER_EXPERIMENTAL:
            return PromotionResult(artifact_id, "reject", False, from_tier=tier,
                                   reason=f"only experimental artifacts can be rejected (is '{tier}')")

        self._collection.delete(ids=[artifact_id])
        result = PromotionResult(artifact_id, "reject", True, from_tier=TIER_EXPERIMENTAL,
                                 reason=reason or f"rejected by {rejected_by}")
        self._audit(result, rejected_by)
        logger.info("Rejected %s (%s)", artifact_id, reason or rejected_by)
        return result

    def demote(self, artifact_id: str, demoted_by: str, reason: str = "") -> PromotionResult:
        """Reverse a promotion: grounded → experimental."""
        meta = self._get_meta(artifact_id)
        if meta is None:
            return PromotionResult(artifact_id, "demote", False, reason="artifact not found")

        tier = meta.get("source_tier", "")
        if tier != TIER_GROUNDED:
            return PromotionResult(artifact_id, "demote", False, from_tier=tier,
                                   reason=f"only grounded artifacts can be demoted (is '{tier}')")

        meta["source_tier"] = TIER_EXPERIMENTAL
        meta["demoted_by"] = demoted_by
        meta["demoted_at"] = datetime.now(timezone.utc).isoformat()
        self._collection.update(ids=[artifact_id], metadatas=[meta])

        result = PromotionResult(artifact_id, "demote", True,
                                 from_tier=TIER_GROUNDED, to_tier=TIER_EXPERIMENTAL,
                                 reason=reason or f"demoted by {demoted_by}")
        self._audit(result, demoted_by)
        logger.info("Demoted %s back to experimental (%s)", artifact_id, reason or demoted_by)
        return result

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _get_meta(self, artifact_id: str) -> dict | None:
        raw = self._collection.get(ids=[artifact_id], include=["metadatas"])
        ids = raw.get("ids", [])
        if not ids:
            return None
        metas = raw.get("metadatas") or [{}]
        return dict(metas[0]) if metas else {}

    def _audit(self, result: PromotionResult, actor: str) -> None:
        """Append an audit record. Never let auditing break the operation."""
        try:
            self._audit_log.parent.mkdir(parents=True, exist_ok=True)
            record = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "actor": actor,
                **result.to_dict(),
            }
            with self._audit_log.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:  # noqa: BLE001
            logger.warning("Failed to write promotion audit record for %s", result.artifact_id)
