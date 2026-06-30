# Cross-Encoder Reranking — Spec v0

> **Status**: Built, tested, measured — **OFF by default** (opt-in `AAA_CROSS_ENCODER=1`).
> **Owner**: Brandt (#12). 2026-06-30.
> An optional second-stage reranker. On the current (hybrid-saturated) eval it shows no net
> gain, so it stays off — but it is wired, graceful, and ready for a harder eval. Same
> evidence-sets-the-default discipline as hybrid.

---

## 1. Why

Bi-encoder retrieval (the store's `all-MiniLM-L6-v2`) encodes query and document independently,
missing fine-grained interactions. A cross-encoder scores the (query, document) *pair* jointly
and is markedly more accurate at ordering — at the cost of one transformer pass per candidate,
so it only reranks a small top-k and adds latency + a model load.

## 2. What was built

`src/pipeline/cross_encoder_rerank.py`:
- `reorder_by_scores(hits, ce_scores, top_k)` — pure reorder of the top-k by CE score; the tail
  is untouched; reported `score` (vector) is preserved, `cross_encoder_score` attached.
- `CrossEncoderReranker` — lazy, optional. Loads `cross-encoder/ms-marco-MiniLM-L-6-v2` on first
  use; if unavailable (not installed / no model / offline) `available` is False and rerank is a
  **graceful no-op**. Process-wide singleton via `get_reranker()`.
- Sits after hybrid in `LinkedInPersonaStore.search()`, gated on `AAA_CROSS_ENCODER=1` (default
  OFF). `rerank_by_outcomes` uses the strongest signal as its base (CE > hybrid > vector), so
  the recommendation path honors CE order when present.
- Tests: `tests/test_cross_encoder_rerank.py` (10) — reorder logic + graceful fallback, no model.

## 3. Measurement (rank-aware A/B, 20 questions)

Hybrid ON (baseline) vs hybrid + cross-encoder:

| metric | hybrid | hybrid + CE | Δ |
|--------|-------:|------------:|----:|
| MRR | 1.0000 | 1.0000 | 0 |
| nDCG@10 | 0.9573 | 0.9349 | **−0.0224** |
| Precision@5 | 0.9100 | 0.9400 | +0.0300 |
| hit@1 rate | 1.0000 | 1.0000 | 0 |

Net wash, slightly negative on nDCG. Per-question it's mixed (e.g. eval-002 0.886→1.000 up,
eval-020 1.000→0.716 down). The cause is a **ceiling**: with hybrid already at MRR = hit@1 = 1.0
the eval has no headroom, so a stronger reranker only reshuffles within already-correct top-N
and can't demonstrate value. The binding constraint is again the eval's discriminating power,
not the reranker.

## 4. Decision

**OFF by default.** No demonstrated net gain on the available eval, and it adds a heavy optional
dependency plus latency (cross-encoding ~20 candidates on CPU approaches the < 200ms budget).
Enabling it now would trade real cost for unproven benefit. The mechanism is built, graceful, and
opt-in (`AAA_CROSS_ENCODER=1`) for the moment a harder eval justifies it.

## 5. What would justify enabling it (follow-ups)
- A **harder eval**: more candidates with subtle, graded relevance differences (beyond the binary
  author/tool/topic oracle) and queries where hybrid does *not* already hit ceiling — only then
  can a cross-encoder's joint scoring show its edge.
- Latency budget: measure end-to-end with CE on; if it exceeds the < 200ms cached target, cap
  `top_k` or run CE only for low-confidence queries.
