"""
Tests for the persona curation guard (src/pipeline/curation.py) and its enforcement in
LinkedInPersonaStore.ingest().

No network, no API keys, no ChromaDB — the store's collection is mocked.
"""

import json
from unittest.mock import MagicMock

import pytest

from src.pipeline.curation import (
    DEFAULT_DENYLIST_PATH,
    CurationEntry,
    PersonaCurationList,
)
from src.pipeline.linkedin_persona_store import LinkedInPersonaStore, PostRecord


# ---------------------------------------------------------------------------
# PersonaCurationList — pure unit tests
# ---------------------------------------------------------------------------

class TestPersonaCurationList:
    def test_empty_list_blocks_nothing(self):
        curation = PersonaCurationList()
        assert not curation.is_blocked("anyone")
        assert curation.blocked_ids == set()
        assert len(curation) == 0

    def test_block_adds_persona(self):
        curation = PersonaCurationList()
        newly = curation.block("kyle-faust", reason="job-announcement", at="2026-06-29")
        assert newly is True
        assert curation.is_blocked("kyle-faust")
        assert curation.blocked_ids == {"kyle-faust"}

    def test_block_existing_returns_false_and_updates(self):
        curation = PersonaCurationList([
            CurationEntry("kyle-faust", "old reason", "2026-04-01")
        ])
        newly = curation.block("kyle-faust", reason="new reason", at="2026-06-29")
        assert newly is False
        assert len(curation) == 1  # no duplicate

    def test_block_empty_persona_raises(self):
        with pytest.raises(ValueError):
            PersonaCurationList().block("", reason="x")

    def test_load_missing_file_is_inert(self, tmp_path):
        curation = PersonaCurationList.load(tmp_path / "does_not_exist.json")
        assert len(curation) == 0
        assert not curation.is_blocked("anyone")

    def test_load_malformed_file_is_inert(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not valid json", encoding="utf-8")
        curation = PersonaCurationList.load(bad)
        assert len(curation) == 0

    def test_save_then_load_roundtrip(self, tmp_path):
        path = tmp_path / "denylist.json"
        curation = PersonaCurationList()
        curation.block("kyle-faust", reason="job-announcement", at="2026-06-29")
        curation.block("ans", reason="personal contact", at="2026-04-01")
        curation.save(path)

        reloaded = PersonaCurationList.load(path)
        assert reloaded.blocked_ids == {"kyle-faust", "ans"}
        assert reloaded.is_blocked("ans")

    def test_save_sorts_entries_for_stable_diffs(self, tmp_path):
        path = tmp_path / "denylist.json"
        curation = PersonaCurationList()
        curation.block("zeta", reason="x", at="2026-01-01")
        curation.block("alpha", reason="x", at="2026-01-01")
        curation.save(path)
        data = json.loads(path.read_text())
        ids = [e["persona_id"] for e in data["blocked_personas"]]
        assert ids == ["alpha", "zeta"]


# ---------------------------------------------------------------------------
# Shipped denylist sanity
# ---------------------------------------------------------------------------

class TestShippedDenylist:
    def test_known_offenders_are_barred(self):
        """The four June re-entrants must be on the shipped denylist."""
        curation = PersonaCurationList.load(DEFAULT_DENYLIST_PATH)
        for pid in ("kyle-faust", "paul-northrup-pe", "matt-luke", "anthony-smith-mba-sta"):
            assert curation.is_blocked(pid), f"{pid} should be barred"


# ---------------------------------------------------------------------------
# Store enforcement
# ---------------------------------------------------------------------------

def _make_record(persona_id: str) -> PostRecord:
    return PostRecord(
        post_id=f"li-{persona_id}-1",
        persona_id=persona_id,
        author=persona_id.replace("-", " ").title(),
        author_url="",
        post_url="https://example.com/post",
        text="A substantive post about agentic AI architecture and evaluation.",
        timestamp="2026-06-01",
        post_type="text",
        image_count=0,
        image_descriptions=[],
        reactor_persona_id="brandtpileggi",
        scraped_at="2026-06-30",
    )


def _initialized_store(curation: PersonaCurationList) -> LinkedInPersonaStore:
    store = LinkedInPersonaStore(curation=curation)
    store._collection = MagicMock()
    store._collection.add.return_value = None
    store._initialized = True
    return store


class TestStoreEnforcement:
    def test_blocked_persona_is_not_ingested(self):
        curation = PersonaCurationList([CurationEntry("kyle-faust", "barred", "2026-06-29")])
        store = _initialized_store(curation)

        added = store.ingest(_make_record("kyle-faust"))

        assert added is False
        store._collection.add.assert_not_called()

    def test_allowed_persona_is_ingested(self):
        curation = PersonaCurationList([CurationEntry("kyle-faust", "barred", "2026-06-29")])
        store = _initialized_store(curation)

        added = store.ingest(_make_record("andrej-karpathy"))

        assert added is True
        store._collection.add.assert_called_once()

    def test_kill_switch_disables_guard(self, monkeypatch):
        """AAA_PERSONA_CURATION=0 makes the guard inert even with a populated denylist."""
        monkeypatch.setenv("AAA_PERSONA_CURATION", "0")
        store = LinkedInPersonaStore()  # loads inert list because env disables it
        store._collection = MagicMock()
        store._initialized = True

        added = store.ingest(_make_record("kyle-faust"))

        assert added is True
        store._collection.add.assert_called_once()

    def test_prune_persona_deletes_indexed_posts(self):
        store = LinkedInPersonaStore(curation=PersonaCurationList())
        store._collection = MagicMock()
        store._collection.get.return_value = {"ids": ["li-1", "li-2"]}
        store._initialized = True

        deleted = store.prune_persona("kyle-faust")

        assert deleted == 2
        store._collection.delete.assert_called_once_with(ids=["li-1", "li-2"])
