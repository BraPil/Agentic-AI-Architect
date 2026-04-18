---
wiki_id: repo_autoresearch
type: repo_page
persona: andrej_karpathy
repo: karpathy/autoresearch
foundational: true
raw_source: data/wiki/raw/karpathy/github_karpathy_autoresearch_readme.md
status: draft
last_updated: 2026-04-18
aaa_relevance:
  - P1.3 — autonomous research loop design
  - P6.1 — self-improvement via overnight experiment runs
  - P4 — orchestration pattern for iterative agent cycles
---

# karpathy/autoresearch

## What It Is

A minimal autonomous research framework: give an AI agent a GPU and a training setup, let it experiment overnight. The agent modifies `train.py`, trains for 5 minutes, checks if validation loss improved, keeps or discards the change, and repeats. A human wakes up to a log of experiments and (hopefully) a better model.

Created March 2026. The framing is deliberately dramatic: Karpathy describes it as the beginning of the era when AI took over frontier research from humans.

## Core Design

Three files that matter:

| File | Owner | Purpose |
|------|-------|---------|
| `prepare.py` | Fixed | One-time data prep, dataloader, evaluation utilities. Not touched by agent. |
| `train.py` | Agent edits | Full GPT model, Muon + AdamW optimizer, training loop. Everything is fair game. |
| `program.md` | Human edits | Instructions for one agent. This is the "research org code." |

The metric is `val_bpb` (validation bits per byte) measured over a fixed 5-minute wall-clock training budget. Vocab-size-independent, so architecture changes compare fairly.

The human's job is to improve `program.md`, not `train.py`. You are programming the **research organization**, not the model.

## Why It Matters for AAA

This is the clearest existing implementation of the AAA Phase 6 self-improvement pattern. Key architectural lessons:

1. **Fixed evaluation metric + time budget** eliminates the "agent games its own scoring" failure. AAA's P3.3 eval harness should follow this: fix the metric, fix the budget.
2. **Human edits the instructions, agent edits the code** — maps directly to `CLAUDE.md` as the human-maintained program.md for AAA's self-improvement loop.
3. **Single-file agent target** (`train.py`) keeps the attack surface small. AAA's Phase 6 equivalent should similarly constrain what the improvement agent can touch.
4. **Overnight async loop** — matches the Phase 4.2 APScheduler pattern: kick off, come back to results.

## Relationship to Other Patterns

- Archon (Cole Medin) provides a more general harness for the same overnight loop idea, but for software tasks rather than ML experiments.
- LLM Wiki (Karpathy) and autoresearch together suggest the same philosophy: **structured index + autonomous overnight loop** as the backbone of a self-improving knowledge system.
