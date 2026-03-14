# ExMorbus V3 Integration: Agentic-AI-Architect as the Architectural Brain

> **Status**: Strategic synthesis document — reviewed 2026-03  
> **Scope**: Defines how Agentic-AI-Architect serves ExMorbus V3, based on MoltBook architectural analysis and the ExMorbus V3 vision conversation.  
> **Maintained by**: This document should be updated whenever the ExMorbus integration design or Agentic-AI-Architect Phase 5 API scope changes.

---

## 1. The MoltBook Architectural Synthesis

### 1.1 What MoltBook Is

MoltBook is a progressive-specialization AI learning platform whose core insight is that **intelligence narrows toward expertise the same way biological organisms grow: by molting old generalist structure and replacing it with specialized capability**.

The platform's architecture has four defining properties, each of which ExMorbus V3 should inherit and amplify for the medical domain:

| Property | MoltBook Pattern | ExMorbus V3 Analogue |
|----------|-----------------|----------------------|
| **Progressive curriculum** | Broad training narrows iteratively toward deep domain expertise | General health → Clinical medicine → Oncology → Novel cancer immunotherapy |
| **Atomized agents** | Agents are irreducible specialists; one responsibility each | Literature agents, evidence agents, hypothesis agents, experiment design agents |
| **Agent economy** | Solutions are traded, graded, and commoditized between agents | Research findings are scored by evidence quality and exchanged as standardized artifacts |
| **Living architecture** | The platform shell is stable IaC; implementations are hot-swappable | PostgreSQL/Redis/Playwright can be replaced without changing the research agent contracts |

### 1.2 The Lobster Shell Principle

The central architectural metaphor emerging from the ExMorbus V3 philosophy is the **lobster shell**: the hard shell (IaC-defined structure, agent contracts, knowledge schemas) persists and grows, while the soft body (concrete tool implementations, LLM providers, storage backends) is periodically shed and replaced with newer, better-adapted tissue.

This directly implies:

- **Agent contracts are first-class artifacts.** Every agent interface (inputs, outputs, error shapes) must be versioned and stable. The implementation inside the shell can change completely.
- **Technology bindings are late-binding.** PostgreSQL, Redis, Playwright, Vercel — these are wired in at deployment time via IaC and environment variables, not hardcoded into agent logic.
- **Architecture knowledge decays rapidly.** The AI tooling landscape changes faster than any human can track. This is exactly why ExMorbus needs Agentic-AI-Architect: to continuously watch the landscape and advise when a better implementation for any shell slot exists.

### 1.3 The Agent Economy Model

In MoltBook-style systems, agents do not merely cooperate — they participate in an **internal economy of research artifacts**:

- **Grading**: Every output artifact carries a confidence/evidence score. Higher-graded artifacts are routed preferentially.
- **Trading**: Agents exchange artifacts through typed message contracts. A `ResearchFinding` from a literature agent is a tradeable unit — it can be consumed by an evidence evaluator, a hypothesis generator, or a documentation agent without those agents knowing or caring about its origin.
- **Commoditization**: High-confidence, repeatedly-validated findings are "distilled" into canonical knowledge entries — the equivalent of a research commodity that has survived market testing.

For ExMorbus V3, this economy operates on **medical research artifacts**: literature citations, evidence summaries, hypothesis proposals, experiment protocols, and outcome reports.

---

## 2. ExMorbus V3 Vision: MoltBook for Medical Research

### 2.1 The Specialization Ladder

ExMorbus V3 structures all knowledge acquisition and agent specialization around a progressive ladder:

```
Level 0 — Broad Foundation (~10% of total training budget)
  Health, nutrition, exercise, psychology, happiness, stress mitigation,
  anatomy, biology, organic chemistry, biochemistry

Level 1 — Clinical Medicine
  Disease mechanisms, pharmacology, clinical trials methodology,
  evidence-based medicine, diagnostic reasoning

Level 2 — Oncology
  Cancer biology, tumor immunology, mutation landscapes,
  treatment modalities (surgery, radiation, chemo, immunotherapy),
  biomarker discovery

Level 3 — Focused Specialization (deepest investment)
  Novel cancer therapy, therapeutic vaccination research,
  experimental immunotherapy design, trial protocol generation,
  outcome analysis and publication
```

