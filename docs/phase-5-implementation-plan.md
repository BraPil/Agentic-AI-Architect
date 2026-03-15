# Phase 5: Implementation Plan — Building the World's Standard Agentic AI Architect System

> This document describes the phased development roadmap for the Agentic AI Architect system, presented narratively and broken down into GitHub development branches and achievable objectives.

---

## 5.1 Narrative: The Vision

We are building a **living intelligence system** — not a static repository, not a one-time research report, but a continuously self-improving AI Architect that knows everything about its own field and gets smarter every day.

The system is designed in concentric circles of capability:

```
Circle 1: Foundation — Can it store and retrieve knowledge?
Circle 2: Discovery — Can it find new knowledge on its own?
Circle 3: Intelligence — Can it understand and synthesize what it finds?
Circle 4: Evolution — Can it refine itself based on new information?
Circle 5: Integration — Can it serve other systems as an AI knowledge oracle?
```

Each phase of development moves us one circle outward. We do not skip circles. We validate each circle before moving to the next.

**Guiding principles**:
1. **Atomic agents**: Each agent does one thing exceptionally well
2. **Observable by default**: Every decision and action is logged and explainable
3. **Composable**: Every component works standalone and in orchestration
4. **Testable**: Every agent has evaluations that confirm it's working correctly
5. **Secure**: Prompt injection defense, API key hygiene, rate limiting from day one

---

## 5.2 Phase Overview

| Phase | Name | Duration | Focus |
|-------|------|----------|-------|
| **P0** | Foundation | 2 weeks | Repository structure, base agent, knowledge store |
| **P1** | Knowledge Discovery | 3 weeks | Crawler, research agent, ingestion pipeline |
| **P2** | Intelligence Layer | 3 weeks | Synthesis, trend scoring, vector search |
| **P3** | Agent Specialization | 4 weeks | Tool discovery, documentation, evaluation |
| **P4** | Orchestration | 3 weeks | Multi-agent coordination, scheduling, state |
| **P5** | API & Integration | 2 weeks | REST/streaming endpoint, external system hooks |
| **P6** | Self-Improvement | 4 weeks | Learning from feedback, knowledge refinement |
| **P7** | Production Hardening | 3 weeks | Observability, security, cost optimization |

**Total estimated development**: ~24 weeks for full v1.0

## 5.2.1 Current Direction Update

The original roadmap is still useful as a phase scaffold, but repository work has already clarified a
more specific execution order.

The most important change is this:

- contract, evaluation, provenance, and query-surface work were pulled earlier than the original
  roadmap implied

That change was intentional.

The repository is no longer just proving that agents can crawl and store information. It is also
proving that AAA can serve structured, machine-readable architectural answers that can later be reused by
other systems.

In practical terms, the current direction inside Phase 1 now includes:

- canonical answer contract definition
- initial evaluation set and executable scoring
- source weighting and learned weighting
- enterprise overlay and segment-aware evaluation
- durable repository memory
- curated-source ingest improvements, including LinkedIn PDF ingest for user-provided research inputs

This means the roadmap should now be read with one governing rule:

build the smallest trustworthy queryable intelligence system first, then widen autonomy and
orchestration around it.

---

## 5.3 Detailed Phase Breakdown

---

### Phase 0: Foundation (Weeks 1–2)
**Branch**: `feature/p0-foundation`

**Narrative**: Before any agent can think, it needs a place to remember. Before any agent can act, it needs a contract to follow. Phase 0 establishes the bedrock.

#### Objectives

**P0.1 — Project Scaffolding** ✅ (this PR)
- Directory structure established
- README with architecture overview
- Five-phase documentation completed
- Base configuration system

**P0.2 — Base Agent Contract**
- Abstract `BaseAgent` class with standardized interface
- Lifecycle methods: `initialize()`, `run()`, `health_check()`, `shutdown()`
- Logging integration with structured output
- Error handling and retry patterns

**P0.3 — Knowledge Base (Structured)**
- SQLite-backed knowledge store with schema migrations
- Namespaced knowledge entries: `education`, `frameworks`, `trends`, `tools`
- CRUD operations with timestamps and source attribution
- JSON serialization for complex objects

