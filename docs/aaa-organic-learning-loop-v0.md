# AAA Organic Learning Loop — Integration Spec v0

> How `BraPil/Organic_Agentic_AutoDev` (OAA) becomes AAA's P6 self-improvement engine:
> a living, regulated MoltBook where AAA's personas live, research, critique, and build for
> each other — closing the learning loop that retrieval alone cannot.
>
> **Status**: Proposed (awaiting build approval). **Date**: 2026-06-28. **Owner**: Brandt (#12).
> **Scope chosen**: (B) close the learning loop first, then expand. Not (A) full live economy.

---

## 1. Context

Two turns ago we found AAA *records and retrieves* its memory but does not *learn from outcomes*
— the P6 learning loop was unbuilt (see `discovery-log` 2026-06-28). OAA is the concrete
mechanism for that loop. This spec defines the integration without triggering the #1 risk in the
discovery log: overbuilding the ecosystem before one trustworthy product exists.

## 2. What OAA provides (ingested 2026-06-28)

- **Bio-mimicry ecosystem**: StemCell → Cell → Organ → Body; 8-trait genome; slime-mold adaptive
  topology; consequence-driven economy (conserved resource pools, niche job board, fitness
  selection, reproduction, death).
- **Working Mouseion runtime** (`src/mouseion/substrate.py` + `contracts.py`): event bus,
  resource pools, `KnowledgeRecordV0` (provenance, confidence, content_hash, review_history),
  niche registry. This is the runtime AAA only has as contract candidates.
- **Multi-domain seam**: `src/domain/exmorbus/` already exists (oncology roles). An `aaa` domain
  fits the same pattern.
- **Honest gap**: OAA is a *dynamics simulator*. Agents differentiate/cluster/evolve on abstract
  energy/signal; they do **not** call LLMs or perform real research yet
  (`[ ] LLM-backed agent cognition` is unchecked). The cognition bridge is the substantive work.

## 3. The mapping (AAA ↔ OAA)

| AAA concept | OAA mechanism |
|---|---|
| 56 indexed personas + board of governors | Cells with genomes derived from persona traits |
| An architecture question (eval set or user) | A `NicheAdvertisementV0` posted to the registry |
| Grounded corpus (ChromaDB, 179 items) | DATA / KNOWLEDGE resource pool agents draw from |
| Adversarial board critique | Critic-role cells; low-fitness artifacts discarded |
| AAA's recommendation | Body synthesis → `KnowledgeRecordV0` |
| "Did the advice work?" | Fitness function → keep/discard (autoresearch principle) |
| The learning | Human-gated promotion of high-confidence artifacts into the corpus |

## 4. The three-tier provenance model (the regulation)

Extends the `source_tier` built on 2026-06-28 (`external`, `internal`) with a third tier:

| Tier | Meaning | In search | In trends | In synthesis |
|------|---------|-----------|-----------|--------------|
| `external` | Thought-leader content (Karpathy, Weng…) | Yes | Yes | Cited as authority |
| `internal` | AAA's own human-written decisions/lessons | Yes | No | Institutional memory |
| `experimental` | **Agent/persona-GENERATED artifacts** | Quarantined* | No | Never cited; labeled experimental |

\* Quarantined = retrievable only via an explicit `include_experimental=true` flag; never surfaced
as fact, never counted in `get_trending_tools`, never placed in `personas_cited`.

**Promotion** `experimental → grounded` requires **confidence ≥ threshold AND human approval**.
This is the echo-chamber firewall — the compounding version of the source-tier defense already in
place. Without it, personas retrain on their own synthetic output and confidence looks earned but
isn't.

## 5. The bounded, regulated cycle

```
1. SEED      Instantiate OAA Environment; register N personas as StemCells
             (genome from persona traits); post the question as a Niche.
2. RUN       Bounded ticks (energy budget = cost/compute cap). Cells differentiate
             (Researcher / Critic / Synthesizer), draw from grounded corpus,
             run LLM-backed research [COGNITION BRIDGE — new], produce
             KnowledgeRecordV0 (provenance + confidence + review_history).
3. CRITIQUE  Critic cells score artifacts adversarially; low fitness discarded.
4. SYNTHESIZE Body produces the candidate answer.
5. HARVEST   Write artifacts to ChromaDB as source_tier=experimental,
             post_type=learning_artifact.
6. GATE      Confidence + human approval to promote. Promoted knowledge improves
             future answers → loop closed.
```

**Regulation summary** ("living *regulated* MoltBook"):
- Bounded energy budget = bounded cost/compute (no runaway).
- Experimental-tier quarantine (no echo chamber).
- Human-gated promotion (approval-gated generative action — matches Brandt's values).
- `sanitize_text()` on all content (OAA already enforces this).
- Confidence gating + `review_history` provenance discipline.

## 6. Mouseion convergence decision

Two Mouseion v0s now exist and overlap (fork risk):
- OAA `src/mouseion/` — working **runtime** (event bus, resource pools, substrate).
- AAA `src/contracts/mouseion.py` — **review/evaluation contracts** (`ReviewState`,
  `CriterionScore`) that OAA lacks.

**Decision**: converge, do not fork further. OAA's runtime is the reference *runtime*; AAA's
review/evaluation contracts feed the promotion gate. AAA depends on OAA's `mouseion` package for
runtime; OAA adopts AAA's `ReviewState`/`CriterionScore` for promotion review. AAA running this
loop **dogfoods and validates the shared substrate before ExMorbus bets on it.**

## 7. Ownership reconciliation

The ownership matrix says ExMorbus owns its MoltBook environment; AAA is the architect/oracle.
This loop does **not** violate that: AAA's loop operates on AAA's *own* domain (architecture
intelligence) to improve AAA's recommendations — dogfooding, not AAA becoming a general platform.
OAA is the shared bio-mimicry engine both AAA and ExMorbus use (OAA already has
`src/domain/exmorbus/`; AAA gets an `aaa` domain or seeds OAA externally).
**AAA = architect. OAA = the engine/substrate. ExMorbus = medical domain.**

## 8. Build slices

| Slice | What | Status | Value |
|-------|------|--------|-------|
| **0** | `experimental`/`grounded` tiers in search/trends/synthesis; `PromotionGate`; 4 MCP tools; CLI | ✅ DONE (2026-06-28) | Regulation firewall in place before any agent output exists |
| **1** | Harvester (KnowledgeRecordV0 JSONL → ChromaDB experimental); persona→genome seeder; deterministic fixture | ✅ DONE (2026-06-28) | Plumbing + tier model proven end-to-end (22 tests; live ChromaDB verified) |
| **2** | Cognition bridge: Cell research step → real LLM calls grounded in AAA corpus | ⬜ NEXT (belongs in OAA) | The actual learning; produces real artifacts |
| **3** | Promotion eval: does a promoted artifact raise AAA's eval score? | ⬜ After slice 2 | Proves the loop *changes AAA's answers* |
| **4** | Policy-based auto-promotion (approve policies, not artifacts); then expand toward (A) | ⬜ Gated on slice 3 | Full living regulated MoltBook |

**Slices 0–1 shipped.** Regulation + plumbing are live and tested against OAA's real
`KnowledgeRecordV0` shape. The loop is: harvest → quarantine (`experimental`) → human gate →
`grounded`. What remains for real value is the cognition bridge (slice 2).

### Integration constraint discovered (2026-06-28)

OAA packages itself as top-level `src/` (`[tool.setuptools.packages.find] include = ["src*"]`)
and has no console entry point. Pip-installing it **collides with AAA's own `src/`**. Therefore
the integration is **process isolation** (which matches the agreed boundary anyway): OAA runs in
its own process and emits a `KnowledgeRecordV0` JSONL artifact file; AAA harvests the file. No
Python-level import. Before slice 2's live run, OAA should either rename its package
(`src` → `organic_agentic_autodev`) or expose a CLI entry point.

## 9. Open decisions for Brandt

1. Dependency mechanism: pip-from-git / git submodule / vendored subset of OAA?
2. Where does the cognition bridge (slice 2) live — in OAA, or an AAA-side bridge layer?
3. Promotion approval surface: MCP tool, CLI command, or REST endpoint?
