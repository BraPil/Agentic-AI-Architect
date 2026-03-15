# Research And Training Cycle v1

## Purpose

This document defines the next operating cycle for the Agentic AI Architect system.

It refines the original prompt's repeated loop of plan, explore, discover, document, learn, train,
refine, and repeat into an explicit operating specification.

## Why This Cycle Exists

The repository now has:

- a strong long-term product vision
- a phased implementation roadmap
- a curated source corpus and influencer watchlist
- durable repository memory

What it still needs is a precise cycle contract that tells the system what one good iteration should
produce.

## Original Vision Preserved

The original vision remains intact:

- build the world's standard for an agentic AI Architect system
- continuously discover architecture concepts, trends, tools, and adoption patterns
- support both standalone use and larger orchestrated systems
- operate in repeated learning and refinement cycles

This cycle spec is not a strategy change.

It is an operational tightening of that strategy.

## Current Cycle Priorities

Based on the latest clarified intent, the next cycle should optimize for:

- enterprise-relevant research first
- machine-readable outputs first
- human-readable outputs derived from the same payload
- source corpus quality, not source count alone
- evaluation readiness, not just documentation growth

## Training Meaning For The Current Phase

For the current phase, `train` means:

- curating a higher-quality source corpus
- building an evaluation set from canonical architecture questions
- improving research and extraction prompts
- ranking and weighting sources by signal quality

It does not yet mean model fine-tuning or weight adaptation.

## The Cycle

### 1. Plan

Select a bounded question set for the cycle.

For the next cycle, prioritize:

- ideal architecture under constraints
- ideal current toolchain and stack
- what is changing now and likely within 4 weeks

### 2. Explore

Expand only the sources that improve answers to the bounded question set.

Do not optimize for generic topic collection.

### 3. Discover

Capture findings into structured records with fields for:

- source identity
- segment relevance
- evidence tier
- change type
- technology lifecycle signal
- recommendation impact

### 4. Document

Every meaningful discovery should become one of:

- a source record
- a reviewed summary
- a decision-support note
- a watchlist or alert candidate

### 5. Learn

Ask explicitly:

- what changed since the last cycle
- what remained stable
- what reusable artifact opportunity appeared
- what should become a wrapper or contract boundary

### 6. Train

Use the cycle outputs to improve:

- source weights
- extraction prompts
- summary prompts
- evaluation criteria
- confidence semantics

### 7. Refine

At cycle close, update:

- the answer contract if needed
- the source rankings
- the question set
- the evidence-tier assumptions
- the next-cycle watchlist

## Evidence Tiers

To avoid overstating weak evidence, every research record should fall into one of these tiers.

### Tier A — Direct

Directly fetched and reviewed source content.

Examples:

- public article fetched successfully
- repository README reviewed directly
- product documentation page parsed directly

### Tier B — Public Companion

Public secondary source directly accessible and closely related to the original blocked or gated source.

Examples:

- blog post by the same author
- public talk or newsletter version of the same concept
- official release notes corresponding to a referenced social post

### Tier C — User Provided

Source content manually supplied by the user.

Examples:

- pasted LinkedIn post content
- exported activity logs
- screenshots or curated notes from the user

### Tier D — Inferred

Conservative working interpretation derived from visible URL slugs, titles, and existing tags only.

This tier is allowed for ingestion and temporary review notes, but should not be mistaken for a direct
content review.

## Segment Overlay Rule

The system must eventually support startup, small-company, and enterprise contexts.

For the next cycle, enterprise is the primary lens.

That means every meaningful recommendation should ask:

- is this enterprise-safe enough to recommend now
- what parts of this recommendation are segment-specific
- what would differ for a startup or smaller company

## Future Governance Constraint

Governance, SecOps, and Auditability will later become their own systems.

For now, treat them as future alignment constraints, not hard blockers.

In practice:

- research them enough to preserve future compatibility
- keep provenance and confidence fields ready now
- do not require full governance gating before current discovery work can proceed

## Expected Outputs From The Next Cycle

The next cycle should produce five concrete outputs.

### 1. First answer contract

The canonical output shape for the first supported question types.

### 2. Initial evaluation set

A scored question set derived from the user's canonical architecture questions.

### 3. Enterprise overlay fields

Structured representation of how a recommendation changes for enterprise contexts.

### 4. Evidence-tier enforcement

Clear distinction between direct review, public companion review, user-supplied content, and inferred
working summaries.

### 5. Source scoring model

An explicit basis for weighting influencer, tool, repo, documentation, and governance sources.

## Immediate Cycle Questions

The user's current canonical question set includes the following themes:

- ideal architecture to meet SLO/SLI/SLA needs
- ideal current tools and tech stack
- most recent and impactful meta shifts
- likely near-term stack changes
- reusable IaC and artifact skeleton opportunities
- how to keep systems adaptable while still compatible with future governance and enterprise controls

These should become the first evaluation backbone for the system.

## Suggested Near-Term Branch Breakdown

The next work should stay inside this repository.

Suggested task branches:

- `task/p1.5-answer-contract-v0`
- `task/p1.6-eval-question-set`
- `task/p1.7-source-weighting-model`
- `task/p1.8-enterprise-overlay-fields`

These are Phase 1 compatible because they tighten the discovery and research loop rather than jumping
ahead into speculative platform work.

## Related Documents

- `docs/first-answer-contract-v0.md`
- `docs/phase-5-implementation-plan.md`
- `docs/phase-1-education.md`
- `docs/influencer-tracker.md`
- `docs/influencer-source-registry.yaml`