# Agentic AI Architect

> **The world's standard for an agentic AI architectural intelligence system** — a self-improving, multi-agent ecosystem that continuously ingests, indexes, and synthesizes everything an AI Architect needs to know, then exposes it as a queryable MCP tool for Claude and any MCP-compatible client.

---

## What This Is

AAA is a **persona-organized knowledge base** built from the real output of leading AI practitioners — their LinkedIn posts, YouTube talks, and GitHub projects — enriched with Claude-extracted claims, tool mentions, and architectural patterns, and served through an MCP server that Claude can call directly.

**Current state (April 2026):**
- **204 indexed items**: 79 LinkedIn posts, 60 blog posts, 24 arXiv abstracts, 20 YouTube transcripts, 14 GitHub READMEs, + more
- **52 unique author personas**: Andrej Karpathy, Cole Medin, Mitko Vasilev, Simon Willison, Lilian Weng, + 47 others
- All items enriched with Claude Haiku extraction (claims, tools, topics, voice signals)
- MCP server with 3 tools: `search_knowledge`, `get_architecture_recommendation`, `get_trending_tools`
- **Eval backbone**: 15 ground-truth questions, 15/15 passing (100%), avg relevance 0.465
- Top tool signal: Claude Code (48×), GitHub (24×), Claude (15×), Cursor (9×)
- ChromaDB snapshot committed — corpus persists across machine restarts

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        INGEST LAYER                         │
│                                                             │
│  Chrome Extension     yt-dlp / youtube-transcript-api       │
│  (LinkedIn posts)     (YouTube transcripts)                 │
│         │                      │                           │
│         └──────────┬───────────┘                           │
│                    │          GitHub API                    │
│                    │          (READMEs)                     │
│                    │               │                       │
│         ┌──────────▼───────────────▼──────────┐            │
│         │   Claude Haiku Extraction            │            │
│         │   directClaims · mentionedTools      │            │
│         │   topics · voiceSignals · summary    │            │
│         └──────────────────┬───────────────────┘            │
└────────────────────────────┼────────────────────────────────┘
                             │
               ┌─────────────▼──────────────┐
               │   ChromaDB Persona Store   │
               │   data/linkedin_store/     │
               │   120 items · 50 personas  │
               │   all-MiniLM-L6-v2 embeds  │
               └─────────────┬──────────────┘
                             │
               ┌─────────────▼──────────────┐
               │      MCP Server            │
               │   src/api/mcp_server.py    │
               │                            │
               │  search_knowledge          │
               │  get_architecture_rec      │
               │  get_trending_tools        │
               └─────────────┬──────────────┘
                             │
               ┌─────────────▼──────────────┐
               │   Claude Desktop /         │
               │   any MCP-compatible       │
               │   client                   │
               └────────────────────────────┘
