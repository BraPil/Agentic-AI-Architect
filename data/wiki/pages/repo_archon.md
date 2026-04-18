---
wiki_id: repo_archon
type: repo_page
persona: cole_medin
repo: coleam00/Archon
foundational: true
raw_source: data/wiki/raw/cole_medin/github_coleam00_Archon_readme.md
status: draft
last_updated: 2026-04-18
aaa_relevance:
  - P6 — self-improvement loop harness (Phase 6 orchestration layer)
  - P4 — evaluated as alternative to LangGraph; rejected for knowledge pipeline, accepted for Phase 6
---

# coleam00/Archon

## What It Is

An open-source workflow engine for AI coding agents. Define development processes (planning, implementation, validation, review, PR creation) as YAML workflows and run them reliably. MIT licensed.

Tagline: "Like what Dockerfiles did for infrastructure and GitHub Actions did for CI/CD — Archon does for AI coding workflows."

## Core Design

YAML workflows live in `.archon/workflows/`. Each workflow is a DAG of nodes. Nodes can be:
- **AI nodes**: prompt templates that invoke Claude Code or another coding agent
- **Deterministic nodes**: bash scripts, git ops, test runners — no AI, just reliable execution
- **Loop nodes**: iterate until a condition (`ALL_TASKS_COMPLETE`, `APPROVED`)
- **Human approval gates**: `interactive: true` pauses for input

Each workflow run gets its own **git worktree** — parallel runs never conflict.

```yaml
# Minimal example
nodes:
  - id: plan
    prompt: "Explore the codebase and create an implementation plan"
  - id: implement
    depends_on: [plan]
    loop:
      prompt: "Implement the next task. Run validation."
      until: ALL_TASKS_COMPLETE
  - id: run-tests
    depends_on: [implement]
    bash: "bun run validate"          # deterministic
  - id: create-pr
    depends_on: [run-tests]
    prompt: "Push changes and create a pull request"
```

Integrations: CLI, Web UI, Slack, Telegram, GitHub, Discord. Requires Bun runtime.

## Decision in AAA

**Rejected for AAA knowledge pipeline (P4).** Archon is a coding agent orchestrator. Its primitives ("fix this issue", "implement this feature", "validate this PR") don't map onto AAA's intelligence cycle ("crawl → research → trend scoring → documentation"). It also requires Bun, contradicting CLAUDE.md's Python-first constraint.

**Accepted for AAA Phase 6 self-improvement loop.** When AAA needs to improve its own code (P6.1), Archon is exactly right — the dark-factory-experiment is the reference implementation. The coding agent orchestration primitives align perfectly with autonomous self-improvement tasks.

## Key Architectural Insights

- **Deterministic scaffolding + AI fill** — the structure is owned and repeatable; intelligence fills in at each step. This is the correct mental model for any agentic pipeline.
- **Worktree isolation** for parallel execution is a cleaner solution than asyncio/ThreadPoolExecutor for tasks that touch the filesystem.
- **YAML as the workflow definition language** makes workflows auditable, versioned, and human-readable in a way that Python code pipelines aren't.
