# AAA LLM Wiki Schema

**Version**: 1.0  
**Last Updated**: 2026-06-28

This document defines the structure, conventions, and operational workflows for the Agentic AI Architect knowledge wiki. The wiki follows Andrej Karpathy's LLM Wiki design: three layers (raw sources, synthesized pages, typed schema) with human curation and LLM-assisted bookkeeping.

---

## Overview

The wiki is a **living, curated git repository of markdown files**. It stores everything the AI Architect system knows: personas, frameworks, trends, tools, architectural patterns, decisions, and operations.

### Three Layers

| Layer | What | Why | Who Updates |
|-------|------|-----|-------------|
| **Raw** (`raw/`) | Immutable source documents | Source of truth; never modified | Ingestion pipeline |
| **Pages** (`pages/`) | Synthesized, curated markdown | Human-digestible knowledge | Human reviewers + LLM synthesis |
| **Schema** (`schema/`) | Typed JSON extracts | Machine-readable queries | LLM extraction + human validation |

### Core Principle

> The wiki is just a git repo. You get version history, branching, and collaboration for free. Human maintains curation and direction; LLM handles bookkeeping and maintenance.

---

## Operations

### 1. Ingest

When a new source enters the system (blog post, GitHub README, YouTube transcript, arXiv paper, LinkedIn post):

```
New source → Store in raw/ → Extract entities/topics → 
Create/update wiki pages → Update index/log → Run lint
```

**Steps**:

1. **Source acquired** (from crawler, pipeline, or user)
2. **File stored** in `raw/<persona>/<type>_<date>_<title>.md` (e.g., `raw/chip_huyen/blog_2025-01-16_Common_pitfalls.md`)
3. **Metadata extracted**: author, date, topics, tools, frameworks mentioned
4. **Wiki pages created/updated**: 
   - Entity page for persona if new (e.g., `pages/persona_chip_huyen.md`)
   - Concept pages for frameworks/tools mentioned
   - Pattern pages for architectural insights
5. **Index updated**: New entries added with `status: draft` or `status: seed`
6. **Log entry appended**: Timestamp, operation, target, result, notes
7. **Lint run**: Check for contradictions, missing links, orphans

**Example log entry**:
```
| 2026-06-28 | Ingest | blog:chip_huyen:common_pitfalls | OK | 15,230 chars; added 3 tools, 2 frameworks |
```

### 2. Query

When searching or synthesizing architectural knowledge:

```
Query + filter → Search relevant pages → 
Synthesize answer with citations → File result page → Update index
```

**Steps**:

1. **Query issued** with filters (persona, topic, framework, date range, confidence threshold)
2. **Relevant pages fetched** from `pages/` (search or manual review)
3. **Evidence gathered** with citations (provenance snapshots from raw/)
4. **Answer synthesized** using LLM or manual composition
5. **Result filed** as new page or update to existing concept page
6. **Index updated** with `status: reviewed` if high-confidence
7. **Log entry appended**

**Example log entry**:
```
| 2026-06-28 | Query | "orchestration patterns" | OK | Synthesized from Archon + Orchestrator pages; 4 sources cited |
```

### 3. Lint

Regular health checks for wiki quality:

```
Scan all pages → Check for contradictions, stale claims, orphans, 
missing cross-references → Report issues → Human triage → Fix or document
```

**Checks**:

- **Orphan detection**: Pages with no backlinks
- **Contradiction detection**: Conflicting facts about same entity
- **Stale content**: Timestamps older than 90 days (flags for refresh)
- **Dead links**: References to non-existent pages
- **Missing index entries**: Pages not listed in index.md
- **Untagged pages**: Pages without persona, topic, or framework tags

**Example lint output**:
```
## Lint Run — 2026-06-28

⚠️  Stale: pages/tool_langchain.md (last update 2026-03-02, now >90 days)
⚠️  Orphan: pages/concept_reward_hacking.md (0 backlinks)
✓  Clean: 48 pages, 0 contradictions, 2 warnings
```

---

## File Naming Conventions

### Raw Sources

Format: `raw/<persona>/<type>_<date>_<title>.md`

Examples:
- `raw/andrej_karpathy/github_nanoGPT_readme.md`
- `raw/chip_huyen/blog_2025-01-16_Common_pitfalls_when_building_generative_AI_applications.md`
- `raw/arxiv_research/arxiv_2026-06-15_Reward_Hacking_in_Reinforcement_Learning.md`
- `raw/brandtpileggi/linkedin_li-7449805326071156736.md`

