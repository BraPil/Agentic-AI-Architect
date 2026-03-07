"""
Trend Tracker Agent — Monitors, scores and ranks emerging AI architecture trends.

Each trend is scored using:
    recency_score       (0–10)  — how recent is the evidence?
    adoption_velocity   (0–10)  — how fast is it being adopted?
    credibility_signal  (0–10)  — how credible are the sources?
    novelty_delta       (0–10)  — how different is it from prior art?

Composite score formula:
    trend_score = (
        recency_score     * 0.30 +
        adoption_velocity * 0.35 +
        credibility_signal* 0.25 +
        novelty_delta     * 0.10
    )

Alerts:
    NEW_TREND    — score > 7.0 within first 30 days of tracking
    DECLINE      — score drops below 5.0 for 60+ consecutive days
    BREAKTHROUGH — score jumps > 2.0 in a single cycle
"""

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any

from .base_agent import BaseAgent


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class TrendScore:
    """Scored snapshot of a trend at a point in time."""

    trend_name: str
    recency: float
    adoption_velocity: float
    credibility: float
    novelty_delta: float
    scored_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    evidence_count: int = 0
    notes: str = ""

    @property
    def composite(self) -> float:
        """Weighted composite trend score (0–10)."""
        return round(
            self.recency * 0.30
            + self.adoption_velocity * 0.35
            + self.credibility * 0.25
            + self.novelty_delta * 0.10,
            2,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "trend_name": self.trend_name,
            "recency": self.recency,
            "adoption_velocity": self.adoption_velocity,
            "credibility": self.credibility,
            "novelty_delta": self.novelty_delta,
            "composite": self.composite,
            "scored_at": self.scored_at.isoformat(),
            "evidence_count": self.evidence_count,
            "notes": self.notes,
        }


@dataclass
class TrendAlert:
    """Notification emitted when a trend crosses a threshold."""

    alert_type: str  # NEW_TREND | DECLINE | BREAKTHROUGH
    trend_name: str
    score: float
    previous_score: float | None
    message: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "alert_type": self.alert_type,
            "trend_name": self.trend_name,
            "score": self.score,
            "previous_score": self.previous_score,
            "message": self.message,
            "created_at": self.created_at.isoformat(),
        }


# ---------------------------------------------------------------------------
# Seed trends (pre-populated; system adds more as it discovers them)
# ---------------------------------------------------------------------------

SEED_TRENDS: dict[str, dict[str, Any]] = {
    "Agentic RAG": {"namespace": "frameworks", "initial_score": 9.0},
    "Dynamic Tool Discovery (MCP-on-demand)": {"namespace": "tools", "initial_score": 9.0},
    "Small Language Models (SLMs)": {"namespace": "tools", "initial_score": 8.8},
    "Reasoning Models (Test-Time Compute)": {"namespace": "frameworks", "initial_score": 8.7},
    "Compound AI Systems": {"namespace": "frameworks", "initial_score": 9.2},
    "Graph RAG": {"namespace": "frameworks", "initial_score": 8.2},
    "AI-Native Development Tools": {"namespace": "tools", "initial_score": 8.3},
    "Enterprise AI Governance": {"namespace": "frameworks", "initial_score": 8.0},
    "Multimodal Production AI": {"namespace": "trends", "initial_score": 8.5},
    "World Models (JEPA)": {"namespace": "frameworks", "initial_score": 6.5},
    "Speculative Decoding": {"namespace": "frameworks", "initial_score": 7.8},
    "On-Device Inference": {"namespace": "trends", "initial_score": 8.0},
    "LangGraph": {"namespace": "tools", "initial_score": 8.5},
    "DSPy Prompt Optimization": {"namespace": "frameworks", "initial_score": 7.5},
    "Computer Use Agents (ACI)": {"namespace": "trends", "initial_score": 7.8},
    "Vibe Coding": {"namespace": "trends", "initial_score": 7.5},
    "Mixture of Experts (MoE)": {"namespace": "frameworks", "initial_score": 8.3},
}


