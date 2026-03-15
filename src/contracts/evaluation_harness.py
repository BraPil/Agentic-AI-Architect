"""Executable scoring harness for v0 query responses.

This module turns the static evaluation set into a deterministic scoring layer
for actual ``/query`` responses. The v0 harness is intentionally heuristic and
field-aware rather than LLM-judged. It exists to create a stable baseline that
can later be replaced or augmented by richer evaluators.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.contracts.answer_contract import AnswerContractV0, Segment
from src.contracts.evaluation_set import EvaluationQuestionV0, build_initial_evaluation_set


MAX_CRITERION_SCORE = 5.0


class CriterionScoreV0(BaseModel):
    """One scored rubric criterion for a query evaluation run."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1)
    score: float = Field(ge=0.0, le=MAX_CRITERION_SCORE)
    max_score: float = MAX_CRITERION_SCORE
    reasoning: str = Field(min_length=1)

    def to_dict(self) -> dict[str, Any]:
        """Return the criterion score as a plain dictionary."""
        return self.model_dump(mode="json")


class QueryEvaluationResultV0(BaseModel):
    """Scored result for a concrete query evaluated against one eval question."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    evaluation_set_version: str = "v0"
    question_id: str = Field(min_length=1)
    query: str = Field(min_length=1)
    answer: AnswerContractV0
    criterion_scores: list[CriterionScoreV0] = Field(min_length=1)
    total_score: float = Field(ge=0.0, le=MAX_CRITERION_SCORE)
    normalized_score: float = Field(ge=0.0, le=1.0)
    verdict: str = Field(min_length=1)
    missing_expectations: list[str] = Field(default_factory=list)
    run_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return the evaluation result as a plain dictionary."""
        return self.model_dump(mode="json")


class QueryEvaluationBatchResultV0(BaseModel):
    """Aggregate result for running the evaluation set against query responses."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    evaluation_set_version: str = "v0"
    result_count: int = Field(ge=1)
    average_total_score: float = Field(ge=0.0, le=MAX_CRITERION_SCORE)
    average_normalized_score: float = Field(ge=0.0, le=1.0)
    verdict_counts: dict[str, int]
    results: list[QueryEvaluationResultV0] = Field(min_length=1)
    run_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return the batch evaluation result as a plain dictionary."""
        return self.model_dump(mode="json")


class SegmentEvaluationComparisonV0(BaseModel):
    """Comparison of one query evaluated across multiple audience segments."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    question_id: str = Field(min_length=1)
    query: str = Field(min_length=1)
    result_count: int = Field(ge=1)
    average_normalized_score: float = Field(ge=0.0, le=1.0)
    verdict_counts: dict[str, int]
    compared_segments: list[Segment] = Field(min_length=1)
    best_segment: Segment | None = None
    score_spread: float = Field(ge=0.0, le=1.0)
    results: list[QueryEvaluationResultV0] = Field(min_length=1)
    run_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return the segment comparison payload as a plain dictionary."""
        return self.model_dump(mode="json")


class EvaluationPerformanceBreakdownV0(BaseModel):
    """Performance summary for one evaluation run type."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    run_type: str = Field(min_length=1)
    count: int = Field(ge=0)
    average_normalized_score: float = Field(ge=0.0, le=1.0)
    verdict_counts: dict[str, int] = Field(default_factory=dict)
    latest_run_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return the performance breakdown as a plain dictionary."""
        return self.model_dump(mode="json")


class EvaluationPerformanceSummaryV0(BaseModel):
    """Aggregate recent performance summary over persisted evaluation runs."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    total_runs: int = Field(ge=0)
    overall_average_normalized_score: float = Field(ge=0.0, le=1.0)
    trend_direction: str = Field(min_length=1)
    latest_run_at: datetime | None = None
    by_run_type: list[EvaluationPerformanceBreakdownV0] = Field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return the performance summary as a plain dictionary."""
        return self.model_dump(mode="json")


class StoredEvaluationRunV0(BaseModel):
    """Persisted evaluation run metadata and payload."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    run_id: str = Field(min_length=1)
    run_type: str = Field(min_length=1)
    query: str = ""
    question_id: str = ""
    average_normalized_score: float = Field(ge=0.0, le=1.0)
    verdict_summary: str = Field(min_length=1)
    created_at: datetime
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Return the stored run as a plain dictionary."""
        return self.model_dump(mode="json")


class EvaluationRunHistoryV0(BaseModel):
    """Collection of persisted evaluation runs."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    count: int = Field(ge=0)
    items: list[StoredEvaluationRunV0] = Field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return the history payload as a plain dictionary."""
        return self.model_dump(mode="json")


def get_evaluation_question(question_id: str) -> EvaluationQuestionV0:
    """Return a question from the initial evaluation set by ID."""
    evaluation_set = build_initial_evaluation_set()
    for question in evaluation_set.questions:
        if question.question_id == question_id:
            return question
    raise KeyError(question_id)


