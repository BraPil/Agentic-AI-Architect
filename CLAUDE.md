# CLAUDE.md — Agentic AI Architect System

> **This file is the single source of truth for every AI coding assistant working on this repository.**
> Read it fully before touching any file. Update it when decisions change.

---

## 0. Mission

We are building the **world's standard for an agentic AI architectural intelligence system** — a self-improving, multi-agent ecosystem that continuously discovers, tracks, synthesises, and documents everything an AI Architect needs to know. The system is designed to operate both as a standalone intelligence endpoint and as a composable module inside larger agentic orchestrations.

This is a Python project. Every line of code you write should move us measurably closer to the vision described in [`docs/phase-5-implementation-plan.md`](docs/phase-5-implementation-plan.md).

---

## 1. How to Read This File

| Section | What It Governs |
|---------|----------------|
| §2 Architecture | Where things live and why |
| §3 Development Principles | The non-negotiable rules |
| §4 Code Standards | Python style, patterns, file conventions |
| §5 Testing | What to test, how to test it |
| §6 Security | Rules that are never bent |
| §7 The Five Phases | Current state, next steps |
| §8 Agent Contract | The BaseAgent interface every agent obeys |
| §9 Anti-Patterns | What NOT to do |
| §10 Workflow | How to work session-to-session |
| §11 Context & State | Managing long coding sessions |

---

## 2. Architecture at a Glance

```
src/
├── agents/          ← atomic agents (one responsibility each)
│   ├── base_agent.py          ← abstract contract ALL agents implement
│   ├── crawler_agent.py       ← fetches external content
│   ├── research_agent.py      ← classifies + extracts knowledge
│   ├── trend_tracker_agent.py ← scores + alerts on trends
│   ├── tool_discovery_agent.py← tracks AI tools landscape
│   ├── documentation_agent.py ← generates structured markdown
│   └── orchestrator.py        ← coordinates agents, CLI entry point
├── knowledge/       ← storage layer
│   ├── knowledge_base.py      ← SQLite structured store (namespaced)
│   └── vector_store.py        ← FAISS / sentence-transformers / TF-IDF
├── pipeline/        ← data flow components
│   ├── ingestion.py           ← URL → KnowledgeBase end-to-end
│   └── processing.py          ← clean, chunk, deduplicate content
└── utils/
    └── helpers.py             ← sanitize_text, chunk_text, retry_with_backoff, rate_limit

config/
└── settings.py      ← all settings via env vars (AAA_ prefix)

docs/
├── phase-1-education.md          ← AI Architect roles + influential figures
├── phase-2-conceptual-frameworks.md ← complete framework matrix
├── phase-3-trends.md             ← scored trend registry
├── phase-4-tools.md              ← tools landscape
├── phase-5-implementation-plan.md← phased dev roadmap + branch structure
└── exmorbus-v3-integration.md    ← ExMorbus V3 integration: MoltBook synthesis, API contracts, vision

tests/               ← mirrors src/ structure
```

**Data flow for one intelligence cycle:**
```
CrawlerAgent
  ↓ raw documents (list[dict])
ResearchAgent
  ↓ findings (list[ResearchFinding.to_dict()])
TrendTrackerAgent ←─┐ (parallel)
ToolDiscoveryAgent ←┘
  ↓ trend_data + tool_data + findings
DocumentationAgent
  ↓ generated markdown documents
KnowledgeBase ← entries persisted throughout
```

---

## 3. Development Principles

These are **non-negotiable**. Every PR must satisfy all of them.

### P1 — Atomic Agents
Each agent in `src/agents/` does **exactly one thing**. If you find yourself adding a second responsibility to an existing agent, create a new agent instead. The `Orchestrator` is the only agent that coordinates others — all others are pure specialists.

### P2 — Observable by Default
Every significant action is logged. Use `self.logger` (provided by `BaseAgent`), not `print()`. Log format: `"AgentName doing X: detail"`. Use `INFO` for normal flow, `WARNING` for recoverable issues, `ERROR` for failures.

### P3 — Contract Before Implementation
Before writing a new agent, define its:
- Input type (what does `_execute(task_input)` receive?)
- Output type (what does it return?)
- Failure modes (what exceptions can it raise? how does it recover?)

