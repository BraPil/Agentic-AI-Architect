# Agentic AI Architect System

> **The world's standard for an agentic AI architectural intelligence system** — a self-improving, multi-agent ecosystem that continuously scours the internet, chat boards, repositories, product documentation, SDKs, and tool specifications to build and maintain the most comprehensive knowledge library for AI Architects in existence.

---

## 🧭 Overview

This system is composed of **atomic, specialized agents** that work together to plan, explore, discover, document, learn, train, refine, and repeat — covering every dimension an AI Architect needs to stay at the leading edge. It is designed to:

- Operate as a **standalone intelligence endpoint** that can be queried by external systems
- Integrate into **larger agentic orchestrations** as a knowledge and advisory module
- Continuously **self-update** as the field evolves — from new tools to new paradigms
- Cover the full AI Architect knowledge stack: frameworks, trends, tools, governance, and emerging research

---

## 📁 Repository Structure

```
Agentic-AI-Architect/
├── README.md                        # This file
├── requirements.txt                 # Python dependencies
├── config/
│   └── settings.py                  # System-wide configuration
├── docs/
│   ├── phase-1-education.md         # AI Architect roles & influential figures
│   ├── phase-2-conceptual-frameworks.md  # All frameworks AI Architects must know
│   ├── phase-3-trends.md            # Current trends & best practices
│   ├── phase-4-tools.md             # Fast-moving AI tools landscape
│   └── phase-5-implementation-plan.md   # Phased dev plan with GitHub branches
├── src/
│   ├── contracts/
│   │   ├── __init__.py
│   │   └── answer_contract.py     # Typed external request/response schemas
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py            # Abstract base for all agents
│   │   ├── crawler_agent.py         # Web crawling & data discovery
│   │   ├── research_agent.py        # Deep research & synthesis
│   │   ├── trend_tracker_agent.py   # Trend monitoring & scoring
│   │   ├── tool_discovery_agent.py  # New tool detection & evaluation
│   │   ├── documentation_agent.py   # Knowledge documentation & structuring
│   │   └── orchestrator.py          # Multi-agent orchestration layer
│   ├── knowledge/
│   │   ├── __init__.py
│   │   ├── knowledge_base.py        # Knowledge storage & retrieval (SQLite + JSON)
│   │   └── vector_store.py          # FAISS-based semantic search
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── ingestion.py             # Data ingestion pipeline
│   │   └── processing.py            # Data processing & enrichment
│   └── utils/
│       ├── __init__.py
│       └── helpers.py               # Shared utility functions
└── tests/
    ├── __init__.py
    ├── test_agents.py               # Agent unit tests
    ├── test_knowledge_base.py       # Knowledge base tests
    └── test_pipeline.py             # Pipeline tests
```

---

## 🔄 The Five Phases

The system is organized around five continuous phases that repeat in a virtuous cycle:

| Phase | Name | Purpose |
|-------|------|---------|
| 1 | **Education** | Understand AI Architect roles, responsibilities, and influential figures |
| 2 | **Conceptual Frameworks** | Track all frameworks, paradigms, and methodologies AI Architects use |
| 3 | **Trends** | Monitor what successful practitioners and startups are doing right now |
| 4 | **Tools** | Track the fast-moving tools landscape and detect breakthroughs early |
| 5 | **Implementation** | Translate knowledge into a phased, actionable development plan |

---

## 🤖 Agent Architecture

```
                        ┌─────────────────────┐
                        │   Orchestrator      │
                        │  (Master Agent)     │
                        └──────────┬──────────┘
                                   │
          ┌────────────┬───────────┼───────────┬────────────┐
          │            │           │           │            │
   ┌──────▼──────┐ ┌───▼────┐ ┌───▼────┐ ┌────▼───┐ ┌──────▼──────┐
   │  Crawler    │ │Research│ │ Trend  │ │  Tool  │ │Documentation│
   │  Agent      │ │ Agent  │ │Tracker │ │Discover│ │   Agent     │
   └──────┬──────┘ └───┬────┘ └───┬────┘ └────┬───┘ └──────┬──────┘
          │            │           │           │            │
          └────────────┴───────────┴───────────┴────────────┘
                                   │
                        ┌──────────▼──────────┐
                        │   Knowledge Base     │
                        │  (Vector Store +     │
                        │   Structured Store)  │
                        └─────────────────────┘
```