### Wiki Pages

Format: `pages/<category>_<entity>.md`

Examples:
- `pages/persona_andrej_karpathy.md`
- `pages/framework_rag.md`
- `pages/tool_langchain.md`
- `pages/pattern_llm_wiki.md`
- `pages/trend_multimodal_models.md`
- `pages/concept_prompt_injection.md`

### Schema Files

Format: `schema/<entity_type>.json`

Examples:
- `schema/personas.json`
- `schema/frameworks.json`
- `schema/tools.json`
- `schema/patterns.json`
- `schema/trends.json`

---

## Markdown Format for Wiki Pages

All wiki pages follow this structure:

```markdown
# [Title]

**Category**: [persona | framework | tool | pattern | trend | concept]  
**Status**: [seed | draft | reviewed | stale]  
**Last Updated**: [YYYY-MM-DD]  
**Sources**: [N] items  
**Confidence**: [high | medium | low]

## Summary

[2-3 sentence overview]

## Key Details

[Main content, organized by subsections]

## Related Entities

- **Personas**: [links to persona pages]
- **Frameworks**: [links to framework pages]
- **Tools**: [links to tool pages]
- **Patterns**: [links to pattern pages]

## Sources

| Source | Date | Evidence |
|--------|------|----------|
| [Link] | YYYY-MM-DD | [Brief quote or summary] |

## Provenance

Last verified: YYYY-MM-DD  
Verified by: [human or llm]  
Confidence basis: [why we trust this entry]
```

---

## Index Format

**File**: `data/wiki/index.md`

Purpose: Content-oriented catalog with one-line summaries, organized by category.

Structure:

```markdown
# AAA Wiki Index

## [Category]

| Page | [Key Metadata] | Status |
|------|---|--------|
| [Link](path) | [summary] | seed/draft/reviewed/stale |
```

Updates:
- Add new entries when pages are created
- Update status as entries progress
- Run "Last rebuilt" timestamp update

---

## Log Format

**File**: `data/wiki/log.md`

Purpose: Append-only chronological record for unix-tool parsing and audit trail.

