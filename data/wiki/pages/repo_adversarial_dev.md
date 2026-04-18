---
wiki_id: repo_adversarial_dev
type: repo_page
persona: cole_medin
repo: coleam00/adversarial-dev
foundational: true
raw_source: data/wiki/raw/cole_medin/github_coleam00_adversarial-dev_readme.md
status: draft
last_updated: 2026-04-18
aaa_relevance:
  - P3.3 — adversarial evaluation harness design
  - P6 — self-improvement loop with adversarial quality gate
  - P3 — agent specialization: Planner / Generator / Evaluator triad
---

# coleam00/adversarial-dev

## What It Is

A GAN-inspired three-agent harness that separates planning, building, and evaluation into distinct agents with distinct context windows. Based on Anthropic's engineering article on harness design for long-running application development. Supports both Claude Agent SDK and Codex SDK.

## The Three Agents

| Agent | Role | Context |
|-------|------|---------|
| **Planner** | Expands a short prompt into a full product spec with sprints | Only the original requirement |
| **Generator** | Builds one feature at a time, commits to git | Plan + current sprint |
| **Evaluator** | Actively tries to break what the generator built, scores ruthlessly | Original requirement only (never the plan) |

The evaluator is an **adversary**, not a reviewer. It runs the application, probes for failures, tests edge cases the generator didn't think of, and scores each criterion 1–10 with a hard pass threshold. If any criterion fails, the sprint returns to the generator with adversarial feedback.

## The Core Insight

> Single agents that plan, build, and evaluate their own work reliably praise their own mediocre output. This is **self-evaluation bias** — the quiet killer of ambitious AI coding projects.

Separating the roles eliminates self-evaluation bias. The evaluator never reads the implementation plan — it only knows the original requirement. This is the same holdout principle as the dark-factory validator.

## Why It Matters for AAA

1. **P3.3 evaluation harness**: AAA's eval framework should use the same three-way separation. The evaluator in the scoring harness must not have access to how a response was generated — only to the original query and the canonical answer contract.

2. **Phase 6 quality gate**: When AAA's self-improvement loop generates changes to its own code, an adversarial evaluator (not the same agent that wrote the change) should run the test suite and try to find failures before any merge.

3. **Sprint contracts before coding**: The pattern of negotiating a spec before implementation maps to AAA's P10 principle: "For any task that takes more than 5 minutes, write a brief plan first."

## Implementation Notes

- Requires Bun runtime (Claude harness: `bun run claude-harness/index.ts "..."`)
- Both Claude Agent SDK and Codex SDK implementations provided
- Output written to `workspace/claude/` and `workspace/codex/`
