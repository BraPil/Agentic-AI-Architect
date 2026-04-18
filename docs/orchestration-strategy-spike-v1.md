# Orchestration Strategy Spike — v1

**Date:** 2026-04-18  
**Scope:** Phase 4 orchestration decision — Archon vs. LangGraph vs. extended BaseAgent  
**Status:** Complete — recommendation accepted, pending Phase 4 decision gate  

---

## 1. Why This Spike Exists

CLAUDE.md §12 records a deferred decision: "Avoid heavy dependencies in Phase 0; LangGraph planned for P4."
The implementation plan (P4.1) says: "Decide and lock the orchestration strategy before broadening runtime complexity."

Two new inputs arrived that changed the evaluation surface:

1. **Archon** (Cole Medin) — an open-source YAML workflow engine for AI coding agents. It is battle-tested inside the dark-factory-experiment and is a real alternative to LangGraph for some problems.
2. **LLM Wiki** (Karpathy) — specifies a three-layer knowledge architecture (raw sources / wiki / schema) with Ingest-Query-Lint operations that directly influences what AAA's "intelligence cycle" needs to do.

The question being answered here is:

> What is the right orchestration strategy for AAA, and when should it change?

---

## 2. What the Current System Already Does

### BaseAgent (`src/agents/base_agent.py`)

The abstract base class provides:
- `initialize() / run() / shutdown()` lifecycle
- `run()` handles timing, status transitions, error capture — **not overrideable by contract**
- `_execute()` is the sole implementation hook
- `AgentResult` as a typed, serializable result envelope
- `health_check()` as a readiness probe

This is a clean, minimal, well-tested contract. Every agent in the system already implements it.

### Orchestrator (`src/agents/orchestrator.py`)

The orchestrator provides:
- Sequential pipeline: Crawl → Research → TrendTracker → ToolDiscovery → Documentation
- Mode-based routing: `full | trends | tools | crawl_only`
- Per-step error counting with `max_cycle_errors` abort
- Cycle result tracking in memory
- CLI entry point with argparse

### What It Lacks

| Gap | Needed by |
|-----|-----------|
| No parallel execution (TrendTracker + ToolDiscovery are independent) | Phase 1/2 performance |
| No step-level retry with backoff | Phase 1 reliability |
| No state persistence across process restarts | Phase 4 |
| No conditional branching beyond mode switch | Phase 4 |
| No human-in-the-loop queue | Phase 4.3 |
| No scheduling (external, APScheduler planned) | Phase 4.2 |
| No streaming output | Phase 5 |
| No graph visualization for debugging | Phase 4+ |

---

## 3. The Three Candidates

### 3.1 Archon

**What it is:** A YAML-defined workflow engine for AI coding agents. Designed to make coding agent behavior deterministic and repeatable. Used as the orchestration layer inside Cole Medin's dark-factory-experiment.

**Core design:**
- Workflows defined in `.archon/workflows/*.yaml`
- Nodes are either deterministic (scripts, shell commands) or AI-driven (Claude Code, etc.)
- Git worktrees for isolated parallel execution
- CLI + Web UI + integrations (Slack, Telegram, GitHub, Discord)
- 17 default coding workflows (fix issue, implement feature, PR review, etc.)

**Strengths:**
- Human-readable YAML workflow definitions
- Already battle-tested for the dark-factory pattern
- Clean audit trail per workflow execution
- Strong governance model (validation independence, budget caps)
- MIT licensed, actively maintained

**Weaknesses for AAA's knowledge pipeline use case:**
- **Wrong shape.** Archon is a coding agent orchestrator. Its primitives are "fix this GitHub issue," "implement this feature," "validate this PR." It has no concept of "crawl sources → extract findings → score trends → generate docs."
- **Requires Bun.** AAA is Python-first. Adding a JavaScript runtime for orchestration contradicts the dependency philosophy in CLAUDE.md §13.
- **Designed for bounded tasks, not continuous cycles.** The intelligence pipeline needs to run indefinitely, adapt its own source list, and score trends over time. Archon is designed for discrete, completion-bounded workflows.
- **No knowledge pipeline primitives.** No concept of KnowledgeEntry, trend scoring, vector search, or source weighting — all of which are core AAA concepts.