def _answer_text(answer: AnswerContractV0) -> str:
    """Build a lowercase text blob from the answer payload for simple matching."""
    overlay_summaries: list[str] = []
    if answer.enterprise_overlay is not None:
        overlay_summaries = [
            answer.enterprise_overlay.reasoning,
            " ".join(answer.enterprise_overlay.key_requirements),
            " ".join(answer.enterprise_overlay.future_alignment_hooks),
            " ".join(delta.adjustment_summary for delta in answer.enterprise_overlay.segment_deltas),
            " ".join(
                " ".join(delta.key_priorities) for delta in answer.enterprise_overlay.segment_deltas
            ),
        ]

    parts = [
        answer.summary,
        " ".join(answer.tradeoffs),
        " ".join(answer.watchlist),
        " ".join(answer.reusable_artifacts),
        " ".join(answer.next_actions),
        " ".join(str(key) for key in answer.recommendation.keys()),
        " ".join(str(value) for value in answer.recommendation.values()),
        " ".join(evidence.title for evidence in answer.evidence),
        " ".join(evidence.why_relevant for evidence in answer.evidence),
        answer.confidence.reasoning,
        *overlay_summaries,
    ]
    return " ".join(parts).lower()


def _score_scope_fit(question: EvaluationQuestionV0, answer: AnswerContractV0) -> CriterionScoreV0:
    """Score whether the answer stays aligned to the requested evaluation question."""
    score = 0.0
    matched_focus = 0
    answer_text = _answer_text(answer)

    if answer.question_type == question.question_type:
        score += 2.0
    if answer.segment == question.segment:
        score += 1.0
    if answer.persona == question.persona:
        score += 1.0
    if answer.time_horizon == question.time_horizon:
        score += 1.0

    for focus in question.scoring_focus:
        tokens = [token for token in focus.lower().replace("-", " ").split() if len(token) > 3]
        if tokens and any(token in answer_text for token in tokens):
            matched_focus += 1

    if matched_focus == 0 and question.scoring_focus:
        reasoning = "Metadata alignment was checked, but the answer text barely reflects the scoring focus."
    else:
        reasoning = (
            f"Metadata alignment is strong and {matched_focus} scoring-focus areas are reflected in the answer text."
        )

    return CriterionScoreV0(name="scope_fit", score=min(score, MAX_CRITERION_SCORE), reasoning=reasoning)


def _score_recommendation_specificity(
    question: EvaluationQuestionV0,
    answer: AnswerContractV0,
) -> tuple[CriterionScoreV0, list[str]]:
    """Score whether the answer makes concrete recommendations."""
    recommendation_keys = len(answer.recommendation)
    must_include_hits = []
    missing_expectations = []
    answer_text = _answer_text(answer)

    score = min(float(recommendation_keys), 3.0)
    if answer.summary:
        score += 1.0
    if answer.tradeoffs:
        score += 1.0

    for expectation in question.must_include:
        tokens = [token for token in expectation.lower().replace("-", " ").split() if len(token) > 3]
        if tokens and any(token in answer_text for token in tokens):
            must_include_hits.append(expectation)
        else:
            missing_expectations.append(expectation)

    score = min(score, MAX_CRITERION_SCORE)
    reasoning = (
        f"The answer includes {recommendation_keys} recommendation fields and satisfies "
        f"{len(must_include_hits)} of {len(question.must_include)} expected content signals."
    )
    return CriterionScoreV0(
        name="recommendation_specificity",
        score=score,
        reasoning=reasoning,
    ), missing_expectations


def _score_evidence_and_provenance(answer: AnswerContractV0) -> CriterionScoreV0:
    """Score evidence quality and provenance completeness."""
    score = 0.0
    evidence_count = len(answer.evidence)
    provenance_count = sum(1 for record in answer.evidence if record.source_name or record.source_url)

    if answer.confidence.reasoning:
        score += 1.0
    if answer.confidence.gaps:
        score += 1.0
    if answer.freshness.sensitive_to_change is not None:
        score += 1.0
    if evidence_count:
        score += 1.0
    if provenance_count:
        score += 1.0

    reasoning = (
        f"The answer includes {evidence_count} evidence records and {provenance_count} records with explicit provenance."
    )
    return CriterionScoreV0(
        name="evidence_and_provenance",
        score=min(score, MAX_CRITERION_SCORE),
        reasoning=reasoning,
    )


def _score_enterprise_overlay(answer: AnswerContractV0) -> CriterionScoreV0:
    """Score whether the answer explains enterprise fit and segment adjustments."""
    overlay = answer.enterprise_overlay
    if overlay is None:
        return CriterionScoreV0(
            name="enterprise_overlay",
            score=0.0,
            reasoning="The answer does not include an enterprise overlay.",
        )

    score = 1.0
    if overlay.reasoning:
        score += 1.0
    if overlay.key_requirements:
        score += 1.0
    if overlay.future_alignment_hooks:
        score += 1.0
    if overlay.segment_deltas:
        score += 1.0

    segment_names = {delta.segment for delta in overlay.segment_deltas}
    if Segment.ENTERPRISE in segment_names:
        score = min(score + 0.5, MAX_CRITERION_SCORE)

    reasoning = (
        f"The answer marks enterprise_safe_now={overlay.enterprise_safe_now} and provides "
        f"{len(overlay.segment_deltas)} segment adjustments."
    )
    return CriterionScoreV0(
        name="enterprise_overlay",
        score=min(score, MAX_CRITERION_SCORE),
        reasoning=reasoning,
    )


