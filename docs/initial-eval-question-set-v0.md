# Initial Eval Question Set v0

## Purpose

This document defines the first scored evaluation set for the v0 answer contract.

It converts the canonical user question themes into a machine-consumable and
human-reviewable question set that can be used to judge answer quality
consistently across future API, retrieval, and synthesis changes.

## Scope

The v0 set is intentionally small.

It covers six question prompts derived from the current cycle priorities:

1. architecture under enterprise SLO, SLI, and SLA constraints
2. ideal current tech stack
3. most important current paradigm shifts
4. likely near-term stack changes over the next 4 weeks
5. reusable IaC, wrapper, and contract artifacts
6. adaptability while staying compatible with future governance and controls

## Scoring Model

Each question uses the same five weighted rubric dimensions.

- `scope_fit` — answer stays on the actual question
- `recommendation_specificity` — answer makes concrete choices
- `enterprise_overlay` — answer explains enterprise safety and segment-specific adjustments
- `evidence_and_provenance` — answer shows confidence and evidence quality
- `actionability` — answer leaves clear tradeoffs, watchlist items, or next actions

Scoring scale:

- `0-5` per criterion
- criterion score multiplied by criterion weight
- summed score used as the total question score

## Implementation Surface

The canonical machine-readable implementation lives in:

- `src/contracts/evaluation_set.py`
- `src/contracts/evaluation_harness.py`

The API exposes the set at:

- `GET /evaluation-set`
- `GET /evaluate/query`
- `GET /evaluate/query-set`

The executable harness currently uses deterministic, field-aware heuristics.

That means it can already score:

- metadata alignment to the evaluation question
- recommendation specificity
- evidence and provenance completeness
- actionability of the returned answer

It does not yet use an LLM judge.

That is intentional for v0 so the baseline stays stable, cheap, and testable.

## Retrieval Dependency

The executable scoring harness is only as useful as the answer retrieval path.

To reduce empty-match evaluations, the query layer now falls back to repository-native sources when
the SQLite knowledge base has no matches.

Current fallbacks include:

- tool registry results from the orchestrator
- trend registry results from the orchestrator
- framework matrix rows from `docs/phase-2-conceptual-frameworks.md`

These fallbacks carry explicit provenance so the evaluation harness can distinguish them from anonymous
low-signal matches.

## Why This Exists Now

The repository already had:

- a documented answer contract
- a queryable API surface
- roadmap references to an initial evaluation set

What it lacked was the actual evaluation artifact.

This file closes that gap and gives future work a stable scoring backbone.