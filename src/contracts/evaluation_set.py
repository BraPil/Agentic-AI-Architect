"""Typed evaluation-set models for the first answer contract.

This module defines a machine-consumable evaluation set for the initial
question families supported by the answer contract. The v0 set is intentionally
small and tied directly to the canonical questions documented in the research
cycle spec.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.contracts.answer_contract import Persona, QuestionType, ResponseMode, Segment, TimeHorizon


# ---------------------------------------------------------------------------
# Evaluation models
# ---------------------------------------------------------------------------


class RubricCriterion(BaseModel):
    """Single weighted scoring criterion for a question."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    weight: float = Field(gt=0.0, le=1.0)

    def to_dict(self) -> dict[str, Any]:
        """Return the rubric criterion as a plain dictionary."""
        return self.model_dump(mode="json")


class EvaluationQuestionV0(BaseModel):
    """One scored evaluation question tied to the answer contract."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    question_id: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    question_type: QuestionType
    response_mode: ResponseMode = ResponseMode.JSON
    segment: Segment
    persona: Persona
    time_horizon: TimeHorizon
    scoring_focus: list[str] = Field(default_factory=list)
    must_include: list[str] = Field(default_factory=list)
    failure_modes: list[str] = Field(default_factory=list)
    rubric: list[RubricCriterion] = Field(min_length=1)

    @field_validator("scoring_focus", "must_include", "failure_modes")
    @classmethod
    def _strip_empty_items(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    @model_validator(mode="after")
    def _validate_rubric_weights(self) -> "EvaluationQuestionV0":
        total_weight = sum(item.weight for item in self.rubric)
        if abs(total_weight - 1.0) > 0.001:
            raise ValueError("rubric weights must sum to 1.0")
        return self

    def to_dict(self) -> dict[str, Any]:
        """Return the evaluation question as a plain dictionary."""
        return self.model_dump(mode="json")


class EvaluationSetV0(BaseModel):
    """Canonical v0 evaluation-set payload for answer quality checks."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    evaluation_set_version: str = "v0"
    contract_version: str = "v0"
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    scoring_scale: str = Field(min_length=1)
    questions: list[EvaluationQuestionV0] = Field(min_length=1)

    @field_validator("evaluation_set_version", "contract_version")
    @classmethod
    def _validate_versions(cls, value: str) -> str:
        if value != "v0":
            raise ValueError("evaluation and contract versions must be 'v0'")
        return value

    @model_validator(mode="after")
    def _validate_unique_ids(self) -> "EvaluationSetV0":
        question_ids = [question.question_id for question in self.questions]
        if len(question_ids) != len(set(question_ids)):
            raise ValueError("question_id values must be unique")
        return self

    def to_dict(self) -> dict[str, Any]:
        """Return the evaluation set as a plain dictionary."""
        return self.model_dump(mode="json")


# ---------------------------------------------------------------------------
# Evaluation set builder
# ---------------------------------------------------------------------------


def _default_rubric() -> list[RubricCriterion]:
    """Return the shared v0 rubric used across the initial question set."""
    return [
        RubricCriterion(
            name="scope_fit",
            description="Addresses the stated question directly without drifting into generic advice.",
            weight=0.2,
        ),
        RubricCriterion(
            name="recommendation_specificity",
            description="Makes concrete architectural or stack choices instead of vague summaries.",
            weight=0.2,
        ),
        RubricCriterion(
            name="enterprise_overlay",
            description="Shows enterprise-safety constraints and how the recommendation shifts by segment.",
            weight=0.2,
        ),
        RubricCriterion(
            name="evidence_and_provenance",
            description="Shows evidence quality, confidence, and source/provenance awareness.",
            weight=0.2,
        ),
        RubricCriterion(
            name="actionability",
            description="Leaves the caller with clear tradeoffs, watchlist items, or next actions.",
            weight=0.2,
        ),
    ]


