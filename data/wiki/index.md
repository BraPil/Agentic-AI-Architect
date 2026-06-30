# AAA Wiki Index

> Content catalog for the Agentic AI Architect knowledge wiki.  
> Three layers: raw/ (source artifacts) → pages/ (curated synthesis) → schema/ (typed extracts).  
> Operations: Ingest, Query, Lint.  
> **Last rebuilt**: 2026-06-30 (corpus 415 after curation-guard prune of 2 off-standard posts)
> **Total items**: 415 indexed (committed snapshot `schema/chromadb_snapshot.json`)
> **Phases referenced**: P0–P5 completed; P6 (organic learning loop) in progress; P7 planned
> **Tracking discipline**: see [pattern_llm_wiki](pages/pattern_llm_wiki.md) — `index.md` = where we are, `log.md` = what we did

---

## Corpus Overview

Counts are by `post_type` from the live store (the ground truth), not by ingest batch.

| Source (post_type) | Count | Tier | Dates |
|--------------------|-------|------|-------|
| LinkedIn persona posts (`image` 129, `text` 16, `video` 12, `article` 6) | 163 | external | 2024-11–2026-06 |
| Blog posts — Willison, Weng, Yan, Ruder, Huyen (`blog_post`) | 117 | external | 2019-03–2026-04 |
| Project learnings — AAA decision/discovery/lesson logs (`project_learning`) | 72 | internal | 2026-04–2026-06 |
| arXiv abstracts (`arxiv_abstract`) | 27 | external | 2026-04–2026-06 |
| YouTube transcripts (`youtube_transcript`) | 20 | external | 2024-06–2026-03 |
| GitHub READMEs (`github_readme`) | 14 | external | 2022-01–2026-04 |
| Promoted learning artifacts (`learning_artifact`) | 2 | grounded | 2026-06 |
| **Total** | **415** | **active** | **2019-03–2026-06** |

Tier split (by `source_tier`): 341 external (untagged), 72 internal, 2 grounded.
Embedding model: `all-MiniLM-L6-v2` (384-dim, local, no API key required).  
Vector store: ChromaDB at `data/linkedin_store/`. Curation guard active (`data/curation_denylist.json`, 9 barred).

---

## Personas (105 Indexed)

> `aaa_project` (72 items) is AAA's own institutional memory (the `project_learning` internal
> tier), not an external thought leader — it is the largest "persona" by count but is excluded
> from trend/community aggregation. The external persona long tail is now ~95 (many seed-tier).

### Tier 1 — Core Founders (2)

| Page | Name | Items | Status | Phase Refs |
|------|------|-------|--------|-----------|
| [persona_andrej_karpathy](pages/persona_andrej_karpathy.md) | Andrej Karpathy | 14 | reviewed | P2.4, P6.1, P6.4 |
| [persona_cole_medin](pages/persona_cole_medin.md) | Cole Medin | 18 | reviewed | P4, P6, P3.3 |

### Tier 2 — Content & ML (12)

| Page | Name | Items | Status |
|------|------|-------|--------|
| [persona_chip_huyen](pages/persona_chip_huyen.md) | Chip Huyen | 10 | reviewed |
| [persona_simon_willison](pages/persona_simon_willison.md) | Simon Willison | 32 | reviewed |
| [persona_lilian_weng](pages/persona_lilian_weng.md) | Lilian Weng | 30 | reviewed |
| [persona_eugene_yan](pages/persona_eugene_yan.md) | Eugene Yan | 30 | reviewed |
| [persona_sebastian_ruder](pages/persona_sebastian_ruder.md) | Sebastian Ruder | 15 | reviewed |
| [persona_arxiv_research](pages/persona_arxiv_research.md) | arXiv Research Community | 27 | reviewed |
| [persona_mitko_vasilev](pages/persona_mitko_vasilev.md) | Mitko Vasilev | 17 | draft |
| [persona_paolo_perrone](pages/persona_paolo_perrone.md) | Paolo Perrone | 8 | draft |
| [persona_brandt_pileggi](pages/persona_brandt_pileggi.md) | Brandt Pileggi (self) | reactor | reviewed |
| Paolo Perrone, Stanislav Beliaev, Alex Wang, GenAI Works, Aishwarya N. Reganti… | Various | 5–11 each | draft/seed |
| ~95 other indexed personas (long tail) | Various | 1–4 each | seed |

### Coverage by Domain

- **LLM Systems**: Karpathy, Weng, Willison, Huyen (94 items)
- **AI Engineering**: Yan, Ruder, Vasilev (62 items)
- **ML Research**: arXiv research community (24 items)
- **Agents & Orchestration**: Cole (dark-factory, Archon, adversarial-dev), Pileggi (18 items)
- **Tools & Infrastructure**: GitHub repos, secondary sources (37 items)

---

## Architectural Patterns & Concepts