### Agent Roles

- **Orchestrator**: Coordinates all agents, manages scheduling, handles inter-agent communication, routes queries from external systems
- **Crawler Agent**: Scours websites, GitHub repos, arXiv, Hacker News, Reddit, Discord, documentation sites, and SDK changelogs
- **Research Agent**: Synthesizes raw crawled data into structured knowledge; identifies relationships between concepts
- **Trend Tracker Agent**: Scores and ranks trends by recency, adoption velocity, and credibility signals
- **Tool Discovery Agent**: Monitors tool releases, deprecations, and paradigm shifts; maintains tool comparison matrices
- **Documentation Agent**: Produces structured markdown documents, summaries, and knowledge graph updates

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- (Optional) API keys for enhanced crawling: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `FIRECRAWL_API_KEY`

### Installation

```bash
# Clone the repository
git clone https://github.com/BraPil/Agentic-AI-Architect.git
cd Agentic-AI-Architect

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run the System

```bash
# Run a full intelligence cycle
python -m src.agents.orchestrator --mode full

# Run a specific phase
python -m src.agents.orchestrator --mode trends

# Query the knowledge base
python -m src.knowledge.knowledge_base query "What are the latest agentic AI frameworks?"

# Start the REST API
uvicorn src.api.rest:app --host 0.0.0.0 --port 8080

# Example endpoints
curl "http://localhost:8080/"
curl "http://localhost:8080/frameworks"
curl "http://localhost:8080/frameworks?trajectory=growing%20fast"
curl "http://localhost:8080/evaluation-set"
curl "http://localhost:8080/evaluate/history"
curl "http://localhost:8080/evaluate/performance"
curl "http://localhost:8080/evaluate/query?question_id=stack-current-enterprise&q=LangGraph"
curl "http://localhost:8080/evaluate/query-segments?question_id=stack-current-enterprise&segments=startup&segments=enterprise&q=LangGraph"
curl "http://localhost:8080/evaluate/query-set?question_type=change_watch"
curl "http://localhost:8080/report/frameworks"
curl "http://localhost:8080/query?q=LangGraph&response_mode=both"
```

---

## 📚 Documentation

- [Phase 1: Education — AI Architect Roles & Influential Figures](docs/phase-1-education.md)
- [Phase 2: Conceptual Frameworks — The Complete Knowledge Stack](docs/phase-2-conceptual-frameworks.md)
- [Phase 3: Trends — What's Setting the Stage for Tomorrow](docs/phase-3-trends.md)
- [Phase 4: Tools — The Fast-Moving AI Tools Landscape](docs/phase-4-tools.md)
- [Phase 5: Implementation Plan — Phased Dev Roadmap](docs/phase-5-implementation-plan.md)
- [Instruction Hierarchy](docs/instruction-hierarchy.md)
- [Repository Memory Protocol](docs/repo-memory-protocol.md)
- [Work Index](docs/work-index.md)
- [Decision Log](docs/decision-log.md)
- [Discovery Log](docs/discovery-log.md)
- [Lessons Learned Log](docs/lessons-learned-log.md)
- [Work Log](docs/work-log.md)
- [First Answer Contract v0](docs/first-answer-contract-v0.md)
- [Enterprise Overlay Fields v0](docs/enterprise-overlay-fields-v0.md)
- [Initial Eval Question Set v0](docs/initial-eval-question-set-v0.md)
- [Source Weighting Model v0](docs/source-weighting-model-v0.md)
- [Source Weighting Model v2](docs/source-weighting-model-v2.md)
- [Segment-Aware Evaluation v2](docs/segment-aware-evaluation-v2.md)
- [Research And Training Cycle v1](docs/research-training-cycle-v1.md)

---

## 🔒 Security & Governance

- All crawled data is sanitized and stored locally before processing
- Prompt injection protection on all LLM interactions (see `src/utils/helpers.py`)
- Configurable rate limiting and robots.txt compliance
- No API keys are ever stored in source code — use `.env` file or environment variables

---

## 🤝 Contributing

This system is designed to grow. See [Phase 5](docs/phase-5-implementation-plan.md) for the full roadmap and branch structure. Open issues or PRs against the appropriate phase branch.

---

## 📄 License

MIT