def build_initial_evaluation_set() -> EvaluationSetV0:
    """Build the initial scored question set for the answer contract."""
    rubric = _default_rubric()
    questions = [
        EvaluationQuestionV0(
            question_id="arch-slo-enterprise",
            prompt=(
                "What is the ideal architecture to meet the SLOs, SLIs, and SLAs for "
                "an enterprise agentic AI system?"
            ),
            question_type=QuestionType.ARCHITECTURE_RECOMMENDATION,
            segment=Segment.ENTERPRISE,
            persona=Persona.ARCHITECT,
            time_horizon=TimeHorizon.NOW,
            scoring_focus=[
                "reliability architecture",
                "operational durability",
                "evaluation and observability",
            ],
            must_include=[
                "orchestrator recommendation",
                "state and workflow durability strategy",
                "evaluation or observability layer",
                "explicit tradeoffs",
            ],
            failure_modes=[
                "ignores enterprise reliability constraints",
                "recommends tools without explaining why",
            ],
            rubric=rubric,
        ),
        EvaluationQuestionV0(
            question_id="stack-current-enterprise",
            prompt="What is the ideal current tech stack for this project right now?",
            question_type=QuestionType.STACK_RECOMMENDATION,
            segment=Segment.ENTERPRISE,
            persona=Persona.ARCHITECT,
            time_horizon=TimeHorizon.NOW,
            scoring_focus=[
                "current stack selection",
                "enterprise compatibility",
                "tooling maturity",
            ],
            must_include=[
                "orchestrator",
                "structured store",
                "retrieval or vector layer",
                "API surface",
                "evaluation tooling",
            ],
            failure_modes=[
                "lists tools without ranking or justification",
                "fails to separate current baseline from future watchlist",
            ],
            rubric=rubric,
        ),
        EvaluationQuestionV0(
            question_id="change-watch-now",
            prompt="What are the most recent and impactful changes to the current paradigm?",
            question_type=QuestionType.CHANGE_WATCH,
            segment=Segment.CROSS_SEGMENT,
            persona=Persona.ARCHITECT,
            time_horizon=TimeHorizon.NOW,
            scoring_focus=[
                "recent shifts",
                "stability versus change",
                "architectural impact",
            ],
            must_include=[
                "top paradigm shifts",
                "why each shift matters",
                "what remains stable",
            ],
            failure_modes=[
                "reports hype without architectural implications",
                "omits confidence or freshness caveats",
            ],
            rubric=rubric,
        ),
        EvaluationQuestionV0(
            question_id="stack-watch-four-weeks",
            prompt="What is likely to become the ideal stack in the next 4 weeks?",
            question_type=QuestionType.CHANGE_WATCH,
            segment=Segment.ENTERPRISE,
            persona=Persona.ARCHITECT,
            time_horizon=TimeHorizon.FOUR_WEEKS,
            scoring_focus=[
                "near-term stack shifts",
                "decision triggers",
                "confidence caveats",
            ],
            must_include=[
                "near-term watchlist",
                "what could change the recommendation",
                "confidence limitations",
            ],
            failure_modes=[
                "presents speculation as certainty",
                "does not distinguish near-term changes from current baseline",
            ],
            rubric=rubric,
        ),
        EvaluationQuestionV0(
            question_id="reusable-artifacts",
            prompt=(
                "What reusable IaC, wrapper, and contract artifacts should be stabilized even as "
                "tools change?"
            ),
            question_type=QuestionType.ARCHITECTURE_RECOMMENDATION,
            segment=Segment.CROSS_SEGMENT,
            persona=Persona.ENGINEER,
            time_horizon=TimeHorizon.QUARTER,
            scoring_focus=[
                "stable seams",
                "artifact reuse",
                "adaptability",
            ],
            must_include=[
                "wrapper interfaces",
                "schema or DTO contracts",
                "IaC or deployment skeletons",
                "what should remain swappable",
            ],
            failure_modes=[
                "focuses only on vendor selection",
                "misses reusable contract boundaries",
            ],
            rubric=rubric,
        ),
        EvaluationQuestionV0(
            question_id="governance-compatible-adaptability",
            prompt=(
                "How should the system stay adaptable while remaining compatible with future "
                "governance, security, and enterprise controls?"
            ),
            question_type=QuestionType.ARCHITECTURE_RECOMMENDATION,
            segment=Segment.ENTERPRISE,
            persona=Persona.OPERATOR,
            time_horizon=TimeHorizon.QUARTER,
            scoring_focus=[
                "future governance compatibility",
                "current delivery speed",
                "review and provenance hooks",
            ],
            must_include=[
                "provenance or evidence fields",
                "confidence semantics",
                "review workflow or escalation path",
                "tradeoff between speed and control",
            ],
            failure_modes=[
                "treats future governance as irrelevant",
                "adds hard blockers without phase awareness",
            ],
            rubric=rubric,
        ),
    ]

    return EvaluationSetV0(
        title="Initial Answer Contract Evaluation Set",
        summary=(
            "First scored question set for validating v0 answer quality against the canonical "
            "architecture, stack, watchlist, artifact, and governance-oriented prompts."
        ),
        scoring_scale="0-5 per rubric criterion, multiplied by criterion weight.",
        questions=questions,
    )