**P0.4 — Vector Store (Semantic Search)**
- FAISS-backed vector store
- Embedding generation (OpenAI `text-embedding-3-small` or local `nomic-embed-text`)
- Chunking strategies (fixed-size, semantic, hierarchical)
- Similarity search with configurable top-k and threshold

**P0.5 — Configuration System**
- `config/settings.py` with Pydantic models
- Environment variable loading (`.env` support)
- Per-environment configs (dev, test, production)
- API key management (never in source code)

#### Success Criteria
- [ ] `BaseAgent` can be subclassed and instantiated
- [ ] Knowledge base can store and retrieve 10,000+ entries in < 100ms
- [ ] Vector store returns semantically relevant results for test queries
- [ ] All unit tests pass: `pytest tests/ -v`

---

### Phase 1: Knowledge Discovery (Weeks 3–5)
**Branch**: `feature/p1-knowledge-discovery`

**Narrative**: The system gets its eyes and ears. The Crawler Agent learns to navigate the internet, respecting rate limits and robots.txt, extracting clean content. The Research Agent learns to read what the crawler finds and extract structured knowledge.

#### Objectives

**P1.1 — Crawler Agent**
- HTTP crawler with rate limiting and exponential backoff
- Playwright-based dynamic site support (JavaScript-rendered pages)
- Firecrawl integration for LLM-optimized content extraction
- Content deduplication (hash-based)
- robots.txt compliance checker
- Configurable source list: arXiv, GitHub, HN, Reddit, Anthropic blog, OpenAI blog, LangChain, LlamaIndex, HuggingFace

**P1.2 — Content Processing Pipeline**
- Raw HTML → clean text (Trafilatura or Readability)
- PDF parsing (PyMuPDF + LlamaParse for complex documents)
- Code block extraction and language detection
- Metadata extraction: title, author, date, URL, source type

**P1.3 — Research Agent (Basic)**
- Extract key concepts from crawled content
- Classify content type: paper / tutorial / tool release / opinion / benchmark
- Generate structured summary with LLM
- Store to knowledge base with source attribution

**P1.4 — Ingestion Pipeline**
- Queue-based processing (Python Queue or Redis for distributed)
- Priority queue: recent content > older content
- Deduplication at ingestion point
- Error handling and dead letter queue

**P1.5 — Canonical Contract And Evaluation Backbone**
- Define the first machine-readable answer contract
- Implement typed request and response schemas
- Define and expose the initial scored evaluation set
- Add executable scoring for query responses
- Persist evaluation history for later trend and weighting analysis

**P1.6 — Source Weighting And Enterprise Overlay**
- Make retrieval source weighting explicit and auditable
- Add learned source multipliers from persisted evaluation outcomes
- Add enterprise overlay fields to the answer contract
- Add segment-aware evaluation and comparison paths

**P1.7 — Curated Input Expansion**
- Capture high-signal influencer and post watchlists as durable source inputs
- Support user-provided LinkedIn PDF ingest as a practical boundary for auth-gated social content
- Seed high-signal retained posts into the knowledge base with provenance metadata

#### Success Criteria
- [ ] Crawler successfully extracts clean text from 100 diverse URLs
- [ ] Research Agent correctly classifies content type with ≥ 85% accuracy
- [ ] Full pipeline ingests 50 arXiv papers and stores structured summaries
- [ ] No robots.txt violations in crawl history
- [ ] Canonical answer contract is stable enough to score repeatedly across a defined question set
- [ ] Evaluation history can be persisted and queried over time

---

### Phase 2: Intelligence Layer (Weeks 6–8)
**Branch**: `feature/p2-intelligence-layer`

**Narrative**: Raw data is not knowledge. The intelligence layer transforms crawled content into structured, queryable, evolving knowledge — with semantic search that understands meaning, not just keywords.

#### Objectives

Phase 2 now assumes that a minimal queryable surface and evaluation backbone already exist.

The emphasis therefore shifts from "can the system answer at all" to "can the system answer with
better synthesis, ranking, and reliability over time."

