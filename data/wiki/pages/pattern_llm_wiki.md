---
wiki_id: pattern_llm_wiki
type: pattern_page
persona: andrej_karpathy
origin: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
foundational: true
raw_source: data/seeds/karpathy_llm_wiki.md
status: reviewed
last_updated: 2026-06-29
aaa_relevance:
  - This file IS the operating spec for data/wiki/ — the LLM-maintained knowledge layer
  - "Tracking what we're doing / where we are" = the index.md (state) + log.md (timeline) discipline below
  - P2.4 — structured index.md beats vector RAG at moderate scale (~100–500 sources)
  - P6.4 — Lint operation and knowledge distillation
---

# LLM Wiki Pattern (Karpathy)

> Authoritative source: Andrej Karpathy, *"LLM Wiki"* gist. Full verbatim text in
> [`data/seeds/karpathy_llm_wiki.md`](../../seeds/karpathy_llm_wiki.md) (curl-captured;
> a WebFetch of the URL once returned a prompt-injected response — see the seed's note).
> This page is the synthesis; the seed is the immutable source.

## The core idea

Most LLM-over-documents setups are **RAG**: upload files, retrieve relevant chunks at
query time, generate an answer. The LLM rediscovers knowledge from scratch on every
question — nothing accumulates.

The LLM Wiki pattern is different: the LLM **incrementally builds and maintains a
persistent, interlinked markdown wiki** that sits *between* you and the raw sources.
A new source isn't just indexed for later — it's read, distilled, and **integrated**:
entity pages updated, summaries revised, contradictions flagged, the synthesis
strengthened or challenged. Knowledge is **compiled once and kept current**, not
re-derived per query.

> **The wiki is a persistent, compounding artifact.** The cross-references are already
> there. The contradictions are already flagged. The synthesis already reflects
> everything read. It gets richer with every source *and every question*.

Division of labor: **the human curates sources, explores, and asks good questions; the
LLM does all the bookkeeping** — summarizing, cross-referencing, filing, consistency.
"Obsidian is the IDE; the LLM is the programmer; the wiki is the codebase."

## Three layers

| Layer | Location | Contents | Who writes |
|-------|----------|----------|------------|
| **Raw sources** | `raw/` + `data/seeds/` | Immutable source artifacts (posts, READMEs, transcripts, papers, gists). Source of truth — never modified. | Ingest pipeline |
| **Wiki pages** | `pages/` | Curated synthesis — one page per persona, concept, tool, pattern, comparison. The LLM owns this layer. | LLM + human review |
| **Schema** | `SCHEMA.md` + `schema/*.json` | The config that disciplines the LLM (conventions, workflows) **and** typed machine-readable extracts. | LLM + human validation |

Note: Karpathy's "schema" is primarily the **governing config doc** (CLAUDE.md / AGENTS.md
/ our `SCHEMA.md`) — the thing that makes the LLM a disciplined maintainer rather than a
generic chatbot. AAA additionally keeps typed JSON extracts under `schema/`.

## Three operations

### Ingest
Drop a source into `raw/`, tell the LLM to process it. Flow: read → discuss takeaways →
write/append a summary page → update `index.md` → update every affected entity/concept
page → append to `log.md`. **A single source can touch 10–15 pages.** Ingest one at a
time with supervision, or batch with less.

### Query
Ask the wiki. The LLM reads `index.md` first to locate pages, reads them, answers with
citations. Answers take whatever form fits — page, comparison table, slide deck, chart.

> **The critical insight: good answers get filed back into the wiki as new pages.** A
> comparison, an analysis, a connection you discovered — these shouldn't vanish into chat
> history. Explorations **compound** in the knowledge base just like ingested sources do.

### Lint
Periodically health-check the wiki: contradictions between pages, stale claims newer
sources superseded, orphan pages, concepts mentioned but lacking a page, missing
cross-references, data gaps a web search could fill. Lint doesn't just clean — **it
surfaces the next questions to investigate and sources to find.**

## Indexing & logging — "where we are" + "what we did"

These two files are how the wiki (and we) stay oriented:

- **`index.md` — content-oriented (the *where we are* snapshot).** A catalog of every
  page with a link + one-line summary, organized by category. Updated on every ingest.
  Read first on every query. At ~100s of pages this beats embedding RAG and needs no
  vector infra.
- **`log.md` — chronological (the *what we did, when* timeline).** Append-only; never
  delete. **Adopt a parseable prefix** so the log is greppable:
  `## [YYYY-MM-DD] <op> | <title>` where `<op>` ∈ `ingest | query | lint`.
  Then `grep "^## \[" data/wiki/log.md | tail -5` gives the last five events.

## Why it works

The hard part of a knowledge base isn't reading or thinking — it's **bookkeeping**.
Humans abandon wikis because maintenance grows faster than value. LLMs don't get bored,
don't forget a cross-reference, and touch 15 files in one pass, so maintenance cost
approaches zero and the wiki stays alive. Lineage: Vannevar Bush's **Memex** (1945) —
a private, actively-curated store with associative trails between documents; the part
Bush couldn't solve was *who does the maintenance*. The LLM does.

---

## How AAA implements this (the operating discipline)

This is the contract for "appropriately tracking what we're doing and where we are."

```
data/wiki/
├── SCHEMA.md         ← the governing config (conventions + workflows)
├── RUNBOOKS.md       ← operations + troubleshooting
├── index.md          ← WHERE WE ARE: content catalog, read first on every query
├── log.md            ← WHAT WE DID: append-only, parseable `## [date] op | title`
├── raw/              ← layer 1: source artifacts (+ data/seeds/ for foundational)
├── pages/            ← layer 2: curated synthesis (persona_*, concept_*, pattern_*, repo_*)
└── schema/           ← layer 3: typed JSON extracts (+ chromadb_snapshot.json)
```

| Pattern element | AAA realization |
|---|---|
| Raw layer | `data/wiki/raw/<persona>/…` and `data/seeds/` for foundational sources |
| Wiki layer | `data/wiki/pages/*.md` |
| Schema (config) | `data/wiki/SCHEMA.md` + repo `CLAUDE.md` |
| Schema (extracts) | `data/wiki/schema/*.json` |
| Index (where we are) | `data/wiki/index.md` |
| Log (what we did) | `data/wiki/log.md` + the durable `docs/*-log.md` ledgers |
| Ingest | `scripts/refresh_corpus.py` (restore → learnings → blog → arXiv → export) |
| Query | `src/api/mcp_server.py` + `src/api/rest_v1.py` |
| Lint | planned (P6.4); today: manual + the lint table in `index.md` |
| "Answers filed back as pages" | a query worth keeping → write a `pages/` page, don't leave it in chat |
| Compounding / vector layer | ChromaDB store (417 items) mirrors the synthesis for semantic search |

**Standing discipline going forward:**
1. **Every meaningful session appends a `log.md` entry** in the `## [date] op | title` form
   (and the relevant `docs/*-log.md` ledger for durable decisions/discoveries/lessons).
2. **Every ingest updates `index.md`** so it always answers "where are we" at a glance.
3. **Worthwhile query answers get filed as `pages/`**, so exploration compounds.
4. **Periodic Lint** flags contradictions/orphans/staleness and proposes the next work.

> Two complementary memory systems coexist: this **external** wiki (Karpathy pattern) for
> what the field knows, and the **internal** `docs/*-log.md` ledgers (decisions/discoveries/
> lessons, ingested as `project_learning`) for what *we* learned building AAA.
