# Knowledge Management — [PROJECT NAME]

> How the system stores, retrieves, and maintains institutional knowledge.
> Inspired by Karpathy's three-layer LLM Wiki design.

---

## Knowledge Taxonomy

*Most repositories collapse these four types. Keeping them separate makes retrieval precise.*

| Type | What | Where | Updated By | Never Contains |
|------|------|-------|-----------|----------------|
| **Facts** | Domain knowledge, external content, research findings | `knowledge/` or `data/` | Ingestion pipeline | Decisions or opinions |
| **Decisions** | Architectural choices, tradeoffs accepted | `docs/decision-log.md`, `adr/` | Humans | Facts or opinions |
| **History** | What happened, when, why | `docs/discovery-log.md`, `docs/work-log.md` | Both | Facts or decisions |
| **Standards** | Rules and conventions | `docs/` companions, `CLAUDE.md` | Humans only | History or facts |

---

## The Three-Layer Wiki Design

*(Adapted from Karpathy's LLM Wiki pattern — see `data/wiki/SCHEMA.md`)*

```
Layer 1: RAW     — Immutable source documents (never modified after ingest)
Layer 2: PAGES   — Synthesized, curated markdown (human-digestible)
Layer 3: SCHEMA  — Typed JSON extracts (machine-queryable)
```

**Why three layers:**
- Raw ensures provenance. You always know where a fact came from.
- Pages ensure readability. A human can review without reading raw sources.
- Schema ensures queryability. A machine can search without reading prose.

**Operations:**
- **Ingest:** Raw source → extract entities → create/update pages → update index → lint
- **Query:** Filter pages → synthesize answer with citations → file result → update index
- **Lint:** Check for contradictions, broken links, orphan pages, stale entries

---

## Knowledge Base Structure

```
[knowledge store location, e.g., data/wiki/]
├── raw/           ← immutable source documents
│   └── [source]/  ← organized by source persona or origin
├── pages/         ← synthesized knowledge pages
│   ├── persona_*.md
│   ├── concept_*.md
│   ├── pattern_*.md
│   └── tool_*.md
├── schema/        ← typed JSON extracts
├── index.md       ← content catalog (human-readable)
├── SCHEMA.md      ← conventions, metadata format, operations
├── RUNBOOKS.md    ← operational guides
└── log.md         ← append-only operation log
```

---

## Namespaces

*Every knowledge entry must have a namespace. Unknown namespace = reject.*

| Namespace | Contents | Examples |
|-----------|----------|---------|
| `[namespace_1]` | [description] | [examples] |
| `[namespace_2]` | [description] | [examples] |
| `general` | Cross-cutting knowledge that doesn't fit above | — |

*Adding a new namespace requires: a row in this table + entry in `docs/decision-log.md`.*

---

## Provenance Requirements

*Every knowledge base entry must carry:*

| Field | Required | Description |
|-------|----------|-------------|
| `source` | Yes | Human-readable source name |
| `source_url` | Yes (if web) | Original URL |
| `retrieved_at` | Yes | Timestamp of ingestion |
| `confidence` | Yes | `high` / `medium` / `low` |
| `namespace` | Yes | From the allowed namespace list |
| `content_hash` | Recommended | For deduplication |

*Entries without provenance are not displayed as facts. They are displayed as `unverified`.*

---

## Knowledge Quality Standards

**Deduplication:** content hash before storing. Same hash = update timestamp, don't create duplicate.

**Staleness policy:**
- Knowledge entries from web sources older than [N] months are flagged `stale`
- Stale entries are not deleted (provenance preserved) but are deprioritized in retrieval
- Scheduled re-ingest refreshes high-value stale sources

**Contradiction handling:**
- When two sources contradict each other, both entries are kept
- A `contradiction` tag is added to both
- Queries return both entries with a note about the conflict; do not silently pick one

**Confidence calibration:**
- `high`: primary source, recent, multiple corroborations
- `medium`: secondary source, or primary source older than [N] months
- `low`: single source, unverified, or synthesized without direct citation

---

## Index Maintenance

*`index.md` (or equivalent) is the human-readable catalog. Keep it accurate.*

**After every ingest batch:**
1. Update item count in index header
2. Add new entries to the appropriate section
3. Update status of existing entries (draft → reviewed, etc.)
4. Run lint to catch broken links and orphans

**Lint checks:**
- [ ] Every page referenced in the index exists
- [ ] Every raw file has a corresponding index entry
- [ ] No pages reference deleted or renamed pages
- [ ] No orphan pages (pages not linked from the index)

---

## Query and Retrieval

*How the system finds and returns knowledge:*

**Search order (priority):**
1. Exact match on title or ID
2. Semantic similarity (vector search) on page content
3. Full-text search fallback if vector store unavailable

**Citation requirement:** every query result must include `source` and `retrieved_at`. Results
without provenance are not returned as facts.

**Retrieval confidence thresholds:**
- Return results with relevance >= [0.X] as direct answers
- Return results with relevance [0.Y]–[0.X] as "related but uncertain"
- Do not return results below [0.Y]

---

*Last updated: [YYYY-MM-DD]*
