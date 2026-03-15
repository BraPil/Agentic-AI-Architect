"""Typed Mouseion Core v0 contracts.

This module defines the first reusable shell contracts that live in AAA while
Mouseion is still housed inside this repository. These models represent shared
candidate objects rather than ExMorbus-specific runtime or medical-domain
objects.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ReviewState(str, Enum):
    """Reusable review-state vocabulary for shell-level objects."""

    DRAFT = "draft"
    UNDER_EVALUATION = "under_evaluation"
    NEEDS_REFINEMENT = "needs_refinement"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class AgentAvailability(str, Enum):
    """Simple availability surface for shell-level agent inspection."""

    AVAILABLE = "available"
    LIMITED = "limited"
    UNAVAILABLE = "unavailable"


class MouseionBaseModel(BaseModel):
    """Base model with strict validation and JSON serialization helpers."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    def to_dict(self) -> dict[str, Any]:
        """Return the model as a JSON-compatible dictionary."""
        return self.model_dump(mode="json")


class CriterionScore(MouseionBaseModel):
    """One criterion score used by a shell-level evaluation record."""

    name: str = Field(min_length=1)
    score: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(min_length=1)


class EventEnvelopeV0(MouseionBaseModel):
    """Stable event wrapper for cross-system event transport."""

    schema_version: str = "mouseion-core-v0"
    event_id: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    producer: str = Field(min_length=1)
    occurred_at: datetime
    subject_id: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)


class AgentProfileV0(MouseionBaseModel):
    """Reusable shell representation of an agent actor."""

    schema_version: str = "mouseion-core-v0"
    identity: str = Field(min_length=1)
    capabilities: list[str] = Field(min_length=1)
    availability: AgentAvailability = AgentAvailability.AVAILABLE
    trust_score: float = Field(ge=0.0, le=1.0)
    permitted_namespaces: list[str] = Field(min_length=1)

    @field_validator("capabilities", "permitted_namespaces")
    @classmethod
    def _strip_empty_items(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]


class TaskRequestV0(MouseionBaseModel):
    """Reusable shell contract for requesting work."""

    schema_version: str = "mouseion-core-v0"
    task_id: str = Field(min_length=1)
    task_type: str = Field(min_length=1)
    requester_id: str = Field(min_length=1)
    requested_capability: str = Field(min_length=1)
    context_refs: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(min_length=1)
    namespace: str = Field(min_length=1)
    due_by: datetime | None = None

    @field_validator("context_refs", "success_criteria")
    @classmethod
    def _strip_empty_refs(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]


class TaskResultV0(MouseionBaseModel):
    """Reusable shell contract for returned work."""

    schema_version: str = "mouseion-core-v0"
    task_id: str = Field(min_length=1)
    producer_id: str = Field(min_length=1)
    result_type: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    artifacts: list[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)
    confidence_basis: str = Field(min_length=1)
    provenance_refs: list[str] = Field(default_factory=list)
    recommended_next_action: str | None = None
    review_state: ReviewState = ReviewState.DRAFT

    @field_validator("artifacts", "provenance_refs")
    @classmethod
    def _strip_empty_ids(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]


class EvaluationV0(MouseionBaseModel):
    """Reusable shell record for evaluating outputs."""

    schema_version: str = "mouseion-core-v0"
    target_id: str = Field(min_length=1)
    evaluator_id: str = Field(min_length=1)
    evaluation_type: str = Field(min_length=1)
    criteria_scores: list[CriterionScore] = Field(min_length=1)
    overall_score: float = Field(ge=0.0, le=1.0)
    expected_outcome_summary: str = Field(min_length=1)
    actual_outcome_summary: str = Field(min_length=1)
    pass_fail: bool
    refinement_allowed: bool
    feedback_summary: str = Field(min_length=1)
    provenance_refs: list[str] = Field(default_factory=list)
    review_state: ReviewState = ReviewState.UNDER_EVALUATION

    @field_validator("provenance_refs")
    @classmethod
    def _strip_empty_provenance(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]


class FeedbackV0(MouseionBaseModel):
    """Bounded refinement signal emitted after evaluation."""

    schema_version: str = "mouseion-core-v0"
    feedback_id: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    issuer_id: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    requested_changes: list[str] = Field(default_factory=list)
    refinement_round: int = Field(ge=0)
    review_state: ReviewState = ReviewState.NEEDS_REFINEMENT

    @field_validator("requested_changes")
    @classmethod
    def _strip_empty_requested_changes(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]


class KnowledgeRecordV0(MouseionBaseModel):
    """Durable shell object for reusable memory and review lineage."""

    schema_version: str = "mouseion-core-v0"
    record_id: str = Field(min_length=1)
    record_type: str = Field(min_length=1)
    producer: str = Field(min_length=1)
    created_at: datetime
    updated_at: datetime | None = None
    confidence_basis: str = Field(min_length=1)
    provenance_refs: list[str] = Field(default_factory=list)
    evaluation_history: list[str] = Field(default_factory=list)
    review_state: ReviewState = ReviewState.DRAFT

    @field_validator("provenance_refs", "evaluation_history")
    @classmethod
    def _strip_empty_history_items(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    @model_validator(mode="after")
    def _validate_timestamps(self) -> "KnowledgeRecordV0":
        if self.updated_at is not None and self.updated_at < self.created_at:
            raise ValueError("updated_at must be greater than or equal to created_at")
        return self
