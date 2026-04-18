---
wiki_id: repo_dark_factory
type: repo_page
persona: cole_medin
repo: coleam00/dark-factory-experiment
foundational: true
raw_source: data/wiki/raw/cole_medin/github_coleam00_dark-factory-experiment_readme.md
status: draft
last_updated: 2026-04-18
aaa_relevance:
  - P4 — orchestration pattern: GitHub as shared state machine
  - P6 — self-improvement loop via automated issue→PR→merge pipeline
  - P3.3 — holdout validation pattern (validator never reads implementation plan)
---

# coleam00/dark-factory-experiment

## What It Is

A live autonomous software factory. Specs go in (as GitHub Issues filed by humans), software comes out. Everything between filing and production — triage, implementation, code review, testing, merging — is handled by Archon workflows running on a cron schedule every 4–6 hours.

The application being built is a dark-mode AI chat app for YouTube video Q&A (RAG over transcripts). But the **factory** building it is the point.

## Stack

1. **Archon** — the workflow engine. Stitches coding agent sessions with deterministic steps (bash, `gh` calls, branching) into end-to-end workflows you actually trust. Lives in `.archon/workflows/`.
2. **Claude Code** — the coding agent. Holds file editing, bash, `gh`, and web fetch tools. Executes inside each Archon AI node.
3. **MiniMax M2.7** — the model (routed via Claude Code). Chosen for cost/throughput: multi-hour daily workflow runs at Anthropic subscription rates would hit limits.

## GitHub as State Machine

The orchestrator holds no state. It reads GitHub labels and decides what to do next.

```
Issues:   factory:triaging → factory:accepted → factory:in-progress → (PR) or factory:rejected
PRs:      factory:implementing → factory:needs-review → factory:approved (auto-merged)
                                                      → factory:needs-fix → (max 2 retries) → factory:needs-human
Priority: priority:critical | high | medium | low  (drives work ordering)
```

## Non-Negotiable Rules (From Prior Dark Factory Research)

1. **Validator never reads the implementation plan** — checks outcome against the issue only. Prevents agents from gaming their own acceptance criteria. (StrongDM holdout pattern.)
2. **Triage has only two verdicts: accept or reject.** No "needs human" inbox.
3. **Governance files (`MISSION.md`, `FACTORY_RULES.md`) can never be modified by the factory.**
4. **One workflow at a time.** Structural throughput cap.
5. **Flood protection.** Non-owner accounts capped at 3 issues/day.
6. **Per-node budget caps** on every workflow node.

## Why It Matters for AAA

- **Phase 4 orchestration**: GitHub-as-state-machine is an alternative to a custom orchestrator. AAA's cycle runner is simpler, but the label-based routing idea could apply to AAA's task/approval queues.
- **Phase 6 self-improvement**: This is the reference implementation for the dark-factory pattern. When AAA needs to improve its own code, this repo shows exactly how to do it: Archon workflows, holdout validation, governance-protected files.
- **Holdout validation**: AAA's eval harness (P3.3) should implement the same principle — the evaluator scores against the original question/requirement, never the implementation.