Document these in the module docstring. Code the interface first, implementation second.

### P4 — Tests Are Not Optional
Write or update tests in `tests/` before (or alongside) implementation. Every new function, class, and agent needs at least one happy-path test and one failure-path test. Tests run with `pytest tests/ -v`.

### P5 — Sanitize External Content
**All** content ingested from external sources (web pages, API responses, user input) must pass through `sanitize_text()` from `src/utils/helpers.py` before being included in any LLM prompt. This is the prompt injection firewall. Do not bypass it. Do not inline new sanitization logic — extend the `_INJECTION_PATTERNS` list in `helpers.py`.

### P6 — Never Commit Secrets
API keys, tokens, passwords, and credentials live **only** in environment variables. The `.env` file is gitignored. The `.env.example` shows the shape without values. If a test needs a key, use `pytest.importorskip` or `unittest.mock.patch`.

### P7 — Phase Discipline
Do not implement features that belong to a later phase until the current phase's success criteria are met. Phase definitions are in `docs/phase-5-implementation-plan.md`. If you are unsure which phase a feature belongs to, ask before implementing.

### P8 — Minimal Blast Radius
When making changes, touch the fewest files possible. If you need to refactor, do it in a separate commit from feature additions. Never reformat files you didn't otherwise change.

### P9 — Docs Are Living Code
When you change behaviour, update the relevant `docs/phase-*.md` file in the same commit. The docs are not optional commentary — they are the specification that the `DocumentationAgent` will eventually maintain automatically.

### P10 — Think Before You Type
For any task that will take more than 5 minutes of implementation, write a brief plan first:
1. What files will change?
2. What is the minimal change that satisfies the requirement?
3. What could go wrong?

State this plan in your response before writing any code.

---

## 4. Code Standards

### Language & Runtime
- **Python 3.11+** only. Use modern syntax: `str | None` (not `Optional[str]`), `list[dict]` (not `List[Dict]`), `match/case` where appropriate.
- Type annotations on all function signatures. No `Any` where a specific type is knowable.

### Style
- Follow PEP 8. Max line length: **100 characters**.
- **Docstrings**: Google-style for classes and public functions. Describe *what* and *why*, not *how*.
- Module-level docstring on every file (see existing files as reference).
- Use f-strings for interpolation; never `%` formatting or `.format()`.

### Imports
- Standard library first, then third-party, then local. Separated by blank lines.
- Avoid `from module import *`.
- Lazy imports (inside functions) are allowed for optional heavy dependencies (FAISS, sentence-transformers, Playwright). Use the `# noqa: PLC0415` comment to silence linter warnings on them.

### File & Module Conventions
- One class per file unless they are tightly coupled data models for that module.
- Section dividers use `# ---...---` (see existing agents as reference).
- Configuration constants at the top of the file, before class definitions.
- Keep files under **400 lines**. If a file grows past 400 lines, split it.

### Data Models
- Use `@dataclass` for structured data transfer objects (see `AgentResult`, `KnowledgeEntry`, `TrendScore`).
- Always implement `to_dict()` on dataclasses that cross module boundaries.
- For validation-heavy models, prefer `pydantic.BaseModel` (the `config/settings.py` models use `@dataclass` for simplicity; new user-facing models should use Pydantic).

### Error Handling
- Catch specific exceptions, not bare `except Exception` in business logic.
- In agent `_execute()` methods, let exceptions propagate — `BaseAgent.run()` catches and logs them automatically.
- Use `# noqa: BLE001` only on the broad catches inside `BaseAgent.run()` and the Orchestrator's cycle runner — nowhere else.

### Naming
- Classes: `PascalCase`. Functions/methods: `snake_case`. Constants: `UPPER_SNAKE_CASE`.
- Agent classes end in `Agent` (e.g. `CrawlerAgent`). Result dataclasses end in `Result` or `Record` or `Finding`.
- Test files mirror source files: `src/agents/crawler_agent.py` → `tests/test_agents.py`.

---

## 5. Testing

### Structure
- `tests/test_agents.py` — all agent tests
- `tests/test_knowledge_base.py` — knowledge layer tests
- `tests/test_pipeline.py` — pipeline and utility tests

