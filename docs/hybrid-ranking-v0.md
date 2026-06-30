# Hybrid Retrieval Ranking — Spec v0

> **Status**: Built, tested, measured — **OFF by default** (opt-in via `AAA_HYBRID_RANKING=1`).
> **Owner**: Brandt (#12). 2026-06-30.
> The mechanism is sound and proven deterministically; it is gated off because the current
> evaluation cannot measure ranking quality, so there is no evidence to justify changing the
> core retrieval order in production. The headline deliverable is that finding.

---

## 1. Why

The persona store ranks purely by cosine similarity on `all-MiniLM-L6-v2`. The discovery log
(2026-06-28) named retrieval ranking as the next lever: *"surface the most on-point evidence
densely — not just more content … reranking, hybrid keyword+vector, or query expansion."*
Dense retrieval is strong on paraphrase but smooths away exact terms — tool names, acronyms
(MCP, RAG), API symbols, rare proper nouns — that a lexical match would catch.

## 2. What was built

`src/pipeline/hybrid_ranking.py` (pure stdlib, no new dependency):
- `tokenize`, `bm25_scores` (BM25 with IDF over the candidate pool), `selective_terms`,
  `hybrid_scores`, `rerank_hits`.
- Fusion is a convex blend, **used only to re-order**: `hybrid = (1-α)·vector + α·lexical_norm`,
  α=0.25. The reported `score` stays the raw vector similarity, so the [0,1] relevance scale and
  every threshold / outcome multiplier built on it are unchanged.
- **Selectivity gate**: lexical only contributes from query terms that are *rare in the pool*
  (document frequency ≤ 50%). Conceptual queries whose terms are common-in-pool get pure vector
  order (an exact no-op).
- Wired into `LinkedInPersonaStore.search()` over the over-fetched pool (pre-trim) so a
  low-vector exact match can be rescued. `rerank_by_outcomes` now uses `hybrid_score` as its
  base when present, so the recommendation path honors hybrid order rather than reverting to
  vector.
- Tests: `tests/test_hybrid_ranking.py` (17, deterministic) prove the mechanism — e.g. a
  lower-vector exact "MCP" match is promoted to rank 1; a clear vector winner is *not* displaced
  by a weak keyword hit; conceptual (no-selective-term) queries are an exact no-op.

## 3. What the eval showed — and why it can't judge a reranker

Baseline (pure vector): **15/15 search questions pass, avg relevance 0.4751.**
Hybrid ON (gated): **15/15 pass, avg relevance 0.4143.** Every individual judgment check
(threshold, author-cited, tools-found, topics-found) was **unchanged on all 15 questions**.

So hybrid caused **zero measurable quality change**, yet "avg relevance" dropped ~0.06. That drop
is a **metric artifact, not harm**:

- `avg relevance` = mean of the **top-1 doc's vector similarity**. The baseline rank-1 is by
  construction the maximum-vector doc. *Any* reorder that changes rank-1 promotes a doc with
  **lower** vector similarity, so this metric can only stay equal or fall under reranking —
  it is structurally incapable of crediting a reranker.
- The pass-rate is **saturated at 15/15**, so it cannot show improvement either.

**Conclusion**: the current eval harness cannot measure ranking quality. It can detect a
catastrophic regression (a check flips) but cannot distinguish a better ordering from a worse
one among already-passing results. This is the binding gap for *all* ranking work (reranking,
hybrid, query expansion), not just this slice.

## 4. Decision

Ship the mechanism **OFF by default**. Rationale:
- No demonstrated benefit on the available eval; changing core retrieval order in production
  without evidence it is net-positive violates the eval-gating discipline (the discipline P6
  slice 2 established and that this slice deliberately followed).
- The lever is ready: flip `AAA_HYBRID_RANKING=1` the moment a ranking-aware eval shows gain.

## 5. What candidate (b) actually needs next (re-scoped)

Before any reranker can be *justified*, the eval must be able to **judge order**:
1. **Ranking-aware metrics** — graded relevance judgments + MRR / nDCG@k, not just top-1
   threshold + presence checks.
2. **Exact-term / keyword questions** — queries with rare tool names, acronyms, API symbols
   where dense retrieval is known to miss and lexical is known to help (e.g. expand on the
   `vllm-turboquant` style question).
3. Then measure hybrid (and a cross-encoder reranker, query expansion) against it, and enable
   what wins.

This reorders the (b) roadmap: **build the measurement instrument first, then the reranker.**
