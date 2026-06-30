# Cross-Encoder Reranking — Spec v0

> **Status**: Built, tested, measured — **OFF by default** (opt-in `AAA_CROSS_ENCODER=1`).
> **Owner**: Brandt (#12). 2026-06-30.
> An optional second-stage reranker. The graded eval shows it *does* improve ranking accuracy
> (every metric), correcting the earlier saturated-eval "no gain" — but it costs ~6 s/query on
> CPU, ~30× the 200 ms budget, so it stays OFF for the live path and is justified only as an
> opt-in for offline/GPU use. Accuracy is gated by latency, not value.

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

## 3. Measurement — two evals, opposite verdicts (read both)

**First measurement, heuristic (saturated) eval — looked like a wash:**

| metric | hybrid | hybrid + CE | Δ |
|--------|-------:|------------:|----:|
| MRR | 1.0000 | 1.0000 | 0 |
| nDCG@10 | 0.9573 | 0.9349 | −0.0224 |
| hit@1 rate | 1.0000 | 1.0000 | 0 |

This was a **ceiling artifact**: hybrid already reached MRR = hit@1 = 1.0 on the binary-oracle
eval, so a stronger reranker had no room to show value.

**Second measurement, LLM-judged graded eval (`docs/ranking-aware-eval-v0.md`) — CE helps:**

| metric | hybrid | hybrid + CE | Δ |
|--------|-------:|------------:|----:|
| MRR | 0.8500 | 0.8750 | **+0.0250** |
| nDCG@10 | 0.7794 | 0.7855 | **+0.0061** |
| Precision@5 | 0.5900 | 0.6200 | **+0.0300** |
| hit@1 rate | 0.8000 | 0.8500 | **+0.0500** |

Once the eval could discriminate, the cross-encoder improved **every** metric. The full stack
compounds: pure-vector → +hybrid → +CE gives hit@1 0.75 → 0.80 → 0.85, nDCG 0.741 → 0.779 → 0.786.
So the cross-encoder *does* improve ranking accuracy — the earlier "no gain" was the metric, not
the method (the same lesson hybrid taught).

## 4. The latency wall — why it stays OFF anyway

End-to-end query latency (median over 5 queries, models warm, this CPU):

| stack | median | vs < 200ms budget |
|-------|-------:|-------------------|
| hybrid only | **60 ms** | well under |
| hybrid + CE | **~6090 ms** | ~30× over the budget, ~100× the cached target |

The cross-encoder runs a transformer forward pass per candidate; on CPU that is ~6 s/query here.
The accuracy gain (nDCG +0.006, hit@1 +0.05) is real but small, and **6 seconds is categorically
disqualifying** for a path with a 200 ms SLA (ExMorbus). So:

**Decision: OFF by default.** Now *justified* as an opt-in (`AAA_CROSS_ENCODER=1`) for offline /
batch / evaluation use where latency doesn't matter — not for the live cached query path.

## 5. What would let it onto the live path (follow-ups)
- **GPU inference** or a much smaller/quantized cross-encoder; re-measure latency.
- **Cap `top_k`** (rerank only the top 5–8) and/or run CE only for low-confidence queries.
- **Async / precompute** for hot queries.
- Note: the graded labels come from an LLM judge (Haiku) — itself a transformer relevance scorer,
  so CE's apparent edge may be mildly inflated by shared inductive bias. Treat the +metrics as
  directional, confirm on a human-spot-checked slice before betting latency budget on it.
