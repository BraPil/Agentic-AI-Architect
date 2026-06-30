"""
Persona curation guard — bars non-practitioner personas from the persona store.

The store holds **only AI/tech practitioners** (standing curation rule). Personal-contact
and job-announcement personas — people the reactor knows but who do not post AI/tech
content — are pruned.

The recurring failure this module closes: pruning removed those personas from the store
but nothing barred *re-entry*, so the next LinkedIn reactions scrape silently re-ingested
them (the same off-standard class was pruned in April 2026 and re-appeared in June 2026).

This module is the persistent bar. A pruned ``persona_id`` goes on a JSON denylist; the
store consults it at ``ingest()`` and refuses re-entry. Prune-and-bar is one act
(``scripts/prune_persona.py``), so a removal can never be silently undone by a later scrape.

This module is intentionally pure (stdlib only, no ChromaDB / embedding deps) so it is
trivially testable and importable from any ingest path.

Configuration:
    AAA_PERSONA_CURATION (env): set to "0" to disable the guard entirely (kill-switch).
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Default denylist location (repo-root relative, mirroring STORE_PATH convention).
DEFAULT_DENYLIST_PATH = Path("data/curation_denylist.json")

SCHEMA_VERSION = "1.0"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class CurationEntry:
    """One barred persona and why it was barred."""

    persona_id: str
    reason: str
    blocked_at: str  # ISO-8601 date or datetime

    def to_dict(self) -> dict:
        return {
            "persona_id": self.persona_id,
            "reason": self.reason,
            "blocked_at": self.blocked_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CurationEntry":
        return cls(
            persona_id=data["persona_id"],
            reason=data.get("reason", ""),
            blocked_at=data.get("blocked_at", ""),
        )


# ---------------------------------------------------------------------------
# Curation list
# ---------------------------------------------------------------------------

class PersonaCurationList:
    """
    A persisted denylist of persona IDs barred from the persona store.

    The list is the source of truth for "this persona is not an AI/tech practitioner and
    must never be (re-)ingested." It is read at ingest time and written when a persona is
    pruned.

    Usage:
        curation = PersonaCurationList.load()
        if curation.is_blocked("kyle-faust"):
            ...  # skip ingest

        curation.block("kyle-faust", reason="job-announcement persona")
        curation.save()
    """

    def __init__(self, entries: list[CurationEntry] | None = None) -> None:
        # Keyed by persona_id so a re-block updates rather than duplicates.
        self._entries: dict[str, CurationEntry] = {}
        for entry in entries or []:
            self._entries[entry.persona_id] = entry

    # ------------------------------------------------------------------
    # Load / save
    # ------------------------------------------------------------------

    @classmethod
    def load(cls, path: str | Path = DEFAULT_DENYLIST_PATH) -> "PersonaCurationList":
        """
        Load the denylist from disk. A missing file yields an empty (inert) list — the
        guard then blocks nothing, which is the safe default for fresh checkouts and tests.
        """
        path = Path(path)
        if not path.exists():
            logger.debug("No persona denylist at %s — curation guard inert.", path)
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Could not read persona denylist %s: %s — guard inert.", path, exc)
            return cls()
        entries = [CurationEntry.from_dict(e) for e in data.get("blocked_personas", [])]
        logger.info("Persona curation guard loaded — %d barred persona(s).", len(entries))
        return cls(entries)

    def save(self, path: str | Path = DEFAULT_DENYLIST_PATH) -> None:
        """Write the denylist to disk (entries sorted by persona_id for stable diffs)."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": SCHEMA_VERSION,
            "description": (
                "Persona IDs barred from the persona store — non-practitioner / "
                "personal-contact / job-announcement personas. Enforced at "
                "LinkedInPersonaStore.ingest(). See src/pipeline/curation.py."
            ),
            "blocked_personas": [
                e.to_dict() for e in sorted(self._entries.values(), key=lambda x: x.persona_id)
            ],
        }
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # ------------------------------------------------------------------
    # Query / mutate
    # ------------------------------------------------------------------

    def is_blocked(self, persona_id: str) -> bool:
        """Return True if this persona is barred from ingest."""
        return persona_id in self._entries

    @property
    def blocked_ids(self) -> set[str]:
        """The set of all barred persona IDs."""
        return set(self._entries)

    def block(self, persona_id: str, reason: str, *, at: str | None = None) -> bool:
        """
        Add (or update) a barred persona.

        Args:
            persona_id: The slug to bar (e.g. "kyle-faust").
            reason: Why it is barred — kept for the audit trail.
            at: ISO timestamp; defaults to now (UTC date). Injectable for deterministic tests.

        Returns:
            True if this newly bars the persona; False if it was already barred (reason updated).
        """
        if not persona_id:
            raise ValueError("persona_id must be non-empty")
        is_new = persona_id not in self._entries
        stamp = at or datetime.now(timezone.utc).date().isoformat()
        self._entries[persona_id] = CurationEntry(
            persona_id=persona_id, reason=reason, blocked_at=stamp
        )
        return is_new

    def __len__(self) -> int:
        return len(self._entries)
