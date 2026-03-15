"""FastAPI REST endpoints for the first queryable API surface.

This module keeps API concerns separate from the orchestrator. It exposes a
small v0 surface that reuses existing orchestrator query methods and wraps
knowledge-base search results in the canonical answer contract.
"""

import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
from typing import Any

from fastapi import FastAPI, HTTPException, Query

from src.agents.orchestrator import Orchestrator
from src.contracts.answer_contract import (
    AnswerContractV0,
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
from src.contracts.evaluation_set import EvaluationSetV0, build_initial_evaluation_set
from src.contracts.evaluation_harness import (
    EvaluationRunHistoryV0,
    EvaluationPerformanceBreakdownV0,
    EvaluationPerformanceSummaryV0,
    QueryEvaluationBatchResultV0,
    QueryEvaluationResultV0,
    SegmentEvaluationComparisonV0,
    StoredEvaluationRunV0,
    evaluate_query_response,
    get_evaluation_question,
    summarize_segment_evaluations,
    summarize_query_evaluations,
)
from src.knowledge.knowledge_base import (
    EvaluationRunRecord,
    KnowledgeBase,
    KnowledgeEntry,
    LearnedWeightProfile,
)

DEFAULT_BEST_BEFORE_DAYS = 7
DEFAULT_QUERY_LIMIT = 5
MAX_QUERY_LIMIT = 20
DOCS_DIR = Path(__file__).resolve().parents[2] / "docs"
PHASE_REPORTS: dict[str, str] = {
    "1": "phase-1-education.md",
    "phase-1": "phase-1-education.md",
    "education": "phase-1-education.md",
    "2": "phase-2-conceptual-frameworks.md",
    "phase-2": "phase-2-conceptual-frameworks.md",
    "frameworks": "phase-2-conceptual-frameworks.md",
    "3": "phase-3-trends.md",
    "phase-3": "phase-3-trends.md",
    "trends": "phase-3-trends.md",
    "4": "phase-4-tools.md",
    "phase-4": "phase-4-tools.md",
    "tools": "phase-4-tools.md",
    "5": "phase-5-implementation-plan.md",
    "phase-5": "phase-5-implementation-plan.md",
    "implementation": "phase-5-implementation-plan.md",
    "implementation-plan": "phase-5-implementation-plan.md",
}
FALLBACK_TOOL_LIMIT = 25
FALLBACK_TREND_LIMIT = 25
SOURCE_WEIGHTING_MODEL_VERSION = "v2"
RETRIEVAL_SOURCE_WEIGHTS: dict[str, float] = {
    "knowledge_base": 1.0,
    "trend_registry": 0.95,
    "framework_matrix": 0.9,
    "tool_registry": 0.85,
}
EVIDENCE_TIER_WEIGHTS: dict[EvidenceTier, float] = {
    EvidenceTier.DIRECT: 1.0,
    EvidenceTier.PUBLIC_COMPANION: 0.85,
    EvidenceTier.USER_PROVIDED: 0.8,
    EvidenceTier.INFERRED: 0.65,
}
FRESHNESS_FLOORS: dict[TimeHorizon, float] = {
    TimeHorizon.NOW: 0.7,
    TimeHorizon.FOUR_WEEKS: 0.78,
    TimeHorizon.QUARTER: 0.85,
}
FRESHNESS_HALF_LIFE_DAYS: dict[TimeHorizon, int] = {
    TimeHorizon.NOW: 30,
    TimeHorizon.FOUR_WEEKS: 60,
    TimeHorizon.QUARTER: 120,
}


def _read_doc(doc_name: str) -> str:
    """Read a markdown document from the repository docs directory."""
    return (DOCS_DIR / doc_name).read_text(encoding="utf-8")


def _extract_title(markdown: str) -> str:
    """Return the first markdown heading or a fallback title."""
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return "Untitled document"


def _parse_markdown_table(markdown: str, heading: str) -> list[dict[str, str]]:
    """Parse a markdown table directly under the requested heading."""
    lines = markdown.splitlines()
    in_section = False
    header: list[str] | None = None
    rows: list[dict[str, str]] = []

    for line in lines:
        if line.strip() == heading:
            in_section = True
            continue

        if in_section and line.startswith("## ") and line.strip() != heading:
            break

        if not in_section:
            continue

        stripped = line.strip()
        if not stripped.startswith("|"):
            if header and rows:
                break
            continue

        cells = [cell.strip() for cell in stripped.strip("|").split("|")]

        if header is None:
            header = cells
            continue

        if all(set(cell) <= {"-", ":"} for cell in cells):
            continue

        if len(cells) != len(header):
            continue

        rows.append(dict(zip(header, cells, strict=True)))

    return rows


def _get_framework_matrix() -> list[dict[str, str]]:
    """Return the framework maturity matrix from the phase-2 document."""
    markdown = _read_doc("phase-2-conceptual-frameworks.md")
    return _parse_markdown_table(markdown, "## 2.11 Framework Maturity Matrix")


def _filter_frameworks(
    frameworks: list[dict[str, str]],
    search: str | None,
    trajectory: str | None,
    status_2024: str | None,
) -> list[dict[str, str]]:
    """Filter framework rows using lightweight server-side predicates."""
    filtered = frameworks

    if search:
        needle = search.strip().lower()
        filtered = [
            row for row in filtered
            if needle in " ".join(row.values()).lower()
        ]

    if trajectory:
        expected = trajectory.strip().lower()
        filtered = [
            row for row in filtered
            if expected in row.get("2026 Trajectory", "").lower()
        ]

    if status_2024:
        expected = status_2024.strip().lower()
        filtered = [
            row for row in filtered
            if expected in row.get("2024 Status", "").lower()
        ]

    return filtered


def _get_phase_report(phase: str) -> dict[str, str]:
    """Return markdown report content for a supported phase alias."""
    key = phase.strip().lower()
    if key not in PHASE_REPORTS:
        raise KeyError(phase)

    doc_name = PHASE_REPORTS[key]
    markdown = _read_doc(doc_name)
    return {
        "phase": key,
        "source_path": f"docs/{doc_name}",
        "title": _extract_title(markdown),
        "format": "markdown",
        "content": markdown,
    }


def _entry_to_evidence(entry: KnowledgeEntry, query: str) -> EvidenceRecord:
    """Convert a stored knowledge entry into a conservative evidence record."""
    source_type = entry.content_type or "knowledge_entry"
    freshness = entry.updated_at.date().isoformat()
    title = entry.title or "Untitled entry"
    evidence_tier = _resolve_evidence_tier(entry)
    retrieval_source = entry.metadata.get("retrieval_source", "knowledge_base")
    why_relevant = f"Matched stored knowledge for query '{query}' in namespace '{entry.namespace}'."
    if retrieval_source == "trend_registry":
        why_relevant = (
            f"Represents a currently tracked trend signal relevant to change detection for '{query}'."
        )
    elif retrieval_source == "tool_registry":
        why_relevant = (
            f"Represents a current tool-registry match relevant to implementation choices for '{query}'."
        )
    elif retrieval_source == "framework_matrix":
        why_relevant = (
            f"Represents a documented framework trajectory signal relevant to '{query}'."
        )
    return EvidenceRecord(
        source_id=entry.entry_id,
        title=title,
        source_type=source_type,
        evidence_tier=evidence_tier,
        freshness=freshness,
        why_relevant=why_relevant,
        source_name=entry.source_name or None,
        source_url=entry.source_url or entry.metadata.get("source_path") or None,
    )


def _normalize_text(value: str) -> str:
    """Normalize text for lightweight keyword scoring."""
    return re.sub(r"\s+", " ", value.strip().lower())


def _resolve_evidence_tier(entry: KnowledgeEntry) -> EvidenceTier:
    """Resolve an evidence tier, treating stored KB entries as direct by default."""
    evidence_tier = entry.metadata.get("evidence_tier")
    if isinstance(evidence_tier, str):
        return EvidenceTier(evidence_tier)
    if isinstance(evidence_tier, EvidenceTier):
        return evidence_tier
    if entry.metadata.get("retrieval_source", "knowledge_base") == "knowledge_base":
        return EvidenceTier.DIRECT
    return EvidenceTier.INFERRED


def _freshness_multiplier(entry: KnowledgeEntry, time_horizon: TimeHorizon) -> float:
    """Return a recency multiplier based on entry age and requested time horizon."""
    age_days = max((datetime.now(timezone.utc) - entry.updated_at).days, 0)
    floor = FRESHNESS_FLOORS[time_horizon]
    half_life = FRESHNESS_HALF_LIFE_DAYS[time_horizon]
    multiplier = floor + (1.0 - floor) * (0.5 ** (age_days / half_life))
    return round(multiplier, 4)


def _learned_source_multiplier(
    entry: KnowledgeEntry,
    segment: Segment,
    learned_profile: LearnedWeightProfile | None,
) -> float:
    """Return a learned source multiplier derived from recent evaluation history."""
    if learned_profile is None or learned_profile.sample_count == 0:
        return 1.0

    retrieval_source = entry.metadata.get("retrieval_source", "knowledge_base")
    segment_weights = learned_profile.segment_source_multipliers.get(segment.value, {})
    return segment_weights.get(
        retrieval_source,
        learned_profile.source_multipliers.get(retrieval_source, 1.0),
    )


def _score_entry_match(
    entry: KnowledgeEntry,
    query: str,
    *,
    segment: Segment,
    time_horizon: TimeHorizon,
    learned_profile: LearnedWeightProfile | None,
) -> float:
    """Compute a lightweight relevance score for keyword-backed results."""
    normalized_query = _normalize_text(query)
    if not normalized_query:
        return entry.confidence

    query_terms = [term for term in normalized_query.split(" ") if term]
    title_text = _normalize_text(entry.title)
    content_text = _normalize_text(entry.content)
    namespace_text = _normalize_text(entry.namespace)

    score = entry.confidence
    retrieval_source = entry.metadata.get("retrieval_source", "knowledge_base")
    evidence_tier = _resolve_evidence_tier(entry)
    score *= RETRIEVAL_SOURCE_WEIGHTS.get(retrieval_source, 0.75)
    score *= EVIDENCE_TIER_WEIGHTS.get(evidence_tier, 0.65)
    score *= _learned_source_multiplier(entry, segment, learned_profile)
    score *= _freshness_multiplier(entry, time_horizon)

    if normalized_query in title_text:
        score += 1.5
    if normalized_query in content_text:
        score += 1.0
    if normalized_query == namespace_text:
        score += 0.75

    for term in query_terms:
        if term in title_text:
            score += 0.4
        if term in content_text:
            score += 0.2
        if term == namespace_text:
            score += 0.1

    return round(score, 4)


def _make_fallback_entry(
    *,
    title: str,
    content: str,
    namespace: str,
    content_type: str,
    source_name: str,
    source_url: str,
    confidence: float,
    evidence_tier: EvidenceTier,
    metadata: dict[str, Any] | None = None,
) -> KnowledgeEntry:
    """Create an in-memory fallback entry with explicit provenance metadata."""
    return KnowledgeEntry(
        title=title,
        content=content,
        namespace=namespace,
        content_type=content_type,
        source_name=source_name,
        source_url=source_url,
        confidence=confidence,
        metadata={
            "evidence_tier": evidence_tier.value,
            **(metadata or {}),
        },
    )


def _query_terms(query: str) -> list[str]:
    """Return normalized query tokens for fallback matching."""
    return [token for token in re.findall(r"[a-zA-Z0-9_+-]+", query.lower()) if len(token) >= 3]


def _matches_query_text(query: str, *values: str) -> bool:
    """Check whether a query phrase or its tokens appear in the provided values."""
    haystack = " ".join(values).lower()
    normalized_query = _normalize_text(query)
    if normalized_query and normalized_query in haystack:
        return True
    terms = _query_terms(query)
    return bool(terms) and all(term in haystack for term in terms)


def _is_broad_change_watch_query(query: str, question_type: QuestionType | None) -> bool:
    """Detect broad prompts that ask for synthesized change-watch output."""
    if question_type == QuestionType.CHANGE_WATCH:
        return True

    lowered = _normalize_text(query)
    markers = [
        "most recent",
        "impactful changes",
        "current paradigm",
        "next 4 weeks",
        "near-term",
        "watchlist",
    ]
    return any(marker in lowered for marker in markers)


def _collect_fallback_entries(
    *,
    query: str,
    question_type: QuestionType | None,
    segment: Segment,
    time_horizon: TimeHorizon,
    namespace: str | None,
    orch: Orchestrator,
    learned_profile: LearnedWeightProfile | None,
    limit: int,
) -> list[KnowledgeEntry]:
    """Collect repo-native fallback entries when the knowledge base has no matches."""
    fallback_entries: list[KnowledgeEntry] = []
    broad_change_watch = _is_broad_change_watch_query(query, question_type)

    if namespace in (None, "tools", "general"):
        for tool in orch.query_tools(top_n=FALLBACK_TOOL_LIMIT):
            text = " ".join(
                [
                    str(tool.get("tool_name", "")),
                    str(tool.get("name", "")),
                    str(tool.get("description", "")),
                    str(tool.get("category", "")),
                ]
            )
            if not _matches_query_text(query, text):
                continue
            tool_name = str(tool.get("tool_name") or tool.get("name") or "Unnamed tool")
            fallback_entries.append(
                _make_fallback_entry(
                    title=tool_name,
                    content=str(tool.get("description", "")),
                    namespace="tools",
                    content_type="tool_registry",
                    source_name="Tool Discovery Registry",
                    source_url=str(tool.get("url", "")),
                    confidence=min(float(tool.get("evaluation_score", 7.0)) / 10.0, 0.95),
                    evidence_tier=EvidenceTier.DIRECT,
                    metadata={"retrieval_source": "tool_registry"},
                )
            )

    if namespace in (None, "trends", "general"):
        for trend in orch.query_trends(top_n=FALLBACK_TREND_LIMIT):
            trend_name = str(trend.get("trend_name", "Unnamed trend"))
            trend_text = " ".join(str(value) for value in trend.values())
            if not broad_change_watch and not _matches_query_text(query, trend_name, trend_text):
                continue
            confidence = float(trend.get("composite", trend.get("score", 7.0)))
            if confidence > 1.0:
                confidence = min(confidence / 10.0, 0.95)
            fallback_entries.append(
                _make_fallback_entry(
                    title=trend_name,
                    content=trend_text,
                    namespace="trends",
                    content_type="trend_registry",
                    source_name="Trend Tracker Registry",
                    source_url="docs/phase-3-trends.md",
                    confidence=max(confidence, 0.6),
                    evidence_tier=EvidenceTier.DIRECT,
                    metadata={
                        "retrieval_source": "trend_registry",
                        "source_path": "docs/phase-3-trends.md",
                        "change_signal": True,
                    },
                )
            )

    if namespace in (None, "frameworks", "general"):
        for row in _get_framework_matrix():
            framework_name = row.get("Framework", "Untitled framework")
            framework_text = " ".join(row.values())
            if not broad_change_watch and not _matches_query_text(query, framework_name, framework_text):
                continue
            fallback_entries.append(
                _make_fallback_entry(
                    title=framework_name,
                    content=(
                        f"2024 Status: {row.get('2024 Status', '')}. "
                        f"2026 Trajectory: {row.get('2026 Trajectory', '')}. "
                        f"Notes: {row.get('Notes', '')}."
                    ),
                    namespace="frameworks",
                    content_type="framework_matrix",
                    source_name="Phase 2 Framework Matrix",
                    source_url="docs/phase-2-conceptual-frameworks.md",
                    confidence=0.72,
                    evidence_tier=EvidenceTier.DIRECT,
                    metadata={
                        "retrieval_source": "framework_matrix",
                        "source_path": "docs/phase-2-conceptual-frameworks.md",
                        "change_signal": True,
                    },
                )
            )

    ranked = sorted(
        fallback_entries,
        key=lambda entry: (
            _score_entry_match(
                entry,
                query,
                segment=segment,
                time_horizon=time_horizon,
                learned_profile=learned_profile,
            ),
            entry.confidence,
        ),
        reverse=True,
    )
    return ranked[:limit]


def _retrieve_entries(
    *,
    kb: KnowledgeBase,
    orch: Orchestrator,
    query: str,
    question_type: QuestionType | None,
    segment: Segment,
    time_horizon: TimeHorizon,
    namespace: str | None,
    limit: int,
) -> list[KnowledgeEntry]:
    """Retrieve entries from the KB first, then repo-native fallbacks if needed."""
    learned_profile = kb.derive_learned_weight_profile()
    entries = kb.search(query=query, namespace=namespace, limit=limit)
    if entries:
        return sorted(
            entries,
            key=lambda entry: (
                _score_entry_match(
                    entry,
                    query,
                    segment=segment,
                    time_horizon=time_horizon,
                    learned_profile=learned_profile,
                ),
                entry.updated_at,
            ),
            reverse=True,
        )[:limit]

    return _collect_fallback_entries(
        query=query,
        question_type=question_type,
        segment=segment,
        time_horizon=time_horizon,
        namespace=namespace,
        orch=orch,
        learned_profile=learned_profile,
        limit=limit,
    )


def _build_query_contract(
    query: str,
    question_type: QuestionType,
    segment: Segment,
    persona: Persona,
    time_horizon: TimeHorizon,
    entries: list[KnowledgeEntry],
    learned_profile: LearnedWeightProfile | None,
    response_mode: ResponseMode,
) -> dict[str, Any]:
    """Wrap keyword-search results in the canonical answer contract."""
    generated_at = datetime.now(timezone.utc)
    ranked_entries = sorted(
        entries,
        key=lambda entry: (
            _score_entry_match(
                entry,
                query,
                segment=segment,
                time_horizon=time_horizon,
                learned_profile=learned_profile,
            ),
            entry.updated_at,
        ),
        reverse=True,
    )
    titles = [entry.title for entry in ranked_entries if entry.title]
    namespaces = sorted({entry.namespace for entry in ranked_entries if entry.namespace})
    summary = (
        f"Retrieved {len(ranked_entries)} knowledge entries related to '{query}'."
        if ranked_entries
        else f"No stored knowledge entries matched '{query}'."
    )
    retrieval_sources = sorted(
        {
            entry.metadata.get("retrieval_source", "knowledge_base")
            for entry in ranked_entries
        }
    )
    tradeoffs = [
        "Results are currently backed by keyword search over the stored knowledge base.",
        "Evidence is marked conservatively until stronger source-level provenance is stored per entry.",
    ]
    if ranked_entries and retrieval_sources != ["knowledge_base"]:
        tradeoffs[0] = (
            "Results combine knowledge-base search with repo-native fallbacks such as tool registries, "
            "trend registries, and framework documentation."
        )
    gaps = []
    if not ranked_entries:
        gaps.append("No matching knowledge-base entries were found for the query.")

    enterprise_overlay = _build_enterprise_overlay(
        question_type=question_type,
        segment=segment,
        ranked_entries=ranked_entries,
        retrieval_sources=retrieval_sources,
    )

    recommendation: dict[str, Any] = {
        "query": query,
        "match_count": len(ranked_entries),
        "top_titles": titles[:3],
        "namespaces_considered": namespaces,
        "retrieval_sources": retrieval_sources,
        "ranking_strategy": (
            "keyword-plus-confidence-plus-learned-weighting-plus-freshness-with-fallbacks"
            if retrieval_sources != ["knowledge_base"]
            else "keyword-plus-confidence-plus-learned-weighting-plus-freshness"
        ),
        "source_weighting_model": SOURCE_WEIGHTING_MODEL_VERSION,
        "requested_segment": segment.value,
        "freshness_decay_applied": True,
        "learned_weighting_active": bool(learned_profile and learned_profile.sample_count),
        "learned_weighting_samples": learned_profile.sample_count if learned_profile else 0,
    }

    if question_type == QuestionType.CHANGE_WATCH:
        recommendation = {
            **recommendation,
            "top_paradigm_shifts": titles[:3],
            "why_each_shift_matters": [
                _entry_to_evidence(entry, query).why_relevant for entry in ranked_entries[:3]
            ],
            "what_remains_stable": [
                "Compound AI systems, retrieval grounding, and observability remain durable architecture anchors.",
            ],
        }
        if ranked_entries:
            summary = (
                f"Retrieved {len(ranked_entries)} change signals related to '{query}' from trends, tools, and framework sources."
            )

    contract = AnswerContractV0(
        question_type=question_type,
        segment=segment,
        persona=persona,
        time_horizon=time_horizon,
        summary=summary,
        recommendation=recommendation,
        enterprise_overlay=enterprise_overlay,
        tradeoffs=tradeoffs,
        evidence=[_entry_to_evidence(entry, query) for entry in ranked_entries],
        confidence=ConfidenceAssessment(
            score=(0.78 if ranked_entries and retrieval_sources == ["knowledge_base"] else 0.7)
            if ranked_entries
            else 0.25,
            reasoning=(
                "Confidence reflects learned source weighting, freshness-aware ranking, and keyword matches found in the knowledge base."
                if ranked_entries and retrieval_sources == ["knowledge_base"]
                else "Confidence reflects learned source weighting, freshness-aware ranking, and repo-native fallback matches with explicit provenance."
                if ranked_entries
                else "Confidence is low because the current keyword search returned no matches."
            ),
            gaps=gaps,
        ),
        watchlist=[
            "response schema integration",
            "source-level provenance capture",
            "semantic retrieval beyond keyword search",
        ],
        reusable_artifacts=[
            "answer contract DTOs",
            "REST query adapter",
            "knowledge-base evidence mapping",
        ],
        next_actions=(
            [
                "Inspect the top matched entries and refine namespace filters.",
                "Add stronger provenance fields to stored knowledge entries.",
            ]
            if entries
            else [
                "Run an intelligence cycle or ingest targeted sources for this topic.",
                "Retry the query with a narrower keyword phrase or namespace filter.",
            ]
        ),
        freshness=FreshnessMetadata(
            generated_at=generated_at,
            best_before=generated_at + timedelta(days=DEFAULT_BEST_BEFORE_DAYS),
            sensitive_to_change=True,
        ),
    )
    return contract.to_response_payload(response_mode=response_mode)


def _build_enterprise_overlay(
    *,
    question_type: QuestionType,
    segment: Segment,
    ranked_entries: list[KnowledgeEntry],
    retrieval_sources: list[str],
) -> EnterpriseOverlayV0:
    """Build a conservative enterprise overlay from retrieval results and question context."""
    evidence_tiers = {
        entry.metadata.get("evidence_tier", EvidenceTier.INFERRED) for entry in ranked_entries
    }
    normalized_tiers = {
        EvidenceTier(tier) if isinstance(tier, str) else tier for tier in evidence_tiers
    }
    has_strong_evidence = bool(
        normalized_tiers.intersection({EvidenceTier.DIRECT, EvidenceTier.PUBLIC_COMPANION})
    )
    if ranked_entries and retrieval_sources == ["knowledge_base"]:
        has_strong_evidence = True
    enterprise_safe_now = bool(ranked_entries) and has_strong_evidence and segment in {
        Segment.ENTERPRISE,
        Segment.CROSS_SEGMENT,
    }

    if question_type == QuestionType.ARCHITECTURE_RECOMMENDATION:
        key_requirements = [
            "workflow durability and failure recovery",
            "typed service and contract boundaries",
            "observability and evaluation reporting",
            "provenance capture for architectural decisions",
        ]
    elif question_type == QuestionType.STACK_RECOMMENDATION:
        key_requirements = [
            "dependency and vendor review",
            "audit-friendly storage and logs",
            "access control and identity hooks",
            "evaluation history retention",
        ]
    else:
        key_requirements = [
            "wrapper boundaries for fast-moving tools",
            "watchlist review cadence",
            "rollback-safe rollout checks",
            "freshness-aware recommendation review",
        ]

    if retrieval_sources != ["knowledge_base"]:
        key_requirements.append("confirm fallback signals against direct production evidence before rollout")

    reasoning = (
        "The recommendation is enterprise-safe enough to use as a current working baseline because it is "
        "backed by retrieved evidence with explicit provenance and segment-aware constraints."
        if enterprise_safe_now
        else "The recommendation is still useful, but enterprise rollout remains provisional because the "
        "current answer depends on partial retrieval coverage or non-enterprise tuning."
    )

    future_alignment_hooks = [
        "preserve source provenance and URLs for future governance systems",
        "keep machine-readable contracts stable across tool swaps",
        "retain evaluation history for change review and audit-friendly comparisons",
    ]
    if question_type == QuestionType.CHANGE_WATCH:
        future_alignment_hooks.append(
            "gate near-term tool adoption behind wrappers until stability and policy implications are clearer"
        )

    segment_deltas = [
        SegmentDeltaV0(
            segment=Segment.STARTUP,
            adjustment_summary="Bias toward speed, managed defaults, and lighter control surfaces.",
            key_priorities=[
                "implementation speed",
                "managed services",
                "minimal platform overhead",
            ],
        ),
        SegmentDeltaV0(
            segment=Segment.SMALL_COMPANY,
            adjustment_summary="Balance delivery speed with a moderate amount of auditability and reuse.",
            key_priorities=[
                "cost-aware managed infrastructure",
                "basic observability",
                "incremental contract hardening",
            ],
        ),
        SegmentDeltaV0(
            segment=Segment.ENTERPRISE,
            adjustment_summary="Require stronger auditability, role separation, change review, and evidence retention.",
            key_priorities=[
                "audit trails",
                "policy hooks",
                "evaluation traceability",
            ],
        ),
    ]

    return EnterpriseOverlayV0(
        enterprise_safe_now=enterprise_safe_now,
        reasoning=reasoning,
        key_requirements=key_requirements,
        future_alignment_hooks=future_alignment_hooks,
        segment_deltas=segment_deltas,
    )


def _persist_evaluation_result(
    *,
    kb: KnowledgeBase,
    run_type: str,
    payload: dict[str, Any],
    query: str = "",
    question_id: str = "",
) -> str:
    """Persist an evaluation result and return its run ID."""
    if run_type == "query":
        average_normalized_score = float(payload.get("normalized_score", 0.0))
        verdict_summary = str(payload.get("verdict", "unknown"))
    else:
        average_normalized_score = float(payload.get("average_normalized_score", 0.0))
        verdict_summary = json.dumps(payload.get("verdict_counts", {}), sort_keys=True)

    record = EvaluationRunRecord(
        run_type=run_type,
        query=query,
        question_id=question_id,
        average_normalized_score=average_normalized_score,
        verdict_summary=verdict_summary,
        payload=payload,
    )
    return kb.store_evaluation_run(record)


def _build_evaluation_history_payload(records: list[EvaluationRunRecord]) -> dict[str, Any]:
    """Convert persisted evaluation run records into the API history payload."""
    history = EvaluationRunHistoryV0(
        count=len(records),
        items=[
            StoredEvaluationRunV0(
                run_id=record.run_id,
                run_type=record.run_type,
                query=record.query,
                question_id=record.question_id,
                average_normalized_score=record.average_normalized_score,
                verdict_summary=record.verdict_summary,
                created_at=record.created_at,
                payload=record.payload,
            )
            for record in records
        ],
    )
    return history.model_dump(mode="json")


def _build_evaluation_performance_payload(records: list[EvaluationRunRecord]) -> dict[str, Any]:
    """Summarize recent persisted evaluation runs into a compact performance view."""
    if not records:
        return EvaluationPerformanceSummaryV0(
            total_runs=0,
            overall_average_normalized_score=0.0,
            trend_direction="insufficient_data",
            latest_run_at=None,
            by_run_type=[],
        ).model_dump(mode="json")

    grouped: dict[str, list[EvaluationRunRecord]] = {}
    for record in records:
        grouped.setdefault(record.run_type, []).append(record)

    by_run_type: list[EvaluationPerformanceBreakdownV0] = []
    for run_type, group in sorted(grouped.items()):
        verdict_counts: dict[str, int] = {"strong": 0, "partial": 0, "weak": 0}
        for record in group:
            if record.run_type == "query":
                verdict = str(record.payload.get("verdict", "unknown"))
                verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
                continue

            for verdict, count in record.payload.get("verdict_counts", {}).items():
                verdict_counts[verdict] = verdict_counts.get(verdict, 0) + int(count)

        by_run_type.append(
            EvaluationPerformanceBreakdownV0(
                run_type=run_type,
                count=len(group),
                average_normalized_score=round(
                    sum(record.average_normalized_score for record in group) / len(group),
                    4,
                ),
                verdict_counts=verdict_counts,
                latest_run_at=max(record.created_at for record in group),
            )
        )

    latest_run_at = max(record.created_at for record in records)
    latest_window = records[:5]
    previous_window = records[5:10]
    trend_direction = "insufficient_data"
    if previous_window:
        latest_average = sum(record.average_normalized_score for record in latest_window) / len(latest_window)
        previous_average = sum(record.average_normalized_score for record in previous_window) / len(previous_window)
        delta = latest_average - previous_average
        if delta >= 0.05:
            trend_direction = "improving"
        elif delta <= -0.05:
            trend_direction = "declining"
        else:
            trend_direction = "steady"

    summary = EvaluationPerformanceSummaryV0(
        total_runs=len(records),
        overall_average_normalized_score=round(
            sum(record.average_normalized_score for record in records) / len(records),
            4,
        ),
        trend_direction=trend_direction,
        latest_run_at=latest_run_at,
        by_run_type=by_run_type,
    )
    return summary.model_dump(mode="json")


def create_app(
    orchestrator: Orchestrator | None = None,
    knowledge_base: KnowledgeBase | None = None,
) -> FastAPI:
    """Create the FastAPI app with injectable dependencies for testing."""
    orch = orchestrator or Orchestrator()
    kb = knowledge_base or KnowledgeBase()
    owns_orchestrator = orchestrator is None
    owns_knowledge_base = knowledge_base is None

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if owns_orchestrator and not orch._agents_initialized:
            orch.initialize()
        if owns_knowledge_base and kb._conn is None:
            kb.initialize()
        yield
        if owns_knowledge_base:
            kb.close()
        if owns_orchestrator:
            orch.shutdown()

    app = FastAPI(
        title="Agentic AI Architect API",
        version="0.1.0",
        description="Minimal REST surface for querying trends, tools, and structured answer payloads.",
        lifespan=lifespan,
    )

    @app.get("/")
    def root() -> dict[str, Any]:
        return {
            "service": "Agentic AI Architect API",
            "status": "ok",
            "docs_url": "/docs",
            "openapi_url": "/openapi.json",
            "primary_routes": [
                "/health",
                "/frameworks",
                "/evaluation-set",
                "/evaluate/history",
                "/evaluate/performance",
                "/evaluate/query",
                "/evaluate/query-segments",
                "/evaluate/query-set",
                "/query",
            ],
        }

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "agents": orch.health_check(),
            "knowledge_entries": kb.count() if kb._conn else 0,
        }

    @app.get("/trends")
    def get_trends(top_n: int = Query(default=10, ge=1, le=50)) -> dict[str, Any]:
        trends = orch.query_trends(top_n=top_n)
        return {"count": len(trends), "items": trends}

    @app.get("/tools")
    def get_tools(
        category: str | None = Query(default=None),
        top_n: int = Query(default=10, ge=1, le=50),
    ) -> dict[str, Any]:
        tools = orch.query_tools(category=category, top_n=top_n)
        return {"count": len(tools), "items": tools}

    @app.get("/frameworks")
    def get_frameworks(
        search: str | None = Query(default=None),
        trajectory: str | None = Query(default=None),
        status_2024: str | None = Query(default=None),
    ) -> dict[str, Any]:
        frameworks = _filter_frameworks(
            frameworks=_get_framework_matrix(),
            search=search,
            trajectory=trajectory,
            status_2024=status_2024,
        )
        return {
            "count": len(frameworks),
            "items": frameworks,
            "source_path": "docs/phase-2-conceptual-frameworks.md",
        }

    @app.get("/report/{phase}")
    def get_report(phase: str) -> dict[str, str]:
        try:
            return _get_phase_report(phase)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"Unknown phase report: {phase}") from exc

    @app.get("/evaluation-set", response_model=EvaluationSetV0)
    def get_evaluation_set(
        question_type: QuestionType | None = Query(default=None),
        segment: Segment | None = Query(default=None),
    ) -> dict[str, Any]:
        evaluation_set = build_initial_evaluation_set()
        questions = evaluation_set.questions

        if question_type is not None:
            questions = [question for question in questions if question.question_type == question_type]

        if segment is not None:
            questions = [question for question in questions if question.segment == segment]

        return evaluation_set.model_copy(update={"questions": questions}).model_dump(mode="json")

    @app.get("/evaluate/query", response_model=QueryEvaluationResultV0)
    def evaluate_query(
        question_id: str = Query(min_length=1),
        q: str | None = Query(default=None),
        namespace: str | None = Query(default=None),
        limit: int = Query(default=DEFAULT_QUERY_LIMIT, ge=1, le=MAX_QUERY_LIMIT),
        persist: bool = Query(default=True),
    ) -> dict[str, Any]:
        if kb._conn is None:
            raise HTTPException(status_code=503, detail="Knowledge base is not initialized")

        try:
            question = get_evaluation_question(question_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"Unknown evaluation question: {question_id}") from exc

        query_text = q or question.prompt
        entries = _retrieve_entries(
            kb=kb,
            orch=orch,
            query=query_text,
            question_type=question.question_type,
            segment=question.segment,
            time_horizon=question.time_horizon,
            namespace=namespace,
            limit=limit,
        )
        answer_payload = _build_query_contract(
            query=query_text,
            question_type=question.question_type,
            segment=question.segment,
            persona=question.persona,
            time_horizon=question.time_horizon,
            entries=entries,
            learned_profile=kb.derive_learned_weight_profile(),
            response_mode=question.response_mode,
        )
        answer = AnswerContractV0(**answer_payload)
        evaluation = evaluate_query_response(query=query_text, question=question, answer=answer)
        payload = evaluation.model_dump(mode="json")
        if persist:
            payload["run_id"] = _persist_evaluation_result(
                kb=kb,
                run_type="query",
                payload=payload,
                query=query_text,
                question_id=question.question_id,
            )
        return payload

    @app.get("/evaluate/query-set", response_model=QueryEvaluationBatchResultV0)
    def evaluate_query_set(
        question_type: QuestionType | None = Query(default=None),
        segment: Segment | None = Query(default=None),
        namespace: str | None = Query(default=None),
        limit: int = Query(default=DEFAULT_QUERY_LIMIT, ge=1, le=MAX_QUERY_LIMIT),
        persist: bool = Query(default=True),
    ) -> dict[str, Any]:
        if kb._conn is None:
            raise HTTPException(status_code=503, detail="Knowledge base is not initialized")

        evaluation_set = build_initial_evaluation_set()
        questions = evaluation_set.questions
        if question_type is not None:
            questions = [question for question in questions if question.question_type == question_type]
        if segment is not None:
            questions = [question for question in questions if question.segment == segment]

        if not questions:
            raise HTTPException(status_code=404, detail="No evaluation questions matched the provided filters")

        results = []
        for question in questions:
            entries = _retrieve_entries(
                kb=kb,
                orch=orch,
                query=question.prompt,
                question_type=question.question_type,
                segment=question.segment,
                time_horizon=question.time_horizon,
                namespace=namespace,
                limit=limit,
            )
            answer_payload = _build_query_contract(
                query=question.prompt,
                question_type=question.question_type,
                segment=question.segment,
                persona=question.persona,
                time_horizon=question.time_horizon,
                entries=entries,
                learned_profile=kb.derive_learned_weight_profile(),
                response_mode=question.response_mode,
            )
            answer = AnswerContractV0(**answer_payload)
            results.append(
                evaluate_query_response(
                    query=question.prompt,
                    question=question,
                    answer=answer,
                )
            )

        payload = summarize_query_evaluations(results).model_dump(mode="json")
        if persist:
            payload["run_id"] = _persist_evaluation_result(
                kb=kb,
                run_type="query-set",
                payload=payload,
            )
        return payload

    @app.get("/evaluate/query-segments", response_model=SegmentEvaluationComparisonV0)
    def evaluate_query_segments(
        question_id: str = Query(min_length=1),
        q: str | None = Query(default=None),
        segments: list[Segment] = Query(
            default=[Segment.STARTUP, Segment.SMALL_COMPANY, Segment.ENTERPRISE]
        ),
        namespace: str | None = Query(default=None),
        limit: int = Query(default=DEFAULT_QUERY_LIMIT, ge=1, le=MAX_QUERY_LIMIT),
        persist: bool = Query(default=True),
    ) -> dict[str, Any]:
        if kb._conn is None:
            raise HTTPException(status_code=503, detail="Knowledge base is not initialized")

        try:
            question = get_evaluation_question(question_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"Unknown evaluation question: {question_id}") from exc

        query_text = q or question.prompt
        learned_profile = kb.derive_learned_weight_profile()
        results = []
        for requested_segment in segments:
            segment_question = question.model_copy(update={"segment": requested_segment})
            entries = _retrieve_entries(
                kb=kb,
                orch=orch,
                query=query_text,
                question_type=question.question_type,
                segment=requested_segment,
                time_horizon=question.time_horizon,
                namespace=namespace,
                limit=limit,
            )
            answer_payload = _build_query_contract(
                query=query_text,
                question_type=question.question_type,
                segment=requested_segment,
                persona=question.persona,
                time_horizon=question.time_horizon,
                entries=entries,
                learned_profile=learned_profile,
                response_mode=question.response_mode,
            )
            answer = AnswerContractV0(**answer_payload)
            results.append(
                evaluate_query_response(
                    query=query_text,
                    question=segment_question,
                    answer=answer,
                )
            )

        payload = summarize_segment_evaluations(
            question_id=question.question_id,
            query=query_text,
            results=results,
        ).model_dump(mode="json")
        if persist:
            payload["run_id"] = _persist_evaluation_result(
                kb=kb,
                run_type="query-segments",
                payload=payload,
                query=query_text,
                question_id=question.question_id,
            )
        return payload

    @app.get("/evaluate/history", response_model=EvaluationRunHistoryV0)
    def get_evaluation_history(
        run_type: str | None = Query(default=None),
        limit: int = Query(default=20, ge=1, le=100),
    ) -> dict[str, Any]:
        if kb._conn is None:
            raise HTTPException(status_code=503, detail="Knowledge base is not initialized")

        records = kb.list_evaluation_runs(limit=limit, run_type=run_type)
        return _build_evaluation_history_payload(records)

    @app.get("/evaluate/performance", response_model=EvaluationPerformanceSummaryV0)
    def get_evaluation_performance(
        limit: int = Query(default=50, ge=1, le=200),
    ) -> dict[str, Any]:
        if kb._conn is None:
            raise HTTPException(status_code=503, detail="Knowledge base is not initialized")

        records = kb.list_evaluation_runs(limit=limit)
        return _build_evaluation_performance_payload(records)

    @app.get("/query", response_model=AnswerContractV0)
    def query_knowledge(
        q: str = Query(min_length=1),
        question_type: QuestionType = Query(default=QuestionType.ARCHITECTURE_RECOMMENDATION),
        response_mode: ResponseMode = Query(default=ResponseMode.JSON),
        segment: Segment = Query(default=Segment.CROSS_SEGMENT),
        persona: Persona = Query(default=Persona.ARCHITECT),
        time_horizon: TimeHorizon = Query(default=TimeHorizon.NOW),
        namespace: str | None = Query(default=None),
        limit: int = Query(default=DEFAULT_QUERY_LIMIT, ge=1, le=MAX_QUERY_LIMIT),
    ) -> dict[str, Any]:
        if kb._conn is None:
            raise HTTPException(status_code=503, detail="Knowledge base is not initialized")

        entries = _retrieve_entries(
            kb=kb,
            orch=orch,
            query=q,
            question_type=question_type,
            segment=segment,
            time_horizon=time_horizon,
            namespace=namespace,
            limit=limit,
        )
        learned_profile = kb.derive_learned_weight_profile()
        return _build_query_contract(
            query=q,
            question_type=question_type,
            segment=segment,
            persona=persona,
            time_horizon=time_horizon,
            entries=entries,
            learned_profile=learned_profile,
            response_mode=response_mode,
        )

    return app


app = create_app()