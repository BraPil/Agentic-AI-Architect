# ExMorbus V3 ↔ Agentic-AI-Architect Integration Design

> **Purpose**: This document specifies the full integration contract between the
> **Agentic-AI-Architect** system (architectural oracle, this repository) and
> **ExMorbus V3** (medical research platform).  It is the authoritative reference for
> both teams and is designed to be ingested by the agent's knowledge-discovery pipeline.
>
> **Status**: Draft — pending Phase 5 REST API and MCP server implementation.  
> **Last updated**: March 2026  
> **Owner**: Architecture Oracle Integration Lead (see `docs/moltbook-research-findings.md §9`)

---

## Table of Contents

1. [Integration Overview](#1-integration-overview)
2. [System Roles and Boundaries](#2-system-roles-and-boundaries)
3. [MoltBook Synthesis for ExMorbus V3](#3-moltbook-synthesis-for-exmorbus-v3)
4. [API Interface Proposals](#4-api-interface-proposals)
   - 4.1 REST Endpoints (Agentic-AI-Architect → ExMorbus consumer)
   - 4.2 Webhook Schema (Agentic-AI-Architect → ExMorbus push)
   - 4.3 MCP Tool Contracts
5. [ExMorbus V3 ArchitectAgent Specification](#5-exmorbus-v3-architectagent-specification)
6. [System Integration Strategies](#6-system-integration-strategies)
7. [Data Contracts and Schemas](#7-data-contracts-and-schemas)
8. [Security and Compliance Requirements](#8-security-and-compliance-requirements)
9. [Operational Runbook](#9-operational-runbook)
10. [Roadmap Alignment](#10-roadmap-alignment)
11. [Change Log](#11-change-log)

---

## 1. Integration Overview

Agentic-AI-Architect and ExMorbus V3 are **complementary systems** with a clear division of
responsibilities:

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        AGENTIC-AI-ARCHITECT                                │
│                    "The Architectural Oracle"                              │
│                                                                            │
│  Continuously discovers, scores, and documents the AI architecture        │
│  landscape.  Answers questions like:                                       │
│  • "What is the best vector store in production today?"                    │
│  • "Which orchestration frameworks are gaining adoption?"                  │
│  • "Has Playwright been superseded for LLM-compatible crawling?"           │
│                                                                            │
│  Outputs: REST API, MCP server, SSE stream, Webhook alerts                │
└────────────────────────────────┬───────────────────────────────────────────┘
                                 │  queries + alert subscriptions
                                 │
                    ┌────────────▼────────────┐
                    │     ArchitectAgent      │  ← lives in ExMorbus V3 repo
                    │  (integration adapter)  │
                    └────────────┬────────────┘
                                 │  recommendations + alerts
                                 ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                           EXMORBUS V3                                      │
│                   "Medical Research Intelligence Platform"                  │
│                                                                            │
│  Ingests medical research, scores evidence, generates hypotheses, and      │
│  tracks the cancer therapy / vaccination research frontier.                │
│                                                                            │
│  Uses Agentic-AI-Architect to keep its OWN architecture current.          │
└────────────────────────────────────────────────────────────────────────────┘
```

**Key principle**: Agentic-AI-Architect does **not** know about medical research.  ExMorbus
V3 does **not** know how to evaluate software architectures.  The ArchitectAgent is the
translation layer.

---

## 2. System Roles and Boundaries

### 2.1 Agentic-AI-Architect Responsibilities

| Responsibility | In Scope | Out of Scope |
|----------------|----------|--------------|
| Track AI tooling landscape | ✅ | Medical content analysis ❌ |
| Score framework adoption trends | ✅ | Medical research scoring ❌ |
| Recommend architectural patterns | ✅ | Recommend research hypotheses ❌ |
| Expose knowledge as queryable API | ✅ | Store ExMorbus research findings ❌ |
| Alert on significant tool/framework changes | ✅ | Alert on medical breakthroughs ❌ |

### 2.2 ExMorbus V3 Responsibilities

| Responsibility | In Scope | Out of Scope |
|----------------|----------|--------------|
| Ingest medical research literature | ✅ | Track software tooling ❌ |
| Score medical evidence quality | ✅ | Score software adoption trends ❌ |
| Generate research hypotheses | ✅ | Generate architecture recommendations ❌ |
| Consume architecture insights | ✅ | Produce architecture insights ❌ |

### 2.3 ArchitectAgent Responsibilities (ExMorbus side)

The `ArchitectAgent` is an ExMorbus V3 agent that:
1. Periodically queries Agentic-AI-Architect for architecture insights relevant to ExMorbus
2. Evaluates whether those insights warrant a shell-layer change
3. Creates architecture review tickets when a change is recommended
4. Feeds confirmed architectural decisions back to the shell's IaC and contract layer

---

## 3. MoltBook Synthesis for ExMorbus V3

This section translates the MoltBook research findings (see `docs/moltbook-research-findings.md`)
into concrete ExMorbus V3 architecture decisions.

### 3.1 Shell Contract Definition

ExMorbus V3 must define its shell before implementing any flesh:

```
exmorbus-v3/
├── shell/
│   ├── contracts/          ← Python ABCs + Pydantic schemas
│   │   ├── agent.py        ← BaseAgent contract
│   │   ├── llm_client.py   ← LLMClient interface
│   │   ├── vector_store.py ← VectorStore interface
│   │   ├── knowledge_store.py
│   │   └── crawler.py
│   ├── events/             ← typed event registry
│   │   ├── registry.py     ← EventRegistry with transition validation
│   │   └── schemas.py      ← Pydantic event schemas
│   ├── curriculum/         ← staged domain specialisation config
│   │   ├── stages.yaml
│   │   └── namespaces.yaml
│   ├── iac/                ← infrastructure definitions
│   │   ├── k8s/
│   │   └── terraform/
│   └── policies/           ← OPA governance
│       └── base.rego
└── flesh/
    └── adapters/           ← technology-specific implementations
```

### 3.2 Curriculum Namespace Configuration

The staged specialisation ladder is encoded as namespace permissions:

```yaml
# shell/curriculum/stages.yaml (ExMorbus V3 — proposed)
stages:
  - id: broad_health
    label: "Broad Health Knowledge"
    training_fraction: 0.10
    namespaces_writable:
      - health/nutrition
      - health/exercise
      - health/psychology
      - health/anatomy
      - health/biology
      - health/chemistry
    advancement_criteria:
      min_entries_per_namespace: 500
      min_coverage_score: 0.75

  - id: clinical_medicine
    label: "Clinical Medicine"
    training_fraction: 0.20
    namespaces_writable:
      - medicine/clinical
      - medicine/pharmacology
      - medicine/diagnostics
    advancement_criteria:
      min_entries_per_namespace: 1000
      min_evidence_grade_rct_fraction: 0.15

  - id: oncology
    label: "Oncology"
    training_fraction: 0.30
    namespaces_writable:
      - oncology/solid_tumors
      - oncology/hematologic
      - oncology/pediatric
    advancement_criteria:
      min_entries_per_namespace: 2000
      min_clinical_trial_coverage: 0.20

  - id: cancer_immunotherapy
    label: "Cancer Immunotherapy and Novel Therapeutics"
    training_fraction: 0.40
    namespaces_writable:
      - immunotherapy/checkpoint_inhibitors
      - immunotherapy/car_t
      - immunotherapy/cancer_vaccines
      - immunotherapy/novel_experimental
    advancement_criteria: null  # terminal stage — no advancement
```

### 3.3 On-Demand Tool Loading Protocol

ExMorbus V3 should implement the load-use-unload pattern for all heavy tools:

```python
# Proposed: exmorbus-v3/shell/contracts/tool_lifecycle.py

from abc import ABC, abstractmethod
from typing import Any

class HeavyTool(ABC):
    """Shell contract for tools that are expensive to keep resident."""

    @abstractmethod
    async def load(self) -> None:
        """Instantiate the tool and acquire all resources.

        Raises:
            RuntimeError: If the tool cannot be instantiated (e.g. missing
                binary, OOM, port conflict).  The caller must not call
                ``execute()`` if ``load()`` raises.
        """

    @abstractmethod
    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        """Execute one task. Must be called between load() and unload()."""

    @abstractmethod
    async def unload(self) -> None:
        """Release all resources. Called even if execute() raised."""

    async def __aenter__(self) -> "HeavyTool":
        await self.load()
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.unload()
```

### 3.4 ArchitectAgent Design Pattern

```python
# Proposed: exmorbus-v3/src/agents/architect_agent.py (sketch)

class ArchitectAgent(BaseAgent):
    """
    Queries Agentic-AI-Architect for architectural recommendations relevant to
    ExMorbus V3 and evaluates whether they warrant a shell-layer change.

    Configuration keys:
        aaa_base_url (str): Base URL of the Agentic-AI-Architect REST API.
        aaa_api_key (str): API key for Agentic-AI-Architect (from env).
        review_interval_days (int): How often to run a full review. Default: 7.
        confidence_threshold (float): Minimum confidence to auto-flag a review
            ticket.  Default: 0.75.
    """
```

---

## 4. API Interface Proposals

### 4.1 REST Endpoints (Agentic-AI-Architect serves, ExMorbus consumes)

These endpoints will be implemented in **Phase 5** of Agentic-AI-Architect.  The contracts
are defined here so ExMorbus V3 can design its ArchitectAgent against a stable interface.

#### `GET /query`

Semantic search across the full knowledge base.

**Request**:
```
GET /query?q={query_text}&namespace={namespace}&top_k={n}&min_confidence={float}
```

**Response** (`200 OK`):
```json
{
  "query": "vector store production 2026",
  "results": [
    {
      "id": "kb-entry-uuid",
      "namespace": "tools",
      "title": "pgvector vs Qdrant vs Pinecone — 2026 comparison",
      "summary": "...",
      "confidence": 0.88,
      "source_url": "https://...",
      "extracted_at": "2026-03-01T12:00:00Z",
      "trend_score": 74.2
    }
  ],
  "total": 12,
  "query_time_ms": 143
}
```

#### `GET /trends`

Current trend scores and rankings, optionally filtered by domain.

**Request**:
```
GET /trends?domain={domain_hint}&limit={n}&min_score={float}&since={ISO8601}
```

**Response** (`200 OK`):
```json
{
  "generated_at": "2026-03-14T00:00:00Z",
  "trends": [
    {
      "topic": "Model Context Protocol (MCP)",
      "score": 91.4,
      "velocity": 12.3,
      "status": "emerging",
      "first_seen": "2025-11-01",
      "recent_sources": ["https://..."],
      "summary": "..."
    }
  ]
}
```

#### `GET /tools`

Tool registry with filter support.

**Request**:
```
GET /tools?category={category}&since={ISO8601}&status={active|deprecated|emerging}
```

**Response** (`200 OK`):
```json
{
  "tools": [
    {
      "name": "Playwright",
      "category": "crawler",
      "status": "active",
      "stars": 68000,
      "last_commit": "2026-03-10",
      "summary": "...",
      "alternatives": ["Firecrawl", "Puppeteer"],
      "deprecation_risk": "low"
    }
  ]
}
```

#### `GET /frameworks`

Framework maturity matrix.

**Request**:
```
GET /frameworks?maturity={emerging|growing|stable|declining}&type={orchestration|rag|vector|llm}
```

#### `POST /ingest`

Submit a URL or text for priority processing.

**Request body**:
```json
{
  "url": "https://arxiv.org/abs/...",
  "priority": "high",
  "namespace": "tools",
  "requester": "exmorbus-v3-architect-agent"
}
```

**Response** (`202 Accepted`):
```json
{
  "job_id": "ingest-uuid",
  "status": "queued",
  "estimated_completion_seconds": 45
}
```

#### `GET /report/{phase}`

Get the latest auto-generated phase report.

**Response** (`200 OK`): Markdown document as `text/markdown`.

### 4.2 Webhook Schema (Agentic-AI-Architect → ExMorbus push)

Agentic-AI-Architect will push events to ExMorbus V3 via webhooks registered through a
subscription API.

#### Webhook Registration

```
POST /webhooks/subscribe
{
  "target_url": "https://exmorbus.example.com/hooks/aaa",
  "events": ["tool_alert", "trend_alert", "arch_recommendation"],
  "secret": "webhook-hmac-secret",
  "filters": {
    "tool_categories": ["crawler", "vector_store", "orchestration", "llm"],
    "min_trend_score": 80.0
  }
}
```

#### Tool Alert Webhook

Fired when a tracked tool's status changes (new major version, deprecation signal, or
replacement detected).

```json
{
  "event": "tool_alert",
  "timestamp": "2026-03-14T19:46:10Z",
  "payload": {
    "tool_name": "Scrapy",
    "alert_type": "replacement_detected",
    "severity": "medium",
    "message": "Firecrawl adoption surpassed Scrapy in AI-adjacent projects (2026 Q1)",
    "replacement_candidate": "Firecrawl",
    "confidence": 0.82,
    "sources": ["https://...", "https://..."],
    "recommendation": "Evaluate Firecrawl as primary crawler for LLM-optimized extraction"
  },
  "signature": "sha256=..."
}
```

#### Trend Alert Webhook

Fired when a trend crosses the configured score threshold or changes velocity significantly.

```json
{
  "event": "trend_alert",
  "timestamp": "2026-03-14T19:46:10Z",
  "payload": {
    "topic": "Mixture-of-Experts routing for agent specialisation",
    "alert_type": "threshold_crossed",
    "score": 83.7,
    "previous_score": 61.2,
    "velocity": "+22.5 in 30 days",
    "relevance_to_medical_ai": "high",
    "summary": "...",
    "sources": ["https://..."]
  },
  "signature": "sha256=..."
}
```

#### Architecture Recommendation Webhook

Fired when Agentic-AI-Architect's trend analysis produces a pattern-level recommendation.

```json
{
  "event": "arch_recommendation",
  "timestamp": "2026-03-14T19:46:10Z",
  "payload": {
    "recommendation_id": "rec-uuid",
    "category": "orchestration",
    "title": "Migrate task queue from APScheduler to Temporal for long-horizon medical research workflows",
    "confidence": 0.79,
    "impact": "high",
    "effort": "medium",
    "rationale": "...",
    "evidence": ["https://...", "https://..."],
    "affects_shell_layer": true,
    "suggested_action": "Schedule shell review within 30 days"
  },
  "signature": "sha256=..."
}
```

### 4.3 MCP Tool Contracts

Agentic-AI-Architect exposes its knowledge base as an MCP server (Phase 5).

#### MCP Tools

| Tool Name | Description | Required Parameters |
|-----------|-------------|---------------------|
| `search_knowledge` | Semantic search across knowledge base | `query: str`, `namespace?: str`, `top_k?: int` |
| `get_trend_score` | Get current score for a named topic | `topic: str` |
| `get_tool_info` | Get details for a named tool | `tool_name: str` |
| `get_latest_report` | Get latest auto-generated phase report | `phase: int` |
| `list_trending_tools` | List tools with rising adoption | `category?: str`, `limit?: int` |

#### MCP Resources

| Resource URI | Description |
|-------------|-------------|
| `knowledge://trends/current` | Latest trend scores (JSON) |
| `knowledge://tools/database` | Full tool registry (JSON) |
| `knowledge://frameworks/matrix` | Framework maturity matrix (Markdown) |
| `knowledge://reports/phase-{n}` | Phase report documents (Markdown) |

#### Example MCP Tool Call (ExMorbus ArchitectAgent)

```python
# In ExMorbus V3 ArchitectAgent._execute():
result = await mcp_client.call_tool(
    server="agentic-ai-architect",
    tool="search_knowledge",
    arguments={
        "query": "vector store for medical research 2026",
        "namespace": "tools",
        "top_k": 5
    }
)
```

---

## 5. ExMorbus V3 ArchitectAgent Specification

### 5.1 Agent Purpose

The `ArchitectAgent` in ExMorbus V3 is the **sole point of contact** with Agentic-AI-Architect.
It runs on a configured schedule (default: weekly) and:

1. Queries Agentic-AI-Architect for relevant architecture updates
2. Correlates results with ExMorbus V3's current shell layer
3. Assigns a **shell impact score** to each finding
4. If impact score ≥ threshold: creates a shell review record
5. Publishes a weekly architecture briefing to the ExMorbus knowledge base

### 5.2 Query Strategy

The ArchitectAgent should maintain a **standing query set** aligned to ExMorbus V3's
shell components:

```python
STANDING_QUERIES = [
    # Vector store tracking
    {"q": "vector store medical research 2026", "namespace": "tools", "category": "vector_store"},
    # LLM routing for specialised medical tasks
    {"q": "LLM medical domain specialisation", "namespace": "tools", "category": "llm"},
    # Orchestration for long-horizon research workflows
    {"q": "agent orchestration long horizon task", "namespace": "frameworks", "category": "orchestration"},
    # Crawler for medical literature (PubMed, arXiv, bioRxiv)
    {"q": "scientific literature crawler LLM optimised", "namespace": "tools", "category": "crawler"},
    # On-demand tool loading patterns
    {"q": "on demand tool loading agentic systems", "namespace": "frameworks", "category": "patterns"},
]
```

### 5.3 Shell Impact Scoring

The ArchitectAgent uses a simple impact matrix to avoid alert fatigue:

| Factor | Weight | Notes |
|--------|--------|-------|
| Affects a shell contract (interface or schema) | 0.4 | Any change to ABCs or Pydantic schemas |
| Confidence ≥ 0.80 | 0.2 | High-confidence recommendation |
| Trend velocity > +15 in 30 days | 0.2 | Fast-moving change signal |
| Replacement candidate for currently-used tool | 0.2 | Direct substitution available |

**Score ≥ 0.6**: Create shell review record (but do not block current cycle).  
**Score ≥ 0.85**: Create shell review record AND notify Architecture Oracle Integration Lead.

### 5.4 Architecture Briefing Format

The weekly briefing should be stored as a knowledge base entry with:
- `namespace`: `general`
- `title`: `Architecture Briefing — Week of {date}`
- Content sections:
  1. **Trend Movements**: Topics that rose or fell ≥ 10 points
  2. **Tool Alerts**: Any tool deprecation or replacement signals
  3. **Recommendations**: Architecture recommendations scored ≥ 0.6
  4. **Shell Stability**: Assessment of whether any shell contracts need review

---

## 6. System Integration Strategies

### Strategy 1: Polling with Local Cache (Phase 1 — before AAA REST API is live)

**Use when**: Agentic-AI-Architect Phase 5 REST API is not yet deployed.

The ArchitectAgent reads directly from the Agentic-AI-Architect **SQLite knowledge base**
if ExMorbus V3 and Agentic-AI-Architect are on the same host:

```python
# Temporary integration: read-only SQLite access
# ⚠️ CONCURRENT ACCESS WARNING: ensure AAA is not mid-write when this runs.
# Use a scheduled window when AAA's intelligence cycle is idle (e.g. between cycles).
# SQLite's WAL mode (PRAGMA journal_mode=WAL) on the AAA side reduces but does not
# eliminate the risk of a reader seeing a partial transaction.
import sqlite3
conn = sqlite3.connect(
    "/path/to/aaa/data/knowledge.db",
    timeout=30,  # wait up to 30s for a lock
    check_same_thread=False,
)
conn.execute("PRAGMA query_only = ON")  # enforce read-only at connection level
# Query namespaces = 'tools' | 'frameworks' | 'trends'
```

**Limitations**: Read-only; no real-time alerts; requires co-location; concurrent-write risk.  
**Transition**: Replace with REST API when Phase 5 is deployed.

### Strategy 2: REST API + Scheduled Polling (Phase 5 — primary strategy)

**Use when**: Agentic-AI-Architect Phase 5 REST API is deployed.

```
ExMorbus ArchitectAgent (weekly schedule)
    ↓ GET /trends + GET /tools + GET /query (standing queries)
Agentic-AI-Architect REST API
    ↓ structured JSON responses
ExMorbus ArchitectAgent processes → shell review records
```

### Strategy 3: MCP Server Integration (Phase 5 — for Claude Desktop / agent-native use)

**Use when**: An AI agent (Claude, GPT-4, etc.) is directly helping an ExMorbus V3
developer and needs live architecture data.

```
Developer assistant (Claude Desktop + MCP)
    ↓ tool call: search_knowledge("vector store options 2026")
Agentic-AI-Architect MCP server
    ↓ structured response
Developer assistant incorporates into recommendation
```

### Strategy 4: Webhook Push + Event Bus (Phase 5+ — for real-time alerts)

**Use when**: High-value, time-sensitive alerts (tool deprecation, major framework shift)
need to reach the ExMorbus shell review queue immediately rather than waiting for the next
polling cycle.

```
Agentic-AI-Architect TrendTrackerAgent detects major shift
    ↓ emits TrendAlert event
Agentic-AI-Architect webhook dispatcher
    ↓ POST /exmorbus/hooks/aaa (HMAC-signed)
ExMorbus V3 webhook handler
    ↓ creates shell review record with priority = "urgent"
ExMorbus ArchitectAgent processes at next available cycle
```

---

## 7. Data Contracts and Schemas

### 7.1 Shared Knowledge Entry Schema

Both systems should use compatible knowledge entry formats to allow future shared indexing:

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class KnowledgeEntry:
    """Shared schema for knowledge entries across both systems."""
    id: str                         # UUID
    namespace: str                  # e.g. "tools", "frameworks", "trends"
    title: str
    summary: str
    source_url: str | None
    confidence: float               # 0.0 – 1.0
    extracted_at: datetime
    tags: list[str] = field(default_factory=list)
    trend_score: float | None = None
    provenance: dict | None = None  # ExMorbus extension: evidence-grade metadata
    domain_stage: str | None = None # ExMorbus extension: curriculum stage

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "namespace": self.namespace,
            "title": self.title,
            "summary": self.summary,
            "source_url": self.source_url,
            "confidence": self.confidence,
            "extracted_at": self.extracted_at.isoformat(),
            "tags": self.tags,
            "trend_score": self.trend_score,
            "provenance": self.provenance,
            "domain_stage": self.domain_stage,
        }
```

### 7.2 Webhook HMAC Verification

All webhooks from Agentic-AI-Architect include an HMAC-SHA256 signature:

```python
import hashlib
import hmac

def verify_webhook(payload_bytes: bytes, signature_header: str, secret: str) -> bool:
    """Return True if signature_header matches the HMAC-SHA256 of payload_bytes.

    Validates that the header is well-formed (starts with "sha256=") before
    comparing, avoiding a timing attack on an unexpected header format.
    """
    if not isinstance(signature_header, str) or not signature_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(
        secret.encode(), payload_bytes, hashlib.sha256
    ).hexdigest()
    # compare_digest is constant-time — safe against timing side-channels
    return hmac.compare_digest(expected, signature_header)
```

---

## 8. Security and Compliance Requirements

### 8.1 General

| Requirement | Mechanism |
|-------------|-----------|
| API authentication | Bearer token (JWT or API key) in `Authorization` header |
| Webhook integrity | HMAC-SHA256 signature verification |
| Secrets management | Environment variables only; never in source code |
| Rate limiting | Both systems implement rate limiting on outbound calls |
| Input sanitisation | All content from Agentic-AI-Architect is sanitised before use in ExMorbus LLM prompts |

### 8.2 ExMorbus V3 Medical-Specific Requirements

| Requirement | Notes |
|-------------|-------|
| No patient data in Agentic-AI-Architect | AAA receives only architectural queries, never medical data |
| Architecture recommendations are not medical advice | Clear labelling required in ExMorbus UI |
| Audit log for all ArchitectAgent queries | Required for research reproducibility |
| Architecture changes require human review before shell deployment | ArchitectAgent creates records; humans approve deployments |

---

## 9. Operational Runbook

### 9.1 ArchitectAgent Health Check

```bash
# From ExMorbus V3 repo:
python -c "from src.agents.architect_agent import ArchitectAgent; a = ArchitectAgent(); a.initialize(); print(a.health_check())"
```

Expected output: `{'status': 'healthy', 'aaa_reachable': True, 'last_review': '...'}`

### 9.2 Manual Architecture Review Trigger

```bash
# Trigger an immediate ArchitectAgent review cycle:
python -m src.agents.architect_agent --run-now
```

### 9.3 Webhook Test

```bash
# Send a test webhook to ExMorbus from Agentic-AI-Architect:
curl -X POST https://aaa.example.com/webhooks/test \
  -H "Authorization: Bearer $AAA_API_KEY" \
  -d '{"target_url": "https://exmorbus.example.com/hooks/aaa", "event": "tool_alert"}'
```

### 9.4 Troubleshooting

| Symptom | Likely Cause | Resolution |
|---------|-------------|------------|
| ArchitectAgent returns no results | AAA REST API not deployed yet | Switch to Strategy 1 (SQLite direct read) |
| Webhook HMAC verification failing | Secret mismatch | Re-sync `AAA_WEBHOOK_SECRET` env var |
| Standing queries returning stale data | AAA knowledge base not yet populated | Trigger ingestion with `POST /ingest` for seed URLs |
| Too many shell review records | Impact score threshold too low | Increase `confidence_threshold` config |

---

## 10. Roadmap Alignment

| Agentic-AI-Architect Phase | ExMorbus V3 Milestone | Integration Available |
|---------------------------|----------------------|----------------------|
| P0 Foundation ✅ | Can read AAA docs manually | Manual research only |
| P1 Knowledge Discovery 🔄 | AAA docs improving; SQLite readable | Strategy 1 (SQLite direct) |
| P2 Intelligence Layer | Rich trend scores available | Strategy 1 + local query script |
| P3 Agent Specialisation | Tool discovery agent operational | Better tool alerts |
| P4 Orchestration | Full intelligence cycle running | Strategy 1 at scale |
| **P5 API & Integration** | **REST API + MCP + Webhooks live** | **Strategies 2, 3, 4 all active** |
| P6 Self-Improvement | AAA improves its own recommendations | Higher confidence scores |
| P7 Production Hardening | AAA is a reliable production dependency | Full production integration |

**Current recommended action**: ExMorbus V3 should design and stub its `ArchitectAgent`
now (using Strategy 1 for local dev) so the integration is ready when AAA Phase 5 ships.

---

## 11. Change Log

| Date | Author | Change |
|------|--------|--------|
| 2026-03 | Agentic-AI-Architect research cycle | Initial document — synthesised from ExMorbus/MoltBook conversation context |

---

*This document is part of the Agentic-AI-Architect knowledge base.*  
*Namespace*: `general` (cross-project architecture)  
*Related*: `docs/moltbook-research-findings.md`, `docs/phase-5-implementation-plan.md`