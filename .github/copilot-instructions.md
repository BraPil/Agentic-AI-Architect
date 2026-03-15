# GitHub Copilot Workspace Instructions
# Agentic AI Architect System

## Project Purpose
A multi-agent Python system that continuously discovers, scores, and documents the AI architecture landscape. Agents are atomic specialists coordinated by an `Orchestrator`. See `CLAUDE.md` for the complete guide and `docs/phase-5-implementation-plan.md` for the roadmap.

---

## Architecture Rules

- **Every agent inherits `BaseAgent`** from `src/agents/base_agent.py`. Implement `_execute()`. Never override `run()`.
- **One responsibility per agent.** `CrawlerAgent` fetches. `ResearchAgent` extracts. `TrendTrackerAgent` scores. `ToolDiscoveryAgent` tracks. `DocumentationAgent` writes. `Orchestrator` coordinates.
- **Data flows in one direction:** `CrawlerAgent → ResearchAgent → [TrendTracker, ToolDiscovery] → DocumentationAgent`. Each stage receives the previous stage's `list[dict]` output.
- **All settings via environment variables** with `AAA_` prefix. Read them through `config/settings.py`. Never hardcode values.
- **All secrets in `.env`** (gitignored). Never in source code.

---

## Python Standards

- Python 3.11+. Use `str | None`, `list[dict]`, `match/case`.
- Type annotations on all public functions and methods.
- Google-style docstrings. Module-level docstring on every file.
- Max 100 chars per line. Max 400 lines per file.
- f-strings only — no `%` or `.format()`.
- `@dataclass` for data transfer objects. Every DTO has `to_dict()`.
- Lazy imports for optional heavy deps (FAISS, Playwright, sentence-transformers). Wrap in `try/except ImportError`.
- Section dividers: `# ---------------------------------------------------------------------------` (a row of dashes — see existing files for the exact pattern).

---

## Security — Always

1. **Call `sanitize_text()` from `src/utils/helpers.py` on ALL external content before any LLM prompt.** This is non-negotiable.
2. Rate-limit every external HTTP call using `rate_limit()` from `src/utils/helpers.py`.
3. Respect `robots.txt` — the `CrawlerAgent._is_allowed()` method handles this; do not bypass it.
4. Log a `WARNING` when sanitization fires so there is an audit trail.
5. Never add a dependency without checking it for known vulnerabilities first.

---

## Testing — Always

- Test file mirrors source file: `src/agents/crawler_agent.py` → `tests/test_agents.py`.
- Every agent needs: one test for `initialize()`, one for success, one for failure path.
- **No network calls in tests.** Mock HTTP requests with `unittest.mock.patch`.
- **No API keys required.** All tests pass with no `.env` file.
- Use `tmp_path` pytest fixture for any file I/O.
- Run: `pytest tests/ -v` — suite must pass in under 10 seconds.

---

## Repository Memory — Always

- Keep durable records in `docs/` for important decisions, discoveries, lessons learned, and completed work.
- Use `docs/work-index.md` as the entry point.
- Do not rely on chat history, issue comments, or PR descriptions as the only record of important context.
- If a meaningful decision or lesson emerges, update the relevant log in the same session when practical.

---

## What NOT to Do

- ❌ Add logic to `orchestrator.py` beyond agent coordination — logic goes in agents.
- ❌ Call LLMs directly outside of agents — inject `llm_client` callable via config.
- ❌ Use `print()` in `src/` — use `self.logger` (INFO/WARNING/ERROR).
- ❌ Write tests that need a real API key — mock the call.
- ❌ Modify `BaseAgent.run()` — it is the lifecycle contract.
- ❌ Skip sanitizing content because "it's from a trusted source".
- ❌ Store any secret, token, or key in source code.
- ❌ Delete or weaken existing passing tests.
- ❌ Leave important decisions or completed work undocumented if they affect future contributors.

---

## Phase Tracking

We are in **Phase 1: Knowledge Discovery**. Do not implement Phase 2+ features yet.

```
P0 Foundation           ✅
P1 Knowledge Discovery  🔄 ← current
P2 Intelligence Layer   ⬜
P3 Agent Specialization ⬜
P4 Orchestration        ⬜
P5 API & Integration    ⬜
P6 Self-Improvement     ⬜
P7 Production Hardening ⬜
```

---

## Commit Message Format

```
<type>(<scope>): <description>
Types: feat | fix | docs | test | refactor | chore
Scope: agents | knowledge | pipeline | config | tests | docs
Example: feat(agents): add Playwright support to CrawlerAgent
```

---

## Knowledge Base Namespaces

Valid `namespace` values for `KnowledgeEntry`: `education` | `frameworks` | `trends` | `tools` | `general`

---

*Full instructions: see `CLAUDE.md` in the repository root.*
