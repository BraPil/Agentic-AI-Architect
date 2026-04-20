"""
Data models for AAA persona layer.

PersonaProfile is derived on-demand from ChromaDB metadata — no static config
files needed. Profiles are freshness-aware and provenance-aware by construction.
"""

from dataclasses import dataclass, field


@dataclass
class PersonaProfile:
    """Runtime profile derived from indexed content for one thought leader."""

    persona_id: str
    display_name: str
    item_count: int
    content_types: list[str] = field(default_factory=list)
    top_topics: list[str] = field(default_factory=list)
    top_tools: list[str] = field(default_factory=list)
    date_range: tuple[str, str] = field(default_factory=lambda: ("", ""))

    def to_dict(self) -> dict:
        return {
            "persona_id": self.persona_id,
            "display_name": self.display_name,
            "item_count": self.item_count,
            "content_types": self.content_types,
            "top_topics": self.top_topics,
            "top_tools": self.top_tools,
            "earliest_item": self.date_range[0],
            "latest_item": self.date_range[1],
        }


@dataclass
class PersonaViewpoint:
    """Synthesized viewpoint from one persona on a question."""

    persona_id: str
    display_name: str
    viewpoint: str
    key_points: list[str]
    relevant_tools: list[str]
    confidence: str          # high | medium | low | insufficient
    confidence_reason: str
    sources_used: int
    provenance: list[dict]

    def to_dict(self) -> dict:
        return {
            "persona_id": self.persona_id,
            "display_name": self.display_name,
            "viewpoint": self.viewpoint,
            "key_points": self.key_points,
            "relevant_tools": self.relevant_tools,
            "confidence": self.confidence,
            "confidence_reason": self.confidence_reason,
            "sources_used": self.sources_used,
            "provenance": self.provenance,
        }
