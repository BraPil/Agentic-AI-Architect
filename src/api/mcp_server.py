"""
MCP server for Agentic AI Architect — exposes the persona intelligence store
to Claude and any MCP-compliant client.

Tools:
  search_knowledge              — semantic search across all indexed content
  get_architecture_recommendation — synthesize top results into a structured recommendation
  get_trending_tools            — most-mentioned tools across the knowledge base

Transport: stdio (default for Claude Desktop integration).

Usage:
  python -m src.api.mcp_server          # stdio transport (Claude Desktop)

Registration (Claude Desktop):
  Add to ~/Library/Application Support/Claude/claude_desktop_config.json:
  {
    "mcpServers": {
      "aaa": {
        "command": "python",
        "args": ["-m", "src.api.mcp_server"],
        "cwd": "/path/to/Agentic-AI-Architect"
      }
    }
  }
"""

import json
import logging
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# Make the repo root importable when run as __main__
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

_STORE_PATH = _REPO_ROOT / "data" / "linkedin_store"
_USAGE_LOG = _REPO_ROOT / "data" / "mcp_usage.jsonl"
_DEFAULT_N = 8
_DEFAULT_TOP_TOOLS = 20
_MAX_N = 25
_SYNTHESIS_MODEL = "claude-haiku-4-5-20251001"
_SYNTHESIS_MAX_TOKENS = 1024
_SCHEMA_VERSION = "1.0"

# ---------------------------------------------------------------------------
# Lazy store singleton (initialized on first use, cached for < 200 ms latency)
# ---------------------------------------------------------------------------

_store = None


def _get_store():
    global _store
    if _store is None:
        from src.pipeline.linkedin_persona_store import LinkedInPersonaStore
        _store = LinkedInPersonaStore(store_path=_STORE_PATH)
        _store.initialize()
    return _store


# ---------------------------------------------------------------------------
# Usage logging
# ---------------------------------------------------------------------------

def _log_tool_call(tool: str, params: dict, result_size: int) -> None:
    """Append a structured tool-call record to the usage log."""
    try:
        _USAGE_LOG.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "tool": tool,
            "params": params,
            "result_bytes": result_size,
        }
        with _USAGE_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        pass  # Never let logging break a tool call


_OUTCOME_LEDGER = _REPO_ROOT / "data" / "recommendation_outcomes.jsonl"

# Kill-switch for the P6 slice-2 outcome re-ranking. On by default; set
# AAA_OUTCOME_WEIGHTING=0 to fall back to pure semantic order (used by the
# before/after eval comparison and as an operational safety valve).
_OUTCOME_WEIGHTING_ENABLED = os.environ.get("AAA_OUTCOME_WEIGHTING", "1").lower() not in (
    "0", "false", "no", "off",
)


def _apply_outcome_weighting(hits: list[dict]) -> tuple[list[dict], dict]:
    """Re-rank retrieval hits by recorded outcome signal (P6 slice 2).

    Sources whose past recommendations were adopted-and-worked rank higher;
    those adopted-and-failed rank lower — but only once an entity has cleared the
    minimum-evidence gate, so a small ledger leaves ranking untouched.

    Best-effort: any failure (or the kill-switch) returns the hits unchanged so
    the recommendation path never breaks on the learning layer.
    """
    status: dict = {"active": False, "enabled": _OUTCOME_WEIGHTING_ENABLED,
                    "min_evidence": None, "gated_personas": 0, "gated_tools": 0}
    if not _OUTCOME_WEIGHTING_ENABLED or not hits:
        return hits, status
    try:
        from src.learning.outcomes import RecommendationOutcomeStore  # noqa: PLC0415
        from src.learning.outcome_weighting import (  # noqa: PLC0415
            MIN_EVIDENCE_DEFAULT, gated_multipliers, rerank_by_outcomes,
        )
        agg = RecommendationOutcomeStore(_OUTCOME_LEDGER).aggregate()
        persona_signal = agg.get("persona_signal", {})
        tool_signal = agg.get("tool_signal", {})
        gated_p = gated_multipliers(persona_signal, MIN_EVIDENCE_DEFAULT)
        gated_t = gated_multipliers(tool_signal, MIN_EVIDENCE_DEFAULT)
        status.update(min_evidence=MIN_EVIDENCE_DEFAULT, gated_personas=len(gated_p),
                      gated_tools=len(gated_t), active=bool(gated_p or gated_t))
        reranked = rerank_by_outcomes(hits, persona_signal, tool_signal, MIN_EVIDENCE_DEFAULT)
        return reranked, status
    except Exception:  # noqa: BLE001
        logger.warning("Outcome weighting failed; falling back to semantic order")
        return hits, status


