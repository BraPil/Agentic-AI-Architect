# Development Workflows — [PROJECT NAME]

> The development lifecycle: how work moves from idea to production.
> Follow this to keep the codebase consistent across contributors and sessions.

---

## The Development Cycle

Every non-trivial change follows this sequence. Do not skip steps.

```
1. ORIENT      → Read CLAUDE.md, relevant companions, decision log
2. PLAN        → Write the minimal plan before writing any code
3. BASELINE    → Tests green before starting. Red baseline = stop.
4. IMPLEMENT   → Smallest change satisfying the requirement
5. TEST        → Happy-path + failure-path coverage for new code
6. DOCUMENT    → Update companions and logs as required by DoD
7. SELF-REVIEW → Check the anti-patterns table; check the DoD checklist
8. PR          → Submit with why, not just what
```

---

## Planning Protocol

*For any task that will take more than 5 minutes to implement, write a brief plan first:*

1. **What files will change?** (list them)
2. **What is the minimal change that satisfies the requirement?**
3. **What could go wrong?** (at least two failure modes)
4. **Does this belong to the current phase?** (check `docs/architecture.md`)

Write this plan as a comment in the PR or as a note to self before coding. Do not start typing
implementation until you've answered all four questions.

---

## Branch Naming

```
feature/p[N]-[phase-name]         ← phase-level feature branch
task/p[N.N]-[task-slug]           ← task-level branch
fix/[short-description]           ← bug fix
docs/[short-description]          ← documentation only
refactor/[short-description]      ← refactoring with no behavior change
chore/[short-description]         ← dependency updates, tooling
```

**Examples:**
```
feature/p1-knowledge-discovery
task/p1.1-crawler-playwright
fix/crawler-robots-txt-edge-case
docs/update-phase-2-frameworks
```

---

## Commit Message Format

```
<type>(<scope>): <short description>

[Optional body: more detail about why, not what]

[Optional footer: breaking changes, related issues]
```

**Types:** `feat` | `fix` | `docs` | `test` | `refactor` | `chore` | `perf`

**Scope:** use the primary directory changed — `agents` | `knowledge` | `pipeline` | `config` | `tests` | `docs`

**Examples:**
```
feat(agents): add Playwright support to CrawlerAgent
fix(knowledge): handle empty namespace in search()
docs(phase-2): add MoE to framework maturity matrix
test(agents): add CrawlerAgent robots.txt edge cases
refactor(pipeline): extract chunk_text into helpers
```

**Rules:**
- Subject line: imperative mood, <= 72 characters, no trailing period
- Body: explain *why* the change was made, not *what* it does (the diff shows what)
- If the commit closes an issue: `Closes #[N]` in footer

---

## Pull Request Protocol

**PR title:** same format as commit message subject

**PR body must include:**

```markdown
## Why
[One paragraph: what problem this solves and why this approach was chosen]

## What Changed
[Bullet list of the significant changes]

## Test Plan
[How to verify this works: specific commands, scenarios, expected output]

## Checklist
- [ ] Tests pass locally
- [ ] DoD checklist complete
- [ ] Companion docs updated
- [ ] Decision log updated (if applicable)
- [ ] No secrets or credentials
```

**Review expectations:**
- Reviewer checks: correctness, DoD compliance, anti-pattern absence, constitution alignment
- Reviewer does not check: formatting (that's the linter's job), personal style preferences
- Author resolves all comments before merge; no unresolved threads at merge time

---

## Testing Standards

**Structure:** `tests/` mirrors `src/`. One test file per source module.

**Every new module needs:**
1. Happy-path test (expected inputs produce expected outputs)
2. Failure-path test (bad inputs raise the right exception, not a generic one)
3. If it does I/O: a test that doesn't require network or credentials

**Running tests:**
```bash
pytest tests/ -v                                          # full suite
pytest tests/test_agents.py -v -k "CrawlerAgent"         # targeted
pytest tests/ --cov=src --cov-report=term-missing         # with coverage
```

**Speed gate:** full suite must complete in under 60 seconds. Slow tests mock the slow part.

**No test should:**
- Make real network calls (mock them)
- Require a `.env` file or API keys
- Write to `data/`, `src/`, or `docs/` (use `tmp_path` fixture)
- Leave state that affects other tests (each test is isolated)

---

## Code Review Checklist

*Use this before requesting review, not as a post-merge ritual.*

**Correctness**
- [ ] Does the code do what the PR description says it does?
- [ ] Are edge cases handled?
- [ ] Are failure modes tested?

**Architecture (Constitution alignment)**
- [ ] Is the change observable? (logged at appropriate level)
- [ ] Is it the simplest approach that works?
- [ ] Are responsibilities correctly scoped? (no fat orchestrator, no god module)
- [ ] Does it make the system more or less testable?

**Security**
- [ ] External content sanitized before LLM prompts?
- [ ] No credentials hardcoded?
- [ ] New HTTP calls rate-limited?
- [ ] New dependencies security-checked?

**Documentation**
- [ ] Relevant companion docs updated?
- [ ] Decision log entry made if an architectural choice was locked in?
- [ ] Surprising behavior or lessons recorded?

---

## Dependency Management

Before adding any new package:

1. **Justify the need** — could standard library or an existing dep solve this?
2. **Security check** — search for known CVEs; check last release date and maintainer activity
3. **Pin major version only** — `requests>=2.31.0` not `requests==2.31.4` (allows security patches)
4. **Document** — add a row to the dependency table in `docs/architecture.md`
5. **Log the decision** — entry in `docs/decision-log.md`

For optional heavy dependencies (ML frameworks, browser engines, etc.):
- Wrap in `try/except ImportError` with a logged fallback
- System must degrade gracefully without them
- Note the optional status in `docs/architecture.md`

---

*Last updated: [YYYY-MM-DD]*
