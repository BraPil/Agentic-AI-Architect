# ExMorbus State Gap Analysis v0

## Purpose

This document is AAA's current analysis of:

- where ExMorbus is now
- where ExMorbus says it wants to go
- what must be built or proven to get from here to there

It is written from AAA's role as ExMorbus's architectural oracle and first real downstream design
customer review surface.

## Why AAA Owns This Analysis

Per `docs/exmorbus-through-aaa-operating-model-v1.md` and
`docs/aaa-exmorbus-ownership-matrix-v0.md`, AAA should retain:

- architectural assessment
- reusable contract implications
- sequencing judgment
- gap analysis
- lessons about what downstream systems need from the shell

ExMorbus should retain the medical-domain implementation and the medical knowledge outputs.

This document therefore analyzes ExMorbus as a downstream runtime system, not as a source of
medical-domain truth.

## Executive Assessment

ExMorbus is no longer a vague MCP-centric scaffold.

It is now a partially verified runtime foundation with:

- native Mouseion shell interoperability
- validated core runtime seams
- optional LangGraph orchestration that works in real execution
- optional MCP integrations with proper opt-in boundaries
- clearer runtime language and a more disciplined architecture direction

That is real progress.

However, ExMorbus is still missing the single most important proof point required for the next stage:

it does not yet have a trustworthy end-to-end research workflow that starts from a real question,
passes through evidence handling and agent execution, and ends in a reproducible, auditable,
reviewable output.

AAA's judgment is therefore:

ExMorbus has largely validated its shell and integration posture, but it has not yet validated its
first useful product loop.

## Where ExMorbus Is Now

### 1. Runtime Identity Is Much Clearer

ExMorbus now describes itself as:

- direct-code-execution first
- reusable-skills second
- optional LangGraph when explicit graph routing is useful
- optional MCP only when an external tool server is genuinely worth the cost

This is materially better than the earlier MCP-centric framing because it reduces architectural drift
and lowers the risk of integration-first overbuilding.

### 2. Shell and Contract Work Has Real Substance

ExMorbus has already implemented and validated runtime-level Mouseion attachment for the key shell-like
objects that AAA cares about architecturally:

- `ResearchQuery`
- `TeamMission`
- `AuditEntry`
- `ValidationReport`
- `QualityCheckpoint`
- `RefinementProposal`
- `AgentCapability`
- `TeamResult`

This matters because it means ExMorbus is no longer only theorizing about reusable shell shape. It is
actually instantiating it in live runtime objects.

### 3. Validation Quality Is Better Than Earlier Scaffolding Suggested

ExMorbus has moved beyond isolated adapter tests and now has:

- broader runtime validation
- manual team execution coverage
- import-safety coverage
- graph-backed runtime coverage
- separate default and optional test surfaces

That is exactly the kind of evidence AAA should want from a downstream design customer.

### 4. ExMorbus Is Still Pre-Workflow

The major missing reality is that ExMorbus does not yet have:

- a real evidence ingestion path tied to one research loop
- a trustworthy query-to-result loop
- a calibrated evidence-quality and acceptance path in real runtime use
- a validated end-user or operator-facing output path

So the shell has improved faster than the product loop.

## Where ExMorbus Wants To Go

Reading the ExMorbus docs, journey review, and AAA's earlier operating-model docs together, the
destination is not a simple single-agent medical tool.

The intended destination is closer to this:

- a medically focused agent-native research environment
- durable, auditable, multi-step research workflows
- agent collaboration and routing across specialized roles
- evidence-grounded research synthesis
- eventually a MoltBook-like or agent-social environment for medical discovery and experimentation

In shorter form:

ExMorbus wants to become a trustworthy agent-native medical research world, not just a runtime shell.

That destination implies several layers of maturity that do not yet exist in practice.

## The Core Gap

AAA sees the central gap as:

validated shell -> validated workflow -> validated product environment

ExMorbus is currently between the first and second stages.

It has enough shell and runtime structure to stop debating its basic posture, but not enough real
workflow proof to justify scaling into a richer research world.

## What ExMorbus Needs From Here To There

### A. The First Trustworthy Workflow

This is the immediate highest-priority requirement.

ExMorbus needs one narrow but fully inspectable workflow that proves all of the following together:

1. a real `ResearchQuery` enters the system
2. evidence is collected from an explicitly supported source set
3. the team or agent path executes in a bounded, understandable sequence
4. quality and validation objects are populated for real reasons
5. the output becomes a `TeamResult` with audit trail and reviewable structure
6. the result is reproducible enough to be tested again

Until this exists, ExMorbus is still architecturally promising but product-wise unproven.

### B. Minimum Viable Evidence Ingestion

