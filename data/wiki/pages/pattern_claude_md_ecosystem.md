---
wiki_id: pattern_claude_md_ecosystem
type: pattern_page
persona: brandt_pileggi
origin: docs/templates/claude-md/
foundational: true
raw_source: docs/templates/claude-md/CLAUDE.md
status: reviewed
last_updated: 2026-06-28
aaa_relevance:
  - P0 — template governs every coding session in AAA from day one
  - P5 — AI Engineering OS concept directly informs ExMorbus integration governance
  - P7 — production hardening uses companion evaluation.md and security.md patterns
related_patterns:
  - pattern_llm_wiki (three-layer structure informs knowledge.md companion)
  - concept_evaluation (evaluation companion extends this pattern)
  - concept_prompt_injection (security companion formalizes injection defense)
---

# AI Engineering Operating System Pattern (CLAUDE.md Ecosystem)

## The Core Idea

Most CLAUDE.md files optimize an AI assistant's *behavior*. This pattern optimizes the
*engineering system the assistant operates inside*. The distinction is significant:

- Behavior rules cover known cases
- An engineering operating system gives the assistant the vocabulary to derive correct
  behavior for novel cases

The centerpiece is an **Architectural Constitution** — eight ranked values that resolve
conflicts without requiring a rule for every situation.

## Origin

Designed in a Board of Governors session (2026-06-28) using adversarial discourse across
indexed AAA personas: Karpathy (empiricist), Willison (anti-bloat), Huyen (production-first),
Weng (systematic rigor), Cole Medin (agentic practitioner), Pileggi (final authority).

The design deliberately incorporated adversarial positions to prevent sycophantic convergence
on the most complex option. Key tensions resolved:

| Tension | Resolution |
|---------|-----------|
| Karpathy (teach thinking) vs. Huyen (constitution over full wiki) | Constitution is the distillation; wiki ingestion optional per session |
| Willison (fewer docs = more compliance) vs. Weng (structure is load-bearing) | Three mandatory files; rest grows organically; DoD is enforcement |
| Weng (structure without integration fails) vs. Willison (templates nobody fills are worse) | DoD checklist wires mandatory files to every task completion |

## Structure

```
CLAUDE.md                     ← ROOT: ~150 lines. Index + constitution + guardrails + DoD
│
├── companion/                ← Deep docs (read on demand per session, not every session)
│   ├── architecture.md       ← Component map, data flows, phase roadmap, tech debt
│   ├── governance.md         ← Protected files, approval matrix, escalation paths
│   ├── workflows.md          ← Dev lifecycle, branching, commit standards, PR process
│   ├── evaluation.md         ← AI eval methodology, benchmarks, uncertainty policy
│   ├── security.md           ← Threat model, injection defense, secret hygiene
│   └── knowledge.md          ← Knowledge taxonomy, three-layer wiki design
│
├── adr/                      ← Architecture Decision Records (instantiated on demand)
├── templates/                ← ADR, runbook, design-doc, incident, RFC templates
│
├── decision-log.md           ← MANDATORY: chronological architectural decisions
├── discovery-log.md          ← MANDATORY: significant findings affecting future work
└── lessons-learned.md        ← MANDATORY: mistakes, surprises, preventive lessons
```

## The Architectural Constitution

The single most important element. Eight values, explicitly priority-ranked.
When two values conflict, the one ranked higher wins — no ambiguity.

| Rank | Value | Demand |
|------|-------|--------|
| 1 | Observability | If not logged and measurable, it doesn't exist |
| 2 | Correctness | Working > fast > elegant. Measure before optimizing |
| 3 | Simplicity | Smallest change satisfying the requirement |
| 4 | Explainability | Every decision has a stated reason. No magic |
| 5 | Testability | If you can't test it, rethink the design |
| 6 | Replaceability | Implementations swap; interfaces are stable |
| 7 | Security | Sanitize, authenticate, rate-limit from day one |
| 8 | Evolvability | Today's choice doesn't lock out tomorrow's option |

