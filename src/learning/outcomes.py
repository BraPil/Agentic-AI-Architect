"""
RecommendationOutcomeStore — the missing half of the P6 learning loop.

Retrieval over internal memory (project_learning ingest) lets AAA *recall* what it
has done. This module lets AAA *learn from outcomes*: it records, for each
architecture recommendation it emits, whether the human actually adopted it and
whether it worked — then aggregates that into a per-persona / per-tool signal that
later ranking slices can weight by.

Design (mirrors PromotionGate's append-only audit pattern):
  - Two event types share one append-only JSONL ledger:
      {"event": "recommendation", recommendation_id, problem_statement, personas_cited, tools, confidence, ts}
      {"event": "outcome",        recommendation_id, adopted, worked, outcome_score, notes, recorded_by, ts}
  - The ledger is the source of truth; get()/pending()/aggregate() replay it.
  - Nothing here mutates the ChromaDB corpus. This slice CAPTURES and EXPOSES the
    signal; wiring it into retrieval ranking is the next slice (see
    docs/p6-outcome-capture-v0.md). Keeping them separate means we never silently
    shift eval scores while the outcome dataset is still tiny.

A "success" is adopted AND worked. Per-persona multipliers use Laplace smoothing so
a single data point cannot swing a source's weight — small-data honesty over
reactivity.
"""

import hashlib
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

_DEFAULT_LEDGER = Path("data/recommendation_outcomes.jsonl")

EVENT_RECOMMENDATION = "recommendation"
EVENT_OUTCOME = "outcome"

# Multiplier bounds for the (future) ranking integration. A source with a perfect
# track record earns at most MULT_MAX; a consistently-failing one at most MULT_MIN.
MULT_MIN = 0.5
MULT_MAX = 1.5


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def compute_recommendation_id(problem_statement: str, generated_at: str) -> str:
    """Stable per-instance id for one recommendation event.

    Includes the timestamp so asking the same question twice yields two distinct
    recommendations (each can have its own outcome).
    """
    digest = hashlib.md5(f"{problem_statement}|{generated_at}".encode("utf-8")).hexdigest()
    return f"rec-{digest[:16]}"


# ---------------------------------------------------------------------------
# Merged view model
# ---------------------------------------------------------------------------

@dataclass
class OutcomeRecord:
    """The merged recommendation+outcome view for one recommendation_id."""

    recommendation_id: str
    problem_statement: str = ""
    personas_cited: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    confidence: str = ""
    recommended_at: str = ""
    # Outcome (None until an outcome event is recorded):
    adopted: bool | None = None
    worked: bool | None = None
    outcome_score: float | None = None
    notes: str = ""
    recorded_by: str = ""
    recorded_at: str = ""

    @property
    def has_outcome(self) -> bool:
        return self.adopted is not None

    @property
    def success(self) -> bool:
        """Adopted AND worked — the signal that should raise a source's weight."""
        return bool(self.adopted) and bool(self.worked)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["has_outcome"] = self.has_outcome
        d["success"] = self.success if self.has_outcome else None
        return d


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------

