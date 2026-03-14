# AI Review Context Prompt
## Complete Handoff for Independent Model Review Sessions

> **How to use this document**: Copy everything between the `---BEGIN PROMPT---` and `---END PROMPT---` markers and paste it as your opening message to any AI model (Claude Opus, GPT-5, Gemini Ultra, etc.). The goal is for each model to independently review the full context, then propose their own solution — after which you will compare them with what has been built and make decisions where visions differ.

---

---BEGIN PROMPT---

# Context Handoff: Agentic AI Architect System — Full Project State

You are being asked to independently review a project and propose your own architecture and implementation approach. This is NOT a request to rubber-stamp existing work. Please think critically, identify gaps and disagreements, and bring your best independent judgment. Your response will be compared with other models' responses and with the existing implementation.

---

## Part 1: The Broader Vision (General)

We are building a **Multi-Agentic Product Management System** — a family of autonomous specialist systems that work together to serve every stage of a complex AI product lifecycle. Each system is its own intelligent agent or team of agents, composable into a larger orchestration.

The planned systems, in order of priority:

| System | Status | Purpose |
|--------|--------|---------|
| **Agentic AI Architect** | 🔄 In active development | World-class AI architecture guidance; the first system we are building |
| **Agentic Data Architect** | ⬜ Planned | Data modeling, pipelines, governance, schema design guidance |
| **Agentic AI & Data Engineering** | ⬜ Planned | Implementation tooling, pipeline scaffolding, infra patterns |
| **Agentic SecOps & Governance** | ⬜ Planned | Security reviews, compliance checks, risk scoring, audit trails |
| **Agentic Computer Scientist** | ⬜ Planned | Algorithm selection, complexity analysis, formal reasoning |
| **Agentic Statistician & Mathematician** | ⬜ Planned | Statistical modeling, hypothesis testing, quantitative analysis |
| **Agentic Monitoring & Control** | ⬜ Planned | Observability, alerting, drift detection, production control loops |

**The overarching product**: A system where any organization building an AI-native product can call upon this multi-agent team — just as a large enterprise would retain a bench of world-class consultants — and receive the depth, breadth, and rigor of that expertise, autonomously and continuously.

**Inter-system composability** is a first-class design constraint. Every system must:
- Expose a queryable API (REST + MCP)
- Emit structured, versioned data schemas
- Be callable by other systems during their operation
- Share a common knowledge bus (a unified knowledge layer)

---

## Part 2: The Specific Focus — Agentic AI Architect System

### 2.1 Core Purpose

The **Agentic AI Architect** is designed to be the world's most capable AI architecture intelligence system. It is not a chatbot with a prompt. It is a living, self-improving, continuously-learning system that:

