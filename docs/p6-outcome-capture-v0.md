# P6 Outcome Capture — Spec v0

> **Status**: Slices 1 + 2 built and tested (2026-06-29). **Owner**: Brandt (#12).
> Slice 1: AAA *records whether its recommendations were adopted and worked* and
> aggregates that into a per-source signal. Slice 2: that signal now *re-ranks live
> retrieval* in `get_architecture_recommendation` — proven sources lead, failed
> sources sink — behind a minimum-evidence gate. The loop is closed.

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

## 6. Slice 1 boundaries (now extended by Slice 2)

- **Slice 1 applied no ranking change** — `weight_multiplier` was computed and exposed but
  not used. Slice 2 (§7) now applies it, but only past the minimum-evidence gate, so eval
  scores stay stable while the dataset is tiny.
- **No auto-grading** (still holds). Outcomes are human-reported. AAA must not grade its own
  homework (same echo-chamber firewall as the experimental→grounded promotion gate).

## 7. Slice 2 — built 2026-06-29

The signal now drives ranking. Implementation: `src/learning/outcome_weighting.py`
(pure functions) consumed by `get_architecture_recommendation` in
`src/api/mcp_server.py`.

**Which rail.** Outcome events are generated on the MCP recommendation path over the
ChromaDB persona store, and the signal keys on persona/tool *entities* that live in
that store. The `source-weighting-model-v2` rail (`src/api/rest.py`) instead weights
`KnowledgeBase` *source types* and learns from eval-run scores — persona multipliers
do not map onto it. So slice 2 wires the outcome signal into **Rail B (the ChromaDB
recommendation path where the outcomes are actually produced)**, not Rail A's
`RETRIEVAL_SOURCE_WEIGHTS`. See `docs/decision-log.md`.

**How it ranks.** After `store.search()` returns semantic hits and before synthesis,
each hit is re-scored as `relevance × outcome_multiplier`, then re-sorted (stable, so
ties keep relevance order). A hit's multiplier is the **mean** of the applicable
entity multipliers — its author persona plus any matched `mentioned_tools` — each
already bounded to `[0.5, 1.5]` by slice 1, so the combination stays in range and no
single source dominates. The original `score` is preserved; `outcome_multiplier` and
`ranking_score` are attached for audit, and the payload carries an `outcome_weighting`
block (`active`, `gated_personas`, `gated_tools`, `min_evidence`).

**Minimum-evidence gate.** An entity's multiplier only leaves neutral once it has
≥ `MIN_EVIDENCE_DEFAULT` (5) recorded outcomes. Below that the re-rank is an *exact
no-op*. Today's ledger is empty, so weighting is inert until real outcomes accrue —
by design: the mechanism is live and tested now, but it never reshapes retrieval on
noise. Kill-switch: `AAA_OUTCOME_WEIGHTING=0`.

**Proving lift.** The live eval harness scores Rail A and cannot measure this rail, so
lift is proven deterministically instead: `tests/test_outcome_weighting.py::
test_seeded_outcomes_lift_proven_persona_to_top` seeds 5 adopted-and-worked outcomes
for a persona and asserts its lower-relevance hit moves from last to first. When real
outcomes accumulate, compare `active:true` vs `AAA_OUTCOME_WEIGHTING=0` recommendation
ordering on the same problem to observe the production delta.

### Still open (slice 3 candidates)
- Segment-aware outcome multipliers (enterprise vs startup), mirroring v2's segment split.
- Decay so stale outcomes weigh less than recent ones.
- Surface the per-entity track record in the recommendation payload for transparency.