def _record_recommendation_event(problem_statement: str, generated_at: str,
                                 synthesis: dict) -> str:
    """Stamp + log a recommendation so its outcome can later be tied back.

    Returns the recommendation_id. Best-effort: any failure degrades to returning
    the id without a ledger entry, never raising into the tool path.
    """
    from src.learning.outcomes import (  # noqa: PLC0415
        RecommendationOutcomeStore, compute_recommendation_id,
    )
    rec_id = compute_recommendation_id(problem_statement, generated_at)
    try:
        RecommendationOutcomeStore(_OUTCOME_LEDGER).record_recommendation(
            recommendation_id=rec_id,
            problem_statement=problem_statement,
            personas_cited=synthesis.get("personas_cited") or [],
            tools=synthesis.get("relevant_tools") or [],
            confidence=str(synthesis.get("confidence", "")),
        )
    except Exception:  # noqa: BLE001
        logger.warning("Failed to log recommendation event %s", rec_id)
    return rec_id


# ---------------------------------------------------------------------------
# Synthesis helper (Claude Haiku)
# ---------------------------------------------------------------------------

_anthropic_client = None


def _get_anthropic():
    global _anthropic_client
    if _anthropic_client is None:
        try:
            import anthropic
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                return None
            _anthropic_client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            return None
    return _anthropic_client


_SYNTHESIS_PROMPT = """\
You are an expert AI Architect. Given the following knowledge excerpts, synthesize a \
concise, actionable architecture recommendation.

The evidence comes from two distinct tiers, and you must treat them differently:
- EXTERNAL items are content from AI thought leaders (LinkedIn posts, blogs, YouTube, \
GitHub, arXiv). These are independent authority.
- "AAA INTERNAL PRIOR" items are this system's OWN past decisions, discoveries, and lessons. \
They are institutional memory, NOT external authority. Use them to stay consistent with prior \
decisions and to avoid repeating known mistakes — but do NOT cite them as if an outside expert \
said them, and do NOT list them under personas_cited.

PROBLEM STATEMENT:
{problem}

RETRIEVED EVIDENCE ({n} items):
{evidence}

Return a JSON object with exactly these keys:
{{
  "recommendation": "2-4 sentence primary recommendation",
  "key_considerations": ["up to 5 specific considerations or tradeoffs"],
  "relevant_tools": ["tools or frameworks mentioned in the evidence that are directly applicable"],
  "personas_cited": ["names of EXTERNAL thought leaders only — never 'Agentic AI Architect'"],
  "internal_priors_applied": ["brief note of any AAA INTERNAL PRIOR items that shaped this answer"],
  "confidence": "high | medium | low",
  "confidence_reason": "one sentence"
}}

Return only valid JSON. No markdown fences."""