**P2.1 — Enhanced Research Agent**
- Relationship extraction: "Tool X is an alternative to Tool Y"
- Trend signal extraction: adoption mentions, deprecation signals, benchmark results
- Concept linking: connect new concepts to existing knowledge base entries
- Confidence scoring for extracted facts

**P2.2 — Trend Tracker Agent**
- Trend scoring formula implementation (recency × velocity × credibility)
- Time-series tracking of trend scores
- Trend emergence detection (new topic surpassing threshold)
- Trend decline detection (established topic falling)
- Weekly trend report generation

**P2.3 — Vector Store Enhancement**
- Namespace-based indexes per knowledge domain
- Hybrid search: BM25 + semantic (for better recall on specific terms)
- Re-ranking with cross-encoder
- Query expansion and HyDE support

**P2.4 — Knowledge Graph (Lightweight)**
- Entity-relationship tracking in SQLite
- "Is related to", "is alternative to", "succeeded by", "part of" relationship types
- Graph traversal queries
- Visualization export (Mermaid diagram format)

#### Success Criteria
- [ ] Trend scores are computed weekly for 50+ tracked topics
- [ ] Vector search returns relevant results with ≥ 0.80 precision@10
- [ ] Knowledge graph has ≥ 500 entity relationships after processing 1000 documents
- [ ] Trend reports generated without manual intervention

---

### Phase 3: Agent Specialization (Weeks 9–12)
**Branch**: `feature/p3-agent-specialization`

**Narrative**: General capability is not enough. The system now develops deep expertise in the areas that matter most to AI Architects: tools, documentation, and evaluation.

#### Objectives

**P3.1 — Tool Discovery Agent**
- GitHub trending repo watcher (topics: ai, llm, rag, agents, mcp)
- Tool metadata extraction: language, license, stars, forks, last commit
- Tool comparison matrix generation
- Breaking change detection from changelogs and release notes
- Replacement/deprecation alerts

**P3.2 — Documentation Agent**
- Automated markdown document generation from knowledge base
- Phase documentation auto-update triggers
- Knowledge summary generation (daily digest)
- Comparison tables: tool X vs. tool Y
- "What's new this week" report generation

**P3.3 — Agent Evaluation Framework**
- Define evaluation criteria per agent
- LLM-as-judge implementation for open-ended outputs
- Benchmark datasets for: crawling quality, extraction accuracy, trend scoring
- Regression testing to detect agent performance degradation
- Dashboard metrics per agent

**P3.4 — Prompt Injection Defense**
- Input sanitization for all external content before LLM processing
- System prompt hardening
- Output validation with Pydantic schemas
- Anomaly detection for unusual agent behavior

#### Success Criteria
- [ ] Tool Discovery Agent identifies GitHub trending AI repos daily
- [ ] Documentation Agent generates phase documents without human intervention
- [ ] Evaluation framework catches a known regression case
- [ ] Prompt injection test suite passes (test file: `tests/test_security.py`)

---

### Phase 4: Orchestration (Weeks 13–15)
**Branch**: `feature/p4-orchestration`

**Narrative**: Individual intelligence is valuable; coordinated intelligence is transformative. The Orchestrator learns to direct agents efficiently, avoid redundant work, and handle failures gracefully.

#### Objectives

**P4.1 — Orchestrator Agent**
- Decide and lock the orchestration strategy before broadening runtime complexity
- Implement either a LangGraph-based state machine or a deliberately retained custom orchestration layer
- Scheduled cycle: daily crawl → research → trend update → documentation refresh
- Dynamic agent spawning based on workload
- Inter-agent message passing with typed messages
- Global state management (what has been processed, what is queued)

