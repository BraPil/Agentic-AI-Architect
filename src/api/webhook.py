"""
Outbound webhook system for proactive architecture alerts.

Subscribers register a URL + optional filter (persona, tool_threshold).
When the corpus is refreshed and a new high-signal tool emerges or
an existing tool rank shifts significantly, registered endpoints receive
a structured POST payload.

Registry file: data/webhook_subscribers.json
Delivery log:  data/webhook_delivery_log.jsonl

Usage:
    from src.api.webhook import WebhookRegistry

    registry = WebhookRegistry()
    registry.register("https://example.com/hook", filters={"min_tool_mentions": 5})
    registry.notify_tool_change(new_tools=["ToolX"], rank_shifts={"Claude Code": +3})
"""

import json
import logging
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_REGISTRY_PATH = _REPO_ROOT / "data" / "webhook_subscribers.json"
_DELIVERY_LOG = _REPO_ROOT / "data" / "webhook_delivery_log.jsonl"
_SCHEMA_VERSION = "1.0"
_TIMEOUT_SECONDS = 10


class WebhookRegistry:
    """Load, manage, and fire outbound webhook notifications."""

    def __init__(self, registry_path: Path = _REGISTRY_PATH) -> None:
        self._path = registry_path
        self._subscribers: list[dict] = []
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                self._subscribers = data.get("subscribers", [])
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to load webhook registry: %s", exc)
                self._subscribers = []

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps({"schema_version": _SCHEMA_VERSION,
                        "subscribers": self._subscribers}, indent=2),
            encoding="utf-8",
        )

    def register(self, url: str, filters: dict | None = None, label: str = "") -> str:
        """Register a new webhook subscriber. Returns the subscriber ID."""
        sub_id = f"sub-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        self._subscribers.append({
            "id": sub_id,
            "url": url,
            "label": label or url,
            "filters": filters or {},
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "active": True,
        })
        self._save()
        logger.info("Webhook registered: %s → %s", sub_id, url)
        return sub_id

    def deregister(self, sub_id: str) -> bool:
        """Deactivate a subscriber by ID. Returns True if found."""
        for sub in self._subscribers:
            if sub["id"] == sub_id:
                sub["active"] = False
                self._save()
                logger.info("Webhook deregistered: %s", sub_id)
                return True
        return False

    def list_subscribers(self) -> list[dict]:
        return [s for s in self._subscribers if s.get("active", True)]

    def notify_tool_change(
        self,
        new_tools: list[str],
        rank_shifts: dict[str, int],
        corpus_size: int = 0,
    ) -> list[dict]:
        """
        Fire a tool-change alert to all active subscribers.

        Args:
            new_tools:    Tool names that newly appeared in the top-20 ranking.
            rank_shifts:  {tool_name: delta} for tools whose rank changed by >=2.
            corpus_size:  Current total indexed items count.

        Returns:
            List of delivery results (one per subscriber).
        """
        if not new_tools and not rank_shifts:
            return []

        payload = {
            "schema_version": _SCHEMA_VERSION,
            "event": "tool_change",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "corpus_size": corpus_size,
            "new_tools": new_tools,
            "rank_shifts": rank_shifts,
            "summary": _build_summary(new_tools, rank_shifts),
        }

        results = []
        for sub in self.list_subscribers():
            result = self._deliver(sub, payload)
            results.append(result)
            self._log_delivery(result)

        return results

    def _deliver(self, subscriber: dict, payload: dict) -> dict:
        """POST the payload to a single subscriber URL."""
        url = subscriber["url"]
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        result = {
            "subscriber_id": subscriber["id"],
            "url": url,
            "attempted_at": datetime.now(timezone.utc).isoformat(),
            "status": "unknown",
            "http_status": None,
            "error": None,
        }
        try:
            req = urllib.request.Request(
                url,
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "AAA-Webhook/1.0",
                    "X-AAA-Schema-Version": _SCHEMA_VERSION,
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=_TIMEOUT_SECONDS) as resp:
                result["http_status"] = resp.status
                result["status"] = "delivered" if resp.status < 300 else "failed"
        except urllib.error.HTTPError as exc:
            result["status"] = "failed"
            result["http_status"] = exc.code
            result["error"] = str(exc)
            logger.warning("Webhook delivery failed (HTTP %d): %s", exc.code, url)
        except Exception as exc:  # noqa: BLE001
            result["status"] = "error"
            result["error"] = str(exc)
            logger.warning("Webhook delivery error: %s → %s", url, exc)

        return result

    def _log_delivery(self, result: dict) -> None:
        try:
            _DELIVERY_LOG.parent.mkdir(parents=True, exist_ok=True)
            with _DELIVERY_LOG.open("a", encoding="utf-8") as f:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")
        except Exception:  # noqa: BLE001
            pass


def _build_summary(new_tools: list[str], rank_shifts: dict[str, int]) -> str:
    parts = []
    if new_tools:
        parts.append(f"New high-signal tools: {', '.join(new_tools)}")
    rising = {t: d for t, d in rank_shifts.items() if d > 0}
    falling = {t: d for t, d in rank_shifts.items() if d < 0}
    if rising:
        parts.append(f"Rising: {', '.join(f'{t} (+{d})' for t, d in rising.items())}")
    if falling:
        parts.append(f"Falling: {', '.join(f'{t} ({d})' for t, d in falling.items())}")
    return ". ".join(parts) or "No significant tool changes."
