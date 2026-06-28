# World-Class CLAUDE.md Template Ecosystem

> An AI Engineering Operating System — not just a prompt file.
> Copy this directory to a new project and fill in the `[PLACEHOLDERS]`.

---

## What This Is

Most CLAUDE.md files optimize Claude's *behavior*. This ecosystem optimizes the *engineering
system Claude operates inside*. The difference is significant:

- Behavior rules tell Claude what to do in known cases
- An engineering operating system gives Claude the vocabulary to derive correct behavior in novel cases

The centerpiece is the **Architectural Constitution** — eight ranked values that resolve conflicts
without requiring a rule for every situation.

---

## Quick Start

```bash
# 1. Copy the ecosystem to your new project
cp -r docs/templates/claude-md/* /path/to/new-project/

# 2. Fill in root CLAUDE.md — takes about 20 minutes
# Focus on: Mission (§1), Tech Stack (§7), Phase Status (§8)

# 3. The Architectural Constitution (§2) stays as-is unless you have strong project-specific reasons

# 4. Create the mandatory three files:
# - decision-log.md (one example entry for your first architectural decision)
# - discovery-log.md (leave empty until you have a real discovery)
# - lessons-learned.md (leave empty until you have a real lesson)

# 5. Create companion docs on demand as the project grows
# Don't fill them all out on day one — that's documentation theater
```

---

## File Map

```
CLAUDE.md                          ← ROOT: The file. ~150 lines. Read every session.
README.md                          ← This file
│
├── companion/                     ← Deep documentation (read on demand, per session)
│   ├── architecture.md            ← System design, component map, phase roadmap
│   ├── governance.md              ← Protected files, approval matrix, escalation
│   ├── workflows.md               ← Dev lifecycle, branching, commits, PR process
│   ├── evaluation.md              ← AI/ML eval methodology, benchmarks, uncertainty
│   ├── security.md                ← Threat model, injection defense, secret hygiene
│   └── knowledge.md               ← Knowledge taxonomy, three-layer wiki design
│
├── adr/                           ← Architecture Decision Records (created on demand)
│   └── 0001-TEMPLATE.md           ← ADR template — copy and number sequentially
│
├── templates/                     ← Document templates (instantiated by the DoD)
│   ├── runbook.md                 ← Operational procedures
│   ├── design-doc.md              ← Feature design (filed before implementation)
│   ├── incident.md                ← Post-incident analysis
│   └── rfc.md                     ← Proposed changes (filed before significant decisions)
│
├── decision-log.md                ← MANDATORY: one entry per architectural decision
├── discovery-log.md               ← MANDATORY: one entry per significant finding
└── lessons-learned.md             ← MANDATORY: one entry per surprising mistake
```

---

## Design Principles

These were resolved through adversarial discourse across engineering personas:

| Principle | Source | Why |
|-----------|--------|-----|
| Root file < 150 lines | Karpathy + Willison | Files that can't be read in 90 seconds don't get read |
| Architectural Constitution, not rule list | Karpathy + Huyen | Values generate rules; rules can't enumerate all cases |
| DoD is the enforcement mechanism | Weng | Standards without gates are suggestions |
| Three mandatory files, rest on demand | Willison | Templates nobody fills out are worse than no templates |
| AI evaluation is non-optional | Cole Medin | A system with no eval has no immune system |
| Karpathy LLM Wiki ingestion is optional | Huyen | Full wiki on every session is expensive; constitution is the distillation |
| Knowledge taxonomy separates facts/decisions/history/standards | Weng + Karpathy | Collapsing these makes retrieval imprecise |

---

## Philosophical Foundation

*From the Board of Governors session that produced this template:*

**Karpathy:** "Teach the model how an LLM engineer thinks, not just what rules to follow. If you
get the thinking framework right, you need fewer rules."

**Huyen:** "The constitution is the distillation. Eight ranked values that give Claude a way to
resolve novel conflicts without a rule for every case."

**Willison:** "Every doc you add is friction. The DoD is what makes docs happen — not good intentions."

**Weng:** "Separate your knowledge types. Facts live somewhere. Decisions live somewhere else.
History lives somewhere else. Mixing them makes all three worse."

**Brandt (#12):** "Ship it. The best CLAUDE.md is one that gets read and followed, not one that
covers every edge case in writing."

---

## Integration with Karpathy's LLM Wiki

This template is designed to complement — not replace — Karpathy's LLM Wiki design pattern.

The wiki (`data/wiki/` in AAA) provides the **knowledge layer**: personas, frameworks, tools,
patterns, indexed and queryable.

This template provides the **engineering governance layer**: how the system is built, by whom,
under what rules, with what safeguards.

Together they form the AI Engineering Operating System:

```
Wiki (knowledge layer)       → what the system knows
CLAUDE.md ecosystem          → how the system is built
Evaluation framework         → how we know the system works
Three-layer architecture     → raw → pages → schema (provenance preserved at every layer)
```

---

## Placeholders to Fill

After copying, `grep -r '\[' . --include="*.md"` will find every placeholder.
Priority order:

1. `CLAUDE.md` §1 (Mission) — most important, sets everything else
2. `CLAUDE.md` §7 (Tech Stack) — enables stack-specific reasoning
3. `CLAUDE.md` §8 (Phase Status) — enables phase discipline
4. `companion/architecture.md` — component map and data flow
5. `companion/governance.md` — protected files and approval matrix
6. Everything else: fill as the project matures