| Page | Category | Description | Status |
|------|----------|-------------|--------|
| [pattern_llm_wiki](pages/pattern_llm_wiki.md) | Pattern | Karpathy's LLM Wiki — full authoritative synthesis + AAA tracking discipline (index/log) | reviewed |
| [pattern_dark_factory](pages/pattern_dark_factory.md) | Pattern | Cole Medin's dark-factory experiment framework | reviewed |
| [pattern_autoresearch_loop](pages/pattern_autoresearch_loop.md) | Pattern | Andrej Karpathy's autonomous research orchestration | draft |
| [pattern_archon_harness](pages/pattern_archon_harness.md) | Pattern | Cole Medin's Archon multi-agent orchestration | draft |
| [pattern_claude_md_ecosystem](pages/pattern_claude_md_ecosystem.md) | Pattern | AI Engineering OS — CLAUDE.md template with Architectural Constitution, companion docs, and initialization survey | reviewed |
| [concept_orchestration](pages/concept_orchestration.md) | Concept | How agents coordinate work and share state | draft |
| [concept_prompt_injection](pages/concept_prompt_injection.md) | Concept | Prompt injection defense and sanitization | draft |
| [concept_evaluation](pages/concept_evaluation.md) | Concept | LLM eval frameworks and ground-truth scoring | reviewed |
| [concept_source_weighting](pages/concept_source_weighting.md) | Concept | Source credibility and learned weighting models | draft |

---

## Tools Landscape

| Name | Mentions | Status | Pages |
|------|----------|--------|-------|
| LangChain | 18 | indexed | tool_langchain |
| Anthropic Claude | 45+ | indexed | tool_claude |
| OpenAI GPT | 12 | indexed | tool_gpt |
| Vercel AI SDK | 6 | indexed | tool_vercel_ai |
| Pinecone | 8 | indexed | tool_pinecone |
| FAISS | 7 | indexed | tool_faiss |
| ChromaDB | 5 | indexed | tool_chromadb |
| MCP (Model Context Protocol) | 8+ | indexed | tool_mcp |
| GitHub Copilot | 6 | indexed | tool_copilot |
| Agentic Frameworks (DSPy, AutoGen, CrewAI, LlamaIndex) | 12 | indexed | pattern_agent_frameworks |

---

## Frameworks & Methodologies

| Name | Category | Mentions | Status |
|------|----------|----------|--------|
| RAG (Retrieval-Augmented Generation) | Architecture | 22 | indexed |
| ReAct (Reasoning + Acting) | Architecture | 14 | indexed |
| Chain of Thought | Prompting | 18 | indexed |
| Multi-Agent Orchestration | Architecture | 12 | indexed |
| In-Context Learning | Training | 16 | indexed |
| Prompt Engineering | Technique | 24 | indexed |
| Evaluation & Benchmarking | Operations | 19 | indexed |

---

## Trending Topics (Q2 2026)

| Topic | Trend | Mentions | Latest |
|-------|-------|----------|--------|
| Multimodal models (GPT-4o, Gemini 3) | Rising | 14 | 2026-04-10 |
| Long-context LLMs (100K+ tokens) | Stable | 8 | 2026-03-15 |
| Agent orchestration | Rising | 18 | 2026-06-20 |
| Reward modeling | Emerging | 5 | 2026-05-01 |
| MCP & tool use | Emerging | 8 | 2026-05-04 |
| Agentic AI systems | Rising | 22 | 2026-06-28 |

---

## Repositories Analyzed (14)

### Karpathy (4 repos)

- nanoGPT (13.8K chars) → [repo_nanogpt](pages/repo_nanogpt.md)
- micrograd (2.4K chars) → [repo_micrograd](pages/repo_micrograd.md)
- makemore (3.0K chars) → [repo_makemore](pages/repo_makemore.md)
- autoresearch (8.0K chars) → [repo_autoresearch](pages/repo_autoresearch.md)

### Cole Medin (4 repos)

- Archon (13.8K chars) → [repo_archon](pages/repo_archon.md)
- dark-factory-experiment (10.5K chars) → [repo_dark_factory](pages/repo_dark_factory.md)
- adversarial-dev (10.4K chars) → [repo_adversarial_dev](pages/repo_adversarial_dev.md)
- second-brain-starter (5.9K chars) → [repo_second_brain_starter](pages/repo_second_brain_starter.md)

### Other (6 repos from secondary sources)

- Various AI infrastructure, coding, ML systems (catalogued in raw/)

---

## Schema Extracts

| File | Entities | Last Updated | Status |
|------|----------|--------------|--------|
| [schema/personas.json](schema/personas.json) | 56 profiles | 2026-06-28 | current |
| [schema/patterns.json](schema/patterns.json) | 8 patterns | 2026-06-20 | current |
| [schema/tools.json](schema/tools.json) | 40+ tools | 2026-06-15 | current |
| [schema/frameworks.json](schema/frameworks.json) | 12 frameworks | 2026-06-10 | current |
| [schema/trends.json](schema/trends.json) | 15 trends | 2026-06-28 | current |
| [schema/research_sources.json](schema/research_sources.json) | 24 papers | 2026-06-15 | current |

