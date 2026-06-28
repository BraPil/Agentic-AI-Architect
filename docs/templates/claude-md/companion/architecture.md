# Architecture — [PROJECT NAME]

> System design, component map, data flows, and phase roadmap.
> Updated when structure changes. Diagrams reflect code, not aspirations.

---

## System Overview

**What it does in one paragraph:**
[Describe the system's core function, inputs, outputs, and primary value proposition.
This is the paragraph a new engineer reads first to understand what they're working on.]

**Architecture style:** [e.g., event-driven microservices / monolith / multi-agent pipeline]

---

## Component Map

```
[Directory / component tree. Match the actual repo structure exactly.]

src/
├── [component_a]/     ← [one-line responsibility]
│   ├── [file.py]      ← [one-line responsibility]
│   └── [file.py]      ← [one-line responsibility]
├── [component_b]/     ← [one-line responsibility]
└── [component_c]/     ← [one-line responsibility]

config/                ← all settings via env vars ([PREFIX]_ namespace)
docs/                  ← specifications, decision records, companion files
tests/                 ← mirrors src/ structure
```

---

## Data Flow

**Primary cycle (one complete operation):**

```
[SourceA]
  ↓ [data type: e.g., list[dict]]
[ComponentB]
  ↓ [data type]
[ComponentC] ←── [parallel branch]
[ComponentD] ←──
  ↓ [data type]
[Sink / Store]
```

**Key invariants:**
- [Invariant 1: e.g., All external content is sanitized before reaching ComponentC]
- [Invariant 2: e.g., ComponentB never writes to storage directly]
- [Invariant 3: e.g., The Orchestrator moves data; it does not transform it]

---

## Interfaces and Contracts

### External interfaces (what other systems call)

| Interface | Type | Version | Schema Location |
|-----------|------|---------|-----------------|
| [API endpoint] | [REST/MCP/webhook] | [v1] | [file path] |
| [Event format] | [JSON/Protobuf] | [v1] | [file path] |

**Schema stability policy:** major version bump for breaking changes; 90-day deprecation notice.

### Internal contracts (what agents/modules promise each other)

| Contract | From | To | Input Type | Output Type |
|----------|------|----|-----------|-------------|
| [BaseAgent._execute()] | Orchestrator | All agents | Any | Any |
| [KnowledgeBase.store()] | All agents | KnowledgeBase | KnowledgeEntry | bool |

---

## Dependency Graph

*List significant dependencies and the reason each was chosen. Update when adding.*

| Package | Version Constraint | Purpose | Upgrade Trigger |
|---------|-------------------|---------|-----------------|
| [package] | [>=major.minor] | [why] | [when to upgrade] |

*No new dependency without an entry here and in `docs/decision-log.md`.*

---

## Phase Roadmap

| Phase | Name | Status | Success Criteria |
|-------|------|--------|-----------------|
| P0 | Foundation | [✅/🔄/⬜] | [e.g., Base agent runs, tests green, knowledge store persists] |
| P1 | [Name] | [status] | [criteria] |
| P2 | [Name] | [status] | [criteria] |
| P3 | [Name] | [status] | [criteria] |

**Current phase:** P[X]

**What "done" means for the current phase:**
- [Criterion 1]
- [Criterion 2]
- [Criterion 3]

---

## Architectural Decisions Summary

*One-line record of significant choices. Full context in `adr/` and `docs/decision-log.md`.*

| Decision | Chosen | Rejected | ADR |
|----------|--------|----------|-----|
| [Decision area] | [Choice made] | [Choice rejected] | [adr/0001-*.md] |

---

## Known Technical Debt

| Item | Impact | Resolution Plan | Priority |
|------|--------|----------------|----------|
| [Debt item] | [What breaks if ignored] | [How to fix when we get to it] | [H/M/L] |

*Debt is not shame — it's deferred decisions. Track it explicitly or it becomes invisible.*

---

*Last updated: [YYYY-MM-DD]*
