# Mouseion to ExMorbus Code Boundary Map v0

## Purpose

This document maps the first Mouseion Core v0 shell objects to the ExMorbus runtime objects that
already exist in code.

This is not a speculative architecture map.

It is based on the current ExMorbus implementation in:

- `workspaces/ExMorbus-v0.1/agents/models.py`
- `workspaces/ExMorbus-v0.1/agents/base.py`
- `workspaces/ExMorbus-v0.1/agents/state.py`
- `workspaces/ExMorbus-v0.1/agents/team.py`
- `workspaces/ExMorbus-v0.1/agents/registry.py`

## Boundary Rule

Mouseion should absorb only the reusable shell shape.

ExMorbus should keep:

- medical-domain semantics
- research-lifecycle domain objects
- product runtime policy and orchestration decisions
- disease and therapy specific evidence structures

## Actual ExMorbus Shell-Adjacent Objects

The following ExMorbus classes are the current bridge candidates.

### `AgentCapability`

File:

- `workspaces/ExMorbus-v0.1/agents/base.py`

Why it matters:

- It already describes an agent as an inspectable actor.
- It contains stable identity, tier, phase, description, input type, output type, and tool/skill
  requirements.

Mouseion mapping:

- `AgentCapability` -> `AgentProfileV0`

ExMorbus-only remainder:

- tier and phase semantics as currently used by ExMorbus orchestration
- required tool and required skill vocabulary as product runtime choices

### `ResearchQuery`

File:

- `workspaces/ExMorbus-v0.1/agents/models.py`

Why it matters:

- It is the current entry object for asking the ExMorbus system to do work.
- It already contains stable identity, scope, constraints, and context metadata.

Mouseion mapping:

- `ResearchQuery` -> `TaskRequestV0`

ExMorbus-only remainder:

- `disease_or_topic`
- disease-specific question framing
- research-specific priority semantics

### `TeamMission`

File:

- `workspaces/ExMorbus-v0.1/agents/models.py`

Why it matters:

- It is the stronger orchestration-level work request in ExMorbus.
- It wraps a `ResearchQuery` with execution pattern, budget, iteration limits, and success criteria.

Mouseion mapping:

- `TeamMission` -> `TaskRequestV0`

ExMorbus-only remainder:

- `assigned_pattern`
- `budget_limit`
- `time_limit_weeks`
- iteration policy for research teams

### `AuditEntry`

File:

- `workspaces/ExMorbus-v0.1/agents/models.py`

Why it matters:

- It is the clearest current event-shaped shell object in ExMorbus.
- It already captures producer, action, phase, timestamp, status, and details.

Mouseion mapping:

- `AuditEntry` -> `EventEnvelopeV0`

ExMorbus-only remainder:

- research-phase labels as currently defined by ExMorbus

### `ValidationReport`

File:

- `workspaces/ExMorbus-v0.1/agents/models.py`

Why it matters:

- It is a structured judgment of whether a protocol should proceed.
- It already includes decision, issues, recommendations, risk and compliance reasoning.

Mouseion mapping:

- `ValidationReport` -> `EvaluationV0`
- `ValidationReport` -> `FeedbackV0`

ExMorbus-only remainder:

- protocol-specific power analysis
- ethics review content
- regulatory compliance content
- revised sample size logic

### `QualityCheckpoint`

File:

- `workspaces/ExMorbus-v0.1/agents/models.py`

Why it matters:

- It is another evaluation-shaped object with an explicit pass/fail decision.

Mouseion mapping:

- `QualityCheckpoint` -> `EvaluationV0`

ExMorbus-only remainder:

- ExMorbus compliance status vocabulary
- checkpoint-specific audit notes

### `RefinementProposal`

File:

- `workspaces/ExMorbus-v0.1/agents/models.py`

Why it matters:

- It is the clearest current bounded refinement object.
- It already captures lessons, new questions, new hypotheses, and action choice.

Mouseion mapping:

- `RefinementProposal` -> `FeedbackV0`

ExMorbus-only remainder:

- `new_hypotheses`
- `revised_query`
- disease-research iteration semantics

### `TeamResult`

File:

- `workspaces/ExMorbus-v0.1/agents/models.py`

Why it matters:

- It is the current shell-adjacent summary of completed work.
- It includes mission identity, team status, findings, next steps, duration, and audit trail.

Mouseion mapping:

- `TeamResult` -> `TaskResultV0`
- `TeamResult` -> `KnowledgeRecordV0`

ExMorbus-only remainder:

- hypothesis result lists as currently represented
- analysis and meta-analysis payloads
- duration and cost semantics specific to ExMorbus team execution

## Objects That Stay ExMorbus-Only

The following classes remain ExMorbus-only in the current pass:

- `Source`
- `EvidenceSignal`
- `EvidenceEvaluation`
- `Hypothesis`
- `ToolRecommendation`
- `ResearchPlan`
- `ExperimentProtocol`
- `ExecutionStatus`
- `ExperimentPackage`
- `AnalysisResult`
- `StrategicDirective`
- `Prediction`
- `MetaAnalysisReport`

Reason:

These are not just shell wrappers.

They encode ExMorbus's research lifecycle, scientific evidence semantics, experimental workflow, or
portfolio strategy model.

## First Adapter Rule

The first ExMorbus adapter layer should:

- adapt current ExMorbus runtime objects into Mouseion-compatible payloads
- validate them against AAA Mouseion contracts when AAA is available
- avoid creating a hard runtime dependency that prevents ExMorbus from running on its own

## First Adapter Surface

The first adapter surface should cover:

- `AgentCapability` -> `AgentProfileV0`
- `ResearchQuery` -> `TaskRequestV0`
- `TeamMission` -> `TaskRequestV0`
- `AuditEntry` -> `EventEnvelopeV0`
- `ValidationReport` -> `EvaluationV0`
- `ValidationReport` -> `FeedbackV0`
- `QualityCheckpoint` -> `EvaluationV0`
- `RefinementProposal` -> `FeedbackV0`
- `TeamResult` -> `TaskResultV0`
- `TeamResult` -> `KnowledgeRecordV0`

## Related Files

- `src/contracts/mouseion.py`
- `docs/mouseion-core-v0.md`
- `docs/exmorbus-only-boundary-v0.md`
- `workspaces/ExMorbus-v0.1/agents/mouseion_adapter.py`
