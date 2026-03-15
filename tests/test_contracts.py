"""Unit tests for the external answer contract models."""

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from src.contracts.answer_contract import (
    AnswerContractV0,
    AnswerRequestContext,
    CallerType,
    ConfidenceAssessment,
    EnterpriseOverlayV0,
    EvidenceRecord,
    EvidenceTier,
    FreshnessMetadata,
    Persona,
    QuestionType,
    ResponseMode,
    Segment,
    SegmentDeltaV0,
    TimeHorizon,
)
from src.contracts.mouseion import (
    AgentAvailability,
    AgentProfileV0,
    EvaluationV0,
    EventEnvelopeV0,
    FeedbackV0,
    KnowledgeRecordV0,
    ReviewState,
    TaskRequestV0,
    TaskResultV0,
)


def _make_contract(**overrides) -> AnswerContractV0:
    generated_at = datetime(2026, 3, 8, 12, 0, tzinfo=UTC)
    defaults = {
        "question_type": QuestionType.STACK_RECOMMENDATION,
        "segment": Segment.ENTERPRISE,
        "persona": Persona.ARCHITECT,
        "time_horizon": TimeHorizon.NOW,
        "summary": "Use a typed contract and keep machine-readable JSON canonical.",
        "recommendation": {
            "orchestrator": "LangGraph",
            "api_surface": "FastAPI",
        },
        "enterprise_overlay": EnterpriseOverlayV0(
            enterprise_safe_now=True,
            reasoning="Typed contracts and evidence retention make the baseline enterprise-safe enough to recommend now.",
            key_requirements=["audit trails", "typed contracts"],
            future_alignment_hooks=["preserve provenance"],
            segment_deltas=[
                SegmentDeltaV0(
                    segment=Segment.ENTERPRISE,
                    adjustment_summary="Keep stronger auditability and change control.",
                    key_priorities=["audit trails", "change review"],
                )
            ],
        ),
        "tradeoffs": ["Temporal may still be preferable for durability-heavy workflows."],
        "evidence": [
            EvidenceRecord(
                source_id="public_source_1",
                title="Architecture recommendation review",
                source_type="public_article",
                evidence_tier=EvidenceTier.DIRECT,
                freshness="2026-03",
                why_relevant="Directly discusses current architecture recommendation tradeoffs.",
            )
        ],
        "confidence": ConfidenceAssessment(
            score=0.72,
            reasoning="The recommendation matches current repo direction and evidence quality.",
            gaps=["More enterprise-specific evidence is still needed."],
        ),
        "watchlist": ["dynamic tool discovery"],
        "reusable_artifacts": ["response schema DTOs"],
        "next_actions": ["Create the first scored evaluation set."],
        "freshness": FreshnessMetadata(
            generated_at=generated_at,
            best_before=generated_at + timedelta(days=28),
            sensitive_to_change=True,
        ),
    }
    defaults.update(overrides)
    return AnswerContractV0(**defaults)


class TestAnswerRequestContext:
    def test_defaults_to_agent_json_mode(self):
        context = AnswerRequestContext()

        assert context.caller_type == CallerType.AGENT
        assert context.response_mode == ResponseMode.JSON
        assert context.segment == Segment.CROSS_SEGMENT

    def test_to_dict_serializes_enum_values(self):
        context = AnswerRequestContext(
            caller_type=CallerType.HUMAN,
            response_mode=ResponseMode.BOTH,
            segment=Segment.ENTERPRISE,
        )

        assert context.to_dict() == {
            "caller_type": "human",
            "response_mode": "both",
            "detail_level": "standard",
            "segment": "enterprise",
            "persona": "architect",
            "time_horizon": "now",
        }


class TestFreshnessMetadata:
    def test_rejects_best_before_earlier_than_generated_at(self):
        generated_at = datetime(2026, 3, 8, 12, 0, tzinfo=UTC)

        with pytest.raises(ValidationError):
            FreshnessMetadata(
                generated_at=generated_at,
                best_before=generated_at - timedelta(days=1),
                sensitive_to_change=True,
            )


class TestConfidenceAssessment:
    def test_rejects_score_outside_range(self):
        with pytest.raises(ValidationError):
            ConfidenceAssessment(score=1.1, reasoning="Too high.", gaps=[])


