"""
Claude Haiku synthesis helpers for persona-layer MCP tools.

All three functions accept an optional anthropic client; when None they fall back
to evidence-only summaries so the system degrades gracefully without an API key.
"""

import json
import logging

from src.personas.models import PersonaViewpoint

logger = logging.getLogger(__name__)

_MODEL = "claude-haiku-4-5-20251001"
_MAX_TOKENS = 1024

# ---------------------------------------------------------------------------
# ask_persona
# ---------------------------------------------------------------------------

_ASK_PERSONA_PROMPT = """\
You are synthesizing the documented public perspective of {display_name} on the question below, \
based solely on their indexed content. You are NOT roleplaying or impersonating them — you are \
summarising what their published work says about this topic.

QUESTION: {question}

EVIDENCE ({n} items from {display_name}'s public content):
{evidence}

Return a JSON object with exactly these keys:
{{
  "viewpoint": "2-4 sentence synthesis of their documented perspective (third person)",
  "key_points": ["up to 5 specific points from their content, with brief justification"],
  "relevant_tools": ["tools or frameworks they explicitly mention in the evidence"],
  "confidence": "high | medium | low | insufficient",
  "confidence_reason": "one sentence — why this confidence level"
}}

Rules:
- Only cite what appears in the evidence. Never invent claims.
- If evidence is sparse or off-topic, set confidence to "low" or "insufficient".
- Return only valid JSON. No markdown fences."""