ExMorbus needs a first source-policy decision and ingest path.

Not a giant ingestion system.

It needs a minimum viable evidence path with:

- one or two source families only
- explicit normalization rules
- explicit provenance handling
- explicit evidence-quality criteria
- explicit failure handling when evidence is weak or conflicting

AAA should strongly prefer a narrow, auditable ingest path over a broad but weak one.

### C. Acceptance And Review Logic

ExMorbus needs a clearer rule for when an output is:

- accepted
- provisional
- rejected
- sent for refinement

The existence of `ValidationReport`, `QualityCheckpoint`, `RefinementProposal`, and `AuditEntry`
means the shell already anticipates this. The missing step is proving the review logic in real
workflow behavior rather than only in model shape.

### D. Stable Workflow-Level Contracts

ExMorbus should avoid changing the shell contracts casually now that the key objects are wired.

From AAA's perspective, the next useful pressure test is not "invent more shell types."
It is "prove the current shell is sufficient for the first research loop, and record where it breaks."

### E. Product-Specific Domain Calibration

AAA should not own this directly, but ExMorbus will need:

- domain-specific evidence-quality calibration
- oncology- and therapy-specific routing logic
- medically specific source prioritization
- medically meaningful scoring thresholds

That is where ExMorbus-specific flesh begins in earnest.

## What AAA Should Want ExMorbus To Avoid

### 1. Avoid Re-centering Around MCP

The architectural realignment away from MCP-centric thinking was correct.

Reversing that now would recreate the same failure mode:

tool transport becomes more developed than the product behavior.

### 2. Avoid Premature Product Surface Work

Web UI, broad API surface, and heavy operator interfaces should not lead the next phase.

They should follow after the first credible workflow is proven.

### 3. Avoid Contract Churn Without Pressure-Test Evidence

The shell should now be exercised, not constantly redesigned.

AAA should only request shell-level changes when the first workflow exposes an actual insufficiency.

### 4. Avoid Broad Ingestion Before Narrow Workflow Credibility

A larger corpus without a proven workflow mostly produces harder-to-debug ambiguity.

## AAA's Recommended Sequence For ExMorbus

### Stage 1. Prove One Workflow

Build one narrow query-to-result loop.

Acceptance criteria:

- deterministic enough to test repeatedly
- auditable enough to inspect
- structured enough to review
- narrow enough to reason about fully

### Stage 2. Pressure-Test The Existing Shell

While implementing that workflow, record:

- which shell objects were sufficient
- which fields were missing
- where review-state semantics were unclear
- where provenance or confidence needs expansion

This is the key feedback AAA wants from ExMorbus next.

### Stage 3. Add Minimal Durability Only Where It Helps

Use Temporal, LangGraph, or other orchestration complexity only where the first workflow clearly
benefits.

Do not use those systems just because they exist.

### Stage 4. Expand Retrieval And Evidence Scope

Only after the first workflow is credible should ExMorbus widen:

- source coverage
- domain breadth
- retrieval complexity
- collaboration patterns

### Stage 5. Build Operator And Product Surfaces

Once workflow quality is real, then ExMorbus can justify:

- a query surface
- operator dashboards
- product interfaces
- broader collaboration mechanics

## What AAA Needs To Learn From ExMorbus Next

The next high-value architectural learning AAA should extract from ExMorbus is not another abstract
ontology pass.

It is this set of downstream signals:

- which Mouseion shell fields survive first real workflow use
- which workflow-review mechanics are missing or awkward
- whether provenance and confidence are sufficient in practice
- which objects remain truly reusable versus ExMorbus-only
- where the architecture underestimates domain-specific calibration needs

Those are the observations that should later refine Mouseion and AAA's reusable architectural doctrine.

## Concrete Output AAA Should Ask ExMorbus To Produce Next

AAA should want ExMorbus to produce the following next artifact set:

1. One implemented query-to-result workflow.
2. One explicit first-source ingest policy.
3. One workflow acceptance and review rubric.
4. One recorded shell-gap review after the workflow runs.
5. One short keep/modify/drop memo for the current shell after pressure-testing.

If ExMorbus produces those five things, AAA will have the right evidence to guide the next round of
architectural refinement.

## Final Judgment

ExMorbus is not stuck.

It has successfully moved from "unclear architecture and transport-first drift" to
"clearer runtime posture and validated shell foundation."

But it has not yet crossed the harder boundary:

from validated architecture components to validated useful research behavior.

That boundary is now the only one that matters most.

AAA's recommendation is therefore straightforward:

do not broaden ExMorbus first.
prove one trustworthy research workflow first.

Only after that should ExMorbus scale outward.