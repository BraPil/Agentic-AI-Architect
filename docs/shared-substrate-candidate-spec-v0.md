# Mouseion Shared Substrate Candidate Spec v0

## Purpose

This document defines the first candidate shared substrate for `Mouseion`, which could eventually
serve both Agentic-AI-Architect and ExMorbus, and later other specialist systems.

It exists to prevent premature new-repo creation while still making real cross-system contracts
explicit inside the current repository.

This is a candidate spec, not yet a fully accepted extracted package.

`Mouseion` is the proper name for the shared substrate, ontological framework, and architectural
grounds on which future specialist systems may be built.

For now, Mouseion remains housed inside AAA.

## Why This Spec Exists Now

The ExMorbus-through-AAA process is expected to reveal which contracts are truly reusable.

However, some candidate shared concerns are already clear enough to name:

- provenance
- confidence
- evaluation
- event naming
- namespace progression
- task and result contracts
- review and approval states

Capturing them now gives the ExMorbus PoC a stable starting point without forcing a new shared
repo before the patterns have been validated.

## Scope

This v0 substrate is intentionally narrow.

It covers only the contracts most likely to be reused across systems.

It does not define:

- a global control plane
- a shared runtime
- shared infrastructure deployment
- shared auth across all future systems
- cross-system monetization or market protocol

It also does not define ExMorbus runtime ownership, domain corpus, or medically specific evidence
semantics. Those remain outside Mouseion and inside ExMorbus.

## Mouseion Candidate Contract Areas

### 1. Entity identity

Every durable cross-system object should have:

- stable id
- type
- version
- created_at
- updated_at
- producer system

Suggested common fields:

```json
{
  "id": "uuid",
  "entity_type": "knowledge_entry",
  "schema_version": "v1",
  "producer": "agentic-ai-architect",
  "created_at": "2026-03-14T00:00:00Z",
  "updated_at": "2026-03-14T00:00:00Z"
}
```

### 2. Provenance

Every meaningful answer, artifact, or evaluation should be traceable.

Suggested common provenance fields:

- source_type
- source_uri
- extracted_at
- extraction_method
- agent_id
- run_id
- citation_span or evidence_ref

This is critical for both AAA and ExMorbus, even though ExMorbus will likely need richer medical
evidence metadata.

### 3. Confidence

Confidence semantics must be explicit and comparable.

Suggested shared model:

- `confidence_score`: float 0.0 to 1.0
- `confidence_label`: low, medium, high
- `confidence_basis`: deterministic_rule, retrieved_evidence, evaluator_score, human_review

This keeps future systems from inventing incompatible confidence language.

### 4. Evaluation contract

Both AAA and ExMorbus will need a reusable shape for scoring outputs.

Suggested shared evaluation fields:

- target_id
- evaluator_id
- evaluation_type
- criteria_scores
- overall_score
- expected_outcome_summary
- actual_outcome_summary
- pass_fail
- refinement_allowed
- feedback_summary

AAA's earlier docs work already suggests two additional rules that should carry into this substrate
candidate:

- evaluations should be persistable so later weighting and routing can learn from historical outcomes
- evaluation payloads should remain machine-readable first, with any human explanation rendered from the
  same stored structure

### 5. Event naming

Cross-system events should follow one stable shape.

Suggested event envelope:

```json
{
  "event_id": "uuid",
  "event_type": "artifact.evaluated",
  "schema_version": "v1",
  "producer": "exmorbus",
  "occurred_at": "2026-03-14T00:00:00Z",
  "subject_id": "uuid",
  "payload": {}
}
```

Suggested naming convention:

`domain.object.action`

Examples:

- `knowledge.entry.ingested`
- `task.requested`
- `artifact.submitted`
- `artifact.evaluated`
- `feedback.issued`
- `contract.revised`

### 6. Namespace progression

AAA and ExMorbus both need durable namespace rules.

Suggested shared concepts:

- namespace id
- parent namespace
- write policy
- review policy
- maturity stage

ExMorbus will specialize this into the training funnel:

- health
- medicine
- oncology
- novel therapies
- cancer vaccines

AAA will keep its own knowledge namespaces, but the contract shape for namespace metadata should
be reusable.

The earlier segment-aware evaluation work in AAA suggests a useful analogue here: ExMorbus may need
domain-stage-aware evaluation and routing, where the same task or artifact is judged differently
depending on where it sits in the health-to-oncology progression funnel.

### 7. Task and result contracts

The ExMorbus PoC will likely surface generic reusable task contracts.

Suggested shared base task request fields:

- task_id
- task_type
- requester_id
- requested_capability
- context_refs
- success_criteria
- due_by
- namespace

Suggested shared base task result fields:

- task_id
- producer_id
- result_type
- summary
- artifacts
- confidence
- provenance
- recommended_next_action

### 8. Review states

Low-confidence and high-impact outputs need a common review state language.

Suggested common review states:

- draft
- under_evaluation
- needs_refinement
- accepted
- rejected
- superseded

These should be treated as explicit contract values rather than UI states only, because AAA's prior
repo-memory and evaluation work already showed that hidden state leads to weak auditability and poor
reuse.

## Reused AAA Patterns

This candidate substrate is no longer based only on abstract future-system reasoning. It now also
inherits concrete patterns already documented inside AAA:

- canonical machine-readable contracts from `docs/first-answer-contract-v0.md`
- structured overlay and context adjustment fields from `docs/enterprise-overlay-fields-v0.md`
- scored evaluation surfaces from `docs/initial-eval-question-set-v0.md`
- explicit retrieval and evidence weighting from `docs/source-weighting-model-v0.md`
- learned weighting from persisted evaluation history in `docs/source-weighting-model-v2.md`
- durable memory and logging discipline from `docs/repo-memory-protocol.md`

The ExMorbus PoC is the first real chance to test whether those patterns are product-general or only
fit AAA's first answer-serving surface.

The first typed Mouseion shell pass for these reusable objects now begins in:

- `src/contracts/mouseion.py`
- `docs/mouseion-core-v0.md`
- `docs/exmorbus-only-boundary-v0.md`

## What ExMorbus Should Pressure-Test First

The first PoC should pressure-test these substrate candidates hardest:

1. task request and result contracts
2. evaluation and feedback contract
3. namespace progression metadata
4. provenance and confidence compatibility
5. review-state model

If these break down under the ExMorbus PoC, they are not ready for extraction.

## Extraction Criteria

Do not move Mouseion into a separate shared repo until all of the following are true:

1. AAA uses the contract in real execution or durable storage.
2. ExMorbus uses the contract in a real PoC workflow.
3. At least one contract survives revision without major conceptual change.
4. The cost of duplicate maintenance exceeds the cost of extraction.

## Immediate Next Step

Keep Mouseion housed inside AAA while:

1. Mouseion Core contracts are formalized in AAA.
2. ExMorbus implements against them in its own repo.
3. AAA learns from architectural performance feedback rather than absorbing ExMorbus domain
  knowledge.

## Related Documents

- `docs/mouseion-core-v0.md`
- `docs/exmorbus-only-boundary-v0.md`
- `docs/aaa-exmorbus-ownership-matrix-v0.md`

Use this substrate candidate spec as the constraint layer for the first ExMorbus shell ontology and
the first MoltBook-like PoC loop.