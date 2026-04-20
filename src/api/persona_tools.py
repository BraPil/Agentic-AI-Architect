"""
Persona-layer MCP tools for AAA — ask_persona, compare_personas, get_consensus.

Registered via register_persona_tools(mcp) to keep mcp_server.py under the
400-line limit. All synthesis is delegated to src.personas.synthesis.
"""

import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_SCHEMA_VERSION = "1.0"
_DEFAULT_N = 8
_MAX_N = 25
_MAX_COMPARE_PERSONAS = 6


def register_persona_tools(mcp) -> None:
    """Attach persona tools to an existing FastMCP instance."""

    # ------------------------------------------------------------------
    # Lazy imports (keep startup fast; avoid circular imports)
    # ------------------------------------------------------------------

    def _get_store():
        from src.api.mcp_server import _get_store as _mcp_get_store  # noqa: PLC0415
        return _mcp_get_store()

    def _get_client():
        from src.api.mcp_server import _get_anthropic  # noqa: PLC0415
        return _get_anthropic()

    # ------------------------------------------------------------------
    # ask_persona
    # ------------------------------------------------------------------

    @mcp.tool()
    def ask_persona(
        persona_id: str,
        question: str,
        n_sources: int = _DEFAULT_N,
    ) -> str:
        """Get one thought leader's documented perspective on a question.

        Searches only that persona's indexed content (LinkedIn posts, YouTube
        transcripts, blog posts, GitHub READMEs) and synthesises their viewpoint
        using Claude. Returns confidence level and provenance so you know exactly
        what evidence informed the answer.

        Args:
            persona_id: Persona slug, e.g. "andrej-karpathy", "cole-medin",
                        "chip-huyen", "simon-willison", "lilian-weng".
                        Use get_trending_tools or /v1/personas to list available slugs.
            question: What you want to know — any AI architecture or tools question.
            n_sources: Items to retrieve before synthesis (1–25, default 8).

        Returns:
            JSON with viewpoint, key_points, relevant_tools, confidence,
            confidence_reason, sources_used, and provenance snippets.
        """
        from src.personas.registry import build_persona_profile  # noqa: PLC0415
        from src.personas.synthesis import ask_persona_synthesis  # noqa: PLC0415

        n_sources = max(1, min(n_sources, _MAX_N))
        store = _get_store()
        client = _get_client()

        profile = build_persona_profile(persona_id, store)
        display_name = profile.display_name if profile else persona_id

        hits = store.search(query=question, n_results=n_sources, persona_id=persona_id)

        viewpoint = ask_persona_synthesis(
            persona_id=persona_id,
            display_name=display_name,
            question=question,
            hits=hits,
            client=client,
        )

        payload = json.dumps({
            "schema_version": _SCHEMA_VERSION,
            "question": question,
            **viewpoint.to_dict(),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }, indent=2, ensure_ascii=False)

        _log("ask_persona", {"persona_id": persona_id, "question": question[:80]}, len(payload))
        return payload

    # ------------------------------------------------------------------
    # compare_personas
    # ------------------------------------------------------------------

    @mcp.tool()
    def compare_personas(
        question: str,
        personas: str = "",
        n_sources: int = 6,
    ) -> str:
        """Compare how multiple thought leaders view the same question.

        Runs ask_persona for each specified persona, then synthesises agreements,
        disagreements, and unique angles across the group.

        Args:
            question: The question to compare perspectives on.
            personas: Comma-separated persona slugs to compare, e.g.
                      "andrej-karpathy,chip-huyen,simon-willison".
                      Defaults to a curated set of 4 well-indexed personas.
            n_sources: Items per persona before synthesis (1–25, default 6).

        Returns:
            JSON with per-persona viewpoints plus agreements, disagreements,
            unique_perspectives, and a cross-persona synthesis.
        """
        from src.personas.registry import build_persona_profile  # noqa: PLC0415
        from src.personas.synthesis import ask_persona_synthesis, compare_personas_synthesis  # noqa: PLC0415

        n_sources = max(1, min(n_sources, _MAX_N))
        store = _get_store()
        client = _get_client()

        persona_ids = [p.strip() for p in personas.split(",") if p.strip()]
        if not persona_ids:
            # Default curated set — well-indexed personas
            persona_ids = ["andrej-karpathy", "cole-medin", "chip-huyen", "simon-willison"]
        persona_ids = persona_ids[:_MAX_COMPARE_PERSONAS]

        viewpoints = []
        for pid in persona_ids:
            profile = build_persona_profile(pid, store)
            display_name = profile.display_name if profile else pid
            hits = store.search(query=question, n_results=n_sources, persona_id=pid)
            vp = ask_persona_synthesis(
                persona_id=pid,
                display_name=display_name,
                question=question,
                hits=hits,
                client=client,
            )
            viewpoints.append(vp)

        comparison = compare_personas_synthesis(question, viewpoints, client)

        payload = json.dumps({
            "schema_version": _SCHEMA_VERSION,
            "question": question,
            "personas_compared": len(viewpoints),
            "viewpoints": [v.to_dict() for v in viewpoints],
            "comparison": comparison,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }, indent=2, ensure_ascii=False)

        _log("compare_personas", {"question": question[:80], "personas": personas}, len(payload))
        return payload

    # ------------------------------------------------------------------
    # get_consensus
    # ------------------------------------------------------------------

    @mcp.tool()
    def get_consensus(
        question: str,
        personas: str = "",
        n_sources: int = 15,
    ) -> str:
        """Get the AI community's consensus view on a question.

        Searches broadly across all indexed personas (or a specified subset),
        then synthesises the dominant view, minority positions, and unresolved
        tensions. Useful for understanding where the field broadly agrees vs
        where debates remain open.

        Args:
            question: The question or topic to find consensus on.
            personas: Optional comma-separated persona slugs to restrict the
                      search. Leave empty to search all 56+ indexed personas.
            n_sources: Total items to retrieve before synthesis (1–25, default 15).

        Returns:
            JSON with consensus, minority_views, key_tensions, agreement_level,
            agreement_reason, and personas_cited.
        """
        from src.personas.synthesis import get_consensus_synthesis  # noqa: PLC0415

        n_sources = max(1, min(n_sources, _MAX_N))
        store = _get_store()
        client = _get_client()

        if personas.strip():
            persona_ids = [p.strip() for p in personas.split(",") if p.strip()]
            all_hits: list[dict] = []
            per = max(1, n_sources // len(persona_ids))
            for pid in persona_ids:
                hits = store.search(query=question, n_results=per, persona_id=pid)
                all_hits.extend(hits)
            # Re-sort by score descending
            all_hits.sort(key=lambda h: h.get("score", 0), reverse=True)
            hits_for_synthesis = all_hits[:n_sources]
        else:
            hits_for_synthesis = store.search(query=question, n_results=n_sources)

        consensus = get_consensus_synthesis(question, hits_for_synthesis, client)

        payload = json.dumps({
            "schema_version": _SCHEMA_VERSION,
            "question": question,
            "evidence_count": len(hits_for_synthesis),
            "persona_filter": personas or None,
            **consensus,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }, indent=2, ensure_ascii=False)

        _log("get_consensus", {"question": question[:80], "personas": personas}, len(payload))
        return payload


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _log(tool: str, params: dict, result_size: int) -> None:
    try:
        from src.api.mcp_server import _log_tool_call  # noqa: PLC0415
        _log_tool_call(tool, params, result_size)
    except Exception:  # noqa: BLE001
        pass