Priority ordering is what separates this from a list of platitudes. "Observability vs.
Simplicity" has a deterministic answer: add the log line.

## Initialization Survey

The template detects its own unconfigured state (grep for `[PROJECT NAME]`) and runs
a structured 5-block interview before allowing any other work:

- Block 1 (~1 min): Project identity
- Block 2 (~3 min): Mission, users, success criteria, non-goals
- Block 3 (~3 min): Technology stack with rationale
- Block 4 (~3 min): Phase structure and current priorities
- Block 5 (~2 min): Governance, protected files, test command

After the survey: fills all placeholders, bootstraps companion files, creates first
decision-log entry, deletes the INIT section, commits a configured CLAUDE.md.

## The Definition of Done as Enforcement Mechanism

*From Weng's position in the design session:*

Documentation standards without a gate are suggestions. The DoD checklist is the gate.
Mandatory files get filled because the DoD asks for them, not because engineers remember.

```
A task is not complete until:
□ Tests pass (happy-path + failure-path)
□ Companion docs updated
□ decision-log.md updated if architectural decision made
□ lessons-learned.md updated if something surprising happened
□ ADR filed if significant architectural choice locked in
□ No hardcoded secrets
□ External content sanitized before LLM prompt inclusion
```

## Three Mandatory Files (from day one)

| File | Purpose | When Updated |
|------|---------|-------------|
| `decision-log.md` | Chronological architectural decisions | Every architectural choice |
| `discovery-log.md` | Findings that change future work | Every significant discovery |
| `lessons-learned.md` | Mistakes and preventive lessons | Every surprise or failure |

These three create institutional memory that survives session boundaries, contributor
turnover, and context window limits.

## Key Design Decisions

**Root file stays lean (< 150 lines).** A file that can't be read in 90 seconds won't
be read every session. The root file is an index + constitution + non-negotiable rules.
Depth lives in companion files, read on demand.

**Companion files read on demand, not every session.** The session protocol says: identify
which companions apply to this session's task, read those, skip the rest. This keeps
context usage proportional to task complexity.

**Templates instantiate on demand, not day one.** ADR, runbook, incident, design-doc, RFC
templates exist in `templates/`. They get instantiated when the DoD requires one. Creating
all 16 template instances on day one is documentation theater.

**Knowledge taxonomy separates four types** (from Weng + Karpathy):
- Facts → `knowledge/` or `data/`
- Decisions → `decision-log.md`, `adr/`
- History → `discovery-log.md`, `work-log.md`
- Standards → companion docs, `CLAUDE.md`

Collapsing these makes retrieval imprecise and mutation unsafe.

## Relationship to Karpathy's LLM Wiki Pattern

These two patterns are complementary layers of the same system:

```
LLM Wiki Pattern (pattern_llm_wiki)
  └── provides: knowledge layer (what the system knows)
      raw/ → pages/ → schema/ (provenance preserved)

CLAUDE.md Ecosystem Pattern
  └── provides: governance layer (how the system is built)
      constitution → guardrails → DoD → companion docs

Together:
  Wiki (knowledge) + CLAUDE.md (governance) = AI Engineering Operating System
```

The `knowledge.md` companion in the CLAUDE.md ecosystem directly encodes the
three-layer wiki design, enabling any project using this template to adopt
Karpathy's pattern without needing to derive it independently.

## AAA Application

The AAA codebase is the reference implementation of this pattern:
- `CLAUDE.md` → root file with constitution and 14 governance sections
- `docs/` → companion files (architecture, governance, work logs)
- `data/wiki/` → the Karpathy LLM Wiki layer
- `docs/decision-log.md`, `docs/discovery-log.md`, `docs/lessons-learned-log.md` → mandatory files

Template location: `docs/templates/claude-md/` — 16 files, copy and fill placeholders.
