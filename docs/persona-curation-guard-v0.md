# Persona Curation Guard — Spec v0

> **Status**: Built and tested (2026-06-30). **Owner**: Brandt (#12).
> Bars non-practitioner personas from the persona store at the `ingest()` chokepoint, so a
> pruned persona can never be silently re-added by a later LinkedIn reactions scrape.

---

## 1. Why

The standing curation rule is that the store holds **only AI/tech practitioners**.
Personal-contact and job-announcement personas — people the reactor (Brandt) knows but who
do not post AI/tech content — are pruned.

The recurring failure: pruning removed those personas from ChromaDB but **nothing barred
re-entry**. The same off-standard class was pruned in **April 2026** (ANS, Alex Dobrenko,
Jeneé O., Karen Robes Meeks, Alex Arend) and **re-appeared in June 2026** (kyle-faust,
paul-northrup-pe, matt-luke, anthony-smith-mba-sta) via the June reactions scrape. Manual
re-pruning each cycle is not a fix — it is the same work forever.

Worse, the June prune was itself **incomplete**: when the guard went live on 2026-06-30 it
found `kyle-faust` and `anthony-smith-mba-sta` still in the 417-item snapshot. The guard
caught the bug it was built to prevent, on its first run.

## 2. The guard

```
LinkedIn reactions scrape → process_linkedin_export.py → store.ingest(record)
                                                              │
                                          curation.is_blocked(persona_id)?
                                              ├─ yes → log WARNING, return False (skip)
                                              └─ no  → index as normal
```

Enforced **at the store layer** (`LinkedInPersonaStore.ingest()`), not in any one ingest
script — so every ingest path (the export processor, the PDF ingest, the weekly refresh,
any future one) inherits the bar. This is the same lesson as the `source_tier` /
`include_experimental` quarantine: *enforce trust/curation boundaries at the lowest shared
data layer, never at one caller.* (See `docs/lessons-learned-log.md`, 2026-06-28.)

## 3. Data model

One JSON denylist, `data/curation_denylist.json` (the source of truth):

```json
{
  "schema_version": "1.0",
  "blocked_personas": [
    {"persona_id": "kyle-faust", "reason": "...", "blocked_at": "2026-06-30"}
  ]
}
```

- `persona_id` is the author slug (`persona_slug("Kyle Faust") → "kyle-faust"`).
- Entries are sorted by `persona_id` on save for stable diffs.
- A missing or malformed file makes the guard **inert** (blocks nothing) — the safe default
  for fresh checkouts and tests.

## 4. Surfaces

| Surface | Entry point |
|---------|-------------|
| Core (pure) | `src/pipeline/curation.py` (`PersonaCurationList`, `CurationEntry`) |
| Enforcement | `LinkedInPersonaStore.ingest()` — skips barred personas; `store.curation` exposes the list |
| Prune + bar (one act) | `scripts/prune_persona.py --persona <id> --reason "..."` — deletes from store **and** bars |
| Inspect | `scripts/prune_persona.py --list` |
| Kill-switch | `AAA_PERSONA_CURATION=0` (env) makes the guard inert |
| Tests | `tests/test_curation.py` (13 tests, no network/keys/ChromaDB) |

## 5. Prune-and-bar is one act

The root cause was that deletion and barring were separate (only deletion happened).
`scripts/prune_persona.py` does both atomically: it removes the persona's posts via
`store.prune_persona(persona_id)` **and** writes the persona to the denylist. After a prune,
re-export the snapshot (`scripts/export_chromadb_snapshot.py`) so the deletion persists.

## 6. Design choices

- **Denylist over a topical/LLM classifier.** A persistent denylist is exact, deterministic,
  auditable, and zero-cost; it precisely fixes the observed bug (pruned → re-added). A topic
  heuristic risks false-negatives (dropping a real practitioner whose one captured post is
  off-topic). A classifier can be layered on later as an *additional* signal; the denylist is
  the floor.
- **Inert by default.** Missing file, malformed file, or `AAA_PERSONA_CURATION=0` → blocks
  nothing. The guard can never cause a silent corpus loss it wasn't explicitly told to.
- **Small blast radius.** One new pure module, one seed file, one guard clause, one helper
  method on the store, one CLI. No change to search, ranking, or any existing test.

## 7. Still open (v1 candidates)

- Ingest-time topical classifier as a *second* signal that flags likely non-practitioners for
  human review (suggest, never auto-bar — same human-gate discipline as the promotion gate).
- A periodic audit that re-checks the live store against the denylist and reports drift
  (the 2026-06-30 manual check, automated).