---

## Lint & Maintenance Status

| Check | Result | Date | Notes |
|-------|--------|------|-------|
| Orphan detection | 0 orphans | 2026-06-28 | Clean |
| Contradiction check | 0 contradictions | 2026-06-28 | All sources aligned |
| Stale content (>90 days) | 3 entries | 2026-06-28 | Marked for refresh |
| Dead links | 0 broken | 2026-06-28 | All links valid |
| Untagged pages | 0 | 2026-06-28 | All pages tagged |

---

## Raw Sources Organization

```
data/wiki/raw/
├── andrej_karpathy/          (4 READMEs, ~27K chars)
├── cole_medin/               (4 READMEs, ~40K chars)
├── chip_huyen/               (10 blog posts, ~85K chars)
├── simon_willison/           (31 blog posts, ~220K chars)
├── lilian_weng/              (30 blog posts, ~412K chars)
├── eugene_yan/               (30 blog posts, ~210K chars)
├── sebastian_ruder/          (15 blog posts, ~180K chars)
├── arxiv-research/           (24 paper abstracts, ~48K chars)
├── mitko_vasilev/            (6 READMEs, ~35K chars)
├── brandtpileggi/            (79 LinkedIn posts, ~156K chars)
└── [39 other personas]/      (misc content, ~180K chars)
```

---

## Wiki Documentation

| File | Purpose | Status |
|------|---------|--------|
| [SCHEMA.md](SCHEMA.md) | Three-layer structure, conventions, workflows | current |
| [RUNBOOKS.md](RUNBOOKS.md) | Operations guides, troubleshooting, scaling | current |
| [index.md](index.md) | This file — content catalog | current |
| [log.md](log.md) | Append-only ingest/query/lint log | current |

---

## Recent Updates (June 2026)

**Last 30 Days**:

- ✅ P6 organic learning loop (OAA bridge) slices 0–3 built and proven (answer relevance lifts measured)
- ✅ P6 outcome capture slices 1–2 — record adopted+worked; signal re-ranks live retrieval (gated, inert until data)
- ✅ Persona curation guard — non-practitioner personas barred at ingest (denylist enforced at `store.ingest()`); caught 2 that were still indexed → store **417 → 415**
- ✅ Full blog corpus re-ingested (115 posts); store reconciled to 417, then 415 after curation prune
- ✅ Fixed CI corpus-regression bug: `refresh_corpus.py` now restores the snapshot **before** ingest (+4 tests)
- ✅ Re-synthesized Karpathy LLM-Wiki philosophy; codified the index.md/log.md tracking discipline
- ✅ LinkedIn exporter v1.1 (absolute timestamps + batch mode)

**Next Actions**:

- [ ] **Retrieval ranking/density** — hybrid lexical+vector (RRF), then optional reranker; eval-gated (next lever per discovery-log) ← in progress
- [ ] P6 slice 3 — segment-aware outcome multipliers, recency decay, surface per-entity track record (deferred until real outcome data accrues)
- [ ] Ingest ExMorbus integration docs and design contracts
- [ ] Regenerate schema extracts (`build_wiki_schema.py`) — `personas.json` still says 56, store now has 105

---

## How to Update This Index

1. **Add new entries** when pages are created in `pages/`
2. **Update status** as pages progress: `seed` → `draft` → `reviewed` → `stale`
3. **Add raw sources** when new content ingested into `raw/`
4. **Run lint** after bulk ingest: `python3 scripts/lint_wiki.py`
5. **Rebuild schema** after changes: `python3 scripts/build_wiki_schema.py`
6. **Update timestamp** and refresh this index: `data/wiki/index.md`
7. **Commit** with message: `chore(wiki): index rebuild; [summary of changes]`

---

## Integration with AAA System

This wiki serves as the knowledge reference layer for:

- **MCP Tools**: `search_knowledge`, `ask_persona`, `compare_personas`, `get_consensus`
- **REST API v1**: `/v1/search`, `/v1/recommend`, `/v1/trending-tools`, `/v1/personas`
- **Evaluation Backbone**: Ground-truth questions and persona/framework/tool references
- **Source Weighting**: Credibility and learned multipliers for each persona/source
- **Trend Detection**: Monitor topic emergence, tool adoption, framework maturity
- **Decision Log**: Architecture decisions documented in concept pages
- **Operations**: Runbooks and incident recovery guides

---

*Wiki maintained by: Agentic AI Architect development team*  
*Based on: Andrej Karpathy's LLM Wiki design*  
*Last verified: 2026-06-30*