### Rules
1. **No network calls in tests.** Mock or stub any HTTP request. Use `unittest.mock.patch` for requests, LLM clients, and file I/O that touches external systems.
2. **No API keys required.** All tests must pass in a fresh environment with no `.env` file. Use `config={"llm_client": None}` or equivalent for agent tests.
3. **Use `tmp_path` for file I/O** (pytest fixture). Never write to `data/` during tests.
4. **Every agent needs**: at least one test for `initialize()`, one for successful `_execute()`, one for error handling, and one for `health_check()`.
5. **The full suite runs in under 10 seconds.** If your test is slow, mock the slow part.

### Running Tests
```bash
pytest tests/ -v              # full suite
pytest tests/test_agents.py -v -k "Crawler"   # specific class
pytest tests/ --cov=src --cov-report=term-missing  # with coverage
```

---

## 6. Security

### Mandatory Rules — Never Deviate

| Rule | Why |
|------|-----|
| Call `sanitize_text()` on all external content before LLM calls | Prevents prompt injection via crawled web content |
| All secrets via env vars only | Prevents credential leaks in git history |
| Rate limit every external API call | Prevents abuse bans and cost runaway |
| Respect `robots.txt` in CrawlerAgent | Legal and ethical compliance |
| Validate all external API responses with Pydantic or explicit key checks | Prevents crashes from unexpected shapes |
| Log at WARNING or higher when sanitization fires | Creates an audit trail for injection attempts |

### Adding New Injection Patterns
If you discover a new prompt injection technique, add its detection pattern to `_INJECTION_PATTERNS` in `src/utils/helpers.py` AND add a test for it in `tests/test_pipeline.py::TestSanitizeText`.

### Dependency Security
Before adding a new package to `requirements.txt`, check it for known vulnerabilities. Prefer packages with recent activity and broad adoption. Pin major versions (`requests>=2.31.0`), not exact versions (to allow security patch auto-updates).

---

## 7. The Five Phases — Current State

```
Phase 0: Foundation           ✅ COMPLETE
Phase 1: Knowledge Discovery  🔄 IN PROGRESS  ← we are here
Phase 2: Intelligence Layer   ⬜ NOT STARTED
Phase 3: Agent Specialization ⬜ NOT STARTED
Phase 4: Orchestration        ⬜ NOT STARTED
Phase 5: API & Integration    ⬜ NOT STARTED  ← ExMorbus V3 integration target
Phase 6: Self-Improvement     ⬜ NOT STARTED
Phase 7: Production Hardening ⬜ NOT STARTED
```

**Phase 1 current priorities** (from `docs/phase-5-implementation-plan.md`):
- P1.1 Crawler Agent: Playwright integration for JS-rendered pages
- P1.2 Content Processing Pipeline: PDF parsing (PyMuPDF + LlamaParse)
- P1.3 Research Agent: LLM-powered extraction (requires `llm_client` config)
- P1.4 Ingestion Pipeline: Queue-based processing with priority

**Phase 5 strategic context** (from `docs/exmorbus-v3-integration.md`):
Phase 5 is now defined with a concrete first integration target: **ExMorbus V3**, a medical research multi-agent platform that uses Agentic-AI-Architect as its standing architectural oracle. The full integration design, API contracts, and MCP tool specifications are documented in `docs/exmorbus-v3-integration.md`. Key Phase 5 additions driven by ExMorbus:
- `get_architecture_recommendation` MCP tool (P5.3)
- ExMorbus adapter with < 200ms cached query latency (P5.4)
- Outbound webhook for proactive architecture alerts (P5.4)
- `schema_version` on all API responses (P5.1)

**Before starting any new work**, check this section and the implementation plan. If the phase status above is out of date, update it.

---

## 8. The BaseAgent Contract

Every agent in `src/agents/` **must** inherit from `BaseAgent` and implement `_execute()`. Everything else is provided by the base class.

