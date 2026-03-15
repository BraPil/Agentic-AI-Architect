# Repository Memory Protocol

## Purpose

This repository needs durable memory.

The project spans architecture, research, implementation, reviews, and long-lived strategic decisions. If lessons, discoveries, and completed work are not recorded in a consistent way, the repository will repeatedly:

- rediscover the same facts
- re-open already-settled decisions
- repeat failed approaches
- lose the rationale behind completed work

This protocol defines how to capture and index repository memory.

## The Memory Surfaces

Use these files together:

- `docs/work-index.md` — master index and entry point
- `docs/decision-log.md` — durable decision ledger
- `docs/discovery-log.md` — research and field discoveries
- `docs/lessons-learned-log.md` — mistakes, surprises, and preventive lessons
- `docs/work-log.md` — major completed work, validation, and outcomes

## What Must Be Recorded

### Record in the decision log when:

- a strategic direction is chosen
- an architectural tradeoff is resolved
- a repository boundary is fixed
- a sequencing decision is made
- a rule becomes durable enough to affect future work

### Record in the discovery log when:

- an external trend, tool, framework, or practitioner insight materially changes direction
- a meaningful pattern is found in research
- a source proves high-value enough to track continuously
- a comparison produces a useful conclusion

### Record in the lessons learned log when:

- a mistake led to wasted work or confusion
- a plan failed for a clear reason
- a hidden risk was discovered during implementation
- a repeated anti-pattern was noticed
- a previous assumption turned out to be wrong

### Record in the work log when:

- a substantial change lands in the repository
- a merge closes out a meaningful branch of work
- a validation milestone is reached
- a roadmap-related task is completed

## Minimum Logging Standard For Meaningful Work

For any meaningful unit of work, capture:

- date
- title
- scope
- what changed
- why it changed
- what was validated
- what remains open
- which other documents were updated

## Indexing Rules

Every new durable record should be reachable from `docs/work-index.md`.

That means:

- add or maintain an index entry
- keep names stable and descriptive
- avoid burying important decisions only inside long narrative documents

## Writing Style Rules

Entries should be:

- concise
- factual
- dated
- explicit about rationale
- explicit about impact on future work

Avoid vague entries such as:

- "updated docs"
- "fixed some issues"
- "did architecture work"

Prefer entries such as:

- "Accepted repo-boundary decision: keep Agentic-AI-Architect as a product repo and defer shared repo extraction until a second real system exists"

## Anti-Patterns

Do not:

- rely on chat history as the only memory
- store key decisions only in a pull request description
- leave work outcomes undocumented after merge
- record lessons with no preventive action
- duplicate the same decision across many files without an index entry

## Maintenance Expectations

When major work changes the repository, update the memory system in the same session whenever practical.

At minimum, keep the following synchronized:

- decision memos
- decision log
- work log
- work index

## Relationship To Other Docs

- `CLAUDE.md` defines the operating rules
- roadmap and decision memos define strategy
- the memory protocol captures durable operational knowledge produced while following those documents