# ---------------------------------------------------------------------------
# TrendTrackerAgent
# ---------------------------------------------------------------------------

class TrendTrackerAgent(BaseAgent):
    """
    Maintains a scored trend registry and generates alerts.

    Configuration keys:
        new_trend_threshold (float): Alert score for new trends (default 7.0).
        decline_threshold (float): Score below which a trend is declining (default 5.0).
        breakthrough_delta (float): Score jump that triggers a breakthrough alert (default 2.0).
        history (dict): Existing trend score history to seed from.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(name="TrendTrackerAgent", config=config)
        self._new_trend_threshold: float = self.config.get("new_trend_threshold", 7.0)
        self._decline_threshold: float = self.config.get("decline_threshold", 5.0)
        self._breakthrough_delta: float = self.config.get("breakthrough_delta", 2.0)
        # trend_name -> list of TrendScore (chronological)
        self._history: dict[str, list[TrendScore]] = {}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        super().initialize()
        self._seed_initial_trends()
        self.logger.info("TrendTrackerAgent tracking %d trends", len(self._history))

    # ------------------------------------------------------------------
    # Core execution
    # ------------------------------------------------------------------

    def _execute(self, task_input: Any = None) -> dict[str, Any]:
        """
        Score trends using research findings as evidence.

        Args:
            task_input: List of ResearchFinding dicts from ResearchAgent.

        Returns:
            dict with keys: scores (list), alerts (list), summary (str)
        """
        findings: list[dict[str, Any]] = task_input if isinstance(task_input, list) else []
        alerts: list[dict[str, Any]] = []

        # Update scores based on new findings
        self._ingest_findings(findings)

        # Score all tracked trends
        current_scores: list[dict[str, Any]] = []
        for trend_name, history in self._history.items():
            score = self._compute_score(trend_name, history, findings)
            previous = history[-1] if history else None
            history.append(score)

            # Check alert conditions
            alert = self._check_alerts(score, previous)
            if alert:
                alerts.append(alert.to_dict())

            current_scores.append(score.to_dict())

        # Sort by composite score descending
        current_scores.sort(key=lambda s: s["composite"], reverse=True)

        summary = self._generate_summary(current_scores, alerts)

        return {
            "scores": current_scores,
            "alerts": alerts,
            "summary": summary,
            "total_trends": len(current_scores),
        }

    # ------------------------------------------------------------------
    # Scoring logic
    # ------------------------------------------------------------------

    def _compute_score(
        self,
        trend_name: str,
        history: list[TrendScore],
        findings: list[dict[str, Any]],
    ) -> TrendScore:
        """Compute a fresh TrendScore for a single trend."""
        trend_lower = trend_name.lower()

        # Count how many recent findings mention this trend
        evidence_count = sum(
            1 for f in findings
            if trend_lower in f.get("summary", "").lower()
            or trend_lower in " ".join(f.get("concepts", [])).lower()
            or trend_lower in " ".join(f.get("tools_mentioned", [])).lower()
        )

        # Recency: decay based on days since last evidence
        recency = self._recency_score(history)

        # Adoption velocity: based on evidence count in this cycle (max out at 10)
        adoption_velocity = min(10.0, evidence_count * 1.5 + (history[-1].adoption_velocity * 0.7 if history else 5.0))

        # Credibility: maintain from prior; boost on high-evidence cycles
        prior_cred = history[-1].credibility if history else 7.0
        credibility = min(10.0, prior_cred + 0.2 * (evidence_count > 0))

        # Novelty delta: how much has the score changed?
        novelty_delta = 5.0  # default mid-range
        if history:
            prior_composite = history[-1].composite
            delta = abs(prior_composite - (recency * 0.30 + adoption_velocity * 0.35 + credibility * 0.25 + novelty_delta * 0.10))
            novelty_delta = min(10.0, 5.0 + delta * 2)

        return TrendScore(
            trend_name=trend_name,
            recency=recency,
            adoption_velocity=round(adoption_velocity, 2),
            credibility=round(credibility, 2),
            novelty_delta=round(novelty_delta, 2),
            evidence_count=evidence_count,
        )

    def _recency_score(self, history: list[TrendScore]) -> float:
        """Higher score for trends with recent evidence; decays over time."""
        if not history:
            return 7.0  # New trend — assume moderately recent
        last = history[-1].scored_at
        days_since = (datetime.now(timezone.utc) - last).days
        # Exponential decay: 10 at day 0, ~7 at day 7, ~5 at day 30
        return round(max(1.0, 10.0 * math.exp(-0.015 * days_since)), 2)

    # ------------------------------------------------------------------
    # Alert logic
    # ------------------------------------------------------------------

    def _check_alerts(self, score: TrendScore, previous: TrendScore | None) -> TrendAlert | None:
        """Emit an alert if the trend score crosses a threshold."""
        composite = score.composite
        prev_composite = previous.composite if previous else None

        # NEW_TREND: first time above threshold
        if prev_composite is None and composite >= self._new_trend_threshold:
            return TrendAlert(
                alert_type="NEW_TREND",
                trend_name=score.trend_name,
                score=composite,
                previous_score=None,
                message=f"New trend '{score.trend_name}' emerged with score {composite:.1f}",
            )

        if prev_composite is not None:
            # BREAKTHROUGH: score jumped significantly
            if composite - prev_composite >= self._breakthrough_delta:
                return TrendAlert(
                    alert_type="BREAKTHROUGH",
                    trend_name=score.trend_name,
                    score=composite,
                    previous_score=prev_composite,
                    message=(
                        f"Trend '{score.trend_name}' jumped from {prev_composite:.1f} "
                        f"to {composite:.1f} (+{composite - prev_composite:.1f})"
                    ),
                )

            # DECLINE: score dropped below threshold
            if prev_composite >= self._decline_threshold and composite < self._decline_threshold:
                return TrendAlert(
                    alert_type="DECLINE",
                    trend_name=score.trend_name,
                    score=composite,
                    previous_score=prev_composite,
                    message=f"Trend '{score.trend_name}' is declining (score {composite:.1f})",
                )

        return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _seed_initial_trends(self) -> None:
        """Pre-populate history with seed trends."""
        for name, meta in SEED_TRENDS.items():
            initial = meta.get("initial_score", 7.0)
            seed_score = TrendScore(
                trend_name=name,
                recency=initial,
                adoption_velocity=initial,
                credibility=initial,
                novelty_delta=initial,
                scored_at=datetime.now(timezone.utc) - timedelta(days=1),
                notes="seed",
            )
            self._history[name] = [seed_score]

    def _ingest_findings(self, findings: list[dict[str, Any]]) -> None:
        """Add any newly discovered trends from research findings."""
        for finding in findings:
            for concept in finding.get("concepts", []):
                concept_clean = concept.strip()
                if concept_clean and concept_clean not in self._history:
                    self._history[concept_clean] = []

    def _generate_summary(self, scores: list[dict[str, Any]], alerts: list[dict[str, Any]]) -> str:
        """Produce a human-readable trend summary."""
        top5 = scores[:5]
        lines = ["## Trend Summary\n"]
        lines.append(f"**Total trends tracked**: {len(scores)}\n")
        lines.append(f"**Alerts generated**: {len(alerts)}\n")
        lines.append("\n### Top 5 Trends\n")
        for i, s in enumerate(top5, 1):
            lines.append(f"{i}. **{s['trend_name']}** — score {s['composite']:.1f}")
        if alerts:
            lines.append("\n### Alerts\n")
            for a in alerts:
                lines.append(f"- [{a['alert_type']}] {a['message']}")
        return "\n".join(lines)

    def get_top_trends(self, n: int = 10) -> list[dict[str, Any]]:
        """Return the top-n trends by composite score."""
        scores = []
        for trend_name, history in self._history.items():
            if history:
                scores.append(history[-1].to_dict())
        return sorted(scores, key=lambda s: s["composite"], reverse=True)[:n]
