"""
Tests for the persona layer — models, registry, synthesis, and MCP tools.

All tests run without an API key (no network calls, no LLM calls).
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.personas.models import PersonaProfile, PersonaViewpoint
from src.personas.synthesis import (
    _extract_tools,
    _strip_fences,
    ask_persona_synthesis,
    compare_personas_synthesis,
    get_consensus_synthesis,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_hit(author="Test Author", persona_id="test-persona", post_type="blog_post",
              score=0.8, text="Some insight about AI agents.", tools="Claude,LangChain"):
    return {
        "post_id": "test-001",
        "document": text,
        "score": score,
        "metadata": {
            "author": author,
            "persona_id": persona_id,
            "post_type": post_type,
            "mentioned_tools": tools,
            "timestamp": "2025-06-01",
        },
    }


def _make_viewpoint(**kwargs) -> PersonaViewpoint:
    defaults = dict(
        persona_id="test-persona",
        display_name="Test Author",
        viewpoint="They value pragmatic tooling.",
        key_points=["Uses Claude", "Prefers simple pipelines"],
        relevant_tools=["Claude"],
        confidence="medium",
        confidence_reason="Moderate evidence.",
        sources_used=3,
        provenance=[],
    )
    defaults.update(kwargs)
    return PersonaViewpoint(**defaults)


# ---------------------------------------------------------------------------
# PersonaProfile
# ---------------------------------------------------------------------------

class TestPersonaProfile:
    def test_to_dict_keys(self):
        p = PersonaProfile(
            persona_id="foo-bar",
            display_name="Foo Bar",
            item_count=10,
            content_types=["blog_post"],
            top_topics=["agents"],
            top_tools=["Claude"],
            date_range=("2024-01-01", "2025-06-01"),
        )
        d = p.to_dict()
        assert d["persona_id"] == "foo-bar"
        assert d["item_count"] == 10
        assert "earliest_item" in d and "latest_item" in d


class TestPersonaViewpoint:
    def test_to_dict_roundtrip(self):
        vp = _make_viewpoint()
        d = vp.to_dict()
        assert d["confidence"] == "medium"
        assert "provenance" in d


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class TestRegistry:
    def _mock_store(self, metas=None):
        store = MagicMock()
        ids = ["id-1", "id-2"] if metas else []
        store._collection.get.return_value = {
            "ids": ids,
            "metadatas": metas or [],
        }
        store.get_personas.return_value = [{"persona_id": "test-persona"}]
        return store

    def test_build_profile_returns_none_for_unknown(self):
        from src.personas.registry import build_persona_profile
        store = self._mock_store(metas=[])
        result = build_persona_profile("nonexistent", store)
        assert result is None

    def test_build_profile_derives_display_name(self):
        from src.personas.registry import build_persona_profile
        metas = [
            {"author": "Jane Smith", "post_type": "blog_post", "topics": "agents,RAG",
             "mentioned_tools": "Claude", "timestamp": "2025-01-01"},
        ]
        store = self._mock_store(metas=metas)
        profile = build_persona_profile("jane-smith", store)
        assert profile is not None
        assert profile.display_name == "Jane Smith"
        assert "blog_post" in profile.content_types
        assert "Claude" in profile.top_tools

    def test_build_profile_date_range(self):
        from src.personas.registry import build_persona_profile
        metas = [
            {"author": "A", "post_type": "text", "topics": "", "mentioned_tools": "",
             "timestamp": "2024-03-01"},
            {"author": "A", "post_type": "text", "topics": "", "mentioned_tools": "",
             "timestamp": "2025-07-15"},
        ]
        store = self._mock_store(metas=metas)
        profile = build_persona_profile("a", store)
        assert profile.date_range == ("2024-03-01", "2025-07-15")


# ---------------------------------------------------------------------------
# Synthesis helpers
# ---------------------------------------------------------------------------

class TestSynthesisHelpers:
    def test_strip_fences_no_fences(self):
        assert _strip_fences('{"a": 1}') == '{"a": 1}'

    def test_strip_fences_json_fence(self):
        fenced = "```json\n{\"a\": 1}\n```"
        result = _strip_fences(fenced)
        assert result == '{"a": 1}'

    def test_strip_fences_plain_fence(self):
        fenced = "```\n{\"b\": 2}\n```"
        result = _strip_fences(fenced)
        assert result == '{"b": 2}'

    def test_extract_tools_deduplicates(self):
        hits = [
            _make_hit(tools="Claude,LangChain"),
            _make_hit(tools="Claude,OpenAI"),
        ]
        tools = _extract_tools(hits)
        assert tools.count("Claude") == 1
        assert "LangChain" in tools
        assert "OpenAI" in tools


# ---------------------------------------------------------------------------
# ask_persona_synthesis — no-client fallback
# ---------------------------------------------------------------------------

class TestAskPersonaSynthesis:
    def test_no_client_returns_low_confidence(self):
        hits = [_make_hit()]
        result = ask_persona_synthesis("test", "Test Author", "What about agents?", hits, client=None)
        assert result.confidence in ("low", "insufficient")
        assert result.sources_used == 1

    def test_no_hits_returns_insufficient(self):
        result = ask_persona_synthesis("test", "Test Author", "anything", hits=[], client=None)
        assert result.confidence == "insufficient"

    def test_client_called_with_hits(self):
        hits = [_make_hit()]
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "viewpoint": "They like agents.",
            "key_points": ["point 1"],
            "relevant_tools": ["Claude"],
            "confidence": "high",
            "confidence_reason": "Strong evidence.",
        }))]
        mock_client.messages.create.return_value = mock_response

        result = ask_persona_synthesis("test", "Test Author", "What about agents?", hits, mock_client)
        assert result.confidence == "high"
        assert result.viewpoint == "They like agents."
        assert mock_client.messages.create.called

    def test_client_failure_falls_back_gracefully(self):
        hits = [_make_hit()]
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = RuntimeError("API error")

        result = ask_persona_synthesis("test", "Test Author", "question?", hits, mock_client)
        assert result.confidence == "low"
        assert "Synthesis failed" in result.viewpoint


# ---------------------------------------------------------------------------
# compare_personas_synthesis — no-client fallback
# ---------------------------------------------------------------------------

class TestComparePersonasSynthesis:
    def test_no_client_returns_unique_perspectives(self):
        vps = [_make_viewpoint(persona_id="a"), _make_viewpoint(persona_id="b")]
        result = compare_personas_synthesis("question?", vps, client=None)
        assert "a" in result["unique_perspectives"]
        assert "b" in result["unique_perspectives"]

    def test_client_called(self):
        vps = [_make_viewpoint()]
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "agreements": ["agree1"],
            "disagreements": [],
            "unique_perspectives": {"test-persona": "unique view"},
            "synthesis": "Overall they agree.",
        }))]
        mock_client.messages.create.return_value = mock_response

        result = compare_personas_synthesis("question?", vps, mock_client)
        assert result["agreements"] == ["agree1"]


# ---------------------------------------------------------------------------
# get_consensus_synthesis — no-client fallback
# ---------------------------------------------------------------------------

class TestGetConsensusSynthesis:
    def test_no_client_returns_personas_cited(self):
        hits = [_make_hit(author="Alice"), _make_hit(author="Bob")]
        result = get_consensus_synthesis("question?", hits, client=None)
        assert "Alice" in result["personas_cited"] or "Bob" in result["personas_cited"]

    def test_no_hits_returns_unknown_agreement(self):
        result = get_consensus_synthesis("question?", hits=[], client=None)
        assert result["agreement_level"] == "unknown"

    def test_client_called(self):
        hits = [_make_hit()]
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "consensus": "The community agrees.",
            "minority_views": [],
            "key_tensions": [],
            "agreement_level": "strong",
            "agreement_reason": "Everyone said so.",
            "personas_cited": ["Test Author"],
        }))]
        mock_client.messages.create.return_value = mock_response

        result = get_consensus_synthesis("question?", hits, mock_client)
        assert result["agreement_level"] == "strong"