**P4.2 — Task Queue & Scheduling**
- APScheduler integration for recurring tasks
- Priority-based task queue
- Rate limiting per external service
- Graceful degradation when external services are unavailable
- Task deduplication (don't crawl the same URL twice in 24h)

**P4.3 — Human-in-the-Loop**
- Approval queue for high-confidence auto-publications
- Flagging uncertain extractions for human review
- Feedback mechanism: "This trend score is wrong" → re-calibration
- Audit log for all automated decisions

**P4.4 — Error Recovery**
- Circuit breaker pattern for external API calls
- Dead letter queue with retry backoff
- Agent health monitoring
- Automatic agent restart on failure
- Alert notification on repeated failures

#### Success Criteria
- [ ] Full intelligence cycle runs end-to-end without human intervention
- [ ] System recovers from simulated API failure (chaos test)
- [ ] Orchestrator logs show clear decision trace for each cycle
- [ ] 24-hour automated run produces ≥ 100 new knowledge base entries

---

### Phase 5: API & Integration (Weeks 16–17)
**Branch**: `feature/p5-api-integration`

**Narrative**: The system opens its doors. Other agents, dashboards, and systems can now query this knowledge oracle. The primary integration target for v1.0 is ExMorbus V3, a medical research multi-agent platform that uses Agentic-AI-Architect as its standing architectural advisor. The full integration design is in `docs/exmorbus-v3-integration.md`.

#### Objectives

Some API work has already been pulled forward because contract and evaluation discipline depend on it.

That means Phase 5 should now be read as "expand and harden the external surface" rather than "create
the first external surface from scratch."

**P5.1 — REST API**
- FastAPI-based REST endpoint
- Endpoints:
  - `GET /query` — canonical contract-backed answer surface
  - `GET /trends` — current trend scores and rankings
  - `GET /tools` — tool database with filters
  - `GET /frameworks` — framework maturity matrix
  - `GET /evaluation-set` — served evaluation backbone
  - `GET /evaluate/query` — score one query response
  - `GET /evaluate/query-set` — score question batches
  - `GET /evaluate/query-segments` — compare one query across segments
  - `GET /evaluate/history` — persisted evaluation run history
  - `GET /evaluate/performance` — compact performance summary over evaluation runs
  - `POST /ingest` — submit a URL for processing
  - `GET /report/{phase}` — get latest phase report
  - `GET /recommend` — architecture recommendation for a problem statement (required by ExMorbus)
  - `GET /alerts` — trend alerts since a given timestamp (required by ExMorbus)
  - `GET /compare` — side-by-side tool comparison (required by ExMorbus)
  - `GET /health/summary` — knowledge freshness and system health (required by ExMorbus)
- OpenAPI spec generation
- Per-client API key authentication (required for ExMorbus usage tracking)
- All responses include `schema_version` field for forward-compatible versioning

**P5.2 — Streaming Endpoint**
- Server-Sent Events (SSE) for streaming knowledge responses
- WebSocket support for real-time trend updates
- Compatible with Vercel AI SDK streaming format

**P5.3 — MCP Server Interface**
- Expose knowledge base as an MCP server
- Tools: `search_knowledge`, `get_trend_score`, `get_tool_info`, `get_latest_report`, `get_architecture_recommendation`
- Resources: `knowledge://trends/current`, `knowledge://tools/database`
- Compatible with Claude Desktop and any MCP-compliant client
- Designed for on-demand load/unload (< 200ms cached query latency) to support token-efficient usage patterns
- See `docs/exmorbus-v3-integration.md §4.1` for full MCP tool specifications

**P5.4 — Integration Adapters**
- LangChain tool wrappers for the knowledge API
- LlamaIndex query engine adapter
- Webhook support for external system notifications (required for ExMorbus proactive architecture alerts)
  - Webhook contract defined in `docs/exmorbus-v3-integration.md §4.4`
  - Events: `trend_alert`, `tool_deprecated`, `framework_emerged`, `architecture_shift`
- **ExMorbus adapter** (`src/api/adapters/exmorbus.py`): typed client that wraps REST + MCP + webhook registration for seamless ExMorbus V3 integration
- Optional `tags` filter on `/query` and `/recommend` for medical-adjacent architecture concerns: `medical_agents`, `data_compliance`, `evidence_pipelines`, `long_running_workflows`, `human_in_loop`

#### Success Criteria
- [ ] REST API responds to query in < 500ms for cached, < 2s for live
- [ ] MCP server connects to Claude Desktop and returns accurate responses
- [ ] API handles 100 concurrent requests without degradation
- [ ] OpenAPI spec passes validation
- [ ] ExMorbus adapter can load MCP tool, run `search_knowledge`, and unload in a single round trip under 500ms
- [ ] Webhook delivery fires within 5 minutes of trend alert detection
- [ ] All response types include `schema_version`; breaking changes bump major version

---

### Phase 6: Self-Improvement (Weeks 18–21)
**Branch**: `feature/p6-self-improvement`

**Narrative**: The system learns from its own outputs. Poor-quality extractions get corrected. High-confidence patterns are reinforced. The knowledge base improves with every cycle.

#### Objectives

**P6.1 — Feedback Collection**
- User rating on query responses (thumbs up/down + optional text)
- Internal agent self-evaluation (did the tool achieve its objective?)
- Cross-agent validation (Research Agent validates Crawler Agent output quality)

**P6.2 — Knowledge Refinement**
- Stale knowledge detection (last verified > 30 days for fast-moving topics)
- Contradiction detection (conflicting information in knowledge base)
- Confidence decay (confidence score reduces as content ages without reconfirmation)
- Automatic re-research for stale high-importance topics

**P6.3 — Prompt Optimization (DSPy Integration)**
- Use DSPy to optimize extraction prompts based on feedback data
- A/B test prompt variations for key extraction tasks
- Track prompt version performance over time
- Automated prompt regression prevention

**P6.4 — Knowledge Distillation**
- Periodic "synthesis" runs that produce refined understanding from accumulated evidence
- Generate canonical entries for key topics from multiple source documents
- Remove outdated entries when superseded by refined understanding

#### Success Criteria
- [ ] Knowledge quality score improves week-over-week for 4 consecutive weeks
- [ ] Stale content detection catches 90%+ of outdated entries
- [ ] DSPy prompt optimization improves extraction accuracy by ≥ 5%
- [ ] No contradictory high-confidence facts in knowledge base

---

### Phase 7: Production Hardening (Weeks 22–24)
**Branch**: `feature/p7-production`

**Narrative**: The system is ready to run 24/7, cost-efficiently, securely, and observably. This phase makes it production-grade.

#### Objectives

**P7.1 — Observability Stack**
- Structured logging (JSON format, ECS schema)
- OpenTelemetry tracing
- Metrics: query latency, extraction quality, trend score drift, cost per cycle
- Dashboard (Grafana or simple HTML dashboard)
- Alerting on SLO violations

**P7.2 — Cost Optimization**
- Token counting and budget tracking per agent
- LLM routing: cheap model for classification, expensive model for synthesis
- Caching layer for repeated LLM calls (exact + semantic cache)
- Cost per knowledge base entry tracking
- Monthly cost projection dashboard

**P7.3 — Security Hardening**
- Dependency vulnerability scanning (Dependabot / Safety)
- Secret scanning prevention
- Rate limiting on all external-facing endpoints
- Input validation with comprehensive Pydantic schemas
- Regular prompt injection regression tests

**P7.4 — Documentation & Runbooks**
- Operations runbook: how to restart, debug, recover
- New developer guide: how to add a new agent
- Contributing guide: how to add a new knowledge source
- Architecture decision records (ADRs) for key design choices

#### Success Criteria
- [ ] System runs 168 hours (1 week) without human intervention
- [ ] Monthly LLM costs stay under configured budget ($X)
- [ ] Zero critical security vulnerabilities (Bandit + Safety scan clean)
- [ ] Runbook enables new team member to diagnose issues without prior knowledge

---

## 5.4 GitHub Branch Structure

```
main
├── feature/p0-foundation
│   ├── task/p0.1-scaffolding           # ✅ Completed
│   ├── task/p0.2-base-agent
│   ├── task/p0.3-knowledge-base
│   ├── task/p0.4-vector-store
│   └── task/p0.5-configuration
│
├── feature/p1-knowledge-discovery
│   ├── task/p1.1-crawler-agent
│   ├── task/p1.2-content-processing
│   ├── task/p1.3-research-agent
│   ├── task/p1.4-ingestion-pipeline
│   ├── task/p1.5-answer-contract-v0
│   ├── task/p1.6-eval-question-set
│   ├── task/p1.7-source-weighting-model
│   ├── task/p1.8-enterprise-overlay-fields
│   ├── task/p1.9-evaluation-persistence
│   └── task/p1.10-linkedin-pdf-ingest
│
├── feature/p2-intelligence-layer
│   ├── task/p2.1-enhanced-research
│   ├── task/p2.2-trend-tracker
│   ├── task/p2.3-vector-enhancement
│   └── task/p2.4-knowledge-graph

├── research/exmorbus-through-aaa-v1
│
└── spike/exmorbus-shell-poc-v1
```

Branch usage should follow the operating guidance in `docs/branch-strategy-summary.md`.

The practical rule is:

- use `task/...` for bounded implementation work
- use `research/...` for durable ontology and contract work
- use `spike/...` for fast validation of shell shape

Additional planned feature branches remain:

```
feature/p3-agent-specialization
│   ├── task/p3.1-tool-discovery
│   ├── task/p3.2-documentation-agent
│   ├── task/p3.3-evaluation-framework
│   └── task/p3.4-prompt-injection-defense
│
├── feature/p4-orchestration
│   ├── task/p4.1-orchestrator
│   ├── task/p4.2-task-scheduling
│   ├── task/p4.3-human-in-loop
│   └── task/p4.4-error-recovery
│
├── feature/p5-api-integration
│   ├── task/p5.1-rest-api
│   ├── task/p5.2-streaming
│   ├── task/p5.3-mcp-server
│   └── task/p5.4-integration-adapters
│
├── feature/p6-self-improvement
│   ├── task/p6.1-feedback-collection
│   ├── task/p6.2-knowledge-refinement
│   ├── task/p6.3-prompt-optimization
│   └── task/p6.4-knowledge-distillation
│
feature/p7-production
    ├── task/p7.1-observability
    ├── task/p7.2-cost-optimization
    ├── task/p7.3-security-hardening
    └── task/p7.4-documentation
```

---

## 5.5 Technology Stack Decision Matrix

| Layer | Choice | Alternative | Rationale |
|-------|--------|-------------|-----------|
| Language | Python 3.11+ | TypeScript | ML ecosystem; LangChain/LlamaIndex native |
| Agent Framework | Custom `BaseAgent` contract now; orchestration strategy still open | LangGraph / AutoGen | BaseAgent is already the working lifecycle contract; orchestration should not be treated as implicitly settled before an explicit decision |
| LLM (primary) | Claude 3.5 Sonnet | GPT-4o | Best instruction following; long context |
| LLM (fast/cheap) | Claude 3 Haiku | GPT-4o-mini | Cost-optimized for classification tasks |
| Vector Store | FAISS (local) / PostgreSQL + pgvector or Pinecone later | Qdrant | FAISS remains the simplest local baseline; production target should remain open until retrieval and hosting needs are clearer |
| Relational Store | SQLite → PostgreSQL | DynamoDB | Simple start; scale when needed |
| API Framework | FastAPI | Flask | Async; automatic OpenAPI; Pydantic integration |
| Crawler | Firecrawl + Playwright | Scrapy | LLM-ready output; dynamic site support |
| Task Scheduling | APScheduler | Celery | Lightweight; good enough for Phase 4 |
| Monitoring | LangSmith + structured logs | Datadog | LLM-native tracing; cost visibility |
| Prompt Optimization | DSPy | Manual | Systematic optimization over time |

---

## 5.6 Definition of Done — v1.0

The system is considered **v1.0 complete** when:

1. ✅ All 7 phases completed and passing success criteria
2. ✅ System runs fully autonomously for 30 days
3. ✅ Knowledge base contains ≥ 10,000 structured entries
4. ✅ All 5 phase documents are auto-maintained and current
5. ✅ REST API and MCP server are operational
6. ✅ Monthly cost is < $100 (using model routing and caching)
7. ✅ Zero unhandled exceptions in 30-day run log
8. ✅ External AI system successfully queries knowledge base and gets useful response
9. ✅ Trend alerts have notified about ≥ 3 genuine new trends before they went mainstream
10. ✅ Another developer can set up and run the system with the README alone
11. ✅ ExMorbus V3 can load the MCP tool, query `search_knowledge`, and receive a useful architectural recommendation in under 500ms (validates the on-demand low-token usage model)
12. ✅ At least one proactive webhook alert has been delivered to a registered external system
