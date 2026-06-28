"""
Seeder — the AAA → OAA influence boundary.

AAA does not run OAA's cognition; it *suggests and influences* OAA's ecosystem by
producing a seed spec: which personas should enter the MoltBook as agents, what
genome each should carry, and what question (niche) the ecosystem should pursue.
OAA consumes this spec, runs its own processes, and emits artifacts AAA harvests.

The genome traits mirror OAA's 8-trait model (see OAA src/core/genome.py / README):
    curiosity, risk_tolerance, specialisation, cooperation,
    persistence, compassion, plus differentiation_threshold.

This keeps AAA as the architect that steers, and OAA as the engine that runs.
"""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# OAA AgentRole values that AAA personas naturally map toward.
_ROLE_RESEARCHER = "researcher"
_ROLE_CRITIC = "critic"
_ROLE_SYNTHESIZER = "synthesizer"
_ROLE_INNOVATOR = "innovator"
_ROLE_CURATOR = "curator"


@dataclass
class PersonaSeed:
    """A persona's entry spec for the OAA ecosystem."""

    agent_id: str
    display_name: str
    suggested_role: str
    genome: dict[str, float]
    capabilities: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# Curated genome leanings for AAA's core personas. Values bias probabilities in
# OAA, they do not dictate behavior. compassion is biased >0.5 per OAA doctrine.
_CORE_PERSONA_GENOMES: dict[str, dict[str, Any]] = {
    "andrej-karpathy": {
        "display_name": "Andrej Karpathy",
        "suggested_role": _ROLE_RESEARCHER,
        "genome": {"curiosity": 0.95, "risk_tolerance": 0.6, "specialisation": 0.9,
                   "cooperation": 0.6, "persistence": 0.85, "compassion": 0.65},
        "capabilities": ["llm_systems", "first_principles", "minimalism"],
    },
    "simon-willison": {
        "display_name": "Simon Willison",
        "suggested_role": _ROLE_CRITIC,
        "genome": {"curiosity": 0.9, "risk_tolerance": 0.8, "specialisation": 0.5,
                   "cooperation": 0.7, "persistence": 0.7, "compassion": 0.6},
        "capabilities": ["pragmatism", "tooling", "skeptical_testing"],
    },
    "lilian-weng": {
        "display_name": "Lilian Weng",
        "suggested_role": _ROLE_SYNTHESIZER,
        "genome": {"curiosity": 0.85, "risk_tolerance": 0.35, "specialisation": 0.85,
                   "cooperation": 0.65, "persistence": 0.95, "compassion": 0.65},
        "capabilities": ["rigor", "survey_synthesis", "evaluation"],
    },
    "eugene-yan": {
        "display_name": "Eugene Yan",
        "suggested_role": _ROLE_RESEARCHER,
        "genome": {"curiosity": 0.85, "risk_tolerance": 0.45, "specialisation": 0.75,
                   "cooperation": 0.75, "persistence": 0.85, "compassion": 0.7},
        "capabilities": ["applied_ml", "recsys", "evaluation", "practical_patterns"],
    },
    "sebastian-ruder": {
        "display_name": "Sebastian Ruder",
        "suggested_role": _ROLE_RESEARCHER,
        "genome": {"curiosity": 0.9, "risk_tolerance": 0.4, "specialisation": 0.85,
                   "cooperation": 0.7, "persistence": 0.9, "compassion": 0.65},
        "capabilities": ["nlp_research", "survey", "transfer_learning"],
    },
    "chip-huyen": {
        "display_name": "Chip Huyen",
        "suggested_role": _ROLE_CRITIC,
        "genome": {"curiosity": 0.8, "risk_tolerance": 0.4, "specialisation": 0.7,
                   "cooperation": 0.7, "persistence": 0.8, "compassion": 0.7},
        "capabilities": ["production_systems", "ml_ops", "pragmatism"],
    },
    "cole-medin": {
        "display_name": "Cole Medin",
        "suggested_role": _ROLE_INNOVATOR,
        "genome": {"curiosity": 0.9, "risk_tolerance": 0.85, "specialisation": 0.6,
                   "cooperation": 0.8, "persistence": 0.75, "compassion": 0.7},
        "capabilities": ["agentic_orchestration", "experimentation"],
    },
    "brandt-pileggi": {
        "display_name": "Brandt Pileggi",
        "suggested_role": _ROLE_CURATOR,
        "genome": {"curiosity": 0.85, "risk_tolerance": 0.7, "specialisation": 0.6,
                   "cooperation": 0.75, "persistence": 0.9, "compassion": 0.8},
        "capabilities": ["product_judgment", "ecosystem_thinking", "final_approval"],
    },
}


def default_personas() -> list[str]:
    """The core persona set seeded into a learning cycle by default."""
    return list(_CORE_PERSONA_GENOMES.keys())


def _generic_genome() -> dict[str, float]:
    """Neutral genome for personas without a curated profile (compassion biased >0.5)."""
    return {"curiosity": 0.6, "risk_tolerance": 0.5, "specialisation": 0.5,
            "cooperation": 0.6, "persistence": 0.6, "compassion": 0.6}


def build_persona_seed(persona_id: str, display_name: str | None = None) -> PersonaSeed:
    """Build a single persona's OAA seed spec, curated if known, generic otherwise."""
    curated = _CORE_PERSONA_GENOMES.get(persona_id)
    if curated:
        return PersonaSeed(
            agent_id=persona_id,
            display_name=curated["display_name"],
            suggested_role=curated["suggested_role"],
            genome=dict(curated["genome"]),
            capabilities=list(curated["capabilities"]),
        )
    return PersonaSeed(
        agent_id=persona_id,
        display_name=display_name or persona_id.replace("-", " ").title(),
        suggested_role=_ROLE_RESEARCHER,
        genome=_generic_genome(),
        capabilities=[],
    )


def build_seed_spec(question: str, persona_ids: list[str] | None = None,
                    urgency: float = 0.8) -> dict[str, Any]:
    """Produce the full AAA → OAA seed spec for one learning cycle.

    Args:
        question: the architecture question the ecosystem should pursue (the niche).
        persona_ids: personas to seed as agents (defaults to the core set).
        urgency: niche urgency (0–1); higher pulls more agents toward it.

    Returns:
        A dict with a `niche` (the question) and `agents` (persona seeds), ready to
        be written to a file and handed to OAA.
    """
    ids = persona_ids or default_personas()
    agents = [build_persona_seed(pid).to_dict() for pid in ids]
    return {
        "schema_version": "v0",
        "niche": {
            "description": question,
            "required_capabilities": [_ROLE_RESEARCHER, _ROLE_CRITIC, _ROLE_SYNTHESIZER],
            "urgency": urgency,
            "posted_by": "agentic-ai-architect",
        },
        "agents": agents,
    }


def write_seed_spec(spec: dict[str, Any], path: Path | str) -> Path:
    """Write a seed spec to disk for OAA to consume."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
    return out
