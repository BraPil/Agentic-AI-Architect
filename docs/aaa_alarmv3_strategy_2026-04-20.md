# AAA + ALARMv3 Strategy Notes — 2026-04-20

## Purpose

This document captures the planning discussion about how `BraPil/Agentic-AI-Architect` (AAA) and `BraPil/ALARMv3` should evolve together, with a strong focus on:

- using AAA to guide ALARMv3 development
- deciding whether ALARMv3 should become MCP-first
- defining a Codespaces-native workflow
- defining how AAA should support influencer/persona analogs
- clarifying how Claude Code should be used to build all of this

---

## 1. Initial conclusion: how AAA should help develop ALARMv3

The initial recommendation was:

- run `Agentic-AI-Architect` as a separate service/process
- keep `ALARMv3` as the active coding workspace
- let ALARMv3 consume AAA over REST initially
- later consider MCP surfaces once the core contracts stabilize

At that point, ALARMv3 was understood as still being in a planning/research state, while AAA already had the shape of a standalone advisory system with orchestrator, specialized agents, knowledge base, and REST API.

### Key idea
AAA should act as:
- architectural oracle
- planning advisor
- knowledge/advisory backend
- future persona/chorus system

---

## 2. ALARMv3 direction: should it be an MCP?

The recommendation evolved toward:

- **Yes, ALARMv3 should likely become MCP-capable**
- **Yes, going MCP-first for v3 can make sense**
- **But ALARMv3 should not be only an MCP wrapper**
- it still needs a real core engine underneath

### Recommended shape
ALARMv3 should have:

1. **Core Engine**
   - codebase discovery
   - architecture mapping
   - dependency crawling
   - analysis
   - recommendation generation
   - transformation/orchestration

2. **MCP Interface**
   - attach to active workspace
   - expose tools/resources/prompts
   - run guided workflows inside Codespaces

3. **Adapters**
   - local filesystem adapter
   - git/sibling repo adapter
   - local artifact sink
   - future SharePoint sync adapter
   - future AAA advisory adapter

### Important principle
MCP should be the **interaction surface**, not the whole product.

---

## 3. ALARMv3 envisioned workflow

The intended ALARMv3 v3 user experience was described as follows:

### Phase A — Attach to legacy app workspace
A user opens a GitHub Codespace on a legacy application repository.

ALARM MCP should:
- identify the current workspace/repo
- determine the codebase in focus
- confirm with the user what the target repo is
- confirm archive/reference behavior
- set guardrails to preserve the source repo as untouched reference

### Phase B — Recursive discovery and architectural mapping
ALARM should:
- ingest the README and launcher(s)
- identify functions, dependencies, entrypoints, and code relationships
- recursively traverse dependent files/modules
- fan work out in parallel
- map/document the full structure of the application
- produce architecture maps and knowledge artifacts
- build indexed knowledge and embeddings

### Phase C — Full analysis
ALARM should then:
- perform security analysis
- identify version issues
- identify functionality/integration issues
- detect modernization opportunities
- produce prioritized recommendations for improvements/upgrades

### Phase D — Transformation mode
After presenting recommendations, ALARM should:
- ask the user which improvements to implement
- create a separate target repo/workspace
- build the improved/new version there
- test and simulate it
- generate documentation for the updated version too

---

## 4. Critical safety/quality corrections to the vision

A major refinement to the vision was:

### Do not claim unverifiable “100.000% understanding”
Instead, ALARM should aim for **exhaustive, auditable coverage** and report coverage explicitly.

Recommended reporting:
- files discovered
- files parsed
- files skipped/unparseable
- unresolved references
- confidence by subsystem
- coverage exceptions
- uncertain/incomplete areas

### Approval boundaries are required
Before destructive or generative steps, ALARM must require explicit user approval for:
- creating target repo/workspace
- implementation work
- dependency upgrades
- destructive transforms
- PR creation/integration actions

---

## 5. Recommended ALARMv3 architecture

### 5.1 Core internal components

Recommended major components:

- **Workspace Manager**
  - identify repo/workspace
  - normalize paths
  - determine source/artifact/target boundaries

- **Guardrail Manager**
  - preserve source repo immutability
  - define write boundaries
  - manage approvals and policy

- **Discovery Engine**
  - read root docs/configs/launchers
  - identify languages and entrypoints
  - create recursive traversal queue

- **Swarm Orchestrator**
  - coordinate bounded parallel workers
  - maintain visited graph
  - deduplicate tasks
  - checkpoint progress

- **Knowledge + Index Layer**
  - file inventory
  - symbol graph
  - dependency graph
  - architecture notes
  - chunks/embeddings
  - findings/recommendations

- **Analysis Engine**
  - security heuristics
  - version/dependency analysis
  - integration analysis
  - architecture risk analysis

