"""
REST API v1 — clean HTTP surface wrapping the ChromaDB persona store.

Designed for ExMorbus V3 and any HTTP client that can't use MCP stdio transport.
All responses carry schema_version for stable contract versioning.

Routes:
  GET  /v1/health
  GET  /v1/search
  GET  /v1/recommend
  GET  /v1/trending-tools
  GET  /v1/personas
  POST /v1/webhooks/register
  DELETE /v1/webhooks/{sub_id}
  GET  /v1/webhooks
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

_SCHEMA_VERSION = "1.0"
_REPO_ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# Lazy store + MCP imports (same singletons as mcp_server)
# ---------------------------------------------------------------------------

def _get_store():
    from src.api.mcp_server import _get_store as _mcp_get_store  # noqa: PLC0415
    return _mcp_get_store()


def _search(query: str, persona: str = "", n: int = 8, min_date: str = "") -> dict:
    from src.api.mcp_server import search_knowledge  # noqa: PLC0415
    return json.loads(search_knowledge(query=query, persona=persona, n_results=n, min_date=min_date))


def _recommend(problem: str, n: int = 8) -> dict:
    from src.api.mcp_server import get_architecture_recommendation  # noqa: PLC0415
    return json.loads(get_architecture_recommendation(problem_statement=problem, n_sources=n))


def _trending(top_n: int = 20, persona: str = "", post_type: str = "") -> dict:
    from src.api.mcp_server import get_trending_tools  # noqa: PLC0415
    return json.loads(get_trending_tools(top_n=top_n, persona=persona, post_type=post_type))


# ---------------------------------------------------------------------------
# Request/response models
# ---------------------------------------------------------------------------

class WebhookRegisterRequest(BaseModel):
    url: str
    label: str = ""
    filters: dict = {}


class WebhookRegisterResponse(BaseModel):
    schema_version: str
    subscriber_id: str
    url: str
    registered_at: str


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/v1", tags=["v1"])


@router.get("/health")
def health() -> dict:
    """Health check — returns store item count and API key status."""
    try:
        store = _get_store()
        count = store.count
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"Store unavailable: {exc}") from exc

    return {
        "schema_version": _SCHEMA_VERSION,
        "status": "ok",
        "corpus_size": count,
        "api_key_set": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/search")
def search(
    q: str = Query(min_length=1, description="Natural language query"),
    persona: str = Query(default="", description="Persona slug filter, e.g. andrej-karpathy"),
    n: int = Query(default=8, ge=1, le=25, description="Max results"),
    min_date: str = Query(default="", description="ISO date lower bound, e.g. 2025-01-01"),
) -> dict:
    """Semantic search across all indexed content."""
    return _search(q, persona=persona, n=n, min_date=min_date)


@router.get("/recommend")
def recommend(
    problem: str = Query(min_length=10, description="Architecture problem or question"),
    n: int = Query(default=8, ge=1, le=25, description="Sources to retrieve before synthesis"),
) -> dict:
    """Get a Claude-synthesized architecture recommendation with cited sources."""
    return _recommend(problem, n=n)


@router.get("/trending-tools")
def trending_tools(
    top_n: int = Query(default=20, ge=1, le=100, description="How many tools to return"),
    persona: str = Query(default="", description="Filter to a specific persona"),
    post_type: str = Query(default="", description="Filter by content type"),
) -> dict:
    """Get the most frequently mentioned AI tools across all indexed content."""
    return _trending(top_n=top_n, persona=persona, post_type=post_type)


@router.get("/personas")
def personas() -> dict:
    """List all indexed author personas with item counts."""
    store = _get_store()
    persona_list = store.get_personas()
    return {
        "schema_version": _SCHEMA_VERSION,
        "total_personas": len(persona_list),
        "personas": persona_list,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/webhooks/register", response_model=WebhookRegisterResponse)
def register_webhook(body: WebhookRegisterRequest) -> dict:
    """Register a URL to receive proactive tool-change alerts."""
    from src.api.webhook import WebhookRegistry  # noqa: PLC0415
    registry = WebhookRegistry()
    sub_id = registry.register(url=body.url, filters=body.filters, label=body.label)
    return {
        "schema_version": _SCHEMA_VERSION,
        "subscriber_id": sub_id,
        "url": body.url,
        "registered_at": datetime.now(timezone.utc).isoformat(),
    }


@router.delete("/webhooks/{sub_id}")
def deregister_webhook(sub_id: str) -> dict:
    """Deactivate a webhook subscriber."""
    from src.api.webhook import WebhookRegistry  # noqa: PLC0415
    registry = WebhookRegistry()
    found = registry.deregister(sub_id)
    if not found:
        raise HTTPException(status_code=404, detail=f"Subscriber not found: {sub_id}")
    return {"schema_version": _SCHEMA_VERSION, "deregistered": sub_id}


@router.get("/webhooks")
def list_webhooks() -> dict:
    """List all active webhook subscribers."""
    from src.api.webhook import WebhookRegistry  # noqa: PLC0415
    registry = WebhookRegistry()
    subs = registry.list_subscribers()
    return {
        "schema_version": _SCHEMA_VERSION,
        "total": len(subs),
        "subscribers": [{"id": s["id"], "url": s["url"], "label": s["label"],
                          "registered_at": s["registered_at"]} for s in subs],
    }