def _synthesize(problem: str, hits: list[dict]) -> dict:
    """Call Claude Haiku to synthesize search results into a recommendation."""
    client = _get_anthropic()
    if client is None:
        return _fallback_synthesis(problem, hits)

    evidence_lines = []
    for i, h in enumerate(hits, 1):
        meta = h.get("metadata", {})
        post_type = meta.get("post_type", "")
        score = h.get("score", 0)
        doc_snippet = h.get("document", "")[:600]
        tier = meta.get("source_tier", "")
        if tier == "internal" or post_type == "project_learning":
            lt = meta.get("learning_type", "note")
            label = f"AAA INTERNAL PRIOR ({lt})"
        elif tier == "experimental":
            label = "EXPERIMENTAL (unpromoted agent artifact — treat as a hypothesis, not authority)"
        elif tier == "grounded":
            label = "AAA GROUNDED (human-promoted agent artifact)"
        else:
            author = meta.get("author", meta.get("persona_id", "unknown"))
            label = f"{author} ({post_type})"
        evidence_lines.append(
            f"[{i}] {label}, relevance={score:.2f}:\n{doc_snippet}"
        )

    prompt = _SYNTHESIS_PROMPT.format(
        problem=problem,
        n=len(hits),
        evidence="\n\n".join(evidence_lines),
    )

    try:
        msg = client.messages.create(
            model=_SYNTHESIS_MODEL,
            max_tokens=_SYNTHESIS_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        return json.loads(raw)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Synthesis failed: %s — using fallback", exc)
        return _fallback_synthesis(problem, hits)


def _fallback_synthesis(problem: str, hits: list[dict]) -> dict:
    """Return a structured fallback when Claude is unavailable."""
    tools: list[str] = []
    personas: list[str] = []
    internal_priors: list[str] = []
    for h in hits:
        meta = h.get("metadata", {})
        # Only external content counts as a cited persona. Internal priors and
        # agent-generated artifacts (experimental/grounded) are never external authority.
        non_external = (meta.get("source_tier") in ("internal", "experimental", "grounded")
                        or meta.get("post_type") in ("project_learning", "learning_artifact"))
        if non_external:
            title = meta.get("title", "") or h.get("document", "")[:80]
            internal_priors.append(title[:80])
        else:
            author = meta.get("author", "")
            if author:
                personas.append(author)
        for t in meta.get("mentioned_tools", "").split(","):
            t = t.strip()
            if t:
                tools.append(t)

    top_tools = list(dict.fromkeys(tools))[:5]
    top_personas = list(dict.fromkeys(personas))[:5]

    snippets = [h.get("document", "")[:200] for h in hits[:3]]
    summary = " | ".join(s.strip() for s in snippets if s.strip())

    return {
        "recommendation": (
            f"Based on {len(hits)} retrieved knowledge items relevant to your problem, "
            f"the following themes emerged: {summary[:300]}"
        ),
        "key_considerations": [
            "Review the raw search results for full context.",
            "Set ANTHROPIC_API_KEY for AI-synthesized recommendations.",
        ],
        "relevant_tools": top_tools,
        "personas_cited": top_personas,
        "internal_priors_applied": list(dict.fromkeys(internal_priors))[:5],
        "confidence": "low",
        "confidence_reason": "No LLM synthesis available — raw retrieval only.",
    }


# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="Agentic AI Architect",
    instructions=(
        "This server provides access to a curated knowledge base of AI architecture intelligence, "
        "built from LinkedIn posts, YouTube transcripts, blog posts, and GitHub READMEs by leading "
        "AI practitioners (Andrej Karpathy, Cole Medin, Chip Huyen, Simon Willison, Lilian Weng, "
        "and 50+ others). "
        "Use search_knowledge to find relevant insights, get_architecture_recommendation for "
        "synthesized guidance on a specific problem, and get_trending_tools to see what tools "
        "the AI community is actively discussing."
    ),
)


@mcp.tool()
def search_knowledge(
    query: str,
    persona: str = "",
    n_results: int = _DEFAULT_N,
    min_date: str = "",
    include_experimental: bool = False,
) -> str:
    """Search the AI architecture knowledge base using semantic similarity.

    Args:
        query: Natural language query — what you want to know about AI architecture,
               tools, workflows, or best practices.
        persona: Optional. Filter results to a specific thought leader.
                 Examples: "andrej-karpathy", "cole-medin", "chip-huyen".
                 Leave empty to search across all personas.
        n_results: Number of results to return (1–25, default 8).
        min_date: Optional. Only return content published on or after this date.
                  Format: YYYY-MM-DD (e.g. "2025-01-01"). Leave empty for all dates.
        include_experimental: Include unpromoted agent-generated artifacts (the
                  quarantined `experimental` tier). Default False — these are NOT
                  trusted knowledge and must be reviewed via the promotion tools first.

    Returns:
        JSON array of matching knowledge items, each with author, content snippet,
        relevance score, post type, timestamp, and key metadata (tools, topics, claims).
    """
    n_results = max(1, min(n_results, _MAX_N))
    store = _get_store()
    # Over-fetch when quarantining so post-filtering doesn't starve the result set.
    fetch_n = n_results if include_experimental else min(_MAX_N, n_results + 10)

    # Build optional date filter for ChromaDB where clause
    date_filter: dict | None = None
    if min_date.strip():
        date_filter = {"timestamp": {"$gte": min_date.strip()}}

    # Combine persona filter with date filter
    persona_filter = persona.strip() or None
    if date_filter and persona_filter:
        where = {"$and": [{"persona_id": persona_filter}, date_filter]}
        persona_filter_for_store = None  # handled in where
    elif date_filter:
        where = date_filter
        persona_filter_for_store = None
    else:
        where = None
        persona_filter_for_store = persona_filter

    if where:
        try:
            total = store._collection.count()
            raw = store._collection.query(
                query_texts=[query],
                n_results=min(fetch_n, max(1, total)),
                where=where,
                include=["documents", "metadatas", "distances"],
            )
            hits = [
                {
                    "post_id": raw["ids"][0][i],
                    "document": raw["documents"][0][i],
                    "metadata": raw["metadatas"][0][i],
                    "score": round(1.0 - raw["distances"][0][i], 4),
                }
                for i in range(len(raw["ids"][0]))
            ]
        except Exception as exc:  # noqa: BLE001
            logger.warning("Date-filtered search failed (%s) — falling back to unfiltered", exc)
            hits = store.search(query=query, n_results=fetch_n,
                                persona_id=persona_filter_for_store,
                                include_experimental=include_experimental)
    else:
        hits = store.search(
            query=query,
            n_results=fetch_n,
            persona_id=persona_filter_for_store,
            include_experimental=include_experimental,
        )

    # Quarantine: drop unpromoted agent-generated artifacts unless explicitly requested.
    if not include_experimental:
        hits = [h for h in hits
                if h.get("metadata", {}).get("source_tier") != "experimental"]
    hits = hits[:n_results]

    results = []
    for h in hits:
        meta = h.get("metadata", {})
        results.append({
            "post_id": h.get("post_id"),
            "author": meta.get("author", meta.get("persona_id", "unknown")),
            "persona_id": meta.get("persona_id"),
            "post_type": meta.get("post_type"),
            "timestamp": meta.get("timestamp") or meta.get("scraped_at"),
            "relevance_score": h.get("score"),
            "snippet": h.get("document", "")[:500],
            "mentioned_tools": [t.strip() for t in meta.get("mentioned_tools", "").split(",") if t.strip()],
            "topics": [t.strip() for t in meta.get("topics", "").split(",") if t.strip()],
            "summary": meta.get("summary", ""),
            "post_url": meta.get("post_url", ""),
        })

    payload = json.dumps({
        "schema_version": _SCHEMA_VERSION,
        "query": query,
        "persona_filter": persona or None,
        "min_date_filter": min_date or None,
        "total_results": len(results),
        "results": results,
    }, indent=2, ensure_ascii=False)

    _log_tool_call("search_knowledge", {"query": query, "persona": persona, "n_results": n_results,
                                         "min_date": min_date}, len(payload))
    return payload


