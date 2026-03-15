# AAA ExMorbus Ownership Matrix v0

## Purpose

This document defines the current ownership boundary between:

- `Agentic-AI-Architect` as the architectural intelligence and decision surface
- `ExMorbus` as the medically specific product and research environment
- the thin set of Mouseion shared-substrate candidates that should still be designed inside AAA first

AAA should be thought of as the architect, design lab, and institutional memory.

ExMorbus should be thought of as the actual medically focused school, world, and operating entity
that uses the environment AAA helped design.

The MoltBook-like environment belongs to ExMorbus, not AAA.

It exists to stop shell work from drifting into one of two failure modes:

- pushing domain-specific ExMorbus content into AAA
- pushing reusable architectural and contract reasoning out of AAA too early

## Governing Rule

Use this rule first:

- if the work is architectural data gathering, architecture evaluation, reusable contract design, or
  decision method, it belongs in AAA
- if the work is medically specific, oncology specific, cancer-research specific, or only meaningful
  inside the ExMorbus product loop, it belongs in ExMorbus
- if the work looks reusable across systems, treat it as a shared-substrate candidate, but still
  design and pressure-test it inside AAA before extracting it elsewhere

## Ownership Categories

### `AAA`

AAA owns:

- architecture research and trend discovery
- architecture decision support
- reusable contract and schema design
- evaluation method and scoring doctrine
- provenance, confidence, and review-state conventions
- branch, repo, and ecosystem sequencing decisions
- durable ontology capture about what future systems should inherit
- long-term learning about how successful its solutions are for the systems it designs

AAA does not own ExMorbus's ongoing medical knowledge corpus just because AAA helped design the
system that produced it.

### `ExMorbus`

ExMorbus owns:

- medically specific data and workflows
- oncology and cancer-vaccine funnel design
- cancer-research opportunity discovery and execution loops
- medically specific routing thresholds and domain calibration
- research artifacts that only make sense in the medical domain
- product-specific shell details that do not generalize beyond ExMorbus
- the MoltBook-like runtime environment in which its agents live and work
- its own discoveries, analyses, and domain outputs
- its own API and CLI interfaces for dissemination of that domain knowledge to other systems

### `Shared Candidate`

Shared candidates are Mouseion candidates:

- probably reusable across systems
- still first designed and judged inside AAA
- only later extracted if reuse becomes real rather than speculative

## Example Ownership Matrix

| Item | Owner | Why |
|------|-------|-----|
| Generic `EventEnvelope` with `event_id`, `event_type`, `producer`, `schema_version`, `occurred_at`, and `payload` | Shared candidate | Cross-system contract shape, not product-specific behavior |
| `DomainStage` ladder for `broad health -> clinical medicine -> oncology -> novel therapies -> cancer vaccines` | ExMorbus | Domain progression is medically specific |
| Generic `Evaluation` record with `criteria_scores`, `overall_score`, `feedback_summary`, `review_state`, and `provenance_refs` | Shared candidate | Reusable scoring and review surface across systems |
| Medical evidence object with `trial_phase`, `modality`, `tumor_type`, `preclinical_vs_clinical`, and `mechanism_of_action` | ExMorbus | Oncology-specific evidence semantics |
| Routing score model using `utility`, `evidence_quality`, `execution_reliability`, `domain_fit`, and `refinement_responsiveness` | Shared candidate | General shell logic for task selection and evaluation-aware routing |
| Thresholds and calibration for choosing the best oncology agent for a cancer-research task | ExMorbus | Product and domain-specific routing policy |
| Generic `TaskRequest` contract with `task_id`, `requested_capability`, `success_criteria`, `namespace`, `context_refs`, and `due_by` | Shared candidate | Reusable request shape across systems |
| Generic `AgentProfile` contract with `identity`, `capabilities`, `availability`, `trust_score`, and `permitted_namespaces` | Shared candidate | Shared shell object for agent-native systems |
| Source-ingest pipeline for LinkedIn PDFs, architecture blogs, tool docs, and framework trend tracking | AAA | Architecture intelligence gathering belongs in AAA |
| Corpus-ingest pipeline for oncology papers, therapeutic hypotheses, experimental results, and medical evidence bundles | ExMorbus | Domain corpus and research evidence are product-specific |
| API or CLI surfaces used to disseminate ExMorbus discoveries to other systems such as biomedical engineering systems | ExMorbus | ExMorbus owns its domain outputs and the interfaces used to share them |
| Decision memo about popularity-based vs capability-based vs evaluation-history-based routing | AAA | Architecture decision-making belongs in AAA |
| `KnowledgeRecord` shape with `schema_version`, `producer`, `created_at`, `confidence_basis`, `provenance_refs`, `evaluation_history`, and `review_state` | Shared candidate | Durable reusable memory object |
| Weekly AI-architecture change-detection and answer-generation loop | AAA | This is AAA's core product behavior |
| Opportunity-discovery loop for underexplored cancer-vaccine directions | ExMorbus | Domain-specific opportunity generation |
| Keep/modify/drop comparison of MoltBook mechanics for ExMorbus | AAA | Architecture inheritance decisions belong in AAA even when the target product is ExMorbus |
| Long-term storage of architectural feedback about how well the lobster shell is performing for ExMorbus | AAA | AAA should learn from the success or weakness of its designs rather than absorbing ExMorbus domain content |

