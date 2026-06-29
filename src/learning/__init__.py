"""
AAA learning loop — the regulated bridge between Organic Agentic AutoDev (OAA)
and AAA's knowledge base.

OAA runs as its own process (a living MoltBook of bio-mimicry agents) and emits
KnowledgeRecordV0 artifacts. AAA observes those artifacts (harvester), quarantines
them in an `experimental` provenance tier, and only promotes them to `grounded`
through a human-gated PromotionGate. This closes the P6 learning loop without
letting agent-generated content echo back into the trusted corpus unchecked.

Provenance tiers (see docs/aaa-organic-learning-loop-v0.md):
    external      — thought-leader content (authority)
    internal      — AAA's own human-written decisions/lessons (institutional memory)
    experimental  — agent-GENERATED artifacts, quarantined (never surfaced as fact)
    grounded      — agent artifacts promoted by a human (trusted, but not external authority)
"""

from src.learning.outcomes import (
    OutcomeRecord,
    RecommendationOutcomeStore,
    compute_recommendation_id,
)
from src.learning.promotion import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    PromotionGate,
    PromotionResult,
    TIER_EXPERIMENTAL,
    TIER_GROUNDED,
)

__all__ = [
    "PromotionGate",
    "PromotionResult",
    "DEFAULT_CONFIDENCE_THRESHOLD",
    "TIER_EXPERIMENTAL",
    "TIER_GROUNDED",
    "RecommendationOutcomeStore",
    "OutcomeRecord",
    "compute_recommendation_id",
]
