# Branch Strategy Summary

## Purpose

This document explains how branch types should be used in this repository now that the early
foundation work and the first research/review work have both been merged into `main`.

It exists to prevent two kinds of drift:

- treating every exploratory thread as if it deserves a long-lived product branch
- losing the connection between research branches, durable docs, and actual implementation work

## Current Repository State

The current `main` branch already contains two important merged layers of work.

### 1. Foundation layer

Merged by:

- `merge: integrate agentic systems foundation`

This established the original AAA skeleton:

- base instructions and repo rules
- agent contract and initial agent implementations
- knowledge base and pipeline foundation
- phase docs and the original roadmap
- baseline tests

### 2. Independent review and boundary-setting layer

Merged by:

- `merge: integrate architecture review and repo decision docs`

This added the first durable correction pressure on the original plan:

- independent review artifacts
- multi-model review log
- repository-boundary decision memo

That second merge is what pushed the repo toward a more disciplined stance on:

- keeping AAA as a product repo for now
- avoiding premature ecosystem sprawl
- defining contracts and interfaces earlier
- forcing durable decisions into docs rather than leaving them in chat history

## What Has Happened Since Those Merges

The repository direction has moved further than those two merge commits alone show.

The current working direction now includes:

- canonical answer contracts
- evaluation sets and executable scoring
- source weighting and learned weighting
- repository memory logs and indexing
- LinkedIn PDF ingest and knowledge-base seeding
- ExMorbus-through-AAA operating model and shared-substrate pressure testing

That means future branch strategy should no longer be thought of as just phase branches for a raw
agent skeleton. It now needs to support three parallel kinds of work:

- bounded product implementation
- durable architecture and ontology formation
- fast validation spikes that may or may not survive intact

## Recommended Branch Types

### 1. `main`

Use `main` as the integrated product truth.

It should contain:

- accepted product behavior
- accepted repo doctrine
- durable memory updates
- merged implementation that is coherent enough to be the current system of record

`main` should not become a parking lot for partially related experiments.

### 2. `feature/...`

Use feature branches for phase-scale product work that spans multiple task branches.

Examples:

- `feature/p1-knowledge-discovery`
- `feature/p2-intelligence-layer`

Use them when the work changes a meaningful system slice, not for every single document or test.

### 3. `task/...`

Use task branches for bounded implementation slices that can land independently.

Examples already implied by the repo:

- `task/p1.5-answer-contract-v0`
- `task/p1.6-eval-question-set`
- `task/p1.7-source-weighting-model`
- `task/p1.8-enterprise-overlay-fields`

This should be the default branch type for most implementation work now.

### 4. `research/...`

Use research branches for work whose main output is durable ontology, contracts, evaluation
method, or architectural doctrine.

Examples:

- `research/exmorbus-through-aaa-v1`

Research branches must not end as chat-only or branch-only knowledge. They should produce:

- durable docs in `docs/`
- decision, discovery, lesson, or work-log updates
- a clear judgment about what should become implementation next

### 5. `spike/...`

Use spike branches for fast validation of shape, not for durable doctrine.

Examples:

- `spike/exmorbus-shell-poc-v1`

Spike branches are allowed to be rough, but they must answer a narrow question and feed their
results back into a research branch or directly into repo memory.

### 6. `fix/...` and `docs/...`

Use `fix/...` for narrowly scoped bug fixes and `docs/...` for documentation-only changes that do
not meaningfully alter implementation behavior.

If a docs change records a real architectural decision, make sure the relevant memory logs are
updated too.

## Relationship Between Branch Types

The branch flow should usually be:

1. spike branch validates shape quickly
2. research branch codifies what survived the spike
3. task branch implements the reusable part in the product
4. `main` receives the integrated result and updated memory

Not every change needs all four steps, but future sibling-system work should generally follow that
pattern.

## Current Recommended Strategy

For the current repo state, the recommended operating pattern is:

1. Keep AAA product work landing through bounded `task/...` branches.
2. Use `research/...` branches when the output is contract design, shared-substrate thinking,
   ontology, or operating model refinement.
3. Use `spike/...` branches when ExMorbus or future sibling systems need fast shell validation.
4. Do not open a new standalone specialist repository until the entry criteria in
   `docs/ecosystem-sequencing-memo.md` are met.
5. Treat ExMorbus as the first serious consumer and pressure test of AAA's reusable contracts,
   not as an excuse to bypass AAA and start a parallel architecture universe.

## Practical Rule

Use this heuristic:

- if the outcome is code that should ship, prefer `task/...`
- if the outcome is doctrine that should shape future code, prefer `research/...`
- if the outcome is a quick answer about whether an idea survives contact with implementation,
  prefer `spike/...`

## Related Documents

- `docs/repo-structure-decision-memo.md`
- `docs/ecosystem-sequencing-memo.md`
- `docs/exmorbus-through-aaa-operating-model-v1.md`
- `docs/repo-memory-protocol.md`
- `docs/work-log.md`