def _score_actionability(answer: AnswerContractV0) -> CriterionScoreV0:
    """Score whether the answer leaves the caller with actionable output."""
    score = 0.0
    if answer.tradeoffs:
        score += 1.5
    if answer.watchlist:
        score += 1.5
    if answer.next_actions:
        score += 1.5
    if answer.reusable_artifacts:
        score += 0.5

    reasoning = (
        f"The answer includes {len(answer.tradeoffs)} tradeoffs, {len(answer.watchlist)} watchlist items, "
        f"and {len(answer.next_actions)} next actions."
    )
    return CriterionScoreV0(
        name="actionability",
        score=min(score, MAX_CRITERION_SCORE),
        reasoning=reasoning,
    )


def evaluate_query_response(
    query: str,
    question: EvaluationQuestionV0,
    answer: AnswerContractV0,
) -> QueryEvaluationResultV0:
    """Score a concrete answer payload against one evaluation question."""
    scope_fit = _score_scope_fit(question, answer)
    recommendation_specificity, missing_expectations = _score_recommendation_specificity(
        question,
        answer,
    )
    enterprise_overlay = _score_enterprise_overlay(answer)
    evidence_and_provenance = _score_evidence_and_provenance(answer)
    actionability = _score_actionability(answer)

    criterion_scores = [
        scope_fit,
        recommendation_specificity,
        enterprise_overlay,
        evidence_and_provenance,
        actionability,
    ]
    weighted_total = 0.0
    for criterion in criterion_scores:
        weight = next(
            rubric_item.weight for rubric_item in question.rubric if rubric_item.name == criterion.name
        )
        weighted_total += (criterion.score / MAX_CRITERION_SCORE) * weight * MAX_CRITERION_SCORE

    has_supporting_evidence = bool(answer.evidence)
    low_confidence = answer.confidence.score < 0.5

    normalized_score = weighted_total / MAX_CRITERION_SCORE
    if not has_supporting_evidence and low_confidence:
        normalized_score = min(normalized_score, 0.49)
    elif not has_supporting_evidence or low_confidence:
        normalized_score = min(normalized_score, 0.74)

    normalized_score = round(normalized_score, 4)
    total_score = round(normalized_score * MAX_CRITERION_SCORE, 2)

    if not has_supporting_evidence and low_confidence:
        verdict = "weak"
    elif normalized_score >= 0.8 and has_supporting_evidence:
        verdict = "strong"
    elif normalized_score >= 0.55:
        verdict = "partial"
    else:
        verdict = "weak"

    return QueryEvaluationResultV0(
        question_id=question.question_id,
        query=query,
        answer=answer,
        criterion_scores=criterion_scores,
        total_score=total_score,
        normalized_score=normalized_score,
        verdict=verdict,
        missing_expectations=missing_expectations,
    )


def summarize_query_evaluations(
    results: list[QueryEvaluationResultV0],
) -> QueryEvaluationBatchResultV0:
    """Aggregate multiple query evaluation results into one scorecard."""
    verdict_counts: dict[str, int] = {"strong": 0, "partial": 0, "weak": 0}
    for result in results:
        verdict_counts[result.verdict] = verdict_counts.get(result.verdict, 0) + 1

    count = len(results)
    average_total_score = round(sum(result.total_score for result in results) / count, 2)
    average_normalized_score = round(
        sum(result.normalized_score for result in results) / count,
        4,
    )

    return QueryEvaluationBatchResultV0(
        result_count=count,
        average_total_score=average_total_score,
        average_normalized_score=average_normalized_score,
        verdict_counts=verdict_counts,
        results=results,
    )


def summarize_segment_evaluations(
    question_id: str,
    query: str,
    results: list[QueryEvaluationResultV0],
) -> SegmentEvaluationComparisonV0:
    """Aggregate the same query evaluated across multiple segments."""
    verdict_counts: dict[str, int] = {"strong": 0, "partial": 0, "weak": 0}
    for result in results:
        verdict_counts[result.verdict] = verdict_counts.get(result.verdict, 0) + 1

    best_result = max(results, key=lambda result: result.normalized_score)
    scores = [result.normalized_score for result in results]
    return SegmentEvaluationComparisonV0(
        question_id=question_id,
        query=query,
        result_count=len(results),
        average_normalized_score=round(sum(scores) / len(scores), 4),
        verdict_counts=verdict_counts,
        compared_segments=[result.answer.segment for result in results],
        best_segment=best_result.answer.segment,
        score_spread=round(max(scores) - min(scores), 4),
        results=results,
    )