1. **Discovers** new knowledge about AI architecture (frameworks, tools, trends, papers, practitioner insights)
2. **Synthesizes** that knowledge into structured, queryable intelligence
3. **Tracks** the evolution of the field over time (what's rising, falling, converging)
4. **Documents** its findings in human-readable and machine-queryable formats
5. **Serves** as an expert advisory module to other agentic systems during their architecture phases

### 2.2 What Has Been Built (Current State)

The repository lives at: `github.com/BraPil/Agentic-AI-Architect`

**Branch**: `copilot/create-agentic-systems` (active development)

#### Repository Structure
```
Agentic-AI-Architect/
├── CLAUDE.md                    ← AI coding agent instructions (canonical)
├── .github/copilot-instructions.md  ← GitHub Copilot workspace instructions
├── .cursorrules                 ← Cursor IDE session rules
├── README.md                    ← System overview and quick start
├── requirements.txt             ← Python deps (core required; heavy optional)
├── config/
│   └── settings.py              ← All config via env vars (AAA_ prefix)
├── docs/
│   ├── phase-1-education.md     ← AI Architect roles, responsibilities, influential figures
│   ├── phase-2-conceptual-frameworks.md  ← Complete framework knowledge stack
│   ├── phase-3-trends.md        ← 10 scored macro trends (2025–2026)
│   ├── phase-4-tools.md         ← Tools landscape by category with status signals
│   └── phase-5-implementation-plan.md   ← 8-phase dev roadmap with GitHub branches
├── src/
│   ├── agents/
│   │   ├── base_agent.py        ← Abstract lifecycle contract (ALL agents inherit this)
│   │   ├── crawler_agent.py     ← Web crawling; 13 sources; robots.txt; dedup
│   │   ├── research_agent.py    ← Content classification + knowledge extraction
│   │   ├── trend_tracker_agent.py  ← Trend scoring (recency×velocity×credibility)
│   │   ├── tool_discovery_agent.py ← Tool registry; deprecation detection
│   │   ├── documentation_agent.py  ← Markdown generation; digests; reports
│   │   └── orchestrator.py      ← Pipeline coordinator; CLI entry point
│   ├── knowledge/
│   │   ├── knowledge_base.py    ← SQLite structured store; namespaced; full-text search
│   │   └── vector_store.py      ← FAISS → sentence-transformers → TF-IDF fallback
│   ├── pipeline/
│   │   ├── ingestion.py         ← URL → KnowledgeBase end-to-end
│   │   └── processing.py        ← Clean, chunk, deduplicate
│   └── utils/
│       └── helpers.py           ← sanitize_text (prompt injection), rate_limit, retry
└── tests/
    ├── test_agents.py           ← Agent tests
    ├── test_knowledge_base.py   ← Knowledge layer tests
    └── test_pipeline.py         ← Pipeline and utility tests
```

#### Core Design Decisions Made

| Decision | Chosen Approach | Rationale |
|----------|-----------------|-----------|
| Agent framework | Custom `BaseAgent` for now; LangGraph planned for Phase 4 | Avoid framework lock-in before patterns are clear; LangGraph adds stateful coordination later |
| Structured store | SQLite (dev) → PostgreSQL (scale) | Zero-infra start |
| Vector store | FAISS local → Pinecone cloud | FAISS for dev (no server); graceful degradation to TF-IDF when no embedding model |
| LLM integration | `llm_client` callable injected via config | Provider-agnostic; testable without API keys |
| Prompt injection defense | Central `sanitize_text()` in `src/utils/helpers.py` | Auditable, testable, all-or-nothing |
| Config | `@dataclass` + env vars with `AAA_` prefix | Simple; no Pydantic runtime dep for config layer |
| Crawler UA | Custom branded User-Agent string | Rate-limit-friendly identification |

#### The BaseAgent Contract (every agent follows this)

```python
class BaseAgent(ABC):
    """
    Lifecycle: __init__ → initialize() → run() → [N cycles of _execute()] → shutdown()
    The run() method is NEVER overridden — it handles timing, status, exception capture.
    Only _execute() contains agent-specific logic.
    """
    def initialize(self) -> None: ...      # Set up resources
    def _execute(self, task_input) -> Any: ...  # Core logic (MUST IMPLEMENT)
    def health_check(self) -> dict: ...    # Confirm operational
    def shutdown(self) -> None: ...        # Release resources
```

#### Data Pipeline (one intelligence cycle)

```
CrawlerAgent.run()
  → list[dict] (raw documents with url, title, content, content_hash, metadata)
ResearchAgent.run(documents)
  → list[dict] (findings: title, summary, content_type, concepts, tools_mentioned,
                people_mentioned, source_url, confidence, namespace)
TrendTrackerAgent.run(findings)
  → dict (scores, alerts, summary, total_trends)
ToolDiscoveryAgent.run(findings)
  → dict (registry, alerts, newly_discovered, total_tools)
DocumentationAgent.run({findings, trend_data, tool_data, cycle_number})
  → list[dict] (generated markdown documents)
KnowledgeBase ← entries persisted throughout all stages
```

#### Knowledge Namespaces
Valid values: `education` | `frameworks` | `trends` | `tools` | `general`

#### Trend Scoring Formula
```python
trend_score = (
    recency_score    * 0.30 +   # How recent is the signal?
    adoption_velocity * 0.35 +  # How fast is adoption growing?
    credibility_signal * 0.25 + # How credible is the source?
    novelty_delta    * 0.10     # How new is this vs. existing knowledge?
)
# Alerts: NEW_TREND (>7.0 in 30 days), BREAKTHROUGH (+2.0 delta), DECLINE (<5.0 for 60 days)
```

#### Tool Evaluation Matrix
```
Capability:    Does it solve the problem well?         [0-10]
Maturity:      Production-ready? Active maintenance?   [0-10]
Ecosystem fit: Works with existing stack?              [0-10]
Cost profile:  Token/API/compute costs                 [0-10]
Community:     Size, activity, support quality         [0-10]
Security:      Vulnerabilities, compliance             [0-10]
Longevity:     VC backing, team, roadmap               [0-10]
```

#### 8-Phase Development Roadmap

| Phase | Name | Status | Branch |
|-------|------|--------|--------|
| P0 | Foundation | ✅ Complete | `feature/p0-foundation` |
| P1 | Knowledge Discovery | 🔄 In Progress | `feature/p1-knowledge-discovery` |
| P2 | Intelligence Layer | ⬜ | `feature/p2-intelligence-layer` |
| P3 | Agent Specialization | ⬜ | `feature/p3-agent-specialization` |
| P4 | Orchestration | ⬜ | `feature/p4-orchestration` |
| P5 | API & Integration | ⬜ | `feature/p5-api-integration` |
| P6 | Self-Improvement | ⬜ | `feature/p6-self-improvement` |
| P7 | Production Hardening | ⬜ | `feature/p7-production` |

#### Test Suite
- **119 passing tests**, zero external dependencies required
- No API keys needed to run the full suite
- `pytest tests/ -v` completes in under 10 seconds

#### Technology Stack (current/planned)

```
Language:        Python 3.11+
Agent base:      Custom BaseAgent (→ LangGraph at Phase 4)
LLM primary:     Claude 3.5 Sonnet (via llm_client injectable)
LLM fast/cheap:  Claude 3 Haiku
Vector store:    FAISS (dev) / Pinecone (production)
Relational:      SQLite (dev) / PostgreSQL (production)
Crawler:         requests + Playwright (JS sites) + Firecrawl (LLM-ready)
API:             FastAPI (Phase 5)
Scheduling:      APScheduler (Phase 4)
Monitoring:      LangSmith + structured logging (Phase 7)
Prompt opt:      DSPy (Phase 6)
```

---

## Part 3: The Knowledge Base — What We've Learned About the Field

### 3.1 Who Are the Influential AI Architecture Practitioners?

**Research & Foundational Thinkers**:
- **Andrej Karpathy** — "Software 2.0" thesis; exceptional communicator; coined "vibe coding" (2025)
- **Yann LeCun** — Chief critic of pure LLM approaches; JEPA architecture; world models
- **Ilya Sutskever** — Co-creator of GPT series; now at SSI focused on super-alignment
- **Dario Amodei** — Anthropic; Constitutional AI; responsible scaling policies
- **Demis Hassabis** — DeepMind; AlphaFold; Gemini

**Agentic Systems & Architecture Practitioners**:
- **Harrison Chase** — LangChain/LangGraph; defines de-facto agentic framework patterns
- **Jerry Liu** — LlamaIndex; RAG architecture patterns
- **Swyx (Shawn Wang)** — "AI Engineer" concept; Latent.Space; production AI writing
- **Simon Willison** — Documents decisions explicitly; LLM CLI tool; practical AI journalism
- **Lilian Weng** — Deep rigorous blog posts on agents, RLHF, diffusion models
- **Chip Huyen** — "Designing ML Systems"; feature stores, MLOps

**Key patterns from their practice**:
- Simon Willison: Document decisions explicitly; nothing should be implicit
- Karpathy: Understand what you're accepting; "vibe coding" risks → need architecture oversight
- Swyx: AI output should be treated like a PR, not a commit; eval-first
- Lilian Weng: Security-first; sanitize everything that touches an LLM
- Chip Huyen: Production ML requires treating data as a first-class system concern

### 3.2 Top Trends Right Now (2025–2026)

1. **[9.5] Rise of AI Engineering** — A distinct discipline between DS and SWE; production AI systems; 400%+ job growth
2. **[9.2] Compound AI Systems** — Multiple specialized models + tools orchestrated; replacing single-model approaches
3. **[9.0] Agentic RAG** — Dynamic retrieval decisions; query routing/rewriting; Graph RAG; Self-RAG
4. **[9.0] MCP + Dynamic Tool Discovery** — Universal tool protocol → dynamic load/unload pattern
5. **[8.8] Small Language Models (SLMs)** — Phi-3, Gemma, Llama 3.2 eating the middle market; on-device
6. **[8.7] Reasoning Models / Test-Time Compute** — o1/o3, DeepSeek R1; thinking budget as a new KPI
7. **[8.5] Multimodal AI as Infrastructure** — Claude 3.5, GPT-4o, Gemini 1.5 in production workflows
8. **[8.3] AI-Native Dev Tools** — Cursor, Devin, SWE-agent; AI in the development loop
9. **[8.0] Enterprise AI Governance** — EU AI Act enforcement; NIST AI RMF; board-level AI risk
10. **[7.5] Vibe Coding Phenomenon** — Low-barrier AI coding → more systems needing architecture oversight

### 3.3 Key Framework Signals

- **LangGraph** > LangChain for agents (stateful, production-ready)
- **LlamaIndex** is best-in-class for RAG pipelines
- **DSPy** growing fast for programmatic prompt optimization
- **FAISS** remains stable utility; **pgvector** growing for teams already on Postgres
- **vLLM** + **SGLang** are fastest open-source inference options
- **MCP** is rapidly becoming the universal tool protocol standard

### 3.4 Tools That Are Actually Used in Production (the signal, not the hype)

- **Cursor** — fastest-growing dev tool in history; AI-native IDE
- **LangSmith** — LLM tracing and evaluation; high adoption with LangGraph
- **Firecrawl** — LLM-ready web data extraction
- **Ollama** — local model serving; developer favourite
- **Modal** — serverless GPU; ML workloads

---

## Part 4: The Broader Ecosystem — ExMorbus V3 and MoltBook

### 4.1 ExMorbus V3 (External Consuming System)

**ExMorbus V3** is a sister project that will use Agentic-AI-Architect as its **architectural
oracle**.  It is a **medically-focused intelligence platform** modelled on the MoltBook
architecture pattern, with a staged domain specialisation curriculum:

```
Broad Health (10%) → Clinical Medicine (20%) → Oncology (30%) → Cancer Immunotherapy (40%)
```

Key integration points (documented in `docs/exmorbus-v3-integration.md`):
- ExMorbus V3 queries AAA via `GET /query`, `GET /trends`, `GET /tools` (REST, Phase 5)
- AAA pushes tool alerts and architecture recommendations to ExMorbus via webhooks
- AAA exposes knowledge via MCP server for direct agent consumption
- ExMorbus has an `ArchitectAgent` that calls AAA and creates shell review records

### 4.2 MoltBook Reference Architecture (Key Concepts)

MoltBook is the reference pattern from which ExMorbus V3 is derived.  Its core ideas
(documented in `docs/moltbook-research-findings.md`) are:

**Shell / Flesh separation**:
- **Shell** (persistent, IaC-defined): contracts, interfaces, event topology, governance policies
- **Flesh** (replaceable, tech-specific): LLM providers, vector stores, crawlers, APIs

**On-demand tool loading** (estimated ~3% of resident-MCP token overhead — needs
empirical validation; treat as a design-direction estimate, not a measured figure):
```python
async with HeavyTool() as tool:   # load
    result = await tool.execute(task)
# unload happens automatically
```

**Living Architecture Doctrine**: architecture is a continuously-curated artifact, not a
static diagram.  The Agentic-AI-Architect system is the primary engine for keeping it current.

---

## Part 5: The Coding Standards and Architecture Principles Used

### Python Standards
- Python 3.11+. `str | None` not `Optional[str]`. `list[dict]` not `List[Dict]`.
- Type annotations on all function signatures.
- Google-style docstrings. Module-level docstring on every file.
- Max 100 chars/line. Max 400 lines/file.
- f-strings only. `@dataclass` for DTOs. Every DTO has `to_dict()`.
- Optional heavy deps: `try/except ImportError` with graceful fallback.

### Architecture Rules
- Every agent inherits `BaseAgent`. Only `_execute()` is implemented. Never override `run()`.
- One responsibility per agent. No fat agents.
- `sanitize_text()` on ALL external content before LLM prompts. Non-negotiable.
- All secrets in `.env`. Never in source. All config via env vars with `AAA_` prefix.
- Rate limit every external HTTP call with `rate_limit()` utility.
- No network calls in tests. No API keys required. 119 tests pass clean.

### Anti-Patterns to Avoid
- Fat Orchestrator: logic beyond routing goes in agents
- God Agent: one agent doing crawling + research + scoring
- Inline LLM calls outside of agents
- Bare `requests.get()` without rate limiting
- Tests that require a real API key

---

## Part 6: What We Are Asking You To Do

### Your Task

1. **Read everything above carefully.** Understand the specific system (Agentic AI Architect), the broader vision (Multi-Agentic Product Management System), what has been built, the decisions made, and the roadmap ahead.

2. **Independently produce your own architectural proposal** for how you would design and build this system. Do not be constrained by what has already been built — propose what you think is the *best* approach. Where you agree with existing decisions, say so and why. Where you disagree or see a better path, say so clearly and specifically.

3. **Address these specific questions** in your proposal:

   **Architecture questions**:
   - Is the current agent architecture (custom `BaseAgent` → LangGraph at Phase 4) the right approach, or would you do it differently from the start?
   - Is the data flow (Crawler → Research → TrendTracker → ToolDiscovery → Documentation) the right pipeline structure? What would you change?
   - Is SQLite → PostgreSQL + FAISS → Pinecone the right storage progression? What would you choose?
   - What is the right way to handle the transition from a single-system build to the multi-system vision (AI Architect + Data Architect + Engineering + SecOps + etc.)?

   **Design questions**:
   - How should the shared knowledge layer work across all the planned systems?
   - What is the right inter-system communication protocol (REST? MCP? message bus? shared DB?)?
   - How would you design the MCP server interface so this system can be called by other agentic systems during their architecture phase?
   - What is missing from the current Phase 1–7 roadmap?

   **ExMorbus V3 / external system integration questions**:
   - AAA is planned to serve as the architectural oracle for ExMorbus V3 (a medical research
     platform modelled on MoltBook's shell/flesh pattern).  How should AAA's Phase 5 REST API
     and MCP server be designed to serve an external system like ExMorbus efficiently and
     securely?
   - The MoltBook "lobster shell" pattern (persistent shell contracts + hot-swappable flesh
     implementations + on-demand tool loading) is the reference architecture for ExMorbus V3.
     Does this pattern apply to AAA itself?  What would it look like if AAA adopted it?
   - ExMorbus V3 needs a staged domain curriculum (health → medicine → oncology → immunotherapy).
     Should AAA know anything about domain-specific architecture patterns for medical AI systems,
     or should it remain purely domain-agnostic?

   **Prioritization questions**:
   - If you had to deliver a *useful, production-ready v0.1* in 2 weeks, what would you build and what would you cut?
   - What is the highest-leverage capability to develop next (after current Phase 1 work)?
   - What are the top 3 risks to this project that should be mitigated now?

4. **Evaluate the AI coding agent instructions** (`CLAUDE.md`, `.github/copilot-instructions.md`, `.cursorrules`). Are they complete? Accurate? Do they set the right constraints? What would you add, remove, or change to make AI coding assistants more productive and less likely to make costly mistakes on this project?

5. **Propose a GitHub Codespaces configuration** for this project. What dev container setup, pre-installed tools, MCP integrations, and environment configuration would give a developer (or AI coding agent) the best possible working environment for this specific project?

---

## Part 7: Format of Your Response

Please structure your response as follows:

```
## 1. Architecture Assessment
[What you agree with, what you'd change, and why — specific, not generic]

## 2. Your Proposed Architecture
[Your complete architectural vision — draw ASCII diagrams if helpful]

## 3. Storage & Knowledge Layer Proposal
[How you'd design the shared knowledge layer for the multi-system future]

## 4. Roadmap Critique & Revision
[What you'd change about the phased plan and why]

## 5. v0.1 Proposal (2-week scope)
[The minimal viable version that proves core value]

## 6. Top Risks & Mitigations
[The 3–5 most important risks and how to address them]

## 7. AI Agent Instructions Review
[What's good, what's missing, what you'd change in CLAUDE.md / .cursorrules]

## 8. GitHub Codespaces Configuration
[Your proposed devcontainer.json and setup]

## 9. What I Would Do Differently From Day One
[Honest assessment — what decisions would you have made differently?]
```

Be direct. Be specific. Cite reasons. This is a design review, not a praise session. The goal is to find the best path forward, not to validate what's already been done.

---

## Part 8: Appendix: The Repository AI Coding Agent Instructions (for reference)

The following is the current `CLAUDE.md` (the canonical instruction file). Review it as part of your evaluation:

---

### Mission
Building the world's standard for an agentic AI architectural intelligence system — a self-improving, multi-agent ecosystem that continuously discovers, tracks, synthesises, and documents everything an AI Architect needs to know.

### Architecture Summary
- `src/agents/` — atomic agents; all inherit BaseAgent; one responsibility each
- `src/knowledge/` — SQLite structured store + FAISS vector store
- `src/pipeline/` — ingestion and processing pipeline
- `src/utils/helpers.py` — sanitize_text, chunk_text, retry_with_backoff, rate_limit
- `config/settings.py` — all settings via env vars with AAA_ prefix

### Non-Negotiable Principles
1. Atomic Agents — one responsibility, never combine
2. Observable by Default — self.logger always, never print()
3. Contract Before Implementation — define I/O types before coding
4. Tests Are Not Optional — happy path + failure path for every agent
5. Sanitize External Content — sanitize_text() before any LLM call
6. Never Commit Secrets — .env file only
7. Phase Discipline — don't implement Phase N+1 during Phase N
8. Minimal Blast Radius — fewest files changed per PR
9. Docs Are Living Code — update phase docs in same commit as behavior changes
10. Think Before You Type — state your plan before writing code

### Current Phase
Phase 1: Knowledge Discovery (Crawler, Research Agent, Ingestion Pipeline)

---

---END PROMPT---

---

## Notes on Using This Document

### For Codespace Sessions
When starting a GitHub Codespace for this project, paste the full prompt above into your AI assistant as the first message. This primes the model with complete context, preventing it from making assumptions or re-designing things that are already decided.

### Comparing Responses
After getting responses from multiple models:
1. Map areas of agreement — these are likely correct or at least defensible
2. Map areas of disagreement — these are the decisions that need human judgment
3. Look for things no model mentions — these are likely blind spots in the current design
4. Weight proposals that come with specific tradeoffs over generic recommendations

### When Updating This Document
This document should be updated whenever:
- A major architectural decision is finalized
- A new system is added to the multi-agent product family
- Phase status changes (a phase completes or begins)
- The core technology stack changes

*Last updated: March 2026. Current phase: P1 Knowledge Discovery. ExMorbus V3 integration context added.*
