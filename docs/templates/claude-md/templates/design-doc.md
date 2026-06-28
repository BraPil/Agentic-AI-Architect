# Design Doc — [FEATURE NAME]

**Author:** [name]  
**Date:** [YYYY-MM-DD]  
**Status:** [Draft | In Review | Approved | Implemented | Abandoned]  
**Phase:** [P0–P7]  
**Reviewers:** [names]

---

## Summary

[Two to three sentences: what this doc proposes, what problem it solves, and the recommended approach.]

---

## Problem Statement

[What is broken, missing, or painful? Who experiences this problem? What does the world look like
without this feature? Quantify the impact where possible.]

---

## Goals

- [Goal 1: measurable, specific]
- [Goal 2: measurable, specific]

## Non-Goals

- [What this design explicitly does not address]
- [What is deferred to a later phase]

---

## Background

[Context a reviewer needs to understand the problem space. Link to relevant ADRs, prior designs,
or external resources. Do not reproduce what's already in linked docs.]

---

## Design

### Overview

[High-level description of the proposed solution. Include a diagram if the system interaction
is complex. Keep it conceptual here — details go in the subsections below.]

### Data Flow

```
[Diagram or description of how data moves through the new or changed components]
```

### Interface Changes

**New or changed public interfaces:**

```python
# Before (or "New interface"):
[signature / schema / API endpoint]

# After (or omit if new):
[signature / schema / API endpoint]
```

**Backward compatibility:** [How existing consumers are affected. Breaking changes require a
major version bump and 90-day deprecation notice per `docs/governance.md`.]

### Implementation Plan

| Step | Description | Estimated Size | Phase |
|------|-------------|---------------|-------|
| 1 | [First implementation step] | [S/M/L] | [P-current.X] |
| 2 | [Second step] | [S/M/L] | [P-current.X] |

### Testing Strategy

- **Unit tests:** [what will be unit-tested and how]
- **Integration tests:** [what requires integration testing]
- **Evaluation set:** [if AI components, how correctness will be measured]
- **Performance:** [any benchmarks needed before shipping]

---

## Alternatives Considered

### Alternative 1 — [Name]

[Brief description]

**Why rejected:** [Specific reason aligned with the Architectural Constitution]

### Alternative 2 — [Name]

[Brief description]

**Why rejected:** [Specific reason]

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| [Risk 1] | [H/M/L] | [H/M/L] | [What reduces the risk] |
| [Risk 2] | [H/M/L] | [H/M/L] | [What reduces the risk] |

---

## Open Questions

- [ ] [Question that needs an answer before this can be approved]
- [ ] [Question that can be resolved during implementation]

---

## References

- [ADR or decision that constrains this design]
- [External doc or prior art]

---

*Design docs are not contracts. They're shared thinking. Implementation may diverge from
this doc — when it does, update the doc or file a new one.*
