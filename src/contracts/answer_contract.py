"""Pydantic models for the first answer contract.

This module implements the machine-readable request and response schema defined
in ``docs/first-answer-contract-v0.md``. The models validate external-facing
payloads and provide one helper for deriving a human-readable rendering from the
same canonical response body.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class CallerType(str, Enum):
    """Supported caller categories for response negotiation."""

    HUMAN = "human"
    AGENT = "agent"
    DASHBOARD = "dashboard"
    SERVICE = "service"


class ResponseMode(str, Enum):
    """Output mode requested by the caller."""

    JSON = "json"
    HUMAN = "human"
    BOTH = "both"


class DetailLevel(str, Enum):
    """Requested response detail level."""

    BRIEF = "brief"
    STANDARD = "standard"
    DEEP = "deep"


class Segment(str, Enum):
    """Audience segment for the answer."""

    STARTUP = "startup"
    SMALL_COMPANY = "small-company"
    ENTERPRISE = "enterprise"
    CROSS_SEGMENT = "cross-segment"


class Persona(str, Enum):
    """Persona for whom the answer is tuned."""

    ARCHITECT = "architect"
    ENGINEER = "engineer"
    OPERATOR = "operator"
    EXECUTIVE = "executive"


class TimeHorizon(str, Enum):
    """Decision horizon for the answer."""

    NOW = "now"
    FOUR_WEEKS = "4-weeks"
    QUARTER = "quarter"


class QuestionType(str, Enum):
    """Supported top-level question types for contract v0."""

    ARCHITECTURE_RECOMMENDATION = "architecture_recommendation"
    STACK_RECOMMENDATION = "stack_recommendation"
    CHANGE_WATCH = "change_watch"


class EvidenceTier(str, Enum):
    """Evidence-strength categories for sourced claims."""

    DIRECT = "direct"
    PUBLIC_COMPANION = "public_companion"
    USER_PROVIDED = "user_provided"
    INFERRED = "inferred"


# ---------------------------------------------------------------------------
# Nested models
# ---------------------------------------------------------------------------


class AnswerRequestContext(BaseModel):
    """Request metadata used for response negotiation."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    caller_type: CallerType = CallerType.AGENT
    response_mode: ResponseMode = ResponseMode.JSON
    detail_level: DetailLevel = DetailLevel.STANDARD
    segment: Segment = Segment.CROSS_SEGMENT
    persona: Persona = Persona.ARCHITECT
    time_horizon: TimeHorizon = TimeHorizon.NOW

    def to_dict(self) -> dict[str, Any]:
        """Return the normalized request context as a plain dictionary."""
        return self.model_dump(mode="json")


class EvidenceRecord(BaseModel):
    """Single evidence record supporting a recommendation."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    source_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    evidence_tier: EvidenceTier
    freshness: str = Field(min_length=1)
    why_relevant: str = Field(min_length=1)
    source_name: str | None = None
    source_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return the evidence record as a plain dictionary."""
        return self.model_dump(mode="json")