Format: Pipe-separated table with columns:
- **Timestamp**: ISO 8601 (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
- **Operation**: Ingest | WikiPage | Query | Lint | Schema | UpdatedIndex | UpdatedConceptPage
- **Target**: What was processed (filename, entity, query)
- **Result**: OK | WARNING | DEFERRED | FAILED
- **Notes**: Details (size, entity count, reason, etc.)

```markdown
| 2026-06-28 | Ingest | blog:chip_huyen:common_pitfalls | OK | 15,230 chars; 3 tools, 2 frameworks |
| 2026-06-28 | WikiPage | pages/concept_evaluation.md | OK | Updated from synthesis; 8 sources |
| 2026-06-28 | Lint | pages/ | WARNING | 1 stale entry; 2 orphans |
```

Rules:
- Never delete entries
- Append new entries at the bottom
- Use consistent prefixes for parsability

---

## Status Lifecycle

| Status | Meaning | Action |
|--------|---------|--------|
| **seed** | Stub created; outline present | Flesh out content or mark draft |
| **draft** | Content present; human review pending | Review and update provenance |
| **reviewed** | Human verified; sources checked | No action; maintain provenance |
| **stale** | Last verified >90 days ago | Refresh or update date if still valid |

---

## Metadata Tagging

Every wiki page should include metadata tags for searchability:

```yaml
tags:
  - persona: [slug]
  - framework: [slug]
  - tool: [slug]
  - pattern: [slug]
  - trend: [slug]
  - phase: [P1-P7 phase references]
  - topic: [topic slug]
```

---

## Schema Extract Guidelines

Typed JSON schema files capture structured metadata. Regenerate after bulk updates:

```bash
python3 scripts/build_wiki_schema.py
```

Each schema file includes:
- `schema_version`: Current version (e.g., "1.0")
- `updated_at`: Last rebuild timestamp
- `description`: What this schema represents
- Array of typed entities with fields

---

## Runbook: Ingest New Content

**When**: Daily, or as new sources arrive  
**Duration**: 5–15 min per source  
**Who**: Automation pipeline or human curator

**Steps**:

1. Acquire source (crawler, user upload, API)
2. Move to `raw/<persona>/<type>_<date>_<title>.md`
3. Extract metadata (author, date, topics, tools, frameworks)
4. Create persona page if new
5. Create/update concept pages for mentioned entities
6. Add entry to `index.md`
7. Append log entry to `log.md`
8. Run `python3 scripts/lint_wiki.py` to check for issues
9. Commit to git

**Example**:
```bash
# Ingest new blog post
cp ~/Downloads/chip_huyen_post.md data/wiki/raw/chip_huyen/blog_2026-06-28_New_Eval_Patterns.md
# Extract and file... → pages/concept_evaluation.md updated
# Log and index...
python3 scripts/lint_wiki.py
git add data/wiki/ && git commit -m "ingest(wiki): Chip Huyen on evaluation patterns"
```

---

## Runbook: Lint and Maintain

**When**: Weekly or after bulk ingest  
**Duration**: 5–10 min  
**Who**: Automation or human curator

**Steps**:

1. Run lint checker: `python3 scripts/lint_wiki.py`
2. Review warnings (stale, orphans, contradictions)
3. For each warning:
   - **Stale**: Verify still valid or mark for refresh
   - **Orphan**: Link from concept page or mark as deprecated
   - **Contradiction**: Research and reconcile or document disagreement
4. Update `log.md` with lint result
5. Commit any changes

```bash
python3 scripts/lint_wiki.py | tee lint_report.txt
# Review and fix issues...
git add data/wiki/ && git commit -m "chore(wiki): lint maintenance; 2 stale entries refreshed"
```

---

## Runbook: Query and Synthesize

**When**: On-demand or periodic synthesis runs  
**Duration**: 10–30 min  
**Who**: Human architect or LLM agent

**Steps**:

1. Define query + filters (persona, framework, topic, date range)
2. Gather relevant pages from `pages/`
3. Extract evidence with provenance snapshots
4. Synthesize answer using LLM or manual composition
5. Create new page or update existing concept page
6. Add citations and sources
7. Set `status: draft` for human review
8. Update `index.md` and append `log.md`
9. Commit and link from related pages

**Example**:
```markdown
# Query Result: Orchestration Patterns in Agentic AI

**Status**: draft  
**Query**: "How do Cole Medin and Andrej Karpathy approach orchestration?"  
**Synthesized**: 2026-06-28  
**Sources**: Archon (Cole), autoresearch (Andrej), papers (3)

## Answer

[Synthesis with citations]

## Sources

| Source | Evidence |
|--------|----------|
| Archon README | "queue-based orchestration with bounded workers" |
| autoresearch gist | "durable checkpointing for agent state" |
```

---

## Integration with AAA System

The wiki serves as:

1. **Knowledge base reference** for MCP tools and synthesis queries
2. **Decision log** for architectural choices
3. **Source registry** for bias/weighting analysis
4. **Trend tracker** input (framework adoption, tool emergence)
5. **Evaluation reference** for persona/framework/tool ground truth

When the MCP server or REST API synthesizes an answer, it should cite wiki pages in the provenance field.

---

## Git Workflow

**Commits** should use this message format:

```
<type>(<scope>): <subject>

Types: ingest | query | lint | schema | docs | maintenance
Scope: wiki, personas, frameworks, tools, patterns, trends

Examples:
ingest(wiki): Chip Huyen blog on evaluation patterns
query(wiki): Synthesized orchestration strategy from 4 sources
lint(wiki): Refresh stale entries; document 2 contradictions
schema(wiki): Rebuild personas.json after ingest
```

---

## FAQ

**Q: Should I update raw files?**  
A: No. Raw files are immutable. If a source needs correction, create a new version or note the correction in the pages/ file.

**Q: How often should I lint?**  
A: Weekly or after bulk ingest. More often if you have a bot doing continuous updates.

**Q: What if two sources contradict?**  
A: Document both views in the wiki page. Don't delete either. Tag with `confidence: low` and note the disagreement in sources section.

**Q: Can I delete pages?**  
A: Rarely. Mark as stale or deprecated instead. If truly obsolete, remove from index but keep raw file and note in log.

**Q: How do I extract schema files?**  
A: Run `python3 scripts/build_wiki_schema.py` after ingest. Commit generated JSON files.

---

*Schema maintained by: Agentic AI Architect development team*  
*Based on: Andrej Karpathy's LLM Wiki design*
