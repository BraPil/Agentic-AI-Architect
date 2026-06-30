"""
outcome_weighting.py — P6 outcome capture, slice 2: turn the recorded outcome
signal into a retrieval re-ranking multiplier.

Slice 1 (`outcomes.py`) records whether each architecture recommendation was
adopted and whether it worked, and aggregates a per-persona / per-tool
`weight_multiplier`. This module is the *consumer*: it re-ranks the retrieval
hits feeding ``get_architecture_recommendation`` so sources with a proven
real-world track record rank higher, and sources whose advice was
adopted-and-failed rank lower.

Two firewalls keep this honest, mirroring the rest of the P6 loop:
  - **Minimum-evidence gate** — an entity's multiplier only leaves neutral
    (1.0) once it has at least ``min_evidence`` recorded outcomes. With a tiny
    ledger this makes re-ranking an exact no-op: ranking moves only on real
    signal, never noise. (Same small-data honesty as the Laplace prior that
    produced the multiplier in the first place.)
  - **Bounded, averaged combination** — a hit's final multiplier is the mean of
    the applicable entity multipliers (each already bounded to ``[0.5, 1.5]`` by
    ``outcomes.py``), so a single source can never dominate and the result stays
    in range.

Pure functions only: no I/O, no ChromaDB, no LLM. The store (`outcomes.py`)
produces the signal, this module applies it, and the caller (`mcp_server.py`)
wires them together — keeping ranking logic out of the transport layer and
unit-testable in isolation.
"""

import re
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# An entity needs at least this many recorded outcomes before its multiplier is
# allowed to move ranking. Deliberately conservative: below it, re-ranking is an
# exact no-op so a handful of early outcomes never reshape retrieval.
MIN_EVIDENCE_DEFAULT = 5

NEUTRAL = 1.0


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------

def _normalize(name: str) -> str:
    """Collapse a persona/tool name to a stable match key.

    ``"Andrej Karpathy"`` -> ``"andrejkarpathy"``; ``"andrej-karpathy"`` ->
    ``"andrejkarpathy"``. This lets the signal keys (display names cited by the
    synthesizer) match the ``author`` / ``persona_id`` fields on a hit's
    metadata regardless of which surface form each side used.
    """
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def gated_multipliers(signal_section: dict | None, min_evidence: int) -> dict[str, float]:
    """Map ``normalized entity name -> multiplier`` for entities past the gate.

    ``signal_section`` is one of ``aggregate()["persona_signal"]`` /
    ``["tool_signal"]``: ``{entity: {recommended, worked, success_rate,
    weight_multiplier}}``. Entities with fewer than ``min_evidence`` recorded
    outcomes (``recommended`` count) are omitted — and an omitted entity is
    therefore treated as neutral by the reranker.
    """
    out: dict[str, float] = {}
    for name, stats in (signal_section or {}).items():
        if not isinstance(stats, dict):
            continue
        if int(stats.get("recommended", 0)) < min_evidence:
            continue
        mult = stats.get("weight_multiplier")
        if mult is None:
            continue
        key = _normalize(name)
        if key:
            out[key] = float(mult)
    return out


def hit_multiplier(
    hit: dict[str, Any],
    persona_mults: dict[str, float],
    tool_mults: dict[str, float],
) -> float:
    """Outcome multiplier for one hit = mean of applicable entity multipliers.

    A hit is attributed to exactly one persona (its author) plus any of its
    ``mentioned_tools`` that have cleared the gate. With no applicable entity the
    multiplier is neutral (``1.0``), leaving the hit's semantic rank untouched.
    """
    meta = hit.get("metadata", {}) or {}
    applicable: list[float] = []

    # One persona per hit — prefer the display-name match, fall back to slug;
    # never count both for the same author.
    for field in ("author", "persona_id"):
        key = _normalize(str(meta.get(field, "")))
        if key and key in persona_mults:
            applicable.append(persona_mults[key])
            break

    if tool_mults:
        seen: set[str] = set()
        for raw in str(meta.get("mentioned_tools", "")).split(","):
            key = _normalize(raw)
            if key and key not in seen and key in tool_mults:
                seen.add(key)
                applicable.append(tool_mults[key])

    if not applicable:
        return NEUTRAL
    return sum(applicable) / len(applicable)


def rerank_by_outcomes(
    hits: list[dict[str, Any]],
    persona_signal: dict | None,
    tool_signal: dict | None,
    min_evidence: int = MIN_EVIDENCE_DEFAULT,
) -> list[dict[str, Any]]:
    """Re-sort hits by ``base relevance * outcome multiplier``.

    Non-mutating: returns new hit dicts. The original ``score`` (semantic
    relevance) is preserved; ``outcome_multiplier`` and ``ranking_score`` are
    attached for auditability. Sorting is stable, so hits with equal ranking
    scores keep their incoming (relevance) order.

    The base relevance is the store's strongest ranking signal — the
    cross-encoder score if present, else the hybrid score, else the raw vector
    ``score`` — so outcome weighting scales the ranking the store actually
    produced rather than silently reverting to pure vector order. See
    src/pipeline/hybrid_ranking.py and src/pipeline/cross_encoder_rerank.py.

    When nothing has cleared the evidence gate the input order is returned
    unchanged (an exact no-op) — the common case while the outcome ledger is
    still small.
    """
    persona_mults = gated_multipliers(persona_signal, min_evidence)
    tool_mults = gated_multipliers(tool_signal, min_evidence)

    if not persona_mults and not tool_mults:
        return list(hits)

    ranked: list[dict[str, Any]] = []
    for h in hits:
        mult = hit_multiplier(h, persona_mults, tool_mults)
        # Strongest available ranking signal: cross-encoder > hybrid > vector.
        if "cross_encoder_score" in h:
            base = float(h["cross_encoder_score"])
        elif "hybrid_score" in h:
            base = float(h["hybrid_score"])
        else:
            base = float(h.get("score", 0.0))
        new = dict(h)
        new["outcome_multiplier"] = round(mult, 4)
        new["ranking_score"] = round(base * mult, 6)
        ranked.append(new)

    ranked.sort(key=lambda x: x["ranking_score"], reverse=True)
    return ranked
