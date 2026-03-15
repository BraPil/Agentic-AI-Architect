# Instruction Hierarchy

## Purpose

This document explains which instruction sources govern work in this repository, what each one is for, and how conflicts should be resolved.

The goal is to remove ambiguity for humans and AI coding assistants so the repository behaves predictably across long-running sessions.

## Order of Precedence

When instructions conflict, follow them in this order:

1. Direct user request for the current task
2. Platform or system-level safety and operating rules
3. Session-level coding agent instructions
4. Repository instruction files
5. Planning and decision documents
6. Default style and tool behavior

Higher levels override lower levels.

## Instruction Sources In This Repository

### 1. Current task request

Source:

- the current user prompt and any follow-up clarification

Purpose:

- defines the immediate goal
- determines what outcome matters right now
- should be followed unless it conflicts with a higher-priority rule

### 2. Repository canonical instruction file

Source:

- `CLAUDE.md`

Purpose:

- the main operating guide for work in this repository
- defines architecture, development principles, anti-patterns, testing rules, security rules, and workflow expectations
- should be treated as the primary repository-specific instruction source

Why it matters:

- it is the closest thing this repository has to a constitution
- it explains not just what to do, but what not to do

### 3. GitHub Copilot repository instructions

Source:

- `.github/copilot-instructions.md`

Purpose:

- a concise project-specific ruleset tailored for Copilot
- reinforces architecture, testing, security, and phase discipline

Why it matters:

- it is short enough to be applied consistently in routine work
- it should stay aligned with `CLAUDE.md`

### 4. Cursor rules

Source:

- `.cursorrules`

Purpose:

- a condensed version of key repo rules for Cursor sessions
- useful as a fast operational reminder

Why it matters:

- keeps the most important repo rules visible in another tool surface

### 5. Planning and decision documents

Sources include:

- `docs/phase-5-implementation-plan.md`
- `docs/repo-structure-decision-memo.md`
- `docs/ecosystem-sequencing-memo.md`
- `docs/multi-model-review-log.md`

Purpose:

- define the roadmap, accepted decisions, ecosystem sequencing, and open architectural questions

Why they matter:

- these documents constrain strategic choices
- they are not optional commentary; they record decisions already made

### 6. Knowledge capture and indexing protocol

Sources:

- `docs/repo-memory-protocol.md`
- `docs/work-index.md`
- `docs/decision-log.md`
- `docs/discovery-log.md`
- `docs/lessons-learned-log.md`
- `docs/work-log.md`

Purpose:

- record what has been learned, decided, discovered, and completed so the repository does not repeatedly lose context

Why it matters:

- this is the operational memory system for the repo
- it reduces relearning, rediscovery, and duplicated work

## Conflict Resolution Rules

### If a task request conflicts with a repo plan

Follow the task request unless it violates a higher-level rule.

Then update the relevant planning document if the task changes the plan.

### If two repo documents disagree

Use this order:

1. `CLAUDE.md`
2. accepted decision memos
3. the latest roadmap document
4. supporting review documents

Then fix the inconsistency in the repository.

### If a decision has been made but not propagated

Do not silently rely on memory or chat context.

Update:

- the relevant decision memo or decision log
- the affected roadmap or instruction file
- the work log if the change was made as part of active work

## Operating Principle

Work should be governed by explicit repository state, not by unstated recollection.

If something is important enough to shape future work, it should exist in a durable file in this repository.