```

---

## Repository Structure

```
Agentic-AI-Architect/
├── src/
│   ├── api/
│   │   ├── mcp_server.py           ← MCP server (Sprint 1) — 3 tools
│   │   └── rest.py                 ← FastAPI REST surface
│   ├── agents/
│   │   ├── base_agent.py           ← Abstract base all agents implement
│   │   ├── crawler_agent.py
│   │   ├── research_agent.py
│   │   ├── trend_tracker_agent.py
│   │   ├── tool_discovery_agent.py
│   │   ├── documentation_agent.py
│   │   └── orchestrator.py
│   ├── contracts/
│   │   └── answer_contract.py      ← Typed request/response schemas
│   ├── knowledge/
│   │   ├── knowledge_base.py       ← SQLite structured store
│   │   └── vector_store.py         ← FAISS semantic search
│   ├── pipeline/
│   │   ├── linkedin_persona_store.py  ← ChromaDB persona store
│   │   ├── youtube_ingest.py          ← YouTube transcript pipeline
│   │   ├── github_ingest.py           ← GitHub README pipeline
│   │   ├── ingestion.py
│   │   └── processing.py
│   └── utils/
│       └── helpers.py
├── scripts/
│   ├── run_mcp_server.sh              ← MCP server launcher
│   ├── ingest_blogs.py                ← Blog RSS/Atom → ChromaDB
│   ├── ingest_arxiv.py                ← arXiv abstracts → ChromaDB
│   ├── process_linkedin_export.py     ← LinkedIn export → ChromaDB
│   ├── extract_transcript_sources.py  ← YouTube transcripts → ChromaDB
│   ├── fetch_youtube_transcripts.py   ← yt-dlp / transcript-api fetcher
│   ├── export_chromadb_snapshot.py    ← Export ChromaDB to JSON snapshot
│   ├── restore_chromadb_snapshot.py   ← Restore ChromaDB from snapshot
│   └── run_eval.py                    ← Evaluation suite runner
├── extensions/
│   └── linkedin-exporter/             ← Chrome MV3 extension (v22)
│       ├── manifest.json
│       ├── content.js                 ← Rolling scrape with final-top pass
│       └── popup.js
├── data/
│   └── linkedin_store/                ← ChromaDB persistent store (gitignored)
│       ├── chroma.sqlite3             ← HNSW index + metadata (6.9 MB)
│       └── <segment-id>/              ← Raw embedding vectors
├── docs/
│   ├── phase-1-education.md
│   ├── phase-2-conceptual-frameworks.md
│   ├── phase-3-trends.md
│   ├── phase-4-tools.md
│   ├── phase-5-implementation-plan.md
│   ├── work-log.md                    ← Completed work history
│   ├── decision-log.md                ← Accepted architectural decisions
│   ├── discovery-log.md               ← Key discoveries affecting future work
│   └── lessons-learned-log.md
├── claude_desktop_config.json         ← Claude Desktop registration snippet
├── config/settings.py
├── requirements.txt
└── tests/
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- `ANTHROPIC_API_KEY` — for Claude Haiku extraction and MCP synthesis (optional but recommended)

### Installation

```bash
git clone https://github.com/BraPil/Agentic-AI-Architect.git
cd Agentic-AI-Architect

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
pip install chromadb sentence-transformers  # persona store dependencies
```

### Connect to Claude Desktop (MCP)

1. Edit `claude_desktop_config.json` — set `cwd` to your local path and add your API key
2. Merge the `mcpServers` block into `~/Library/Application Support/Claude/claude_desktop_config.json`
3. Restart Claude Desktop

You can now ask Claude things like:
- *"What does Karpathy say about LLM OS design?"*
- *"Give me an architecture recommendation for memory in a multi-agent system"*
- *"What AI tools are most discussed right now?"*

### Run the MCP server manually

```bash
# stdio transport (for Claude Desktop / MCP clients)
ANTHROPIC_API_KEY=sk-ant-... ./scripts/run_mcp_server.sh

# or directly
python -m src.api.mcp_server
```

### Ingest new content

```bash
# Blog posts (Simon Willison + Lilian Weng — no cookies needed)
ANTHROPIC_API_KEY=sk-ant-... python3 scripts/ingest_blogs.py

# arXiv paper abstracts (no API key needed for fetch)
ANTHROPIC_API_KEY=sk-ant-... python3 scripts/ingest_arxiv.py

# Process a LinkedIn Chrome extension export
ANTHROPIC_API_KEY=sk-ant-... python3 scripts/process_linkedin_export.py \
  --export docs/linkedin_export_*.json --persona brandtpileggi

# Fetch and index YouTube transcripts
ANTHROPIC_API_KEY=sk-ant-... python3 scripts/fetch_youtube_transcripts.py \
  --cookies scripts/cookies.txt
```

### Persistence

```bash
# Export current ChromaDB to committed JSON snapshot
python3 scripts/export_chromadb_snapshot.py

# Restore after Codespace restart / new machine
python3 scripts/restore_chromadb_snapshot.py
```

### Evaluation

```bash
# Run full eval suite (15 questions)
python3 scripts/run_eval.py

# Single question
python3 scripts/run_eval.py --question eval-001 --verbose
```

### REST API (legacy query surface)

```bash
uvicorn src.api.rest:app --host 0.0.0.0 --port 8080

curl "http://localhost:8080/query?q=LangGraph"
curl "http://localhost:8080/frameworks?trajectory=growing+fast"
curl "http://localhost:8080/evaluate/query?question_id=stack-current-enterprise"
```

---

## MCP Tools

