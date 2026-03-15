"""Unit tests for the executable query evaluation harness."""

from datetime import UTC, datetime, timedelta

from src.contracts.answer_contract import (
    AnswerContractV0,
    ConfidenceAssessment,
    EnterpriseOverlayV0,
    EvidenceRecord,
    EvidenceTier,
    FreshnessMetadata,
    Persona,
    QuestionType,
    Segment,
    SegmentDeltaV0,
    TimeHorizon,
)
from src.contracts.evaluation_harness import evaluate_query_response, get_evaluation_question
from src.contracts.evaluation_harness import summarize_query_evaluations


def _make_answer(with_evidence: bool) -> AnswerContractV0:
    generated_at = datetime(2026, 3, 14, 12, 0, tzinfo=UTC)
    evidence = []
    if with_evidence:
        evidence = [
            EvidenceRecord(
                source_id="entry-1",
                title="LangGraph for durable workflows",
                source_type="article",
                evidence_tier=EvidenceTier.INFERRED,
                freshness="2026-03-14",
                why_relevant="Matched durable workflow guidance.",
                source_name="Test Source",
                source_url="https://example.com/langgraph",
            )
        ]

    return AnswerContractV0(
        question_type=QuestionType.STACK_RECOMMENDATION,
        segment=Segment.ENTERPRISE,
        persona=Persona.ARCHITECT,
        time_horizon=TimeHorizon.NOW,
        summary="Use LangGraph, PostgreSQL, pgvector, and FastAPI as the current baseline.",
        recommendation={
            "orchestrator": "LangGraph",
            "structured_store": "PostgreSQL",
            "vector_store": "pgvector",
            "api_surface": "FastAPI",
        },
        enterprise_overlay=EnterpriseOverlayV0(
            enterprise_safe_now=with_evidence,
            reasoning="Enterprise use is supported by typed contracts, provenance, and evaluation reporting.",
            key_requirements=["audit-friendly logs", "typed contracts"],
            future_alignment_hooks=["preserve provenance", "retain evaluation history"],
            segment_deltas=[
                SegmentDeltaV0(
                    segment=Segment.ENTERPRISE,
                    adjustment_summary="Use stricter auditability and change review than startup deployments.",
                    key_priorities=["audit trails", "change review"],
                )
            ],
        ),
        tradeoffs=["Temporal may still be preferable for longer-running durable workflows."],
        evidence=evidence,
        confidence=ConfidenceAssessment(
            score=0.78 if with_evidence else 0.25,
            reasoning="Confidence reflects stored evidence coverage.",
            gaps=[] if with_evidence else ["No matching evidence was found."],
        ),
        watchlist=["near-term stack shifts"],
        reusable_artifacts=["response schema DTOs"],
        next_actions=["Inspect the top matched entries."],
        freshness=FreshnessMetadata(
            generated_at=generated_at,
            best_before=generated_at + timedelta(days=7),
            sensitive_to_change=True,
        ),
    )


class TestEvaluationHarness:
    def test_get_evaluation_question_returns_known_question(self):
        question = get_evaluation_question("stack-current-enterprise")

        assert question.question_type == "stack_recommendation"
        assert question.segment == "enterprise"

    def test_evaluate_query_response_scores_evidence_richer_answer_higher(self):
        question = get_evaluation_question("stack-current-enterprise")
        rich_answer = _make_answer(with_evidence=True)
        weak_answer = _make_answer(with_evidence=False)

        rich_result = evaluate_query_response(
            query="LangGraph",
            question=question,
            answer=rich_answer,
        )
        weak_result = evaluate_query_response(
            query="nonexistent topic",
            question=question,
            answer=weak_answer,
        )

        assert rich_result.normalized_score > weak_result.normalized_score
        assert rich_result.verdict in {"strong", "partial"}
        assert weak_result.verdict in {"partial", "weak"}
        assert any(score.name == "enterprise_overlay" for score in rich_result.criterion_scores)

    def test_summarize_query_evaluations_aggregates_results(self):
        question = get_evaluation_question("stack-current-enterprise")
        result = evaluate_query_response(
            query="LangGraph",
            question=question,
            answer=_make_answer(with_evidence=True),
        )

        summary = summarize_query_evaluations([result, result])

        assert summary.result_count == 2
        assert summary.verdict_counts[result.verdict] == 2