Every agent in ExMorbus V3 is trained and scoped to a specific rung of this ladder. Agents at lower rungs produce generalized findings; agents at higher rungs consume those findings and produce specialized insights. **No single agent spans more than one rung.**

### 2.2 The Atomized Research Agent Ecosystem

The 23-agent architecture from ExMorbus v0.2 maps onto this ladder as follows:

```
Foundation Layer (Level 0)
  HealthCorpusAgent      — ingests and indexes broad health content
  AnatomyKnowledgeAgent  — curates structural biology knowledge base

Discovery Layer (Levels 0–1)
  LiteratureResearcher   — searches PubMed, arXiv, bioRxiv
  EvidenceIdentifier     — scores literature evidence quality
  TrialMonitorAgent      — watches ClinicalTrials.gov for new entries

Analysis Layer (Levels 1–2)
  EvidenceEvaluator      — grades evidence by GRADE/Oxford criteria
  HypothesisGenerator    — generates testable hypotheses from evidence clusters
  BiologyReasonerAgent   — connects mechanism-of-action reasoning chains

Specialization Layer (Level 3)
  CancerTherapyAgent     — focused on novel therapeutic modalities
  VaccinationDesignAgent — experimental vaccination research patterns
  TrialProtocolAgent     — generates draft trial protocols from hypotheses
  OutcomeAnalyzerAgent   — analyzes published trial outcomes

Infrastructure
  ResearchPlanner        — coordinates discovery → analysis → specialization flow
  ExperimentTracker      — logs and monitors active research threads
  ValidationAgent        — cross-validates findings across agents
  DocumentationAgent     — generates structured research summaries
  Orchestrator           — top-level coordination (lobster shell contract)
```

### 2.3 The V3 Architecture Shell

ExMorbus V3 adopts the following shell/implementation separation:

```
SHELL (IaC — stable, versioned, rarely changes)
  Agent contracts (input/output types, error shapes, schema versions)
  Knowledge schemas (entity types, relationship types, namespace hierarchy)
  Pipeline topology (which agent feeds which, in what order)
  Governance policies (data retention, access control, audit requirements)
  Deployment topology (Docker Compose / Kubernetes manifests)

IMPLEMENTATION (hot-swappable — changes as better options emerge)
  LLM providers (Anthropic → Google → open weights as landscape evolves)
  Vector store (FAISS → pgvector → future specialized medical vector DBs)
  Literature sources (PubMed API → semantic scholar → direct crawl)
  Task queue (Python Queue → Redis Streams → Temporal as scale demands)
  Frontend (Vercel → Next.js edge → whatever comes next)
  Infrastructure substrate (single server → Kubernetes → serverless as needed)
```

---

## 3. Agentic-AI-Architect's Role in ExMorbus V3

### 3.1 The Architectural Advisor Model

Agentic-AI-Architect serves ExMorbus V3 in a specific, bounded role: **it watches the AI architecture landscape continuously and advises ExMorbus when a better implementation for any shell slot is available**.

It does NOT:
- Perform medical research itself
- Store or reason about clinical data
- Make research decisions

It DOES:
- Track emerging agentic patterns relevant to multi-agent medical research platforms
- Score and rank tools that could fill ExMorbus's implementation slots
- Alert when ExMorbus's current architecture choices are being superseded
- Answer targeted queries: "What is the best current approach for multi-agent coordination at our scale?"
- Provide architectural rationale for design decisions that ExMorbus must make

This is the **oracle model**: Agentic-AI-Architect is a read-only knowledge oracle that ExMorbus queries when it needs architectural guidance. ExMorbus remains in full control of its own decisions.

### 3.2 Usage Pattern: On-Demand, Low-Token

Per the ExMorbus V3 philosophy of token efficiency (achieving MCP-like results at ~3% of standard token cost), Agentic-AI-Architect is used as an **on-demand tool, loaded at the point of necessity and immediately unloaded**:

```python
# ExMorbus usage pattern (conceptual)
# 1. Load the Agentic-AI-Architect MCP tool — only when an architectural
#    question needs answering (e.g., during architecture review cycles,
#    when a shell slot is being reconsidered, or when a new agent is
#    being designed).
arch_tool = await mcp_manager.load_tool("agentic-ai-architect")

# 2. Query with a targeted, specific question
result = await arch_tool.call("search_knowledge", {
    "query": "best multi-agent coordination patterns for medical research 2026",
    "namespace": "frameworks",
    "top_k": 5
})

# 3. Unload immediately — do not keep resident
await mcp_manager.unload_tool("agentic-ai-architect")
```