| Tool | Description |
|------|-------------|
| `search_knowledge(query, persona?, n_results?)` | Semantic search across all 120 indexed items. Filter by persona slug (e.g. `andrej-karpathy`). Returns author, snippet, relevance score, mentioned tools, topics. |
| `get_architecture_recommendation(problem_statement, n_sources?)` | Retrieves top-k relevant items then synthesizes a structured recommendation via Claude Haiku. Returns recommendation, key considerations, relevant tools, cited personas, and confidence. Falls back to raw retrieval without an API key. |
| `get_trending_tools(top_n?, persona?, post_type?)` | Ranks tools by mention frequency across all indexed content. Currently: Claude Code (48×), GitHub (24×), Claude (15×), Cursor (9×), PyTorch (8×). |

---

## Ingest Pipelines

### Blogs (RSS/Atom → ChromaDB)
- Fetches Simon Willison and Lilian Weng posts from public RSS/Atom feeds — no auth required
- Stable MD5-based post IDs for reliable dedup across runs
- Auto-updates snapshot after ingest
- Add more blogs in `BLOG_REGISTRY` inside `src/pipeline/blog_ingest.py`

### arXiv (API → ChromaDB)
- Fetches paper abstracts via the arXiv Atom API (no key required)
- 7 curated queries: agentic AI, RAG, memory, evaluation, code gen, CoT, RLHF
- Deduped across queries within a single run

### LinkedIn (Chrome extension → ChromaDB)
1. Install `extensions/linkedin-exporter/` as an unpacked Chrome extension
2. Navigate to your LinkedIn activity/reactions page and click the extension popup
3. Export JSON lands in your downloads
4. Run `scripts/process_linkedin_export.py` with `ANTHROPIC_API_KEY` set

### YouTube (yt-dlp → ChromaDB)
- Two-stage fetcher: `youtube-transcript-api` (fast) → `yt-dlp` fallback (handles cloud IP blocks)
- From Codespace/cloud: requires `--cookies scripts/cookies.txt` (export from a logged-in browser via "Get cookies.txt LOCALLY" extension)
- Auto-calls `extract_transcript_sources.py` after fetch to embed into ChromaDB

### GitHub (API → ChromaDB)
- Fetches README.md for specified repos via GitHub API
- No auth required for public repos; set `GITHUB_TOKEN` to avoid rate limits

---

## Knowledge Store

ChromaDB lives at `data/linkedin_store/` (gitignored — local only). It uses:
- **Embedding model:** `all-MiniLM-L6-v2` (384-dim, runs locally, no API key)
- **Index:** HNSW cosine similarity
- **Collection:** `linkedin_reactions` — all content types in one collection, organized by `persona_id` + `post_type` metadata

Moving machines: copy `data/linkedin_store/` or re-run ingest scripts.

---

## Roadmap

```
Sprint 1 — Make it queryable         ✅ COMPLETE
  MCP server with 3 tools, 120-item corpus, all content enriched

Sprint 2 — Widen the knowledge base  ✅ COMPLETE
  +60 blog posts (Simon Willison, Lilian Weng), +24 arXiv abstracts
  Persistence: ChromaDB snapshot committed to repo

Sprint 3 — Evaluation backbone       ✅ COMPLETE
  15 ground-truth questions, 15/15 passing (100%), avg relevance 0.465
  run_eval.py scoring harness for regression detection

Sprint 4 — Autonomous refresh        ⬜ NEXT
  Scheduled ingest cycles (cron / APScheduler)
  Change detection: alert when new high-signal content appears
  More blog sources (Chip Huyen, Sebastian Ruder, newsletter digests)
  ExMorbus V3 integration (architectural oracle API)
```

Full roadmap: [docs/phase-5-implementation-plan.md](docs/phase-5-implementation-plan.md)
ExMorbus integration spec: [docs/exmorbus-v3-integration.md](docs/exmorbus-v3-integration.md)

---

## Security

- All crawled/external content passes through `sanitize_text()` before any LLM call (`src/utils/helpers.py`)
- API keys via environment variables only — never in source code
- Cookie files (`.txt`) are gitignored — never commit them
- Rate limiting on all external API calls

---

## License

MIT
