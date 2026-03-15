"""Unit tests for the initial answer-contract evaluation set."""

from pydantic import ValidationError
import pytest

from src.contracts import EvaluationSetV0, build_initial_evaluation_set
from src.contracts.evaluation_set import EvaluationQuestionV0, RubricCriterion


class TestEvaluationSetV0:
    def test_builder_returns_six_canonical_questions(self):
        evaluation_set = build_initial_evaluation_set()

        assert evaluation_set.evaluation_set_version == "v0"
        assert evaluation_set.contract_version == "v0"
        assert len(evaluation_set.questions) == 6
        assert evaluation_set.questions[0].question_id == "arch-slo-enterprise"

    def test_builder_covers_multiple_question_types(self):
        evaluation_set = build_initial_evaluation_set()

        question_types = {question.question_type for question in evaluation_set.questions}
        assert question_types == {
            "architecture_recommendation",
            "stack_recommendation",
            "change_watch",
        }

    def test_each_question_uses_normalized_rubric_weights(self):
        evaluation_set = build_initial_evaluation_set()

        for question in evaluation_set.questions:
            total_weight = sum(item.weight for item in question.rubric)
            assert total_weight == pytest.approx(1.0)

    def test_rejects_duplicate_question_ids(self):
        question = EvaluationQuestionV0(
            question_id="duplicate-id",
            prompt="Test prompt",
            question_type="stack_recommendation",
            segment="enterprise",
            persona="architect",
            time_horizon="now",
            rubric=[
                RubricCriterion(name="fit", description="fit", weight=1.0),
            ],
        )

        with pytest.raises(ValidationError):
            EvaluationSetV0(
                title="Invalid set",
                summary="Should fail because IDs repeat.",
                scoring_scale="0-5",
                questions=[question, question],
            )

    def test_rejects_rubric_weights_that_do_not_sum_to_one(self):
        with pytest.raises(ValidationError):
            EvaluationQuestionV0(
                question_id="bad-rubric",
                prompt="Bad rubric prompt",
                question_type="architecture_recommendation",
                segment="enterprise",
                persona="architect",
                time_horizon="now",
                rubric=[
                    RubricCriterion(name="fit", description="fit", weight=0.7),
                    RubricCriterion(name="evidence", description="evidence", weight=0.2),
                ],
            )