@mcp.tool()
def get_architecture_recommendation(
    problem_statement: str,
    n_sources: int = _DEFAULT_N,
) -> str:
    """Get a synthesized AI architecture recommendation for a specific problem.

    Searches the knowledge base for relevant insights from leading AI practitioners,
    then uses Claude to synthesize a structured recommendation with cited sources.

    Args:
        problem_statement: Describe the architecture problem, decision, or question.
                           Examples:
                           - "How should I design memory for a multi-agent system?"
                           - "What's the best approach for agentic coding workflows?"
                           - "Should I use RAG or fine-tuning for domain adaptation?"
        n_sources: Number of knowledge items to retrieve before synthesis (1–25, default 8).

    Returns:
        JSON object with: recommendation, key_considerations, relevant_tools,
        personas_cited, confidence, and the raw evidence used.
    """
    n_sources = max(1, min(n_sources, _MAX_N))
    store = _get_store()

    hits = store.search(query=problem_statement, n_results=n_sources)
    if not hits:
        payload = json.dumps({
            "recommendation": "No relevant knowledge found for this problem statement.",
            "key_considerations": [],
            "relevant_tools": [],
            "personas_cited": [],
            "confidence": "low",
            "confidence_reason": "Knowledge base returned no results.",
            "evidence_count": 0,
        }, indent=2)
        _log_tool_call("get_architecture_recommendation",
                       {"problem_statement": problem_statement[:100], "n_sources": n_sources},
                       len(payload))
        return payload

    # P6 slice 2: re-rank by recorded outcome signal before synthesis so proven
    # sources lead the evidence the synthesizer sees. No-op until an entity
    # clears the minimum-evidence gate.
    hits, outcome_weighting = _apply_outcome_weighting(hits)

    synthesis = _synthesize(problem_statement, hits)

    evidence_summary = [
        {
            "author": h.get("metadata", {}).get("author", "unknown"),
            "post_type": h.get("metadata", {}).get("post_type"),
            "relevance_score": h.get("score"),
            "outcome_multiplier": h.get("outcome_multiplier", 1.0),
            "snippet": h.get("document", "")[:300],
        }
        for h in hits
    ]

    # P6 outcome capture: stamp a stable id and log the recommendation event so an
    # outcome (adopted? worked?) can later be tied back. Best-effort — must never
    # break the recommendation itself.
    generated_at = datetime.now(timezone.utc).isoformat()
    recommendation_id = _record_recommendation_event(problem_statement, generated_at, synthesis)

    payload = json.dumps({
        "schema_version": _SCHEMA_VERSION,
        "recommendation_id": recommendation_id,
        **synthesis,
        "problem_statement": problem_statement,
        "evidence_count": len(hits),
        "evidence_summary": evidence_summary,
        "outcome_weighting": outcome_weighting,
        "generated_at": generated_at,
        "outcome_hint": "Record what happened with record_recommendation_outcome("
                        f"'{recommendation_id}', adopted=…, worked=…) to teach AAA.",
    }, indent=2, ensure_ascii=False)

    _log_tool_call("get_architecture_recommendation",
                   {"problem_statement": problem_statement[:100], "n_sources": n_sources},
                   len(payload))
    return payload


