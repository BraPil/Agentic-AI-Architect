"""
MCP tools for the learning loop — human-gated promotion of agent-generated
artifacts from the quarantined `experimental` tier to the trusted `grounded` tier.

This is the primary approval surface (MCP-first, matching AAA's interaction model):
Claude shows the human the candidate, its provenance and confidence, and the human
approves in natural language. The same PromotionGate also backs the CLI
(scripts/promote_learnings.py).

Tools registered:
    list_promotion_candidates    — experimental artifacts awaiting review
    promote_artifact             — experimental → grounded (confidence-gated)
    reject_artifact              — remove an experimental artifact
    demote_artifact              — grounded → experimental (undo a promotion)
    record_recommendation_outcome — P6: log whether a recommendation was adopted + worked
    get_outcome_summary          — P6: aggregate the learned outcome signal
"""

import json
import logging

logger = logging.getLogger(__name__)

_SCHEMA_VERSION = "1.0"


def _gate():
    """Build a PromotionGate over the live ChromaDB collection."""
    from src.api.mcp_server import _get_store  # noqa: PLC0415
    from src.learning.promotion import PromotionGate  # noqa: PLC0415
    return PromotionGate(_get_store()._collection)


def _outcome_store():
    """Build a RecommendationOutcomeStore over the shared outcome ledger."""
    from src.api.mcp_server import _OUTCOME_LEDGER  # noqa: PLC0415
    from src.learning.outcomes import RecommendationOutcomeStore  # noqa: PLC0415
    return RecommendationOutcomeStore(_OUTCOME_LEDGER)


def register_learning_tools(mcp) -> None:
    """Register the four learning-loop promotion tools on the MCP server."""

    @mcp.tool()
    def list_promotion_candidates(min_confidence: float = 0.0) -> str:
        """List agent-generated artifacts awaiting human review for promotion.

        These are `experimental`-tier artifacts produced by the Organic Agentic
        AutoDev learning loop. They are quarantined: not surfaced as fact, not
        counted in trends, until a human promotes them.

        Args:
            min_confidence: Only show artifacts with at least this confidence (0-1).

        Returns:
            JSON list of candidates with id, title, confidence, author, topics, snippet.
        """
        gate = _gate()
        candidates = gate.list_candidates(min_confidence=min_confidence)
        payload = {
            "schema_version": _SCHEMA_VERSION,
            "total_candidates": len(candidates),
            "min_confidence": min_confidence,
            "candidates": [c.to_dict() for c in candidates],
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)

    @mcp.tool()
    def promote_artifact(artifact_id: str, approved_by: str = "brandt") -> str:
        """Promote an experimental artifact to the trusted `grounded` tier.

        Requires the artifact's confidence to meet the gate threshold. Promotion
        is recorded in an audit log and is reversible via demote_artifact.

        Args:
            artifact_id: The artifact ID (from list_promotion_candidates).
            approved_by: Who approved this promotion (for the audit trail).

        Returns:
            JSON result with ok, from_tier, to_tier, confidence, reason.
        """
        result = _gate().promote(artifact_id, approved_by)
        return json.dumps({"schema_version": _SCHEMA_VERSION, **result.to_dict()},
                          indent=2, ensure_ascii=False)

    @mcp.tool()
    def reject_artifact(artifact_id: str, reason: str = "", rejected_by: str = "brandt") -> str:
        """Reject and remove an experimental artifact from the knowledge base.

        Args:
            artifact_id: The artifact ID to reject.
            reason: Why it was rejected (for the audit trail).
            rejected_by: Who rejected it.

        Returns:
            JSON result with ok and reason.
        """
        result = _gate().reject(artifact_id, rejected_by, reason)
        return json.dumps({"schema_version": _SCHEMA_VERSION, **result.to_dict()},
                          indent=2, ensure_ascii=False)

    @mcp.tool()
    def demote_artifact(artifact_id: str, reason: str = "", demoted_by: str = "brandt") -> str:
        """Reverse a promotion: move a grounded artifact back to experimental.

        Args:
            artifact_id: The artifact ID to demote.
            reason: Why it was demoted (for the audit trail).
            demoted_by: Who demoted it.

        Returns:
            JSON result with ok, from_tier, to_tier, reason.
        """
        result = _gate().demote(artifact_id, demoted_by, reason)
        return json.dumps({"schema_version": _SCHEMA_VERSION, **result.to_dict()},
                          indent=2, ensure_ascii=False)

    @mcp.tool()
    def record_recommendation_outcome(
        recommendation_id: str,
        adopted: bool,
        worked: bool = False,
        outcome_score: float = -1.0,
        notes: str = "",
        recorded_by: str = "brandt",
    ) -> str:
        """Tell AAA what actually happened with a past architecture recommendation.

        This closes the P6 learning loop: AAA can only learn from outcomes if you
        report them. The `recommendation_id` is returned by
        get_architecture_recommendation.

        Args:
            recommendation_id: The id from the recommendation you're grading.
            adopted: Did you actually follow the recommendation?
            worked: If adopted, did it work out? (ignored when not adopted)
            outcome_score: Optional 0–1 quality rating; pass a negative value to omit.
            notes: Free-text context (what shipped, what broke, why).
            recorded_by: Who is recording this outcome.

        Returns:
            JSON with the merged outcome record, or an error if the id is unknown.
        """
        score = None if outcome_score is None or outcome_score < 0 else outcome_score
        try:
            record = _outcome_store().record_outcome(
                recommendation_id, adopted=adopted, worked=worked,
                outcome_score=score, notes=notes, recorded_by=recorded_by,
            )
        except ValueError as exc:
            return json.dumps({"schema_version": _SCHEMA_VERSION, "ok": False,
                               "error": str(exc)}, indent=2)
        return json.dumps({"schema_version": _SCHEMA_VERSION, "ok": True,
                           **record.to_dict()}, indent=2, ensure_ascii=False)

    @mcp.tool()
    def get_outcome_summary() -> str:
        """Summarize what AAA has learned from recommendation outcomes so far.

        Returns overall adoption/success rates plus a per-persona and per-tool
        success signal (with smoothed weight multipliers a future ranking pass can
        apply). Also lists how many recommendations still await an outcome.

        Returns:
            JSON aggregate: adoption_rate, success_rate, mean_outcome_score,
            persona_signal, tool_signal, pending_outcomes.
        """
        agg = _outcome_store().aggregate()
        return json.dumps({"schema_version": _SCHEMA_VERSION, **agg},
                          indent=2, ensure_ascii=False)