```python
class MyNewAgent(BaseAgent):
    """
    One-line description of what this agent does.

    Configuration keys:
        key_name (type): Description and default.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(name="MyNewAgent", config=config)
        # Pull config values here, with defaults
        self._some_setting: int = self.config.get("some_setting", 42)

    def initialize(self) -> None:
        super().initialize()  # ALWAYS call super first
        # Set up connections, caches, seed data

    def _execute(self, task_input: Any = None) -> Any:
        # Core logic here
        # - task_input type must match what the Orchestrator passes
        # - return type must be documented in the class docstring
        # - raise exceptions for unrecoverable errors
        # - use self.logger, not print()
        pass

    def shutdown(self) -> None:
        # Clean up connections, files
        super().shutdown()  # ALWAYS call super last
```

**The `run()` method is provided by `BaseAgent` and must NOT be overridden.** It handles timing, status transitions, and exception capture automatically.

### Agent Data Flow Contract

```
Orchestrator.run_cycle()
  │
  ├─ CrawlerAgent.run()          → list[dict]  (raw documents)
  ├─ ResearchAgent.run(docs)     → list[dict]  (research findings)
  ├─ TrendTrackerAgent.run(findings) → dict   (scores + alerts)
  ├─ ToolDiscoveryAgent.run(findings) → dict  (registry + alerts)
  └─ DocumentationAgent.run({findings, trend_data, tool_data, cycle_number})
                                 → list[dict]  (generated docs)
```

When adding a new agent to the pipeline, update **both** `Orchestrator._execute()` and this section.

---

## 9. Anti-Patterns

These are patterns that feel right but are wrong for this codebase. Recognise them. Refuse them.

### ❌ Fat Orchestrator
Adding business logic to `orchestrator.py` beyond agent coordination. The Orchestrator moves data — it does not process it. Logic goes in specialised agents.

### ❌ God Agent
An agent that does crawling AND research AND trend scoring. Split into three agents. The `Orchestrator` connects them.

### ❌ Inline LLM Calls
Calling an LLM directly in a utility function, pipeline, or data model. LLM calls belong in agents. Pass an `llm_client` callable via config.

### ❌ Bare `requests.get()` Without Rate Limiting
Always use `rate_limit()` from `helpers.py` before any external HTTP call. For crawling operations, use the `_session` from `CrawlerAgent` (which sets the correct User-Agent header). For other agents that need HTTP access, create a dedicated session with the standard User-Agent from `config/settings.py`.

### ❌ Tests That Require `.env`
Any test that fails in CI without API keys is a broken test. Mock the API call.

### ❌ Print Debugging
`print()` is banned in `src/`. Use `self.logger.debug()` for temporary debugging. Remove before committing.

### ❌ Modifying `BaseAgent.run()`
The base class run method is the lifecycle contract. If you need different lifecycle behaviour, override `initialize()` or `shutdown()`, never `run()`.

### ❌ Skipping `sanitize_text()` "Because it's an internal source"
An "internal source" can have been poisoned by an external actor. Sanitize everything that touches an LLM prompt.

### ❌ Naming Agents After Their Implementation
`FAISSSearchAgent` is wrong. `SemanticSearchAgent` is right. Implementations change; responsibilities don't.

### ❌ Knowledge Base Without Namespace
Every entry stored in `KnowledgeBase` must have a `namespace`. Valid values: `education`, `frameworks`, `trends`, `tools`, `general`. Adding a new namespace requires updating this list and the docs.

---

## 10. Workflow

### Starting a New Feature

1. **Check the phase.** Is this feature in the current phase? (See §7)
2. **Check existing code.** Read the relevant source files before writing anything.
3. **Write the plan.** State: what files change, what the minimal diff is, what could go wrong.
4. **Write the test first** (or alongside), not after.
5. **Implement the minimal change** that makes the test pass.
6. **Update docs** if behaviour or architecture changed.
7. **Run the full suite.** `pytest tests/ -v` must pass clean.

### Naming Branches (Git)
Follow the pattern from `docs/phase-5-implementation-plan.md`:
```
feature/p1-knowledge-discovery    ← phase-level feature branch
task/p1.1-crawler-playwright      ← task-level branch
fix/crawler-robots-txt-edge-case  ← bug fix
docs/update-phase-2-frameworks    ← documentation only
```

