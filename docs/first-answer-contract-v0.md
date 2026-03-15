# First Answer Contract v0

## Purpose

This document defines the first answer contract for the Agentic AI Architect system.

The system needs a stable answer shape before it can be evaluated, improved, or consumed reliably by
other agents, dashboards, or humans.

This contract is the first formal step from "research repository" toward "queryable architecture
intelligence system."

## Why A Contract Is Needed

Without an answer contract, the system cannot reliably answer:

- what kinds of questions it supports first
- what fields every answer must include
- how confidence and evidence should be represented
- how a dashboard or downstream agent should consume responses
- how a human-readable answer should be derived from the same underlying output

The contract therefore becomes:

- the canonical answer shape
- the evaluation target for the first query set
- the handoff format for future agentic systems and dashboards

## v0 Design Decision

Canonical output should be machine-readable.

Human-readable responses should be rendered from the same underlying structured payload.

This preserves one source of truth while supporting:

- API and schema stability for downstream systems
- direct human querying for interactive use
- future dashboard and monitoring/control integrations

## Response Negotiation

The system should not maintain separate reasoning modes for humans and agents.

Instead, it should use one canonical contract and vary presentation through request metadata.

### Recommended request fields

- `caller_type`: `human` | `agent` | `dashboard` | `service`
- `response_mode`: `json` | `human` | `both`
- `detail_level`: `brief` | `standard` | `deep`
- `segment`: `startup` | `small-company` | `enterprise` | `cross-segment`
- `persona`: `architect` | `engineer` | `operator` | `executive`
- `time_horizon`: `now` | `4-weeks` | `quarter`

### Default behavior

- Default to `json` when no mode is provided.
- Interactive clients may ask a lightweight first question such as `Are you human?` or present a quick
  response-mode picker.
- FastAPI and other programmatic surfaces should allow callers to skip any prompt and provide explicit
  request parameters directly.

### Recommended implementation rule

- machine callers should always be able to request raw schema output without extra interaction
- human callers should be able to request rendered answers from the same payload
- when `response_mode=both`, the API should return canonical JSON plus a rendered summary field

## Current Governance Constraint

For the current cycle, governance, security, and auditability should be treated as important future
alignment constraints, but not as hard gating logic on all recommendations.

That means:

- the system should research and expose those dimensions
- the system should preserve fields needed by future Governance, SecOps, and Auditability systems
- the system may still prioritize moderate speed and broad discovery while those future systems are being
  planned

## v0 Supported Question Types

The first contract should support three tightly related question families.

### 1. Architecture recommendation under constraints

Example:

- What is the ideal architecture to meet the SLOs, SLIs, and SLAs for this project?

### 2. Current toolchain and tech-stack recommendation

Example:

- What is the ideal tech stack for this project currently?
- What are the ideal tools to accomplish this goal?

### 3. Change detection and near-term watchlist

Example:

- What are the most recent and impactful changes to the current paradigm?
- What is likely to become the ideal stack in the next 4 weeks?

These three question types should share a common payload so downstream systems do not need separate
adapters.

## Canonical v0 Payload

Every v0 answer should contain the following top-level fields.

```json
{
  "contract_version": "v0",
  "question_type": "architecture_recommendation",
  "segment": "enterprise",
  "persona": "architect",
  "time_horizon": "now",
  "summary": "Recommended architecture and why.",
  "recommendation": {},
  "enterprise_overlay": {},
  "tradeoffs": [],
  "evidence": [],
  "confidence": {},
  "watchlist": [],
  "reusable_artifacts": [],
  "next_actions": [],
  "freshness": {},
  "rendered_response": null
}
```

## Field Definitions

### `contract_version`

The schema version for the response payload.

### `question_type`

Allowed v0 values:

- `architecture_recommendation`
- `stack_recommendation`
- `change_watch`

### `segment`

The audience or operating context the answer is optimized for.

Allowed values:

- `startup`
- `small-company`
- `enterprise`
- `cross-segment`

### `persona`

The role for whom the answer is being rendered or tuned.

### `time_horizon`

The decision horizon being addressed.

Allowed values:

- `now`
- `4-weeks`
- `quarter`

### `summary`

Short canonical summary of the recommendation.

### `recommendation`