@mcp.tool()
def get_trending_tools(
    top_n: int = _DEFAULT_TOP_TOOLS,
    persona: str = "",
    post_type: str = "",
) -> str:
    """Get the most frequently mentioned AI tools across the knowledge base.

    Analyzes all indexed content to surface which tools, frameworks, and platforms
    the AI community is actively discussing and recommending.

    Args:
        top_n: How many top tools to return (default 20).
        persona: Optional. Restrict to a specific thought leader's mentions.
                 Examples: "andrej-karpathy", "cole-medin".
        post_type: Optional. Filter by content type: "youtube_transcript",
                   "github_readme", "blog_post", "text", "article".

    Returns:
        JSON object with ranked tool list (name, mention_count, mentioned_by personas),
        plus total indexed items analyzed.
    """
    store = _get_store()

    if persona.strip():
        items = store.get_posts_by_persona(persona.strip())
    else:
        items = _get_all_items(store)

    if post_type.strip():
        items = [i for i in items if i.get("metadata", {}).get("post_type") == post_type.strip()]

    # Community trend signal must reflect EXTERNAL discourse only. Exclude AAA's own
    # internal project learnings AND agent-generated artifacts (experimental/grounded) —
    # they are self-references, not community signal. Include only if explicitly requested.
    explicitly_internal = (post_type.strip() in ("project_learning", "learning_artifact")
                           or persona.strip() in ("aaa_project", "oaa_agent"))
    if not explicitly_internal:
        items = [
            i for i in items
            if i.get("metadata", {}).get("source_tier") not in ("internal", "experimental", "grounded")
            and i.get("metadata", {}).get("post_type") not in ("project_learning", "learning_artifact")
        ]

    tool_counter: Counter = Counter()
    tool_personas: dict[str, set] = {}

    for item in items:
        meta = item.get("metadata", {})
        author = meta.get("author", meta.get("persona_id", "unknown"))
        tools_str = meta.get("mentioned_tools", "")
        for tool in tools_str.split(","):
            tool = tool.strip()
            if not tool:
                continue
            tool_counter[tool] += 1
            tool_personas.setdefault(tool, set()).add(author)

    ranked = [
        {
            "tool": tool,
            "mention_count": count,
            "mentioned_by": sorted(tool_personas[tool]),
            "persona_count": len(tool_personas[tool]),
        }
        for tool, count in tool_counter.most_common(top_n)
    ]

    payload = json.dumps({
        "schema_version": _SCHEMA_VERSION,
        "total_items_analyzed": len(items),
        "unique_tools_found": len(tool_counter),
        "persona_filter": persona or None,
        "post_type_filter": post_type or None,
        "top_tools": ranked,
    }, indent=2, ensure_ascii=False)

    _log_tool_call("get_trending_tools",
                   {"top_n": top_n, "persona": persona, "post_type": post_type},
                   len(payload))
    return payload


def _get_all_items(store) -> list[dict]:
    """Retrieve all items from the store for aggregation."""
    try:
        result = store._collection.get(include=["documents", "metadatas"])
        return [
            {"post_id": pid, "document": doc, "metadata": meta}
            for pid, doc, meta in zip(
                result["ids"], result["documents"], result["metadatas"]
            )
        ]
    except Exception:  # noqa: BLE001
        return []


# ---------------------------------------------------------------------------
# Persona tools (ask_persona, compare_personas, get_consensus)
# ---------------------------------------------------------------------------

try:
    from src.api.persona_tools import register_persona_tools  # noqa: PLC0415
    register_persona_tools(mcp)
except Exception as _persona_exc:  # noqa: BLE001
    logger.warning("Persona tools not loaded: %s", _persona_exc)

try:
    from src.api.learning_tools import register_learning_tools  # noqa: PLC0415
    register_learning_tools(mcp)
except Exception as _learning_exc:  # noqa: BLE001
    logger.warning("Learning tools not loaded: %s", _learning_exc)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")
