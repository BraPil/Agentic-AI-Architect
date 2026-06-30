# Rank-Aware Retrieval Eval — Spec v0

> **Status**: Built and tested (2026-06-30). **Owner**: Brandt (#12).
> Measures retrieval *ordering* quality (MRR, nDCG@k, precision@k, hit@1) so rerankers can be
> judged. Built because `run_eval.py` is structurally blind to ranking; it immediately
> justified enabling hybrid reranking. See `docs/hybrid-ranking-v0.md`.

---

## 1. Why

`scripts/run_eval.py` scores pass/fail presence checks. Two properties make it unable to judge
a reranker (discovery-log 2026-06-30):
- **Saturated pass-rate** — 15/15 already pass, so a better ordering can't raise it.
- **Vector-biased relevance** — its "avg relevance" is the mean top-1 *vector* similarity,
  which can only *fall* under any reorder (a promoted doc has lower vector sim than the
  max-vector doc it displaced). It penalizes reordering and can never credit it.

So "no change" and "improvement" look identical (or improvement looks like regression). A
reranker needs a metric that rewards pulling relevant docs higher.

## 2. The instrument

`src/pipeline/ranking_metrics.py` (pure, stdlib) + `scripts/eval_ranking.py` (runner).

**Metrics** (per question, over the ranked result list, k=10):
- **MRR** — 1 / rank of the first relevant result.
- **nDCG@k** — graded, exponential-gain DCG normalized against the ideal ordering.
- **Precision@5** — fraction of the top 5 that are relevant.
- **hit@1** — is the rank-1 result relevant?

**Label-free graded relevance oracle** — `grade_result(result, question) → 0..3`: +1 per
matched ground-truth signal the question specifies (`must_cite_author`, `expected_tools`,
`expected_topics`). No manual per-document judgments: it reuses fields the ground truth already
carries, so the instrument exists today and stays in sync with the question set. A result is
relevant at grade ≥ 1.

## 3. Usage

```bash
# Score current ordering
python3 scripts/eval_ranking.py

# A/B a reranker
AAA_HYBRID_RANKING=0 python3 scripts/eval_ranking.py --output data/rank_off.json
AAA_HYBRID_RANKING=1 python3 scripts/eval_ranking.py --output data/rank_on.json
python3 scripts/eval_ranking.py --compare data/rank_off.json data/rank_on.json
```

Tests: `tests/test_ranking_metrics.py` (17 — metrics + oracle, all deterministic).

## 4. Question set

20 search questions. eval-016..020 (added 2026-06-30) are **exact-term/keyword** cases — rare
tokens a dense embedding tends to smooth away — chosen by mining the corpus for distinctive
low-document-frequency terms and verifying each against the indexed docs:

| id | exact term(s) | owner | min_rel |
|----|---------------|-------|--------:|
| eval-016 | BIG-Bench | Sebastian Ruder | 0.35 |
| eval-017 | AGENTS.md | (multiple) | 0.40 |
| eval-018 | adversarial attacks / jailbreaking | Lilian Weng | 0.35 |
| eval-019 | llmfit | Stanislav Beliaev | 0.30 |
| eval-020 | AWQ / GPTQ / vLLM | Mitko Vasilev | 0.15 |

All 20 keep `run_eval.py` green (20/20). On this expanded set the hybrid A/B re-confirmed the
win: MRR 0.925→1.000, nDCG@10 0.889→0.957, P@5 0.870→0.910, hit@1 0.850→1.000.

## 5. Integration

`run_eval.py` now computes these metrics from the results it already fetches and prints a
`Ranking — MRR … nDCG@k … P@5 … hit@1 …` line alongside the pass-rate, persisting them under
`ranking` in `eval_results.json`. So every eval run tracks ordering quality, guarding against
regressions the pass/fail checks can't see — no extra queries, no separate invocation needed.
`scripts/eval_ranking.py` remains for A/B work (`--compare`, env toggles).

## 6. Limitations / follow-ups
- The oracle is binary-ish per signal (substring match); it cannot grade *partial* topical
  relevance beyond presence. Adequate for ordering comparison, not absolute quality.
- Grow the set further as the corpus grows; keep adding exact-term cases.
- Track the `ranking` block over time / fail CI on a material drop.