Structured recommendation object.

Examples:

- chosen orchestrator
- chosen vector store
- chosen evaluation stack
- recommended source strategy

### `enterprise_overlay`

Structured enterprise and segment-adjustment metadata.

Minimum v0 fields:

- `enterprise_safe_now`
- `reasoning`
- `key_requirements`
- `future_alignment_hooks`
- `segment_deltas`

Each `segment_delta` should explain how the recommendation shifts for a specific segment and what that
segment should prioritize.

### `tradeoffs`

Flat list of meaningful tradeoffs or caveats.

### `evidence`

List of evidence records used to support the answer.

Each evidence record should contain:

- `source_id`
- `title`
- `source_type`
- `evidence_tier`
- `freshness`
- `why_relevant`

Optional evidence fields may also be included when available:

- `source_name`
- `source_url`

### `confidence`

Structured confidence object.

Minimum fields:

- `score`
- `reasoning`
- `gaps`

### `watchlist`

Near-term items that may change the answer.

### `reusable_artifacts`

Candidate wrappers, IaC skeletons, templates, and reusable components suggested by the answer.

This field exists because one of the core user goals is to identify mostly unchanging artifact and IaC
opportunities despite changing tools.

### `next_actions`

Recommended next concrete steps.

### `freshness`

Metadata indicating the recency and validity window of the answer.

Minimum fields:

- `generated_at`
- `best_before`
- `sensitive_to_change`

### `rendered_response`

Optional human-readable rendering derived from the canonical payload.

Only populated when `response_mode=human` or `response_mode=both`.

## Human Rendering Rule

Human output should be generated from the canonical payload, not authored independently.

That means human answers should be a projection of:

- `summary`
- `recommendation`
- `tradeoffs`
- `evidence`
- `confidence`
- `watchlist`
- `next_actions`

This prevents divergence between what humans see and what downstream systems consume.

## Minimal Example

```json
{
  "contract_version": "v0",
  "question_type": "stack_recommendation",
  "segment": "enterprise",
  "persona": "architect",
  "time_horizon": "now",
  "summary": "Use LangGraph, PostgreSQL, pgvector, and FastAPI as the current baseline.",
  "recommendation": {
    "orchestrator": "LangGraph",
    "structured_store": "PostgreSQL",
    "vector_store": "pgvector",
    "api_surface": "FastAPI"
  },
  "tradeoffs": [
    "Temporal may be preferable later for durability-heavy enterprise workflows.",
    "Tooling choices should remain wrapper-friendly to allow rapid substitution."
  ],
  "evidence": [
    {
      "source_id": "influencer_allie_k_miller",
      "title": "Claude Code in 5 Minutes",
      "source_type": "public_article",
      "evidence_tier": "direct",
      "freshness": "2026-03",
      "why_relevant": "Shows practical adoption framing for AI coding workflows."
    }
  ],
  "confidence": {
    "score": 0.72,
    "reasoning": "Recommendation fits current ecosystem maturity and repo direction.",
    "gaps": [
      "More enterprise-specific validation sources are still needed.",
      "Some high-signal LinkedIn sources remain auth-blocked."
    ]
  },
  "watchlist": [
    "dynamic tool discovery",
    "runtime-loaded MCP patterns",
    "small language model operationalization"
  ],
  "reusable_artifacts": [
    "tool-wrapper interface",
    "response schema DTOs",
    "evaluation harness skeleton"
  ],
  "next_actions": [
    "Expand enterprise evidence sources.",
    "Define wrapper conventions for swappable tools.",
    "Create scoring rubric for architecture recommendation questions."
  ],
  "freshness": {
    "generated_at": "2026-03-08",
    "best_before": "2026-04-05",
    "sensitive_to_change": true
  },
  "rendered_response": null
}
```

## Immediate Implementation Implications

This contract means the next cycle should produce:

- a typed schema representation for the payload
- a first evaluation set based on the supported question types
- evidence-tier rules for sourced answers
- response-mode negotiation in the eventual FastAPI layer

## Related Documents

- `docs/phase-5-implementation-plan.md`
- `docs/ecosystem-sequencing-memo.md`
- `docs/influencer-tracker.md`
- `docs/influencer-source-registry.yaml`