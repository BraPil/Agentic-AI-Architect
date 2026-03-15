# ExMorbus-Only Boundary v0

## Purpose

This document defines what is explicitly not part of Mouseion Core and should therefore remain in
ExMorbus.

It exists to prevent AAA and Mouseion from absorbing product-specific medical-domain flesh.

## Core Rule

If an object is only meaningful because ExMorbus is a medically focused system, it should remain in
ExMorbus.

## ExMorbus-Only Object Families

### 1. Medical evidence objects

Examples:

- trial phase metadata
- modality
- tumor type
- preclinical versus clinical status
- mechanism of action
- response and toxicity fields

These belong to ExMorbus because they are domain semantics, not reusable shell structure.

### 2. Oncology domain stages

Examples:

- broad health
- clinical medicine
- oncology
- novel cancer therapies
- cancer vaccines and adjacent modalities

The generic idea of namespace or progression metadata may be reusable.

The actual medical-domain ladder is ExMorbus-owned.

### 3. Cancer-specific opportunity types

Examples:

- underexplored vaccine directions
- modality-specific tool gaps
- contradictory oncology evidence clusters
- therapeutic-hypothesis generation targets

These belong to ExMorbus because they are expressions of the product's research mission.

### 4. Domain thresholds and calibration

Examples:

- thresholds for choosing the best oncology agent
- domain-specific routing confidence thresholds
- medical evidence sufficiency thresholds
- domain fit calibration for oncology workflows

The reusable idea of routing and evaluation belongs in Mouseion.

The actual numbers and policies belong in ExMorbus.

### 5. ExMorbus dissemination interfaces

Examples:

- ExMorbus-owned API payloads for external biomedical systems
- ExMorbus-owned CLI surfaces for agentic interaction
- medically specific export formats and downstream interface policy

ExMorbus owns its own domain outputs and the interfaces used to disseminate them.

## ExMorbus Runtime Ownership

The MoltBook-like runtime environment belongs to ExMorbus.

That includes:

- the world in which ExMorbus agents live and work
- the medically focused community and economy
- the runtime interactions that produce domain knowledge

AAA may help design and evaluate this environment.

AAA does not own it as runtime product territory.

## What AAA Should Learn Instead

AAA should retain architectural feedback such as:

- whether Mouseion shell contracts held up
- where interface friction appeared
- what ExMorbus wanted the system to do but the architecture could not yet support
- where evaluation and review logic were too weak
- which reusable structures deserve refinement

This keeps AAA as institutional memory for architecture rather than a shadow copy of ExMorbus's
medical corpus.

## Related Documents

- `docs/mouseion-core-v0.md`
- `docs/aaa-exmorbus-ownership-matrix-v0.md`
- `docs/exmorbus-through-aaa-operating-model-v1.md`
