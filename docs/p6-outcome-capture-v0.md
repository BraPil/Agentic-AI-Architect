# P6 Outcome Capture — Spec v0

> **Status**: Slice 1 built and tested (2026-06-29). **Owner**: Brandt (#12).
> The first half of true P6 learning: AAA now *records whether its recommendations
> were adopted and worked*, and aggregates that into a per-source signal. Wiring the
> signal into live retrieval ranking is **Slice 2** (deliberately deferred).

---

## 1. Why

The discovery log (2026-06-28) established the gap: AAA **records and retrieves** its
memory but does not **learn from outcomes**. Indexing the decision/discovery/lesson logs
into ChromaDB made internal memory *searchable* — a retrieval prerequisite — but a
recommendation that was followed and failed looked identical to one that was followed and
succeeded. Nothing fed real-world results back into how AAA weights its sources.

This slice closes the capture side of that loop. It is intentionally scoped so the
*measurement* exists and is trustworthy before any *behavior change* rides on it.

## 2. The loop

```
get_architecture_recommendation(problem)
    → stamps recommendation_id, logs a `recommendation` event   (automatic)
        → human acts on it in the real world
            → record_recommendation_outcome(id, adopted, worked, score?)   (human, MCP/CLI)
                → get_outcome_summary()  → adoption/success rates + per-source signal
                    → [Slice 2] retrieval ranking weights sources by that signal
```

## 3. Data model

One append-only JSONL ledger, `data/recommendation_outcomes.jsonl`, two event types
(mirrors the `PromotionGate` audit pattern; the ledger is the source of truth, replayed
on read):

| Event | Fields |
|-------|--------|
| `recommendation` | recommendation_id, problem_statement, personas_cited, tools, confidence, ts |
| `outcome` | recommendation_id, adopted, worked, outcome_score, notes, recorded_by, ts |

- **recommendation_id** = `rec-{md5(problem|generated_at)[:16]}` — per-instance (same
  question asked twice → two gradable recommendations).
- **success** ≡ `adopted AND worked`. "Adopted but didn't work" is a distinct, valuable
  negative signal — not the same as "ignored".
- **Last outcome wins** — an outcome can be corrected by re-recording it.
- An outcome for an unknown id is **rejected** (you can only grade what AAA emitted).

## 4. The signal

`aggregate()` rolls the ledger into:
- Overall `adoption_rate`, `success_rate`, `mean_outcome_score`.
- `persona_signal` and `tool_signal`: per-entity `{recommended, worked, success_rate,
  weight_multiplier}`.

**weight_multiplier** uses Laplace smoothing — `(worked + 1) / (recommended + 2)` mapped
onto `[0.5, 1.5]`. With zero data the multiplier is the neutral midpoint (1.0-ish); one
outcome nudges rather than dictates. This is small-data honesty: a single failure must not
zero out a source's weight.

## 5. Surfaces

| Surface | Entry point |
|---------|-------------|
| Automatic stamping | `get_architecture_recommendation` returns `recommendation_id` + `outcome_hint` |
| MCP — record | `record_recommendation_outcome(id, adopted, worked, outcome_score, notes)` |
| MCP — inspect | `get_outcome_summary()` |
| CLI | `scripts/record_outcome.py <id> --adopted --worked --score …` / `--summary` / `--pending` |
| Core | `src/learning/outcomes.py` (`RecommendationOutcomeStore`, `OutcomeRecord`) |
| Tests | `tests/test_outcomes.py` (14 tests, no network/keys) |

## 6. Explicitly NOT in this slice (Slice 2)

- **No ranking change.** `weight_multiplier` is computed and exposed but **not** applied to
  retrieval/eval. The store does not touch ChromaDB. This keeps eval scores stable while
  the dataset is tiny.
- **No auto-grading.** Outcomes are human-reported. AAA must not grade its own homework
  (same echo-chamber firewall principle as the experimental→grounded promotion gate).

## 7. Slice 2 (next)

1. Feed `persona_signal` / `tool_signal` multipliers into the source-weighting model
   (`docs/source-weighting-model-v2.md`) so retrieval ranking reflects what actually worked.
2. Add a minimum-evidence threshold (e.g. ≥5 outcomes for an entity) before its multiplier
   leaves neutral, so ranking only moves on real signal.
3. Track eval relevance before/after to prove the weighting helps, not hurts.
