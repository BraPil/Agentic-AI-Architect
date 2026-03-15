# Mouseion Core v0

## Purpose

This document defines the first operational version of `Mouseion` inside
`Agentic-AI-Architect`.

`Mouseion` is the proper name for the thin reusable shell that may eventually be shared across
multiple specialist systems.

For now, Mouseion remains housed inside AAA.

It should be understood as:

- the shared substrate
- the ontological framework
- the common architectural grounds on which future systems can be built

Mouseion is not yet a separate repo or runtime system.

It is the shared building code and civic infrastructure being discovered and formalized through AAA.

## Why Mouseion Exists

AAA needs a way to design systems that can evolve quickly without losing durable seams.

ExMorbus needs a shell strong enough to support a medically focused agent world without forcing
its medical-domain specifics back into AAA.

Mouseion exists to separate:

- reusable shell structure
- from product-specific domain implementation

## Current Mouseion Role

At the current stage, Mouseion is:

- designed inside AAA
- pressure-tested through ExMorbus
- retained as reusable architecture only if it survives contact with a real downstream system

This means Mouseion is currently both:

- an architectural spec surface
- the first typed contract layer for reusable shell objects

## Mouseion Core Objects v0

The first Mouseion Core slice should remain intentionally small.

### 1. `EventEnvelope`

The stable event wrapper for cross-system activity.

Required concerns:

- event identity
- event type
- producer
- schema version
- occurrence timestamp
- subject identity
- payload

### 2. `AgentProfile`

The reusable shell representation of an agent as an inspectable actor.

Required concerns:

- identity
- capabilities
- availability
- trust score
- permitted namespaces

### 3. `TaskRequest`

The shell contract for asking an agent or system to perform work.

Required concerns:

- task identity
- requester
- requested capability
- success criteria
- context references
- namespace
- optional due time

### 4. `TaskResult`

The shell contract for returned work.

Required concerns:

- source task identity
- producing actor
- result type
- summary
- artifact references
- confidence
- provenance
- next action suggestion
- review state

### 5. `Evaluation`

The reusable shell record for judging outputs.

Required concerns:

- target identity
- evaluator identity
- evaluation type
- criterion scores
- overall score
- expected versus actual outcome summary
- pass/fail outcome
- refinement allowance
- feedback summary
- provenance references
- review state

### 6. `Feedback`

The bounded refinement signal issued after evaluation.

Required concerns:

- target identity
- issuer identity
- summary
- requested changes
- refinement round
- review state

### 7. `KnowledgeRecord`

The shell object for durable memory that can survive implementation change.

Required concerns:

- stable identity
- record type
- producer
- timestamps
- confidence basis
- provenance references
- evaluation history references
- review state

### 8. `ReviewState`

The reusable state vocabulary for low-confidence and high-impact outputs.

Initial states:

- `draft`
- `under_evaluation`
- `needs_refinement`
- `accepted`
- `rejected`
- `superseded`

## What Mouseion Core Is Not

Mouseion Core v0 is not:

- the ExMorbus runtime
- the ExMorbus MoltBook environment
- the ExMorbus medical corpus
- a complete ecosystem control plane
- a separate shared repo yet

## How Mouseion Relates To ExMorbus

AAA should hand Mouseion contracts to ExMorbus as the reusable shell interface.

ExMorbus should implement against those contracts inside the ExMorbus repo.

That means:

- AAA produces shell contracts, architectural guidance, evaluation doctrine, and performance
  feedback hooks
- ExMorbus implements the runtime world, medical-domain logic, and product-owned interfaces

## What AAA Learns Back From ExMorbus

AAA should learn architectural feedback from ExMorbus over time.

Examples:

- shell durability
- routing quality
- interface friction
- review and evaluation weaknesses
- unmet capabilities ExMorbus wants
- which parts of Mouseion need refinement

AAA should not absorb ExMorbus domain findings as AAA product knowledge.

## Typed Contract Layer

The first typed Mouseion shell contracts live in AAA under:

- `src/contracts/mouseion.py`

These models are the first enforceable expression of Mouseion Core v0.

## Extraction Rule

Mouseion should remain housed inside AAA until all of the following are true:

1. ExMorbus is using Mouseion contracts in real implementation.
2. At least one additional downstream specialist system needs the same contracts.
3. The contracts have survived revision without major conceptual collapse.
4. The cost of keeping Mouseion inside AAA exceeds the cost of extraction.

## Related Documents

- `docs/shared-substrate-candidate-spec-v0.md`
- `docs/exmorbus-only-boundary-v0.md`
- `docs/aaa-exmorbus-ownership-matrix-v0.md`
- `docs/exmorbus-through-aaa-operating-model-v1.md`
