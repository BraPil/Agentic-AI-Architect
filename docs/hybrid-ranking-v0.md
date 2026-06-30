# Hybrid Retrieval Ranking — Spec v0

> **Status**: Built, tested, measured — **ON by default** (kill-switch `AAA_HYBRID_RANKING=0`).
> **Owner**: Brandt (#12). 2026-06-30.
> Arc: built the reranker → the existing eval couldn't judge it (a metric artifact looked like
> a regression) → built a rank-aware eval → it showed hybrid clearly helps → enabled it. The
> discipline avoided *both* shipping blind and discarding a good feature on a biased metric.

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

## 4. Interim decision (now superseded): shipped OFF, built the instrument first

The first measurement could not justify enabling hybrid, so it shipped OFF while the missing
instrument was built. This was the correct interim call: don't change core retrieval order on
a metric that can't credit a reorder.

## 5. The instrument — rank-aware eval

`src/pipeline/ranking_metrics.py` + `scripts/eval_ranking.py` add MRR, nDCG@k, precision@k,
and hit@1, with a **label-free graded relevance oracle**: each result earns +1 per matched
ground-truth signal (`must_cite_author`, `expected_tools`, `expected_topics`), grade 0..3.
No manual judgments — it reuses fields the ground truth already carries and stays in sync with
the question set. Run it `AAA_HYBRID_RANKING=0` vs `=1` and `--compare` the two runs.

## 6. Vindication — hybrid clearly helps (enabled by default)

Rank-aware A/B over the 15 search questions (`scripts/eval_ranking.py`, n_results=10):

| metric | hybrid OFF | hybrid ON | Δ |
|--------|-----------:|----------:|----:|
| MRR | 0.9000 | **1.0000** | +0.100 |
| nDCG@10 | 0.8769 | **0.9469** | +0.070 |
| Precision@5 | 0.8400 | **0.9067** | +0.067 |
| hit@1 rate | 0.8000 | **1.0000** | +0.200 |

All four improved. The decisive case: **eval-005 ("vllm-turboquant")** — the exact-term query
hybrid was built for — went from hit@1=0 / first-relevant-at-rank-2 to **rank 1**. Three
queries that had a *non-relevant* doc at rank 1 under pure vector now all lead with a relevant
doc (hit@1 0.80→1.00). This confirms the earlier "avg relevance dropped" was the metric
artifact, not harm. Hybrid is therefore **enabled by default**.

Known cost (small, not overfit away): two conceptual queries (eval-002, eval-006) lost a little
nDCG/P@5 when a pool-rare topic term fired lexical. Net aggregate is positive on every metric;
tuning the selectivity threshold / α to remove those is a follow-up, deferred to avoid
overfitting to 15 questions.

**Re-confirmed on the expanded set (2026-06-30).** Five exact-term questions (eval-016..020:
BIG-Bench, AGENTS.md, adversarial-attacks, llmfit, AWQ/GPTQ) were added; on the 20-question
set the A/B held — MRR 0.925→1.000, nDCG@10 0.889→0.957, P@5 0.870→0.910, hit@1 0.850→1.000,
with run_eval still 20/20. See `docs/ranking-aware-eval-v0.md §4`.

## 7. Open follow-ups
- Re-tune α / selectivity on the larger set; consider a cross-encoder reranker as a second
  stage, measured on the same instrument.
- Wire the rank metrics into `run_eval.py` / CI alongside the pass-rate.