### Commit Messages
```
<type>(<scope>): <short description>

Types: feat | fix | docs | test | refactor | chore
Scope: agents | knowledge | pipeline | config | tests | docs

Examples:
feat(agents): add Playwright support to CrawlerAgent
fix(knowledge): handle empty namespace in search()
docs(phase-2): add MoE to framework maturity matrix
test(agents): add CrawlerAgent robots.txt edge cases
```

---

## 11. Context & State Management

### When You Start a New Session

Before writing any code:
1. Run `git status` and `git log --oneline -5` to understand where the branch is.
2. Read this file (`CLAUDE.md`) fully.
3. Read the relevant phase doc (`docs/phase-X-*.md`) for the work at hand.
4. Run `pytest tests/ -v` to confirm the baseline is green.

### When a Session Gets Long

If you're more than 50 messages into a conversation:
- Summarise what has been accomplished in this session
- Identify the next concrete task
- Recommend starting a fresh session with that task as the prompt

### When You're Unsure

If a decision isn't clearly covered by this document:
1. Check `docs/phase-5-implementation-plan.md` for architectural guidance.
2. Default to the simpler of two approaches.
3. Write a comment in the code explaining the decision: `# Decision: X over Y because Z`.
4. Update this file if the decision is general enough to apply elsewhere.

### Files You Must NOT Modify Without Explicit Instruction

| File | Reason |
|------|--------|
| `src/agents/base_agent.py` — `run()` method | Lifecycle contract; changes break all agents |
| `src/utils/helpers.py` — `sanitize_text()` patterns | Security firewall; removals create vulnerabilities |
| `config/settings.py` — env var names | Breaking changes for anyone with a `.env` file |
| `tests/` — existing passing tests | Deleting tests is not "fixing" test failures |

---

## 12. Key Decisions Log

A living record of significant architectural choices and the reasoning behind them.

| Decision | Chosen | Rejected | Reason |
|----------|--------|----------|--------|
| Agent framework | Custom `BaseAgent` | LangGraph (P4+), LangChain | Avoid heavy dependencies in Phase 0; LangGraph planned for P4 |
| Structured store | SQLite | PostgreSQL, DynamoDB | Zero-infra start; migrate to Postgres at scale |
| Vector search | FAISS local + Pinecone cloud | Weaviate, Qdrant | FAISS for dev (no server); Pinecone for prod managed option |
| Embedding fallback | TF-IDF hash vectors | None / fail hard | System must run with zero API keys; graceful degradation |
| Config pattern | `@dataclass` + env vars | Pydantic `BaseSettings` | Pydantic adds runtime dep; revisit if validation needs grow |
| LLM calls in agents | `llm_client` callable injected via config | Hard-coded OpenAI | Provider-agnostic; testable without API keys |
| Crawler UA | Custom branded string | Python-requests default | Identifies us for rate-limit friendly treatment |
| Prompt injection defense | `sanitize_text()` in utils | Per-agent inline sanitization | Central, auditable, testable |
| ExMorbus integration model | Oracle model (read-only, advisory, on-demand) | Embedded agent in ExMorbus | ExMorbus must remain independent; Agentic-AI-Architect advises but never blocks |
| MCP latency target | < 200ms cached | No formal target | ExMorbus on-demand load/unload pattern only works if queries are fast |
| API schema stability | `schema_version` on all responses; major version for breaking changes; 90-day deprecation | No versioning | ExMorbus cannot tolerate mid-project API breaks from its advisor |
| New MCP tool | Add `get_architecture_recommendation` in P5.3 | Only CRUD knowledge endpoints | ExMorbus's primary need is targeted architectural guidance, not raw retrieval |

---

## 13. Dependency Philosophy

- **No new dependencies without a clear reason.** State why in the PR.
- **Prefer standard library** where it covers the need (e.g. `sqlite3`, `re`, `hashlib`).
- **Heavy optional dependencies** (FAISS, Playwright, sentence-transformers, openai) remain optional — the system degrades gracefully without them. Wrap imports in try/except ImportError blocks with a logged fallback.
- **Check for known vulnerabilities** before adding any package.
- **Lock major versions only** in `requirements.txt`. Never exact-pin unless a bug forces it.

---

*This file is maintained by the development team. Last updated: March 2026.*
*When this file diverges from the code, the code wins — but update this file immediately.*
