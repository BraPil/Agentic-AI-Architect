# Sprint 4 Gaps Analysis
*April 2026 — post Sprint 3 review*

---

## On the Relevance Score (0.4649)

**This is not a problem.** The 0.4649 figure is average cosine similarity between query embeddings and their top matching document, computed by ChromaDB using `all-MiniLM-L6-v2`. For a heterogeneous corpus (short LinkedIn posts, long blog articles, YouTube transcripts, arXiv abstracts) with a general-purpose 384-dim model, values in the 0.4–0.6 range are entirely typical. Cosine similarity is not a percentage of "correctness" — it measures geometric proximity in embedding space.

The authoritative quality signal is the **eval pass rate: 15/15 (100%)** on the first run against 15 ground-truth questions. This confirms that the semantic index is returning the right content for the right queries, regardless of the raw similarity number.

Do not chase this number. Chase eval pass rate degradation as the corpus scales.

---

## Identified Gaps

### Gap 1 — No automatic refresh
**Current:** All ingests are manual CLI scripts. No scheduling, no cron, no change detection.  
**Impact:** Corpus will become stale as new content is published. No proactive alerting on new high-signal posts.  
**Fix (Sprint 4):** APScheduler or GitHub Actions cron for weekly ingest of blogs + arXiv. Alert webhook when trending tools shift significantly.

### Gap 2 — No freshness weighting
**Current:** A 2021 arXiv paper and a 2026 LinkedIn post rank identically if their embeddings are equally similar to the query.  
**Impact:** Older, potentially outdated content competes equally with recent practitioner signal.  
**Fix:** Add `published_date` to ChromaDB metadata and apply a recency multiplier in `search_knowledge`. Alternatively, filter by date in the `where` clause when the query implies recency ("what's trending", "recent patterns").

### Gap 3 — No synthesis quality eval
**Current:** The eval harness tests retrieval quality only (does search_knowledge return relevant results?). The `get_architecture_recommendation` synthesis path (Claude Haiku) has no ground-truth tests.  
**Impact:** Haiku synthesis quality could degrade or produce incorrect recommendations without detection.  
**Fix:** Add 5 synthesis eval questions to `eval_ground_truth.json` with expected recommendation patterns. Score with Claude-as-judge.

### Gap 4 — LinkedIn posts are short snippets
**Current:** 79 LinkedIn posts are scraped snippets (typically 200–500 chars). Long-form reasoning from the same authors is in YouTube transcripts and GitHub READMEs, but the LinkedIn entries don't link to those.  
**Impact:** Dilutes relevance for deep technical queries when LinkedIn snippets surface ahead of richer content from the same author.  
**Fix:** Cross-link items at ingest time by `persona_id`. When a LinkedIn post references a video or repo, add the URL as a metadata field so the MCP server can return it.

### Gap 5 — No feedback loop from MCP usage
**Current:** No logging of which MCP tool calls were made, what queries were issued, or which results were used.  
**Impact:** Can't detect query patterns, identify coverage gaps, or surface high-demand topics for targeted ingest.  
**Fix:** Add structured tool-call logging in `mcp_server.py` to a local JSONL file. Aggregate weekly into a query frequency report.

### Gap 6 — Snapshot will grow with corpus
**Current:** Snapshot is 937KB for 204 items. At 2,000 items it'll be ~9MB; at 20,000 items, ~90MB — beyond comfortable git tracking.  
**Impact:** Git history bloat; slow clone times.  
**Fix:** Keep snapshot in git up to ~5,000 items. Above that, move to an S3/GCS bucket or GitHub LFS and update restore script accordingly. Not urgent now.

### Gap 7 — Blog source coverage gaps
**Current:** Only Simon Willison and Lilian Weng.  
**Missing high-value sources:** Chip Huyen (pragmatic ML deployment), Sebastian Ruder (NLP/evaluation), Eugene Yan (RecSys + LLM production), newsletter digests (TLDR AI, The Batch, Import AI).  
**Fix (Sprint 4):** Add to `BLOG_REGISTRY` in `src/pipeline/blog_ingest.py`. Each new source needs an RSS/Atom feed URL and a persona slug.

### Gap 8 — No persona completeness tracking
**Current:** No visibility into which personas have deep coverage vs. thin coverage.  
**Impact:** Queries about underrepresented personas return low-quality results with no warning.  
**Fix:** Add a `persona_coverage_report()` function to the eval harness that shows item count + avg snippet length per persona. Surface in eval output.

---

## What NOT to do before Sprint 4

- Do not upgrade the embedding model (`all-mpnet-base-v2`, `text-embedding-3-small`) — would require re-embedding all 204 items and would invalidate the snapshot. Only worth it if eval pass rate degrades below 80%.
- Do not add HyDE (Hypothetical Document Embeddings) or query expansion yet — retrieval quality is already 100%. Premature complexity.
- Do not add multiple ChromaDB collections — single collection with metadata filters is working; sharding adds operational complexity without benefit below 1M items.

---

## Sprint 4 Priority Order

1. **Blog source expansion** — highest ROI, no infrastructure changes needed (Chip Huyen, Sebastian Ruder, Eugene Yan)
2. **Automated refresh** — APScheduler weekly run of blog + arXiv ingest
3. **Freshness metadata** — add `published_date` to all items, enable date filtering in `search_knowledge`
4. **Synthesis eval** — 5 new eval questions testing `get_architecture_recommendation` output quality
5. **MCP usage logging** — lightweight JSONL log for query analytics
6. **Persona coverage report** — surface thin personas in eval output