class TestAnswerContractV0:
    def test_to_dict_contains_json_compatible_values(self):
        contract = _make_contract()

        payload = contract.to_dict()

        assert payload["contract_version"] == "v0"
        assert payload["question_type"] == "stack_recommendation"
        assert payload["segment"] == "enterprise"
        assert payload["enterprise_overlay"]["enterprise_safe_now"] is True
        assert payload["confidence"]["score"] == 0.72
        assert payload["evidence"][0]["evidence_tier"] == "direct"
        assert payload["evidence"][0]["source_name"] is None
        assert payload["freshness"]["generated_at"].startswith("2026-03-08T12:00:00")

    def test_to_response_payload_adds_human_render_when_requested(self):
        contract = _make_contract()

        payload = contract.to_response_payload(ResponseMode.BOTH)

        assert payload["rendered_response"] is not None
        assert "Recommendation:" in payload["rendered_response"]
        assert "Enterprise overlay:" in payload["rendered_response"]
        assert "Watchlist:" in payload["rendered_response"]

    def test_to_response_payload_keeps_json_mode_canonical(self):
        contract = _make_contract(rendered_response="stale")

        payload = contract.to_response_payload(ResponseMode.JSON)

        assert payload["rendered_response"] is None

    def test_rejects_unknown_contract_version(self):
        with pytest.raises(ValidationError):
            _make_contract(contract_version="v1")

    def test_strips_empty_list_items(self):
        contract = _make_contract(
            tradeoffs=["  keep wrappers stable  ", "  "],
            watchlist=[" near-term shifts ", ""],
            next_actions=[" add evals ", "   "],
        )

        assert contract.tradeoffs == ["keep wrappers stable"]
        assert contract.watchlist == ["near-term shifts"]
        assert contract.next_actions == ["add evals"]


class TestMouseionContracts:
    def test_event_envelope_serializes(self):
        envelope = EventEnvelopeV0(
            event_id="evt-1",
            event_type="task.requested",
            producer="agentic-ai-architect",
            occurred_at=datetime(2026, 3, 15, 12, 0, tzinfo=UTC),
            subject_id="task-1",
            payload={"task_type": "research"},
        )

        assert envelope.to_dict()["schema_version"] == "mouseion-core-v0"
        assert envelope.to_dict()["event_type"] == "task.requested"

    def test_agent_profile_requires_capabilities_and_namespaces(self):
        profile = AgentProfileV0(
            identity="router-agent",
            capabilities=["routing", "matching"],
            availability=AgentAvailability.AVAILABLE,
            trust_score=0.87,
            permitted_namespaces=["general", "research"],
        )

        payload = profile.to_dict()
        assert payload["identity"] == "router-agent"
        assert payload["trust_score"] == 0.87

    def test_task_request_and_result_validate(self):
        request = TaskRequestV0(
            task_id="task-1",
            task_type="hypothesis_generation",
            requester_id="opportunity-scout",
            requested_capability="hypothesis_generation",
            context_refs=["opp-17"],
            success_criteria=["produce 3 hypotheses"],
            namespace="general",
        )
        result = TaskResultV0(
            task_id="task-1",
            producer_id="hypothesis-agent",
            result_type="hypothesis_batch",
            summary="Produced 3 candidate hypotheses.",
            artifacts=["artifact-1"],
            confidence_score=0.74,
            confidence_basis="retrieved_evidence",
            provenance_refs=["source-1"],
            review_state=ReviewState.UNDER_EVALUATION,
        )

        assert request.to_dict()["requested_capability"] == "hypothesis_generation"
        assert result.to_dict()["review_state"] == "under_evaluation"

    def test_evaluation_and_feedback_validate(self):
        evaluation = EvaluationV0(
            target_id="artifact-1",
            evaluator_id="evaluator-agent",
            evaluation_type="artifact_quality",
            criteria_scores=[
                {
                    "name": "utility",
                    "score": 0.8,
                    "rationale": "Useful for the target task.",
                }
            ],
            overall_score=0.8,
            expected_outcome_summary="Strong initial draft.",
            actual_outcome_summary="Mostly strong with one unsupported claim.",
            pass_fail=True,
            refinement_allowed=True,
            feedback_summary="Tighten evidence support for one section.",
            provenance_refs=["source-1"],
        )
        feedback = FeedbackV0(
            feedback_id="fb-1",
            target_id="artifact-1",
            issuer_id="evaluator-agent",
            summary="Add evidence support for the final claim.",
            requested_changes=["cite supporting source"],
            refinement_round=1,
        )

        assert evaluation.to_dict()["criteria_scores"][0]["name"] == "utility"
        assert feedback.to_dict()["review_state"] == "needs_refinement"

    def test_knowledge_record_rejects_invalid_timestamp_order(self):
        created_at = datetime(2026, 3, 15, 12, 0, tzinfo=UTC)

        with pytest.raises(ValidationError):
            KnowledgeRecordV0(
                record_id="kr-1",
                record_type="shell_feedback",
                producer="agentic-ai-architect",
                created_at=created_at,
                updated_at=created_at - timedelta(days=1),
                confidence_basis="human_review",
            )

    def test_knowledge_record_serializes_review_state(self):
        record = KnowledgeRecordV0(
            record_id="kr-1",
            record_type="shell_feedback",
            producer="agentic-ai-architect",
            created_at=datetime(2026, 3, 15, 12, 0, tzinfo=UTC),
            confidence_basis="human_review",
            provenance_refs=["eval-run-1"],
            evaluation_history=["eval-1"],
            review_state=ReviewState.ACCEPTED,
        )

        payload = record.to_dict()
        assert payload["review_state"] == "accepted"
        assert payload["schema_version"] == "mouseion-core-v0"