**Correct role for Archon in AAA:**  
Archon should **not** be the orchestration layer for the knowledge pipeline. It should be evaluated as the **engine for AAA's Phase 6 self-improvement loop** — the part that manages coding agent workflows to improve AAA's own code. Dark-factory-experiment is the reference implementation for that pattern. This is a Phase 6 question, not a Phase 4 question.

---

### 3.2 LangGraph

**What it is:** A graph-based framework for building stateful, multi-agent Python applications. Built by the LangChain team. Designed specifically for agent workflows that require branching, cycles, persistence, and human-in-the-loop.

**Core design:**
- `StateGraph`: a directed graph where nodes are functions/agents and edges carry typed state
- **State**: A `TypedDict` that flows through every node — each node reads it, modifies it, returns it
- **Nodes**: Python functions or `Runnable` objects (can be any callable)
- **Edges**: Deterministic (always go to X) or conditional (branch based on state)
- **Checkpointers**: SQLite, PostgreSQL, or Redis — persist the full state graph between runs
- **Human-in-the-loop**: `interrupt()` — pause graph at any node, wait for human input, resume
- **Streaming**: Token-level and node-level streaming out of the box
- **Multi-agent**: Supervisor + subgraph pattern, swarm pattern, hierarchical graphs
- **LangGraph Platform**: Managed cloud deployment with Studio for visual graph debugging

**Strengths:**
- Parallel node execution is first-class (e.g., TrendTracker + ToolDiscovery can run concurrently)
- Checkpointing gives real resume-on-restart for free
- Conditional branching handles mode-based routing as graph structure, not if/else chains
- Human-in-the-loop is the right primitive for Phase 4.3 (approval queue)
- Streaming support unlocks Phase 5.2
- LangGraph Studio gives the visual cycle graph that operators and developers need
- Mature enough for production (v0.2+, used at scale by many companies)

**Weaknesses:**
- **Heavy dependency.** LangGraph pulls in the full LangChain ecosystem. CLAUDE.md explicitly says this was deferred for Phase 0 precisely because of this. Phase 4 is the right time to revisit.
- **Opinionated state model.** All inter-node communication flows through a single `TypedDict`. This is powerful but requires restructuring the current `AgentResult`-based return types into a unified state schema.
- **Graph compilation step.** The graph must be compiled before execution — not a major cost but a new concept vs. the current imperative pipeline.
- **LLM-node assumption.** LangGraph was designed assuming nodes call LLMs. AAA's agents do call LLMs but also do pure computation (sanitization, scoring, hashing) — these work fine as nodes but feel slightly over-engineered for pure computation steps.
- **Version velocity.** LangGraph moves fast. CLAUDE.md §13 says prefer packages with broad adoption — LangGraph has this, but the API surface changes across minor versions.

**The migration cost from BaseAgent:**  
The BaseAgent contract does not need to change. Each agent's `_execute()` can be wrapped as a LangGraph node in a single adapter function:

```python
def crawler_node(state: AAAState) -> AAAState:
    result = crawler_agent.run(state["task_input"])
    return {**state, "raw_documents": result.data or []}
```

This means the migration is an **Orchestrator-level change**, not an agent-level change. All agents keep their existing code.

---

### 3.3 Extended BaseAgent / Custom Orchestrator

**What it is:** Enhancing the current `Orchestrator` in `src/agents/orchestrator.py` with the specific capabilities it currently lacks, without adopting a framework.

**The targeted additions needed through Phase 3:**