class RecommendationOutcomeStore:
    """Append-only ledger of recommendations and their real-world outcomes."""

    def __init__(self, ledger_path: Path | str = _DEFAULT_LEDGER) -> None:
        self._ledger = Path(ledger_path)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def record_recommendation(
        self,
        recommendation_id: str,
        problem_statement: str,
        personas_cited: list[str] | None = None,
        tools: list[str] | None = None,
        confidence: str = "",
    ) -> None:
        """Log that a recommendation was emitted. Best-effort; never raises."""
        self._append({
            "event": EVENT_RECOMMENDATION,
            "recommendation_id": recommendation_id,
            "problem_statement": problem_statement[:500],
            "personas_cited": personas_cited or [],
            "tools": tools or [],
            "confidence": confidence,
            "ts": _now(),
        })

    def record_outcome(
        self,
        recommendation_id: str,
        adopted: bool,
        worked: bool = False,
        outcome_score: float | None = None,
        notes: str = "",
        recorded_by: str = "brandt",
    ) -> OutcomeRecord:
        """Record whether a recommendation was adopted and whether it worked.

        Returns the merged OutcomeRecord. Raises ValueError for an unknown
        recommendation_id so the caller (CLI/MCP) can report it cleanly.
        """
        # Only record outcomes against recommendations the system actually emitted.
        # Check before appending so a bad id never pollutes the ledger.
        existing = self.get(recommendation_id)
        if existing is None or not existing.recommended_at:
            raise ValueError(f"unknown recommendation_id: {recommendation_id}")

        if outcome_score is not None:
            outcome_score = max(0.0, min(1.0, float(outcome_score)))
        self._append({
            "event": EVENT_OUTCOME,
            "recommendation_id": recommendation_id,
            "adopted": bool(adopted),
            "worked": bool(worked),
            "outcome_score": outcome_score,
            "notes": notes,
            "recorded_by": recorded_by,
            "ts": _now(),
        })
        return self.get(recommendation_id)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def _replay(self) -> dict[str, OutcomeRecord]:
        """Fold the event ledger into a {recommendation_id: OutcomeRecord} map."""
        records: dict[str, OutcomeRecord] = {}
        for event in self._events():
            rid = event.get("recommendation_id")
            if not rid:
                continue
            rec = records.setdefault(rid, OutcomeRecord(recommendation_id=rid))
            if event.get("event") == EVENT_RECOMMENDATION:
                rec.problem_statement = event.get("problem_statement", rec.problem_statement)
                rec.personas_cited = event.get("personas_cited", rec.personas_cited)
                rec.tools = event.get("tools", rec.tools)
                rec.confidence = event.get("confidence", rec.confidence)
                rec.recommended_at = event.get("ts", rec.recommended_at)
            elif event.get("event") == EVENT_OUTCOME:
                # Last outcome wins (outcomes can be corrected by re-recording).
                rec.adopted = event.get("adopted")
                rec.worked = event.get("worked")
                rec.outcome_score = event.get("outcome_score")
                rec.notes = event.get("notes", "")
                rec.recorded_by = event.get("recorded_by", "")
                rec.recorded_at = event.get("ts", "")
        return records

    def get(self, recommendation_id: str) -> OutcomeRecord | None:
        return self._replay().get(recommendation_id)

    def pending(self) -> list[OutcomeRecord]:
        """Recommendations that have been emitted but have no recorded outcome."""
        return [r for r in self._replay().values()
                if not r.has_outcome and r.recommended_at]

    def aggregate(self) -> dict[str, Any]:
        """Roll up the learning signal: overall rates + per-persona/per-tool weights."""
        records = [r for r in self._replay().values() if r.has_outcome]
        total = len(records)
        adopted = sum(1 for r in records if r.adopted)
        worked = sum(1 for r in records if r.success)
        scores = [r.outcome_score for r in records if r.outcome_score is not None]

        persona_signal = self._entity_signal(records, key="personas_cited")
        tool_signal = self._entity_signal(records, key="tools")

        return {
            "total_recommendations": len(self._replay()),
            "outcomes_recorded": total,
            "pending_outcomes": len(self.pending()),
            "adoption_rate": round(adopted / total, 4) if total else None,
            "success_rate": round(worked / total, 4) if total else None,
            "mean_outcome_score": round(sum(scores) / len(scores), 4) if scores else None,
            "persona_signal": persona_signal,
            "tool_signal": tool_signal,
        }

    # ------------------------------------------------------------------
    # Signal
    # ------------------------------------------------------------------

    @staticmethod
    def _laplace_multiplier(successes: int, trials: int) -> float:
        """Smoothed success estimate mapped to a bounded ranking multiplier.

        (successes + 1) / (trials + 2) gives a prior of 0.5 (neutral) with zero
        data, so one outcome nudges rather than dictates. Mapped onto
        [MULT_MIN, MULT_MAX].
        """
        smoothed = (successes + 1) / (trials + 2)
        return round(MULT_MIN + (MULT_MAX - MULT_MIN) * smoothed, 4)

    def _entity_signal(self, records: list[OutcomeRecord], key: str) -> dict[str, dict]:
        """Per-entity (persona or tool) success tally + smoothed weight multiplier."""
        tally: dict[str, dict[str, int]] = {}
        for r in records:
            for entity in getattr(r, key) or []:
                if not entity:
                    continue
                t = tally.setdefault(entity, {"recommended": 0, "worked": 0})
                t["recommended"] += 1
                if r.success:
                    t["worked"] += 1
        return {
            entity: {
                "recommended": t["recommended"],
                "worked": t["worked"],
                "success_rate": round(t["worked"] / t["recommended"], 4) if t["recommended"] else None,
                "weight_multiplier": self._laplace_multiplier(t["worked"], t["recommended"]),
            }
            for entity, t in sorted(tally.items())
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _events(self) -> list[dict]:
        if not self._ledger.exists():
            return []
        events: list[dict] = []
        for line in self._ledger.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                logger.warning("Skipping malformed outcome ledger line")
        return events

    def _append(self, record: dict) -> None:
        """Append one event. Never let logging break the calling operation."""
        try:
            self._ledger.parent.mkdir(parents=True, exist_ok=True)
            with self._ledger.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:  # noqa: BLE001
            logger.warning("Failed to append outcome event for %s",
                           record.get("recommendation_id"))