class ConfidenceAssessment(BaseModel):
    """Confidence metadata for an answer."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    score: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(min_length=1)
    gaps: list[str] = Field(default_factory=list)

    @field_validator("gaps")
    @classmethod
    def _strip_empty_gaps(cls, value: list[str]) -> list[str]:
        return [gap.strip() for gap in value if gap.strip()]

    def to_dict(self) -> dict[str, Any]:
        """Return the confidence record as a plain dictionary."""
        return self.model_dump(mode="json")


class FreshnessMetadata(BaseModel):
    """Freshness window and volatility metadata for an answer."""

    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    best_before: datetime
    sensitive_to_change: bool

    @model_validator(mode="after")
    def _validate_window(self) -> "FreshnessMetadata":
        if self.best_before < self.generated_at:
            raise ValueError("best_before must be greater than or equal to generated_at")
        return self

    def to_dict(self) -> dict[str, Any]:
        """Return the freshness record as a JSON-compatible dictionary."""
        return self.model_dump(mode="json")


class SegmentDeltaV0(BaseModel):
    """Segment-specific adjustment notes for one recommendation."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    segment: Segment
    adjustment_summary: str = Field(min_length=1)
    key_priorities: list[str] = Field(default_factory=list)

    @field_validator("key_priorities")
    @classmethod
    def _strip_empty_priorities(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    def to_dict(self) -> dict[str, Any]:
        """Return the segment delta as a plain dictionary."""
        return self.model_dump(mode="json")


class EnterpriseOverlayV0(BaseModel):
    """Enterprise-safety and segment-adjustment metadata for an answer."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    enterprise_safe_now: bool
    reasoning: str = Field(min_length=1)
    key_requirements: list[str] = Field(default_factory=list)
    future_alignment_hooks: list[str] = Field(default_factory=list)
    segment_deltas: list[SegmentDeltaV0] = Field(default_factory=list)

    @field_validator("key_requirements", "future_alignment_hooks")
    @classmethod
    def _strip_empty_items(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    def to_dict(self) -> dict[str, Any]:
        """Return the enterprise overlay as a plain dictionary."""
        return self.model_dump(mode="json")


# ---------------------------------------------------------------------------
# Contract model
# ---------------------------------------------------------------------------


class AnswerContractV0(BaseModel):
    """Canonical machine-readable answer payload for contract version v0."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    contract_version: str = "v0"
    question_type: QuestionType
    segment: Segment
    persona: Persona
    time_horizon: TimeHorizon
    summary: str = Field(min_length=1)
    recommendation: dict[str, Any] = Field(default_factory=dict)
    enterprise_overlay: EnterpriseOverlayV0 | None = None
    tradeoffs: list[str] = Field(default_factory=list)
    evidence: list[EvidenceRecord] = Field(default_factory=list)
    confidence: ConfidenceAssessment
    watchlist: list[str] = Field(default_factory=list)
    reusable_artifacts: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    freshness: FreshnessMetadata
    rendered_response: str | None = None

    @field_validator(
        "tradeoffs",
        "watchlist",
        "reusable_artifacts",
        "next_actions",
    )
    @classmethod
    def _strip_empty_strings(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    @field_validator("contract_version")
    @classmethod
    def _validate_version(cls, value: str) -> str:
        if value != "v0":
            raise ValueError("contract_version must be 'v0'")
        return value

    def render_human_response(self) -> str:
        """Render a concise human-readable view from the canonical payload."""
        lines = [self.summary]

        if self.recommendation:
            recommendation_items = ", ".join(
                f"{key}={value}" for key, value in self.recommendation.items()
            )
            lines.append(f"Recommendation: {recommendation_items}")

        if self.enterprise_overlay is not None:
            lines.append(
                "Enterprise overlay: "
                f"enterprise_safe_now={self.enterprise_overlay.enterprise_safe_now}; "
                f"requirements={', '.join(self.enterprise_overlay.key_requirements)}"
            )

        if self.tradeoffs:
            lines.append(f"Tradeoffs: {'; '.join(self.tradeoffs)}")

        if self.watchlist:
            lines.append(f"Watchlist: {', '.join(self.watchlist)}")

        if self.next_actions:
            lines.append(f"Next actions: {', '.join(self.next_actions)}")

        return "\n".join(lines)

    def to_response_payload(
        self,
        response_mode: ResponseMode = ResponseMode.JSON,
    ) -> dict[str, Any]:
        """Return canonical JSON with optional human-rendered projection."""
        payload = self.model_dump(mode="json")
        payload["rendered_response"] = None

        if response_mode in (ResponseMode.HUMAN, ResponseMode.BOTH):
            payload["rendered_response"] = self.render_human_response()

        return payload

    def to_dict(self) -> dict[str, Any]:
        """Return the canonical payload as a plain dictionary."""
        return self.model_dump(mode="json")