This pattern means Agentic-AI-Architect must be **fast to respond** (< 500ms for cached queries) and **precise in its answers** (high-signal, low-noise responses that don't require follow-up queries to be useful).

### 3.3 Integration Touch Points

Agentic-AI-Architect is integrated into ExMorbus V3 at the following specific points:

| Integration Point | When It Fires | Query Type | Expected Response Shape |
|-------------------|--------------|------------|------------------------|
| New agent design review | Developer designing a new ExMorbus agent | Architecture patterns for the agent's responsibility | Top 3–5 current patterns with maturity scores |
| Shell slot evaluation | Before choosing/replacing an implementation (e.g., switching task queues) | Tool comparison for the slot category | Comparison matrix: current options ranked by recency + fitness |
| Architecture cycle alert | Weekly architectural health check | Trend alerts for ExMorbus-relevant topics | List of alerts: "X is replacing Y", "Z has emerged as a new option" |
| Hypothesis about architecture | Any agent wondering about an architectural approach | Free-form architectural query | Summarized finding with source references |
| V3 shell design review | When ExMorbus redefines its shell contracts | Architectural validation query | Risk assessment, pattern recommendations, alternative approaches |

---

## 4. Required API and Integration Contracts

### 4.1 MCP Tool Interface (Phase 5 Priority)

The following MCP tool definitions must be available in Agentic-AI-Architect's Phase 5 MCP server to serve ExMorbus:

```python
# Tool: search_knowledge
# Purpose: Semantic search over the knowledge base
# ExMorbus use: finding best architectural patterns for a given need
{
    "name": "search_knowledge",
    "description": "Search the AI architecture knowledge base for relevant findings",
    "inputSchema": {
        "query": "str — natural language question or topic",
        "namespace": "str — one of: frameworks, trends, tools, education, general",
        "top_k": "int — number of results (default 5, max 20)",
        "min_confidence": "float — minimum confidence threshold (default 0.6)",
        "recency_weight": "float — weight for recency in scoring (0.0–1.0, default 0.5)"
    },
    "outputSchema": {
        "results": "list[KnowledgeResult]",
        "query_time_ms": "int",
        "schema_version": "str"
    }
}

# Tool: get_trend_score
# Purpose: Get current trend score and trajectory for a specific topic
# ExMorbus use: evaluating whether to adopt an emerging technology
{
    "name": "get_trend_score",
    "description": "Get the current trend score and trajectory for an AI topic",
    "inputSchema": {
        "topic": "str — topic name or identifier",
        "include_signals": "bool — include raw signal data (default false)"
    },
    "outputSchema": {
        "topic": "str",
        "score": "float — 0.0–1.0",
        "trajectory": "str — rising | stable | declining | emerging | unknown",
        "last_updated": "datetime",
        "signal_count": "int",
        "alerts": "list[TrendAlert]"
    }
}

# Tool: get_tool_info
# Purpose: Get structured information about a specific AI tool or framework
# ExMorbus use: evaluating a tool for a shell implementation slot
{
    "name": "get_tool_info",
    "description": "Get structured information about an AI tool, framework, or library",
    "inputSchema": {
        "tool_name": "str — exact name or fuzzy match",
        "include_alternatives": "bool — include ranked alternatives (default true)"
    },
    "outputSchema": {
        "name": "str",
        "description": "str",
        "category": "str",
        "maturity": "str — emerging | growing | stable | declining",
        "last_significant_change": "date",
        "alternatives": "list[ToolSummary]",
        "architecture_fit_notes": "str"
    }
}

# Tool: get_architecture_recommendation
# Purpose: Get a targeted architectural recommendation for a specific problem
# ExMorbus use: designing new agents, choosing between patterns
{
    "name": "get_architecture_recommendation",
    "description": "Get an architecture recommendation for a specific design question",
    "inputSchema": {
        "problem_statement": "str — description of the architecture decision to make",
        "constraints": "list[str] — known constraints (e.g., 'must work offline', 'Python 3.11+')",
        "current_stack": "dict[str, str] — current technology choices by category"
    },
    "outputSchema": {
        "recommendation": "str — primary recommendation",
        "rationale": "str — reasoning behind recommendation",
        "alternatives": "list[AlternativeApproach]",
        "risk_factors": "list[str]",
        "confidence": "float",
        "sources": "list[SourceReference]"
    }
}

# Tool: get_latest_report
# Purpose: Retrieve a pre-generated phase document or trend report
# ExMorbus use: periodic architecture health reviews
{
    "name": "get_latest_report",
    "description": "Retrieve the latest generated report for a knowledge domain",
    "inputSchema": {
        "report_type": "str — one of: trends, tools, frameworks, education, weekly_digest"
    },
    "outputSchema": {
        "report_type": "str",
        "generated_at": "datetime",
        "content": "str — markdown-formatted report",
        "entry_count": "int"
    }
}
```

### 4.2 REST API Requirements (Phase 5)

ExMorbus needs the following REST endpoints beyond the base plan:

```
GET  /query                     (already planned)
GET  /trends                    (already planned)
GET  /tools                     (already planned)
GET  /frameworks                (already planned)
POST /ingest                    (already planned)
GET  /report/{phase}            (already planned)

NEW — required for ExMorbus integration:
GET  /recommend?problem=...     — architecture recommendation endpoint
GET  /alerts?since=...          — trend alerts since a given timestamp
GET  /compare?tools=a,b,c       — side-by-side tool comparison
GET  /health/summary            — system health + knowledge freshness summary
```

### 4.3 Knowledge Namespaces for Medical/Research Context

The current knowledge namespaces (`education`, `frameworks`, `trends`, `tools`, `general`) are sufficient for Agentic-AI-Architect's internal use. However, ExMorbus queries will often carry implicit medical context. The following **query tags** (not new namespaces) should be supported in search and recommendation endpoints to filter results for medical-adjacent architectural concerns:

```
medical_agents         — agent patterns specific to research/medical domains
data_compliance        — HIPAA, GDPR, clinical data governance patterns
evidence_pipelines     — patterns for literature ingestion and evidence grading
long_running_workflows — patterns for multi-day/multi-week research orchestration
human_in_loop          — patterns for researcher review and approval workflows
```

These are passed as optional `tags` filter on search/recommendation calls, not as separate namespaces.

### 4.4 Event Webhook for Proactive Alerts

ExMorbus V3 should register a webhook endpoint with Agentic-AI-Architect to receive proactive notifications without polling. The webhook contract:

```json
{
  "event_type": "trend_alert | tool_deprecated | framework_emerged | architecture_shift",
  "severity": "info | warning | critical",
  "topic": "string",
  "summary": "string",
  "affected_shell_categories": ["task_queue", "vector_store", "orchestration", ...],
  "recommendation": "string",
  "source_url": "string",
  "timestamp": "ISO 8601 datetime",
  "schema_version": "1.0"
}
```

Agentic-AI-Architect sends this to ExMorbus's registered webhook URL when a significant architectural development is detected. ExMorbus's architecture review agent consumes these events and decides whether to trigger a shell evaluation.

---

## 5. System Integration Requirements for Agentic-AI-Architect

The following requirements, derived from ExMorbus's needs, should be incorporated into Agentic-AI-Architect's Phase 5 planning:

### 5.1 Response Latency
- Cached knowledge queries: < 200ms (ExMorbus uses on-demand tool loading; slow first response defeats the efficiency goal)
- Live queries with LLM synthesis: < 3 seconds
- Trend alert generation: asynchronous; webhook delivery < 5 minutes from detection

### 5.2 Schema Versioning (Non-Negotiable)
All API responses must include `schema_version`. ExMorbus may be pinned to a version while Agentic-AI-Architect evolves. Version negotiation should follow standard semantic versioning. Breaking changes require a new major version and a 90-day deprecation window.

### 5.3 Offline / Degraded Operation
ExMorbus must continue functioning if Agentic-AI-Architect is unavailable. The integration must be purely advisory — no ExMorbus research workflow should block on an Agentic-AI-Architect response. All queries from ExMorbus should have a timeout (configurable, default 5 seconds) and a graceful fallback (log the query, return a cached or empty result, continue).

### 5.4 Authentication
ExMorbus authenticates to Agentic-AI-Architect using an API key (`AAA_API_KEY`) set at deployment time. Agentic-AI-Architect should support per-client API keys to allow usage tracking and rate limiting per integration. Rate limit: 1,000 queries/day per key for the free tier.

### 5.5 Audit Trail
Every query from ExMorbus that influences an architectural decision in ExMorbus should be logged on both sides:
- Agentic-AI-Architect logs: query text, response schema, latency, client ID
- ExMorbus logs: what architectural decision was made, which query informed it, timestamp

This creates a traceable chain from "Agentic-AI-Architect told us to use tool X" to "we chose tool X for shell slot Y on date Z."

---

## 6. Actionable Conclusions and Recommendations

### 6.1 What ExMorbus V3 Needs to Build (Not Agentic-AI-Architect's Job)

The following are ExMorbus's own architectural responsibilities — Agentic-AI-Architect advises on them but does not implement them:

1. **The specialization ladder engine** — the mechanism by which agents at Level 0 produce artifacts that feed agents at Levels 1–2–3
2. **The agent economy protocols** — the typed contracts by which research artifacts are traded between agents, including grading and commoditization schemas
3. **The lobster shell IaC** — the Kubernetes/Terraform/Docker Compose manifests that define the stable shell
4. **The medical knowledge corpus** — the curated ingestion pipelines for PubMed, ClinicalTrials.gov, bioRxiv, etc.

### 6.2 What Agentic-AI-Architect Should Prioritize for ExMorbus

Ranked by impact on ExMorbus V3's development:

1. **MCP server with `search_knowledge` and `get_architecture_recommendation`** — these two tools alone provide 80% of the value to ExMorbus (Phase 5.3 — move up to Phase 2/3 stub)
2. **Trend alerts for medical-adjacent AI categories** — specifically: multi-agent medical research, long-running workflow orchestration, clinical data pipelines, evidence-based AI systems
3. **Tool comparison matrix** — ExMorbus will need to choose between competing options at every shell slot; a queryable comparison endpoint accelerates these decisions
4. **Schema versioning and stability guarantees** — ExMorbus V3 cannot afford to have its architectural advisor change its API mid-project; stability matters more than feature velocity here
5. **Webhook delivery for proactive alerts** — architecture changes in the medical AI space can have compliance and safety implications; proactive alerting is more valuable than reactive querying

### 6.3 The V3 Decision: Reuse, Not Restart

The honest assessment: ExMorbus V2's bones are valuable but the organizing philosophy needs a reframe. Specifically:

| V2 Component | V3 Disposition | Reason |
|---|---|---|
| MCP foundation | **Keep and evolve** | Already built for on-demand tool loading; aligns perfectly with V3 token-efficiency philosophy |
| 23-agent architecture | **Reframe, not rebuild** | Architecture is sound; it just needs to be re-expressed through the specialization ladder lens |
| Phase 1B orchestration adapters | **Keep, with abstraction** | LangGraph and Temporal adapters are valid implementations; wrap them in the lobster shell |
| Context/handoff documentation | **Archive** | Valuable historical record; replace with V3 architecture manifesto as active guide |
| Phase 2 roadmap (Literature Researcher first) | **Resequence** | Start with shell definition and agent contracts; implement Literature Researcher second |

---

## 7. Final Vision: Agentic-AI-Architect's Role in the Medical Research Platform

Agentic-AI-Architect is the **standing brain for AI architecture knowledge** that ExMorbus uses the way a company uses a specialized consultant: not resident, not decision-making, but deeply knowledgeable and always available when needed.

The relationship is:

```
ExMorbus V3 (the researcher)
  ← asks architectural questions →
    Agentic-AI-Architect (the architectural oracle)
      ← continuously learns from →
        The global AI architecture landscape
```

In the medical research context, this means:

- When ExMorbus is deciding how to implement a new agent, it asks the oracle: *"What are the best current patterns for literature-ingestion agents?"*
- When a new orchestration framework emerges that could replace Temporal, the oracle proactively alerts ExMorbus
- When ExMorbus is evaluating its own architecture annually, the oracle can say: *"Your task queue choice from 2026 is now two generations behind — here's the current landscape"*
- When a new medical AI benchmark emerges (e.g., a new standard for clinical evidence grading AI), the oracle surfaces it before the ExMorbus team discovers it manually

The ideal end state is an ExMorbus V3 where **no architectural decision is made without first querying the oracle**, and where the oracle's answers are specific, confident, and grounded in the most current evidence — making ExMorbus's architectural evolution as evidence-based as the medical research it produces.

---

*Document created: March 2026. Update when Phase 5 API contracts are finalized or when ExMorbus V3 integration points are confirmed.*
