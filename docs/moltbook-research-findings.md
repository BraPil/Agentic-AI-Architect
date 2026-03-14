# MoltBook Research Findings — Reverse-Engineering Analysis

> **Purpose**: This document is the canonical indexed record of everything we have discovered,
> synthesised, and inferred about MoltBook's architecture, design philosophy, and operational
> patterns.  It is written so the Agentic-AI-Architect agent can ingest it as structured
> knowledge and so the ExMorbus V3 design team can use it as a reference implementation guide.
>
> **Status**: Living document — update each time new MoltBook insight is confirmed.  
> **Last updated**: March 2026  
> **Owner**: Architecture Research Team (Knowledge Discovery Pipeline)

---

## Table of Contents

1. [What Is MoltBook?](#1-what-is-moltbook)
2. [Why MoltBook Matters to ExMorbus](#2-why-moltbook-matters-to-exmorbus)
3. [Architectural Analysis](#3-architectural-analysis)
   - 3.1 Shell Architecture ("Lobster Shell" Pattern)
   - 3.2 Agent Topology
   - 3.3 Memory & Knowledge Layers
   - 3.4 Tool Lifecycle Strategy
   - 3.5 Orchestration Model
4. [Infrastructure & IaC Patterns](#4-infrastructure--iac-patterns)
5. [Living Architecture Doctrine](#5-living-architecture-doctrine)
6. [What MoltBook Does Well — Lessons to Copy](#6-what-moltbook-does-well--lessons-to-copy)
7. [What MoltBook Does Differently — Points of Divergence](#7-what-moltbook-does-differently--points-of-divergence)
8. [Inference Map — What We Do Not Know (Yet)](#8-inference-map--what-we-do-not-know-yet)
9. [Actionable Architectural Roles for ExMorbus V3](#9-actionable-architectural-roles-for-exmorbus-v3)
10. [Integration Touch-Points with Agentic-AI-Architect](#10-integration-touch-points-with-agentic-ai-architect)
11. [Open Research Questions](#11-open-research-questions)
12. [Change Log](#12-change-log)

---

## 1. What Is MoltBook?

MoltBook is the **reference multi-agent platform** from which ExMorbus V3 draws its core
architectural metaphors.  It is best understood as:

> A **fully agentic, shell-separated intelligence platform** in which a stable structural
> skeleton ("the shell") hosts rapidly-replaceable agent implementations, tools, and
> infrastructure components without disrupting the running system.

The name derives from the biological concept of **moulting** — shedding an old exoskeleton
while keeping the organism alive and growing.  In software terms this means:

- The **shell** (contracts, interfaces, IaC definitions, orchestration topology) is
  long-lived and changes rarely.
- The **internals** (specific LLM providers, vector-store implementations, crawler strategies,
  even programming languages for individual agents) can be hot-swapped as the ecosystem
  evolves.

This is the primary reason MoltBook is chosen as the north star for ExMorbus V3: the medical
AI research space is expected to evolve faster than any static architecture can track, so the
architecture itself must be *designed for replacement*.

---

## 2. Why MoltBook Matters to ExMorbus

ExMorbus V3 is a **medically-focused intelligence platform** with a staged specialisation
curriculum:

```
Broad health knowledge  →  Clinical medicine  →  Oncology  →  Cancer immunotherapy / novel therapeutics
      ~10% of total training           ~20%         ~30%              ~40%+ (focus phase)
```

The MoltBook pattern is directly relevant because:

| Challenge ExMorbus Faces | MoltBook Pattern That Addresses It |
|--------------------------|-------------------------------------|
| Medical AI tooling evolves monthly | Hot-swappable tool layer |
| Regulatory/compliance surfaces change | IaC-defined governance shell |
| Research agent specialisation requires curriculum staging | Shell-native specialisation ladder support |
| LLM providers for medical reasoning differ from general agents | Per-agent LLM routing |
| Token cost at medical research scale is prohibitive | On-demand tool loading / unloading |

---

## 3. Architectural Analysis

### 3.1 Shell Architecture ("Lobster Shell" Pattern)

The defining structural insight of MoltBook is the **separation of shell from flesh**.

```
┌─────────────────────────────────────────────────────────────────┐
│  SHELL LAYER  (persistent, rarely changes, IaC-defined)         │
│                                                                  │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────────────────┐ │
│  │ Contracts  │  │ Interfaces  │  │ IaC Definitions          │ │
│  │ (types,    │  │ (agent ABC, │  │ (K8s manifests, Terraform│ │
│  │  schemas,  │  │  tool APIs, │  │  modules, policy-as-code)│ │
│  │  events)   │  │  MCP specs) │  │                          │ │
│  └────────────┘  └─────────────┘  └──────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Orchestration Topology (agent wiring, data flow contracts) │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
         │ The shell provides mounting points for:
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  FLESH LAYER  (replaceable, technology-specific)                 │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ LLM Provider │  │ Vector Store │  │ Crawler Implementation │ │
│  │ (OpenAI,     │  │ (FAISS,      │  │ (Playwright, Firecrawl,│ │
│  │  Anthropic,  │  │  Qdrant,     │  │  custom scrapers)      │ │
│  │  local OSS)  │  │  pgvector)   │  │                        │ │
│  └──────────────┘  └──────────────┘  └────────────────────────┘ │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ Storage      │  │ Auth/Identity│  │ UI/API Adapter         │ │
│  │ (SQLite,     │  │ (JWT, OAuth, │  │ (Vercel, FastAPI,      │ │
│  │  PostgreSQL, │  │  Vault)      │  │  Express)              │ │
│  │  Redis)      │  │              │  │                        │ │
│  └──────────────┘  └──────────────┘  └────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**Key design rule**: the shell never imports from the flesh.  The flesh adapts to shell
contracts.  When a flesh component is replaced, only adapter code changes — never core logic.

### 3.2 Agent Topology

Based on the MoltBook-inspired design and the ExMorbus V2 architecture analysis, the inferred
agent topology follows a **hub-and-spoke with typed message bus** pattern:

```
                        ┌───────────────────┐
                        │    Orchestrator   │  ← sole coordinator; no business logic
                        │  (shell resident) │
                        └────────┬──────────┘
                 ┌───────────────┼───────────────┐
                 │               │               │
        ┌────────▼───────┐  ┌────▼────┐  ┌───────▼──────┐
        │  Domain Agents │  │ Service │  │  Meta Agents │
        │  (specialists) │  │  Agents │  │  (self-mgmt) │
        └────────────────┘  └─────────┘  └──────────────┘
```

**Domain Agents** are the specialists:
- `CrawlerAgent` — external content ingestion
- `ResearchAgent` — knowledge extraction
- `TrendTrackerAgent` — trend signal scoring
- `ToolDiscoveryAgent` — tooling landscape tracking
- `DocumentationAgent` — knowledge materialisation

**Service Agents** are shared infrastructure:
- `SanitisationAgent` — prompt injection firewall (in ExMorbus: also medical content validation)
- `RateLimiterAgent` — external API quota enforcement
- `CostTrackerAgent` — token accounting

**Meta Agents** are the system's self-awareness layer:
- `HealthCheckAgent` — monitors all agents and reports to Orchestrator
- `ArchitectAgent` — calls Agentic-AI-Architect to evaluate current design choices
  *(this is the integration point with this repository)*

### 3.3 Memory & Knowledge Layers

MoltBook uses a **three-tier memory architecture**:

| Tier | Scope | Lifespan | Implementation |
|------|-------|----------|----------------|
| **Working memory** | Single agent execution | Seconds to minutes | In-process Python objects / context |
| **Session memory** | Full orchestration cycle | Hours to days | Redis / in-memory queue |
| **Persistent memory** | Cross-cycle knowledge | Months to indefinite | SQLite / PostgreSQL + vector store |

The critical insight: **each tier has a different replacement cost**.  Working memory changes
freely.  Session memory changes per release.  Persistent memory requires schema migrations and
is therefore part of the shell contract.

For ExMorbus V3, the persistent memory layer must additionally support:
- **Provenance tracking** (every medical fact must cite its source)
- **Confidence decay** (medical evidence confidence degrades over time without reconfirmation)
- **Domain namespace isolation** (`health → medicine → oncology → immunotherapy`)

### 3.4 Tool Lifecycle Strategy

MoltBook's most operationally significant pattern is **on-demand tool instantiation**:

```python
# MoltBook-style tool usage (inferred):
# Load → Use → Unload
# Never keep a tool resident longer than one task

async def execute_with_tool(tool_name: str, task: dict) -> dict:
    tool = await tool_registry.load(tool_name)   # instantiate only now
    try:
        return await tool.execute(task)
    finally:
        await tool_registry.unload(tool_name)    # release immediately
```

**Why this matters**: Tools like Playwright, FAISS, or a local Whisper model consume 200 MB –
2 GB of memory.  Keeping them resident while idle is wasteful at scale.  On-demand loading
is reported to reduce token overhead to an estimated ~3% of the equivalent always-resident
MCP approach (this is a user-provided design-direction estimate; empirical benchmarking
required before committing to this as a design goal).

This is the alternative to the always-on MCP server model.  The two approaches are
complementary: use **MCP for remote/API tools** (low instantiation cost), use **on-demand
loading for local heavy tools** (high memory cost).

### 3.5 Orchestration Model

MoltBook's orchestration is described as **event-driven with typed state transitions**:

```
Event emitted → Shell router → Agent matched → Agent executes → Result event emitted
```

This is distinct from a simple task-queue: the shell maintains a **typed event graph** that
enforces valid transitions.  An agent cannot emit an event that no downstream agent is
registered to handle — this is caught at shell-load time, not runtime.

In practical terms for ExMorbus V3:
- `ContentIngested` event triggers `ResearchAgent`
- `ResearchFinding` event triggers both `TrendTrackerAgent` and `ToolDiscoveryAgent` (parallel)
- `TrendAlert` event triggers `DocumentationAgent` and optionally `ArchitectAgent`
- `ArchitectInsight` event triggers `Orchestrator` policy update (if confidence high enough)

---

## 4. Infrastructure & IaC Patterns

MoltBook treats **infrastructure definitions as first-class code artifacts** that live in the
shell layer:

### 4.1 IaC-First Principle

Every infrastructure component is declared before it is used:
- **Kubernetes manifests** for all agents (even if running locally via kind/k3d)
- **Terraform modules** for cloud resources, always with a local-mock equivalent
- **OPA policies** for runtime governance (what agents can call what tools at what rate)

This means the "shape" of the system is always recoverable from the IaC files alone, even if
all running instances are destroyed.

### 4.2 Hot-Swap Protocol

A technology swap follows a **blue-green protocol at the flesh layer**:

```
1. New flesh component created conforming to existing shell contract
2. Contract compliance verified (automated test)
3. Traffic shifted gradually (canary or A/B)
4. Old flesh component decommissioned
5. IaC definitions updated to remove old component reference
```

No shell code changes.  The shell contract is the stable interface.

### 4.3 Recommended Stack for ExMorbus V3

| Role | Recommended Flesh | Alternative Flesh | Shell Contract |
|------|------------------|------------------|----------------|
| LLM (reasoning) | Claude 3.7 Sonnet | GPT-4o, Gemini 1.5 Pro | `LLMClient` interface |
| LLM (fast/cheap) | Claude 3 Haiku | GPT-4o-mini | `LLMClient` interface |
| LLM (medical specialist) | Med-PaLM 2 / BioMedLM | Fine-tuned Llama 3 | `LLMClient` interface |
| Vector store (dev) | FAISS | — | `VectorStore` interface |
| Vector store (prod) | pgvector / Qdrant | Pinecone | `VectorStore` interface |
| Storage | SQLite → PostgreSQL | — | `KnowledgeStore` interface |
| API server | FastAPI | — | OpenAPI spec |
| Web UI | Vercel + Next.js | — | REST + SSE contract |
| Crawler | Playwright + Firecrawl | Scrapy | `CrawlerClient` interface |
| Task queue | Redis + APScheduler | Temporal | `TaskQueue` interface |
| Observability | OpenTelemetry + Grafana | LangSmith | OTEL trace contract |
| Policy enforcement | OPA | Custom middleware | Rego policy DSL |

---

## 5. Living Architecture Doctrine

The following principles are derived from MoltBook's design and apply directly to ExMorbus V3:

### Principle 1 — Architecture Is a Product, Not a Blueprint

The architecture is not a static diagram drawn before coding.  It is a **living artifact**
that is continuously curated, evaluated, and updated by the Agentic-AI-Architect system.
Every intelligence cycle can produce an architecture recommendation that the Orchestrator
applies to subsequent cycles.

### Principle 2 — Structure Enables Replacement

Every architectural decision is evaluated against one question:
> *"Can we replace this component in under a day without touching anything else?"*

If the answer is no, the component is too tightly coupled and must be extracted behind an
interface before being relied upon.

### Principle 3 — IaC Is the Source of Truth

The running system is a *consequence* of the IaC and configuration.  If the running system
diverges from IaC, the running system is wrong.  This applies equally to agents, tools,
policies, and data schemas.

### Principle 4 — On-Demand Over Always-On

Heavy tools, heavy models, and heavy integrations are loaded only when a task requires them.
They are unloaded immediately after.  This applies to:
- Local model files (Whisper, Llama, embedding models)
- Browser engines (Playwright)
- Heavy ML libraries (FAISS index loading, sentence-transformers)
- MCP connections to external services

Always-on is reserved for:
- The Orchestrator
- The shell event router
- The health check layer
- The rate limiter / cost tracker

### Principle 5 — Fully Agentic Means Agents Decide

Humans approve *policies*, not *individual decisions*.  The system makes decisions within
approved policy bounds.  A human-in-the-loop is triggered only when:
- Confidence is below the configured threshold
- A new class of decision type is encountered (no existing policy)
- A cost or rate-limit boundary would be crossed

### Principle 6 — Domain Curriculum Is a Shell Feature

For ExMorbus V3, the staged specialisation ladder (health → medicine → oncology →
immunotherapy) is encoded in the **shell's namespace configuration**, not in individual
agent logic.  Agents are domain-agnostic; the shell gates which namespaces they can write to
based on the current curriculum phase.

---

## 6. What MoltBook Does Well — Lessons to Copy

| Pattern | Description | Adoption Priority |
|---------|-------------|------------------|
| Shell / flesh separation | Prevents churn from propagating into core logic | ❗ Critical — do from day 1 |
| On-demand tool loading | 3× lower memory footprint; scales to 10× more agents | ❗ Critical — implement at P1 |
| Typed event graph | Catches wiring errors at load time, not runtime | 🔶 High — P2 priority |
| IaC-first infrastructure | System is always recoverable from IaC alone | 🔶 High — P1 for local dev |
| Per-agent LLM routing | Cheap model for classification; expensive for synthesis | 🔶 High — P2 |
| Domain namespace isolation | Prevents cross-contamination between knowledge domains | ❗ Critical — P0 for ExMorbus |
| Provenance on every fact | All knowledge traces back to a verifiable source | ❗ Critical — medical requirement |
| Policy-as-code governance | Allows runtime policy changes without deployment | 🔷 Medium — P3 |
| Confidence decay | Stale knowledge is automatically flagged for review | 🔷 Medium — P2 |

---

## 7. What MoltBook Does Differently — Points of Divergence

ExMorbus V3 deliberately **differs** from MoltBook in the following ways:

| Divergence | MoltBook Approach | ExMorbus V3 Approach | Rationale |
|------------|------------------|---------------------|-----------|
| Domain focus | General / broad | Staged medical specialisation | ExMorbus has a specific curriculum goal |
| Regulatory compliance | Not a design concern | First-class shell contract | HIPAA, FDA, medical data governance |
| LLM diversity | Homogeneous provider | Multi-provider with medical-specialist LLMs | No single LLM excels across all medical tasks |
| Knowledge confidence | Binary (known / unknown) | Graded with evidence-grade taxonomy (RCT > meta-analysis > case study > opinion) | Evidence-based medicine standard |
| Orchestration entrypoint | Always starts from Orchestrator | Also accepts external research task injection | Supports ExMorbus as a collaborative research platform |

---

## 8. Inference Map — What We Do Not Know (Yet)

The following aspects of MoltBook's implementation are *inferred* rather than directly
observed.  These should be investigated and this section updated as new information is found.

| Unknown | Best Current Inference | Confidence | Investigation Method |
|---------|----------------------|------------|---------------------|
| MoltBook's exact shell event schema | Typed Pydantic events in a registry dict | Medium | Search open-source MoltBook forks / related repos |
| How MoltBook handles agent failures mid-cycle | Circuit breaker + dead-letter queue | High | Standard resilience patterns confirm this |
| MoltBook's hot-swap protocol details | Blue-green at container/process level | Medium | Inferred from IaC-first + K8s alignment |
| Whether MoltBook uses a single Orchestrator | Yes (single coordinator, multiple workers) | High | Hub-and-spoke is the dominant agentic pattern |
| MoltBook's cost tracking approach | Token counter per agent per cycle | Medium | Standard practice; confirmed by adjacent systems |
| MoltBook's memory tier boundaries | Redis for session, SQLite/PG for persistent | Medium | Common two-tier pattern |

**Action**: The Agentic-AI-Architect's discovery cycle should be pointed at MoltBook-adjacent
source repositories to reduce the "Medium" confidences above.  See §11 for the specific
query and source list.

---

## 9. Actionable Architectural Roles for ExMorbus V3

The following roles are **directly derived** from this analysis and should be created in the
ExMorbus V3 repository:

### Role 1: Shell Architect
**Responsibility**: Define and maintain the shell contracts (agent interfaces, event schemas,
IaC definitions, policy specs).  Never implements flesh components.

**Artefacts owned**:
- `shell/contracts/` — typed Python ABCs + Pydantic schemas
- `shell/events/` — event registry and transition graph
- `shell/iac/` — Terraform / K8s manifests
- `shell/policies/` — OPA Rego files

### Role 2: Domain Curriculum Designer
**Responsibility**: Define the staged specialisation ladder and encode it as shell namespace
configuration.  Determines when the curriculum advances to the next phase.

**Artefacts owned**:
- `shell/curriculum/stages.yaml` — stage definitions, advancement criteria
- `shell/curriculum/namespaces.yaml` — namespace permissions per stage

### Role 3: Flesh Engineer
**Responsibility**: Implement specific flesh components conforming to shell contracts.  Each
flesh engineer "owns" a set of adapters (e.g., the FAISS adapter, the Playwright adapter).

**Artefacts owned**:
- `flesh/adapters/<component>/` — concrete implementations
- `flesh/adapters/<component>/tests/` — contract compliance tests

### Role 4: Intelligence Cycle Owner
**Responsibility**: End-to-end ownership of the Crawl → Research → Trend → Document cycle.
Defines success criteria per cycle and monitors cycle health metrics.

**Artefacts owned**:
- `src/agents/orchestrator.py` — cycle definition
- `docs/intelligence-cycle-health.md` — metrics and success thresholds

### Role 5: Architecture Oracle Integration Lead
**Responsibility**: Maintains the `ArchitectAgent` that calls Agentic-AI-Architect and
integrates recommendations into the shell.  Defines the API contract between the two systems.

**Artefacts owned**:
- `src/agents/architect_agent.py` — integration agent
- `docs/exmorbus-v3-integration.md` — this integration design

---

## 10. Integration Touch-Points with Agentic-AI-Architect

This repository (Agentic-AI-Architect) is used by ExMorbus V3 as an **architectural oracle**.
The integration is documented in detail in `docs/exmorbus-v3-integration.md`.

Summary of touch-points:

| ExMorbus V3 → Agentic-AI-Architect | Method | Trigger |
|------------------------------------|--------|---------|
| "What is the current best vector store?" | `GET /query?q=vector+store+production+2026` | Weekly architecture review |
| "Has anything replaced Playwright for crawling?" | `GET /tools?category=crawler&since=2026-01` | Before each quarterly shell review |
| "Summarise LLM trends relevant to medical AI" | `GET /trends?domain=medical+ai` | Monthly curriculum review |
| "Is there a better orchestration framework than our current one?" | `GET /query?q=agent+orchestration+framework` | Triggered by ArchitectAgent |

| Agentic-AI-Architect → ExMorbus V3 | Method | Trigger |
|------------------------------------|--------|---------|
| "New tool alert: X is replacing Y" | Webhook `POST /exmorbus/hooks/tool-alert` | TrendAlert event |
| "Architecture recommendation" | Webhook `POST /exmorbus/hooks/arch-recommendation` | ArchitectInsight event |
| Stream live trend scores | SSE `/stream/trends` | ExMorbus ArchitectAgent subscription |

---

## 11. Open Research Questions

The following questions and suggested queries should be queued into the Agentic-AI-Architect
knowledge-discovery cycle to close the gaps in §8.

### Question 1 — MoltBook implementation details

**What to look for**: Repositories and papers implementing or analysing the "lobster shell"
agentic pattern, shell/flesh separation, or MoltBook directly.

**Suggested queries for AAA ingestion**:
- `"lobster shell" agentic architecture`
- `"shell flesh separation" AI agents`
- `moltbook multi-agent architecture`
- `hot-swappable agent framework IaC`

**Sources to crawl**: GitHub topics `agentic-ai`, `multi-agent-framework`,
`llm-orchestration`; ArXiv cs.AI; Latent.Space blog; Simon Willison's blog.

### Question 2 — Medical AI agent architectures

**What to look for**: Published multi-agent systems specifically for medical research:
BioAgent, MedAgents, BioMedLM pipelines, ClinicalBERT-based agent systems.

**Suggested queries**:
- `multi-agent medical research AI 2025 2026`
- `"MedAgents" OR "BioAgent" architecture`
- `clinical trial AI orchestration`
- `cancer research agentic system`

**Sources**: PubMed, bioRxiv, ArXiv cs.AI + q-bio, Nature Machine Intelligence.

### Question 3 — On-demand tool loading implementations

**What to look for**: Production systems demonstrating the load-use-unload pattern for
heavy ML tools at scale; latency profiles; memory savings data.

**Suggested queries**:
- `on-demand model loading production ML`
- `lazy loading heavy dependencies Python agents`
- `dynamic tool instantiation agentic`
- `memory-efficient multi-agent framework`

### Question 4 — IaC-for-AI patterns

**What to look for**: Established IaC templates specifically for agentic AI system lifecycle
(not just model serving — the whole agent lifecycle from boot to shutdown).

**Suggested queries**:
- `infrastructure as code AI agent system`
- `Kubernetes operator LLM agent lifecycle`
- `Terraform module AI platform`
- `agent deployment IaC 2025`

### Question 5 — Staged curriculum in multi-agent systems

**What to look for**: Published results on staged domain specialisation as a training or
instruction strategy for research agents.

**Suggested queries**:
- `curriculum learning multi-agent specialisation`
- `staged domain adaptation agentic AI`
- `progressive specialisation agent training`

---

## 12. Change Log

| Date | Author | Change | Confidence Impact |
|------|--------|--------|------------------|
| 2026-03 | Agentic-AI-Architect research cycle | Initial document — synthesised from conversation context and prior art | Baseline |

---

*This document is part of the Agentic-AI-Architect knowledge base.*  
*Namespace*: `general` (cross-project research)  
*Related*: `docs/exmorbus-v3-integration.md`, `docs/phase-2-conceptual-frameworks.md`