- **Recommendation Engine**
  - prioritize improvements
  - estimate effort/risk/impact
  - produce actionable plans

- **Transformation Engine**
  - create separate modernization workspace
  - implement selected changes
  - validate/test
  - document new version

- **Sync Adapter Layer**
  - local-first initially
  - SharePoint later

### 5.2 Orchestration model
The discussion strongly recommended:

- **bounded queue/workers**
- **durable orchestration**
- **checkpointing**
- **deterministic fan-out**

and explicitly advised against:
- unconstrained self-cloning agent swarms

The “swarm” should feel swarm-like conceptually, but implementation should really be:
- orchestrator
- queue
- worker pools
- dependency-aware scheduling

### 5.3 Repo role separation
ALARMv3 should distinguish:

1. **Source repo**
   - legacy app
   - read-only/reference/archive

2. **Artifact repo/path**
   - generated knowledge artifacts, maps, indexes, docs

3. **Target modernization repo**
   - writable upgraded implementation workspace

This separation is foundational.

---

## 6. Storage strategy

### Initial recommendation
Start local-first:
- filesystem artifacts
- SQLite or similar relational metadata store
- local vector index

### Later evolution
Move toward:
- Postgres
- pgvector
- SharePoint sync
- externalized artifact destinations

### Output layout suggestion
Suggested local artifact shape:

```text
.alarm/
  sessions/
    <session-id>/
      manifest.json
      approvals.json
      progress.json
      inventory/
      architecture/
      knowledge/
      analysis/
      transformation/
```

A sibling artifact repo was also considered a strong option.

---

## 7. Recommended MCP surface for ALARMv3

ALARMv3 was recommended to expose a focused set of MCP tools/resources.

### Suggested tool groups

#### Session / workspace
- `attach_workspace`
- `inspect_workspace`
- `confirm_guardrails`
- `get_session_status`

#### Discovery / mapping
- `discover_codebase`
- `map_architecture`
- `trace_entrypoints`
- `inventory_dependencies`
- `analyze_subsystem`

#### Knowledge / artifacts
- `build_knowledge_base`
- `export_documentation`
- `list_generated_artifacts`

#### Analysis / recommendations
- `analyze_risks`
- `find_modernization_opportunities`
- `prioritize_recommendations`

#### Implementation
- `plan_upgrade`
- `create_target_workspace`
- `implement_selected_changes`
- `run_validation`
- `generate_upgrade_compendium`

#### Governance / safety
- `show_guardrails`
- `approve_phase`
- `abort_run`

### Suggested resources
Examples proposed:
- `alarm://session/current`
- `alarm://workspace/inventory`
- `alarm://architecture/graph`
- `alarm://analysis/findings`
- `alarm://analysis/recommendations`
- `alarm://execution/progress`

---

## 8. Recommended phased implementation plan for ALARMv3

### Phase 1
Safe attach + discovery:
- workspace detection
- archive confirmation
- guardrails
- README/launcher ingestion
- basic artifact output

### Phase 2
Recursive graph mapping:
- parser pipeline
- dependency resolution
- symbol extraction
- parallel traversal
- coverage accounting

### Phase 3
Knowledge + retrieval:
- chunking
- embedding/indexing
- local search/query
- compendium generation

### Phase 4
Analysis + prioritization:
- security/version/integration checks
- modernization heuristics
- recommendation ranking

### Phase 5
Transformation mode:
- create separate target repo
- implement selected changes
- validate/test
- generate upgraded documentation

### Phase 6
External integrations:
- SharePoint sync adapter
- AAA advisor integration
- PR/issue handoff adapters

---

## 9. AAA direction: influencer/persona analogs

The later part of the conversation turned to AAA itself and how it should model influential voices such as:
- Andrej Karpathy
- Cole Medin
- Alex Wang
- Yann LeCun
- and others

### Key conclusion
Do **not** create 20 standalone cloned bot systems.

Instead, build them **inside AAA**.

### Why
A single AAA system should provide:
- one ingestion pipeline
- one shared knowledge base
- one source weighting model
- one orchestrator
- one MCP/API surface
- on-demand persona instantiation

### Better pattern
Inside AAA, build:
- persona/source profiles
- source-grounded viewpoint agents
- panel/consensus/chorus synthesis

### Recommended AAA additions
Suggested additions included:

- `src/personas/`
  - `registry.py`
  - `models.py`
  - `profiles/*.yaml`

- `src/agents/`
  - `persona_agent.py`
  - `panel_agent.py`
  - `consensus_agent.py`

### Conceptual distinction
These should not pretend to be the real people.

They should be:
- source-grounded approximations of their public views
- freshness-aware
- provenance-aware
- confidence-scored
- able to say “insufficient evidence”

---

## 10. AAA as unified persona/chorus system

The recommended AAA design was:

### Shared infrastructure
Common ingestion and storage for:
- YouTube
- GitHub
- LinkedIn/manual imports
- articles/interviews/posts
- trend extraction
- embeddings
- provenance

### Persona layer
Each person gets:
- source registry
- weighting rules
- topical focus
- trust/freshness rules
- synthesis constraints

### Analog layer
On-demand internal persona agents such as:
- `ColeAnalogAgent`
- `KarpathyAnalogAgent`
- `WangAnalogAgent`

### Group reasoning layer
AAA should also support:
- individual guidance
- small-panel discussion
- consensus view
- disagreement maps
- full chorus recommendations

---

## 11. AAA MCP possibilities

AAA was seen as a strong MCP candidate for the persona system.

Suggested future tools:
- `ask_persona`
- `compare_personas`
- `get_consensus`
- `explain_disagreement`
- `list_recent_influencer_updates`
- `refresh_persona_sources`

Important note:
- these should not boot 20 full always-on services
- they should instantiate needed persona logic on demand against the shared KB

---

## 12. Claude Skills / Routines / groups / Co-work discussion

A question was raised about whether to use:
- Claude Skills
- Claude Routines
- Claude groups
- Claude Co-work / Cowork

### Recommendation
The strongest recommendation was:
- center the architecture around **AAA itself**
- consider Skills as a packaging mechanism for reusable expertise/workflows
- do not hinge the architecture on uncertain or loosely defined feature names unless verified
- do not use Cowork as the primary substrate for the AAA/Codespaces system

### Why
The system being designed is:
- repository-native
- orchestration-heavy
- Codespaces-centered
- MCP/API oriented

That is a better fit for AAA + MCP + integrated coding workflows than a desktop-centric knowledge-work product surface.

---

## 13. Claude Code workflow recommendations

A substantial part of the discussion clarified how to use Claude Code effectively in a GitHub Codespace.

### Main recommendation
Use **both** IDE and terminal workflows, but default to:

- **Claude Code panel** for planning, edits, and design
- **integrated terminal(s)** for runtime, tests, jobs, and optionally terminal-based Claude sessions

### Recommended mental model

#### Claude panel
Use for:
- architecture discussion
- local code changes
- reviewing diffs
- planning/refactoring
- scaffolding modules

#### Runtime terminal
Use for:
- running `uvicorn`
- running APIs/servers
- monitoring live logs

#### Validation terminal
Use for:
- `pytest`
- checks
- verification

#### Jobs terminal
Use for:
- ingestion
- crawling
- indexing
- long-running scripts
- queue workers

#### Optional Claude terminal
Use for:
- terminal-native `claude` sessions
- shell-centric coding loops
- power-user workflows

### Important clarification
“orchestration terminal” and “validation/background jobs terminal” are both terminal-based, but they serve different roles:

- orchestration/interactive work = active control or Claude loop
- validation/background work = execution, jobs, checks, workers

These can be consolidated early, but separation becomes more valuable as complexity grows.

---

## 14. Beginner Codespace setup for AAA

Recommended day-to-day setup in the AAA Codespace:

### Keep open
- Claude Code panel

### Integrated terminals
1. **runtime**
   - API server / uvicorn

2. **validate**
   - tests / pytest

3. **jobs**
   - ingestion / crawling / indexing / scripts

4. **optional: claude**
   - terminal Claude session

This was recommended as the cleanest way to learn and scale the workflow.

---

## 15. Broad strategic summary

### ALARMv3
ALARMv3 should likely become:
- MCP-first in UX
- core-engine-first internally
- safety/guardrail heavy
- local-first in storage
- explicit in coverage reporting
- approval-gated before implementation actions

### AAA
AAA should become:
- the architectural oracle
- a shared persona/chorus system
- a source-grounded influencer intelligence platform
- a reusable knowledge/advisory backend for ALARM and similar systems

### Relationship between AAA and ALARM
AAA should advise and enrich ALARM, while ALARM focuses on:
- legacy code understanding
- architecture mapping
- modernization analysis
- transformation execution in isolated workspaces

---

## 16. Immediate next steps suggested by the conversation

### For ALARMv3
- define exact MCP tools/resources/prompts
- define repo/file structure for v3 implementation
- define local artifact/storage contracts
- define guardrail contract and approval model

### For AAA
- define persona registry schema
- absorb ColeBot pattern into AAA
- define first influencer/source profiles
- define panel/consensus/chorus interaction model
- define MCP/API surfaces for persona queries

### For workflow
- use the AAA Codespace with:
  - panel
  - runtime terminal
  - validate terminal
  - jobs terminal
- begin architecture work in AAA first

---

## Final distilled principle

Build:
- **AAA as the architectural intelligence and persona/chorus system**
- **ALARMv3 as the MCP-first legacy modernization orchestration system**
- and connect them through clean interfaces rather than ad hoc duplication.
