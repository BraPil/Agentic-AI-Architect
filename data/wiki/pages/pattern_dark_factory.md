---
wiki_id: pattern_dark_factory
type: pattern_page
persona: cole_medin
origin: https://github.com/coleam00/dark-factory-experiment
foundational: true
raw_source: data/wiki/raw/cole_medin/github_coleam00_dark-factory-experiment_readme.md
status: reviewed
last_updated: 2026-04-18
aaa_relevance:
  - P6 — self-improvement loop architecture
  - P4 — orchestration: GitHub-as-state-machine
  - P3.3 — holdout validation pattern
---

# Dark Factory Pattern (Cole Medin)

## The Core Idea

Autonomous software factory: **specs go in, software comes out.** Humans file issues; everything between issue and production (triage, implement, review, merge) is handled by AI agents on a cron.

Named after Dan Shapiro's lights-out FANUC plants where robots built robots 24/7 with no humans on the floor.

## The Three Layers

1. **Workflow engine (Archon)** — deterministic scaffolding that orchestrates coding agent sessions. Makes the sequence repeatable and auditable.
2. **Coding agent (Claude Code)** — the AI that actually edits files, runs bash, calls `gh`.
3. **Model** — the LLM doing the reasoning. Swappable (dark-factory uses MiniMax M2.7 for cost).

## State Machine via Labels

The factory uses **GitHub labels as the state machine**. The orchestrator reads labels, not its own memory, to decide what to do next. This makes state visible, debuggable, and resumable after crashes.

```
Issue lifecycle:  triaging → accepted → in-progress → [PR] or rejected
PR lifecycle:     implementing → needs-review → approved (merge) or needs-fix → [retry ×2] → needs-human
```

## The Non-Negotiable Rules

These are lessons from every prior Dark Factory attempt (StrongDM, Spotify Honk, Steve Yegge's Gas Town):

1. **Holdout validation**: Evaluator never reads the implementation plan. Checks outcome against original requirement only.
2. **Binary triage**: Accept or reject. No "needs human" inbox.
3. **Governance files are immutable**: The files that define the factory's purpose and rules can never be modified by the factory.
4. **One workflow at a time**: Structural throughput cap prevents runaway.
5. **Flood protection**: Rate-limit external issue filers.
6. **Per-node budget caps**: Every AI node has a max spend.

## Why It Matters for AAA

| AAA Phase | Dark Factory Lesson |
|-----------|---------------------|
| P3.3 eval harness | Holdout validation — evaluator never sees how the answer was generated |
| P4 orchestration | GitHub-as-state-machine alternative to a custom orchestrator |
| P6 self-improvement | Full reference implementation: Archon + Claude Code + GitHub labels |

## Relationship to Other Patterns

- **autoresearch** (Karpathy): Same overnight-loop philosophy, applied to ML experiments rather than software tasks
- **adversarial-dev** (Cole Medin): Same holdout principle, applied to individual sprint evaluation rather than PR review
- **Archon**: The harness layer that makes both patterns reliable and repeatable