## Inference Rules For Future Decisions

When classifying new work, use these inference rules.

### Put it in AAA when

- it compares architectural patterns
- it defines reusable schemas or DTOs
- it decides how systems should evaluate, route, or review outputs in general
- it gathers architecture-facing research signals
- it records decisions that should guide more than one product
- it records how well AAA-designed architecture is performing for a downstream system

### Put it in ExMorbus when

- it references oncology, cancer vaccines, therapeutic modalities, or medical evidence semantics
- it calibrates routing or scoring for medical-domain work specifically
- it governs product behavior that would make no sense outside ExMorbus
- it ingests or shapes the medical-domain corpus
- it stores, serves, or disseminates ExMorbus discoveries as domain knowledge

### Treat it as a shared candidate when

- it feels product-agnostic
- it would likely be reused by a second specialist system
- it expresses shell-level structure rather than domain substance
- it still needs pressure-testing before extraction

## Immediate Implication For Shell Work

The next typed shell pass should be split conceptually like this:

### Design in AAA first

- `EventEnvelope`
- `AgentProfile`
- `TaskRequest`
- `TaskResult`
- `Evaluation`
- `Feedback`
- `KnowledgeRecord`
- `ReviewState`

These should be designed as reusable shell objects and treated as Mouseion candidates.

### Leave in ExMorbus

- medical evidence objects
- oncology domain stages
- cancer-research opportunity types
- oncology-specific scoring thresholds
- product-specific namespace rules where they stop being generic shell metadata and become medical-domain policy

## Practical Rule For Implementation

If there is uncertainty, prefer this sequence:

1. define the shell object in AAA if it looks reusable
2. keep domain enrichments and policy layers in ExMorbus
3. only extract the shared layer later if at least two real systems reuse it

This preserves the lobster shell idea without letting the shell absorb product-specific flesh.

It also preserves a critical ownership rule:

- AAA learns architectural lessons from ExMorbus
- ExMorbus keeps ownership of ExMorbus knowledge

## Related Documents

- `docs/shared-substrate-candidate-spec-v0.md`
- `docs/mouseion-core-v0.md`
- `docs/exmorbus-only-boundary-v0.md`
- `docs/exmorbus-shell-ontology-v1.md`
- `docs/exmorbus-through-aaa-operating-model-v1.md`
- `docs/ecosystem-sequencing-memo.md`
- `docs/branch-strategy-summary.md`