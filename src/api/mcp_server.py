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
You are an expert AI Architect. Given the following knowledge excerpts retrieved from a corpus \
of AI thought leaders (LinkedIn posts, YouTube transcripts, GitHub READMEs), synthesize a \
concise, actionable architecture recommendation.

PROBLEM STATEMENT:
{problem}

RETRIEVED EVIDENCE ({n} items):
{evidence}

Return a JSON object with exactly these keys:
{{
  "recommendation": "2-4 sentence primary recommendation",
  "key_considerations": ["up to 5 specific considerations or tradeoffs"],
  "relevant_tools": ["tools or frameworks mentioned in the evidence that are directly applicable"],
  "personas_cited": ["names of thought leaders whose content informed this recommendation"],
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
        author = meta.get("author", meta.get("persona_id", "unknown"))
        post_type = meta.get("post_type", "")
        score = h.get("score", 0)
        doc_snippet = h.get("document", "")[:600]
        evidence_lines.append(
            f"[{i}] {author} ({post_type}, relevance={score:.2f}):\n{doc_snippet}"
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
    for h in hits:
        meta = h.get("metadata", {})
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

    Returns:
        JSON array of matching knowledge items, each with author, content snippet,
        relevance score, post type, timestamp, and key metadata (tools, topics, claims).
    """
    n_results = max(1, min(n_results, _MAX_N))
    store = _get_store()

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
                n_results=min(n_results, max(1, total)),
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
            hits = store.search(query=query, n_results=n_results, persona_id=persona_filter_for_store)
    else:
        hits = store.search(
            query=query,
            n_results=n_results,
            persona_id=persona_filter_for_store,
        )

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

    synthesis = _synthesize(problem_statement, hits)

    evidence_summary = [
        {
            "author": h.get("metadata", {}).get("author", "unknown"),
            "post_type": h.get("metadata", {}).get("post_type"),
            "relevance_score": h.get("score"),
            "snippet": h.get("document", "")[:300],
        }
        for h in hits
    ]

    payload = json.dumps({
        "schema_version": _SCHEMA_VERSION,
        **synthesis,
        "problem_statement": problem_statement,
        "evidence_count": len(hits),
        "evidence_summary": evidence_summary,
        "generated_at": datetime.now(timezone.utc).isoformat(),
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


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")