def ask_persona_synthesis(
    persona_id: str,
    display_name: str,
    question: str,
    hits: list[dict],
    client,
) -> PersonaViewpoint:
    """Synthesize one persona's viewpoint from their retrieved content."""
    provenance = [
        {
            "post_type": h.get("metadata", {}).get("post_type"),
            "timestamp": h.get("metadata", {}).get("timestamp") or h.get("metadata", {}).get("scraped_at"),
            "snippet": h.get("document", "")[:200],
        }
        for h in hits[:5]
    ]

    if client is None or not hits:
        confidence = "insufficient" if not hits else "low"
        return PersonaViewpoint(
            persona_id=persona_id,
            display_name=display_name,
            viewpoint=f"No LLM synthesis available. {len(hits)} items found for {display_name}.",
            key_points=[h.get("document", "")[:150] for h in hits[:3]],
            relevant_tools=_extract_tools(hits),
            confidence=confidence,
            confidence_reason="Set ANTHROPIC_API_KEY for AI-synthesized viewpoints.",
            sources_used=len(hits),
            provenance=provenance,
        )

    evidence_lines = []
    for i, h in enumerate(hits, 1):
        meta = h.get("metadata", {})
        ptype = meta.get("post_type", "")
        score = h.get("score", 0)
        snippet = h.get("document", "")[:500]
        evidence_lines.append(f"[{i}] ({ptype}, relevance={score:.2f}):\n{snippet}")

    prompt = _ASK_PERSONA_PROMPT.format(
        display_name=display_name,
        question=question,
        n=len(hits),
        evidence="\n\n".join(evidence_lines),
    )

    try:
        msg = client.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = _strip_fences(msg.content[0].text)
        data = json.loads(raw)
        return PersonaViewpoint(
            persona_id=persona_id,
            display_name=display_name,
            viewpoint=data.get("viewpoint", ""),
            key_points=data.get("key_points", []),
            relevant_tools=data.get("relevant_tools", []),
            confidence=data.get("confidence", "low"),
            confidence_reason=data.get("confidence_reason", ""),
            sources_used=len(hits),
            provenance=provenance,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("ask_persona synthesis failed for %s: %s", persona_id, exc)
        return PersonaViewpoint(
            persona_id=persona_id,
            display_name=display_name,
            viewpoint=f"Synthesis failed: {exc}. Raw evidence available in provenance.",
            key_points=[h.get("document", "")[:150] for h in hits[:3]],
            relevant_tools=_extract_tools(hits),
            confidence="low",
            confidence_reason=f"Synthesis error: {exc}",
            sources_used=len(hits),
            provenance=provenance,
        )


# ---------------------------------------------------------------------------
# compare_personas
# ---------------------------------------------------------------------------

_COMPARE_PROMPT = """\
Below are synthesized viewpoints from different AI thought leaders on the question:
"{question}"

VIEWPOINTS:
{viewpoints}

Identify cross-persona patterns. Return a JSON object with exactly these keys:
{{
  "agreements": ["up to 5 points where multiple personas align"],
  "disagreements": ["up to 5 points where personas diverge — name who disagrees and why"],
  "unique_perspectives": {{"persona_id": "one-sentence distinctive angle they hold that others don't"}},
  "synthesis": "2-3 sentence meta-summary of the overall landscape of opinion"
}}

Return only valid JSON. No markdown fences."""


def compare_personas_synthesis(
    question: str,
    viewpoints: list[PersonaViewpoint],
    client,
) -> dict:
    """Synthesize agreement/disagreement across a set of persona viewpoints."""
    if client is None:
        return {
            "agreements": [],
            "disagreements": [],
            "unique_perspectives": {v.persona_id: v.viewpoint[:150] for v in viewpoints},
            "synthesis": "Set ANTHROPIC_API_KEY for cross-persona comparison synthesis.",
        }

    vp_lines = []
    for v in viewpoints:
        points = "; ".join(v.key_points[:3])
        vp_lines.append(
            f"{v.display_name} (confidence={v.confidence}):\n"
            f"  Viewpoint: {v.viewpoint}\n"
            f"  Key points: {points}"
        )

    prompt = _COMPARE_PROMPT.format(
        question=question,
        viewpoints="\n\n".join(vp_lines),
    )

    try:
        msg = client.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        return json.loads(_strip_fences(msg.content[0].text))
    except Exception as exc:  # noqa: BLE001
        logger.warning("compare_personas synthesis failed: %s", exc)
        return {
            "agreements": [],
            "disagreements": [],
            "unique_perspectives": {v.persona_id: v.viewpoint[:150] for v in viewpoints},
            "synthesis": f"Comparison synthesis failed: {exc}",
        }


# ---------------------------------------------------------------------------
# get_consensus
# ---------------------------------------------------------------------------

_CONSENSUS_PROMPT = """\
Below are {n} knowledge items from AI thought leaders on the question:
"{question}"

EVIDENCE:
{evidence}

Synthesize the community consensus. Return a JSON object with exactly these keys:
{{
  "consensus": "2-4 sentence dominant view that most evidence supports",
  "minority_views": ["up to 3 notable dissenting or alternative positions with attribution"],
  "key_tensions": ["up to 3 unresolved debates or tradeoffs in the evidence"],
  "agreement_level": "strong | moderate | weak | contested",
  "agreement_reason": "one sentence explaining the agreement level",
  "personas_cited": ["display names of thought leaders whose content shaped the consensus"]
}}

Return only valid JSON. No markdown fences."""


def get_consensus_synthesis(
    question: str,
    hits: list[dict],
    client,
) -> dict:
    """Synthesize a community consensus view from broad retrieved evidence."""
    personas_in_hits = list(dict.fromkeys(
        h.get("metadata", {}).get("author", h.get("metadata", {}).get("persona_id", ""))
        for h in hits
        if h.get("metadata", {}).get("author") or h.get("metadata", {}).get("persona_id")
    ))

    if client is None or not hits:
        return {
            "consensus": f"No LLM synthesis available. {len(hits)} items retrieved.",
            "minority_views": [],
            "key_tensions": [],
            "agreement_level": "unknown",
            "agreement_reason": "Set ANTHROPIC_API_KEY for consensus synthesis.",
            "personas_cited": personas_in_hits[:10],
        }

    evidence_lines = []
    for i, h in enumerate(hits, 1):
        meta = h.get("metadata", {})
        author = meta.get("author", meta.get("persona_id", "unknown"))
        ptype = meta.get("post_type", "")
        snippet = h.get("document", "")[:400]
        evidence_lines.append(f"[{i}] {author} ({ptype}):\n{snippet}")

    prompt = _CONSENSUS_PROMPT.format(
        question=question,
        n=len(hits),
        evidence="\n\n".join(evidence_lines),
    )

    try:
        msg = client.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        return json.loads(_strip_fences(msg.content[0].text))
    except Exception as exc:  # noqa: BLE001
        logger.warning("get_consensus synthesis failed: %s", exc)
        return {
            "consensus": f"Synthesis failed: {exc}",
            "minority_views": [],
            "key_tensions": [],
            "agreement_level": "unknown",
            "agreement_reason": f"Synthesis error: {exc}",
            "personas_cited": personas_in_hits[:10],
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return text


def _extract_tools(hits: list[dict]) -> list[str]:
    seen: dict[str, None] = {}
    for h in hits:
        for t in h.get("metadata", {}).get("mentioned_tools", "").split(","):
            t = t.strip()
            if t:
                seen[t] = None
    return list(seen)[:10]
