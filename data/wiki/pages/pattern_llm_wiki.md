---
wiki_id: pattern_llm_wiki
type: pattern_page
persona: andrej_karpathy
origin: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
foundational: true
raw_source: data/seeds/karpathy_llm_wiki.md
status: reviewed
last_updated: 2026-04-18
aaa_relevance:
  - P2.4 — structured KB index design (index.md beats FAISS at <500 sources)
  - P6.4 — knowledge distillation and Lint operation
  - This file IS the implementation spec for data/wiki/
---

# LLM Wiki Pattern (Karpathy)

## The Core Idea

Instead of a vector database, maintain a **human-readable wiki** as the knowledge layer. Structure it in three layers and three operations.

## Three Layers

| Layer | Location | Contents | Who writes |
|-------|----------|----------|------------|
| Raw Sources | `raw/` | Unmodified source artifacts (transcripts, READMEs, posts) | Ingest pipeline |
| Wiki Pages | `pages/` | Curated synthesis — one page per concept, person, tool, pattern | Ingest pipeline + LLM |
| Schema | `schema/` | Typed structured extracts (entities, facts, relationships) | Lint pass |

## Three Operations

### Ingest
Source material → update wiki pages. Every new transcript, README, or post either updates an existing page or creates a new one. Pages accumulate knowledge over time.

### Query
Ask the wiki, file the answer back. A query first hits the index.md to find relevant pages, reads those pages, then returns a structured answer. No FAISS needed at <500 sources.

### Lint
Health-check the wiki for:
- **Contradictions**: two pages that disagree on a fact
- **Orphans**: pages not referenced in index.md
- **Staleness**: pages whose source has been updated but the wiki page hasn't

## Key Files

- `index.md` — catalog of all wiki pages with one-line summaries. This is what the Query operation searches first.
- `log.md` — append-only log of all ingest and lint operations. Never delete entries.

## The Critical Insight for AAA

> **Structured index.md outperforms vector RAG at moderate scale (~100–500 sources).**

At AAA's current scale (dozens of sources), building and maintaining a curated index is better than reaching for FAISS. FAISS introduction should be deferred until the structured index is saturated.

This directly informs P2.3: build the KB index layer first, not last.

## How AAA Implements This

```
data/wiki/
├── index.md          ← content catalog (this is what Query reads)
├── log.md            ← append-only ingest log
├── raw/              ← layer 1: source artifacts
│   ├── karpathy/     ← github_*.md, youtube_*.txt
│   └── cole_medin/
├── pages/            ← layer 2: curated wiki pages
└── schema/           ← layer 3: typed structured extracts
```

Operations map to AAA pipeline components:
- Ingest → `src/pipeline/github_ingest.py`, `src/pipeline/youtube_ingest.py`
- Query → `src/knowledge/knowledge_base.py` + `GET /query`
- Lint → planned for P6.4