| Addition | Effort | Impact |
|----------|--------|--------|
| `asyncio.gather()` for TrendTracker + ToolDiscovery (they are independent) | ~30 min | ~2× cycle throughput on I/O-bound steps |
| Step-level retry with exponential backoff (use existing `retry_with_backoff` in helpers.py) | ~1 hr | Robustness against transient API failures |
| APScheduler integration for recurring cycles | ~2 hr | Enables autonomous operation (Phase 4.2) |
| SQLite cycle history persistence (use existing KB) | ~2 hr | Resume awareness, cycle trend tracking |
| Simple approval queue in SQLite (Phase 4.3) | ~3 hr | Human-in-the-loop for high-confidence actions |

**Total to cover Phase 1–3 requirements:** ~8–10 hours of targeted additions.

**Strengths:**
- No new dependencies
- All existing tests continue to pass without modification
- Stays within the Python-first constraint of CLAUDE.md
- The team (us) owns the entire lifecycle contract
- Incremental — add only what the current phase needs

**Weaknesses:**
- Graph complexity grows faster than a custom orchestrator can manage gracefully
- Parallel execution via `asyncio` in a sync-oriented codebase adds subtle complexity
- Human-in-the-loop via custom SQLite queue is significantly more work than LangGraph's `interrupt()`
- No built-in visualization — the cycle graph lives only in developers' heads
- Streaming is non-trivial to add without a streaming-native architecture
- By Phase 4, the Orchestrator will have grown into the "Fat Orchestrator" anti-pattern if not carefully managed

---

## 4. Head-to-Head Comparison

| Dimension | Extended BaseAgent | LangGraph | Archon |
|-----------|-------------------|-----------|--------|
| **P1–P3 readiness** | ✅ Ready now | ⚠️ Migration cost | ❌ Wrong shape |
| **P4 state persistence** | Manual (SQLite) | ✅ Checkpointers | ❌ N/A |
| **P4 parallel execution** | asyncio (manual) | ✅ Native | ❌ N/A |
| **P4 conditional branching** | if/else in Python | ✅ Conditional edges | ❌ YAML only |
| **P4.3 human-in-the-loop** | Custom queue | ✅ interrupt() | ❌ N/A |
| **P5 streaming** | Manual | ✅ Native | ❌ N/A |
| **P5 MCP server** | Manual | Compatible | ❌ N/A |
| **P6 self-improvement loop** | Custom | Compatible | ✅ Right shape |
| **Dependency weight** | ✅ None | ⚠️ LangChain ecosystem | ⚠️ Requires Bun |
| **Agent code migration** | ✅ None needed | ✅ None needed (adapter) | ❌ Full rewrite |
| **Test suite stability** | ✅ No change | ✅ Orchestrator-level only | ❌ Full rewrite |
| **Visual debugging** | ❌ None | ✅ LangGraph Studio | ✅ Web UI (for coding) |
| **Python-first** | ✅ Yes | ✅ Yes | ❌ Requires Bun |
| **CLAUDE.md alignment** | ✅ Explicit preference | ✅ Planned for P4 | ❌ Not mentioned |

---

## 5. Recommendation

### 5.1 Phases 1–3: Stay on Extended BaseAgent

Continue with the custom Orchestrator. Make these targeted additions as the phases require them:

1. **Immediately (Phase 1):** Wrap TrendTracker + ToolDiscovery in `asyncio.gather()` — they are independent and can run in parallel.
2. **Phase 1/2:** Add step-level retry using existing `retry_with_backoff` from helpers.
3. **Phase 2:** Add SQLite cycle persistence to `Orchestrator` (use the existing `KnowledgeBase` connection, new `cycles` table).
4. **Phase 4.2:** Integrate APScheduler as a thin wrapper around `run_cycle()`.

Do **not** add more than this. Every additional custom primitive is work that LangGraph gives for free at Phase 4.

### 5.2 Phase 4 Decision Gate: Adopt LangGraph

When Phase 4 begins, the graph migration is the right call. The triggers that justify it:

- Human-in-the-loop approval queue is needed (P4.3) — LangGraph's `interrupt()` is far superior to a custom SQLite queue
- More than 6 agents in the pipeline — conditional routing in if/else chains becomes unreadable
- State persistence for cycle resume is needed — Checkpointers beat custom SQLite by a large margin
- Streaming output is needed for Phase 5.2 — LangGraph is streaming-native, custom is painful

**Migration plan at Phase 4:**
1. Define `AAAState: TypedDict` covering all inter-agent state fields
2. Wrap each agent's `run()` in a thin node adapter (no agent code changes)
3. Replace `Orchestrator.run_cycle()` with a compiled `StateGraph`
4. Use `SqliteSaver` checkpointer first (compatible with existing SQLite dependency)
5. Retire the custom Orchestrator loop

The agent contracts (BaseAgent, `_execute()`, AgentResult) do **not** change.

### 5.3 Phase 6: Adopt Archon for the Self-Improvement Loop

Archon is the right engine for the dark-factory-style Phase 6 self-improvement loop — the part where AAA issues, triages, and implements improvements to its own codebase. This is exactly what dark-factory-experiment demonstrates. Archon runs on a separate track from the knowledge pipeline and does not conflict with LangGraph on the intelligence cycle.

---

## 6. Impact on the LLM Wiki Architecture Pattern

Karpathy's LLM Wiki specifies a knowledge architecture (raw sources / wiki / schema, Ingest-Query-Lint) that maps directly onto what AAA's intelligence cycle should become. This does not change the orchestration decision — it deepens the content of what the orchestrator's nodes need to do:

| LLM Wiki operation | AAA pipeline equivalent | Current status |
|-------------------|------------------------|----------------|
| Ingest (source → update wiki pages) | Crawl → Research → KB write | P1.1–P1.3 |
| Query (ask wiki, file answer back) | `/query` endpoint + KB read | P5.1 (partially done) |
| Lint (health-check wiki for contradictions, orphans, staleness) | Knowledge refinement | P6.2 |
| index.md (content catalog) | KB namespace index | Not yet built |
| log.md (append-only cycle log) | Cycle history | Partially (CycleResult) |

The LLM Wiki insight that **structured index outperforms vector RAG at moderate scale (~100–500 sources)** directly informs the P2.3 decision: build a structured KB index layer before reaching for FAISS. Do not introduce FAISS until the structured index is saturated.

---

## 7. Updated Phase 4 Branch Plan

The phase plan should be updated to reflect this decision:

```
feature/p4-orchestration
├── task/p4.0-orchestrator-decision-gate     ← this spike completes this
├── task/p4.1-async-parallel-steps           ← asyncio.gather for P1 (pull forward)
├── task/p4.2-langgraph-migration            ← StateGraph + SqliteSaver at P4 start
├── task/p4.3-apscheduler-wrapper            ← scheduling around the graph
├── task/p4.4-human-in-loop                  ← LangGraph interrupt() + approval UI
└── task/p4.5-error-recovery                 ← circuit breaker + dead letter queue
```

---

## 8. Decisions Recorded

| Decision | Chosen | Rejected | Reason |
|----------|--------|----------|--------|
| Orchestration through Phase 3 | Extended BaseAgent | LangGraph (premature), Archon (wrong shape) | Minimal blast radius; BaseAgent is working; LangGraph migration is Orchestrator-level only |
| Phase 4 orchestration | LangGraph | Custom extension | human-in-the-loop, streaming, parallel, checkpointing all justify the dependency at P4 |
| Archon role | Phase 6 self-improvement loop | Primary orchestration | Archon is a coding agent orchestrator; dark-factory pattern is right for P6, wrong for P1–P4 knowledge pipeline |
| FAISS introduction | After structured KB index | Immediately | LLM Wiki insight: structured index outperforms vector RAG at <500 sources |
| Parallel steps | asyncio.gather for TrendTracker + ToolDiscovery | Sequential | Independent steps; no change to agent contracts |

---

*Spike authored 2026-04-18. Update this document when Phase 4 begins and the LangGraph migration is scoped.*
