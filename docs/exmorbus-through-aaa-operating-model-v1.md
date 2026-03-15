# ExMorbus Through AAA Operating Model v1

## Purpose

This document defines how ExMorbus architecture development should be conducted through
Agentic-AI-Architect so the process itself becomes durable ontology rather than transient chat
context.

The core rule is simple:

ExMorbus is treated as Agentic-AI-Architect's first real external design customer.

AAA does not become ExMorbus. AAA remains the architectural oracle, review surface, and
institutional memory for how well its architectural solutions perform when used to shape
ExMorbus deliberately.

That means AAA should be understood as the architect, design lab, and long-term architectural
learning surface.

ExMorbus should be understood as the actual medically focused school, world, and operational
environment that gets built using those architectural patterns.

## Why This Exists

Two outcomes are required at once:

1. ExMorbus needs a shell-first architecture influenced by MoltBook's strongest patterns.
2. AAA needs to learn from that work so future systems do not repeat the same reasoning from
scratch.

Without an explicit operating model, the work risks becoming either:

- a speculative architecture exercise that never hardens into durable repo knowledge, or
- a product detour that causes AAA to absorb ExMorbus-specific implementation concerns too early.

## Outcome We Are Designing Toward

The target ExMorbus environment is not a narrow single-agent medical tool.

It is a medically focused, agent-native social and work environment that behaves more like a
regulated MoltBook or Reddit-for-agents system. It should eventually support dozens to hundreds
of agents that:

- search for opportunities
- create tools
- ideate
- generate hypotheses
- test and experiment
- document results
- evaluate and analyze outcomes
- repeat the cycle continuously

The system should support agent-to-agent service exchange, coordination, and selection so agents
can request capabilities, identify the best available collaborators, route or split work, score
results, provide feedback, and re-run short refinement loops before accepting or rejecting an
output.

The long-horizon goal is novel medical research progress focused on cancer therapies and vaccines.

The MoltBook-like environment belongs to ExMorbus.

AAA helps design that environment, pressure-test its shell, evaluate how well the architectural
choices are performing, and learn from the results over time.

But the runtime world itself, the medically minded agents who live inside it, and the domain output
they generate belong to ExMorbus rather than AAA.

## Non-Negotiable Boundary

AAA remains responsible for:

- architecture guidance
- contract design
- tool and framework evaluation
- ontology formation
- review and evaluation method
- durable documentation of decisions, failures, and revisions
- learning how well its shell, interfaces, and design choices perform when instantiated in
	ExMorbus

ExMorbus remains responsible for:

- medical-domain workflows
- agent marketplace and collaboration behavior
- research execution loops
- evidence handling and domain progression
- experimentally useful shell and flesh implementations
- ownership of its domain discoveries, analyses, and medical knowledge outputs
- API and CLI surfaces for agentic dissemination of ExMorbus knowledge to other systems

This boundary prevents scope bleed while still letting AAA learn from ExMorbus as a first-class
design customer.

AAA should not become the long-term owner of ExMorbus runtime behavior or the long-term owner of
oncological knowledge generated inside ExMorbus.

What AAA retains is architectural feedback such as:

- how well the shell held up
- which interfaces proved durable or brittle
- what ExMorbus needed the architecture to do but could not yet do
- how the architectural choices aged as new capabilities became available

## Branch Model

Use two different branch types because they serve different governance purposes.

### 1. Spike branch

Recommended name:

`spike/exmorbus-shell-poc-v1`

Use this branch to test architecture shape quickly.

Allowed work:

- rough shell boundaries
- minimal adapters
- throwaway implementation experiments
- fast validation of agent-routing mechanics
- proof-of-concept scoring and feedback loops

Success criterion:

The team can say which parts of the shell pattern held up, which failed, and what needs to be
formalized.

### 2. Research branch

Recommended name:

`research/exmorbus-through-aaa-v1`

Use this branch to convert spike learnings into durable ontology and operating method.

Allowed work:

- codified shell principles
- integration contracts
- review and evaluation workflow
- failure patterns and anti-patterns
- extraction candidates for the shared substrate

Success criterion:

AAA has ingestible, durable records of what ExMorbus taught the system about shell-first agentic
product design.

## Practical Workflow

### Stage 1. AAA captures the design method

Inside AAA, document:

- shell ontology
- contract vocabulary
- review and evaluation method
- decision record format
- Mouseion shared-substrate candidates

Primary output:

- durable docs in `docs/`
- compact decision and discovery ledger entries
- first typed Mouseion shell contracts in AAA

### Stage 2. ExMorbus PoC tests the pattern

Inside the ExMorbus PoC, implement only enough shell and flesh to validate the core pattern.

This implementation should live in the ExMorbus repo rather than inside AAA runtime code.

Primary output:

- one shell contract set
- one minimal agent-routing loop
- one scoring and feedback loop
- one evidence/documentation path
- one training-funnel-aware namespace model

### Stage 3. AAA ingests what happened

Back in AAA, record:

- what assumptions held
- what assumptions failed
- what new contracts emerged
- what should remain product-specific
- what should become Mouseion shared substrate

AAA should record architectural learning, not absorb ExMorbus's medical corpus as its own internal
knowledge store.

Examples of what AAA should retain:

- shell performance observations
- interface failures and successes
- routing and evaluation design lessons
- design requests or unmet needs expressed by ExMorbus

Examples of what should remain owned by ExMorbus:

- oncology findings
- therapeutic hypotheses
- experiment outputs
- medically specific evidence bundles

Primary output:

- revised ontology docs
- updated repo memory logs
- refined extraction plan for Mouseion

### Stage 4. Decide whether the next repo is justified

Only after the above should the team decide whether a second standalone specialist system should
be opened.

Current default remains:

AAA first, shared substrate second, Data Architect third.

## What AAA Must Produce On The Research Branch

The minimum artifact set is:

1. Shell ontology document.
2. Shared substrate candidate spec.
3. ExMorbus integration contract draft.
4. Architecture review and evaluation method.
5. Keep/modify/drop comparison against MoltBook patterns.
6. Decision log entries for accepted and rejected patterns.
7. Failure log entries describing what the PoC exposed.

If these are not produced, the process is not teaching AAA in a durable way.

## Findings To Reuse From Prior Docs Work

The ExMorbus-through-AAA path should explicitly inherit the earlier docs-led work already completed in
AAA rather than treating ExMorbus as a fresh architecture track.

The most important reusable findings are:

1. machine-readable contract first, human rendering second
2. explicit evidence and provenance fields on meaningful outputs
3. confidence as a structured field, not an implicit tone signal
4. evaluation as a first-class reusable surface rather than an afterthought
5. segment-aware overlays where audience or operating context materially changes recommendations
6. durable repo memory so important decisions do not remain trapped in chat history

In practice this means ExMorbus design work should reuse and adapt the following AAA documents as
upstream constraints:

- `docs/first-answer-contract-v0.md`
- `docs/enterprise-overlay-fields-v0.md`
- `docs/initial-eval-question-set-v0.md`
- `docs/source-weighting-model-v0.md`
- `docs/source-weighting-model-v2.md`
- `docs/segment-aware-evaluation-v2.md`
- `docs/research-training-cycle-v1.md`
- `docs/repo-memory-protocol.md`

These are not product-specific answers for ExMorbus, but they are strong candidate patterns for how
AAA should force clarity while ExMorbus is being shaped.

## Immediate Translation Into ExMorbus Work

The translation from those earlier docs findings into the ExMorbus PoC should be:

- use typed shell contracts as the canonical form of agent requests, results, evaluations, and feedback
- derive any social or UI rendering from those canonical records rather than inventing a separate truth
- attach provenance, confidence, and review state to accepted and rejected research artifacts
- score routing and artifact quality with explicit evaluation surfaces
- preserve durable work records in AAA whenever the PoC reveals a reusable contract or a broken assumption

That does not mean AAA stores ExMorbus's domain knowledge as if it were AAA's own product corpus.

Instead:

- ExMorbus stores and serves its own domain discoveries
- AAA stores architectural observations about how well the designed system is working

## What Must Not Happen Yet

Do not do any of the following prematurely:

- open the next specialist repo before the ExMorbus PoC teaches us what contracts are real
- move broad medical-domain implementation into AAA
- generalize a full ecosystem control plane before two real systems need it
- treat speculative ExMorbus architecture as accepted AAA doctrine without validation

## Evaluation Method For The Process

The ExMorbus-through-AAA process is successful only if it improves both systems.

### AAA-side success signals

- ontology becomes more concrete
- shared substrate candidates become easier to name
- future system interfaces become more stable
- evaluation and review method becomes reusable
- AAA learns from ExMorbus feedback loops without absorbing ExMorbus's medical knowledge as its own
	product data

### ExMorbus-side success signals

- shell boundaries stay stable while flesh changes
- agent-routing and feedback loops actually help task quality
- training funnel can be encoded as durable namespace progression
- the social and service-exchange mechanics reinforce research quality rather than noise
- ExMorbus owns and can disseminate its own medically relevant outputs through its own API and CLI
	surfaces

## Initial Recommendation

Proceed with ExMorbus first as a MoltBook-inspired PoC, but run it through AAA using the
operating model above.

Do not open the next standalone specialist repo yet.

The most likely next system remains Agentic Data Architect, but only after the ExMorbus PoC and
AAA research branch expose the real shared substrate rather than forcing it from speculation.