# CLAUDE.md — [PROJECT NAME]

> Governs every AI coding session in this repository.
> Read before touching any file. Keep lean — depth lives in companion docs.
> **When this file conflicts with the code, the code wins. Update this file immediately.**

---

## INIT — Initialization Survey

> **If the title above still reads `[PROJECT NAME]`, this template is unconfigured.**
> **Stop. Do not proceed to any other section. Run the survey below first.**

### Detection

```
grep -c '\[PROJECT NAME\]' CLAUDE.md
```

If that returns `1` or more: this file is a template. Run the survey. Fill the placeholders.
Then delete this entire `## INIT` section before committing.

### Survey Protocol

Ask the user the following questions in order. Do not ask all at once — go block by block,
wait for answers, then move to the next block. After all blocks are complete, write the
answers into the placeholders in this file and in the relevant companion docs.

---

**BLOCK 1 — Identity** *(~1 minute)*

1. What is the project name?
2. One sentence: what does this system do, and for whom?

---

**BLOCK 2 — Mission** *(~3 minutes)*

3. Who are the primary users or consumers of this system?
   *(Could be humans, other services, or other agents — be specific)*
4. What does success look like in 6 months? Give 2–3 measurable outcomes,
   not aspirations. *(e.g., "< 200ms query latency on 95th percentile" not "fast")*
5. What will this system explicitly NOT do?
   *(At least two non-goals — these prevent scope creep)*

---

**BLOCK 3 — Technology Stack** *(~3 minutes)*

6. Primary language and minimum version? *(e.g., Python 3.11+)*
7. Structured storage? *(SQLite / Postgres / DynamoDB / Redis / other — and why)*
8. Vector / semantic search? *(FAISS / Pinecone / ChromaDB / none — and why)*
9. LLM interface? *(Anthropic SDK / OpenAI / local model / none — and why)*
10. Testing framework? *(pytest / jest / go test / other)*
11. Logging and observability approach? *(structlog / OpenTelemetry / print → structured / other)*

---

**BLOCK 4 — Phases** *(~3 minutes)*

12. How many phases does this project have? What are they called?
    *(Use the Phase 0 = Foundation convention if you don't have your own)*
13. Which phase is current?
14. What are the top 2–3 priorities for the current phase?
    *(Concrete tasks, not themes)*

---

**BLOCK 5 — Governance** *(~2 minutes)*

15. Who is the project owner / final approval authority?
    *(The human who has veto power and defines "done")*
16. Are there files that should never be modified without explicit instruction?
    *(List them — base classes, security utilities, env var names, CI configs)*
17. What is the test command? *(e.g., `pytest tests/ -v`)*

---

### After the Survey

Once all blocks are answered:

1. **Fill every `[PLACEHOLDER]` in this file** using the answers above.
2. **Update `companion/architecture.md`** — fill in the component map and data flow
   with whatever is known at this stage. Stubs are fine.
3. **Update `companion/governance.md`** — fill in protected files and the project owner.
4. **Create the first entry in `decision-log.md`** — record the tech stack choices
   (Block 3 answers) as the first architectural decisions.
5. **Delete this entire `## INIT` section** from CLAUDE.md.
6. **Confirm to the user:** "Initialization complete. Here's what was filled in and
   what still needs your review: [list]."

Do not begin any implementation work until initialization is complete.

---

## 0. Ecosystem Map

| Companion File | Governs |
|----------------|---------|
| `docs/architecture.md` | System design, component map, data flows, phase roadmap |
| `docs/governance.md` | Protected paths, approval escalation, file ownership |
| `docs/workflows.md` | Dev lifecycle, branching, commit standards, PR process |
| `docs/evaluation.md` | AI/ML eval methodology, benchmark tracking, uncertainty policy |
| `docs/security.md` | Threat model, injection defense, secret hygiene |
| `docs/knowledge.md` | Knowledge types, storage strategy, retrieval patterns |
| `docs/decision-log.md` | Chronological record of architectural decisions |
| `docs/discovery-log.md` | Important findings that affect future work |
| `docs/lessons-learned.md` | Mistakes, surprises, preventive lessons |
| `adr/` | Architecture Decision Records (created on demand) |
| `runbooks/` | Operational procedures (created on demand) |
| `templates/` | Standard document templates |

*Read only the companions relevant to the current session's task.*

---

## 1. Mission

**Purpose:** [One sentence — what this system does and for whom]

**Users:** [Who consumes this system, directly or indirectly]

**Success looks like:** [Measurable outcomes — not aspirations]

**Non-goals (explicit):** [What this system will never do, stated to prevent scope creep]

---

## 2. Architectural Constitution

*Values, not rules. When two values conflict, the one ranked higher wins.*
*Derive correct behavior for novel situations from these values rather than asking for a rule.*

| Rank | Value | What it demands |
|------|-------|----------------|
| 1 | **Observability** | If it isn't logged and measurable, it doesn't exist |
| 2 | **Correctness** | Working before fast before elegant. Measure before optimizing |
| 3 | **Simplicity** | Smallest change satisfying the requirement. No future-proofing |
| 4 | **Explainability** | Every decision has a stated reason. No magic |
| 5 | **Testability** | If you can't test it, rethink the design |
| 6 | **Replaceability** | Implementations are swappable; interfaces are stable |
| 7 | **Security** | Sanitize, authenticate, rate-limit from day one |
| 8 | **Evolvability** | Today's choice doesn't lock out tomorrow's option |

> **Example conflict resolution:** Observability vs. Simplicity — adding a log line is rarely
> "too complex." Simplicity vs. Correctness — never skip a test to ship faster.

---

## 3. Governance

*Actions requiring explicit human approval before proceeding:*

| Action | Risk | Default |
|--------|------|---------|
| Delete or overwrite files outside the active task scope | Blast radius | **Block** |
| Change public interfaces, API contracts, or wire schemas | Downstream breakage | **Block** |
| Add new dependencies to requirements / package files | Security + bloat | **Block** |
| Commit anything containing credentials, tokens, or keys | Irreversible leak | **Block** |
| Modify CI/CD pipelines or deployment configuration | Affects all contributors | **Block** |
| Push to main, master, or release branches | Requires human gate | **Block** |
| Make irreversible infrastructure changes (drop tables, etc.) | Disaster recovery | **Block** |
| Refactor code outside the active task's stated scope | Scope creep | **Ask** |
| Reference an API or library without citing its source | Hallucination risk | **Ask** |

**Rule:** When uncertain whether an action falls under a guardrail — pause and ask.

---

## 4. Session Protocol

*Execute in order at the start of every coding session:*

1. **Orient to state**
   ```bash
   git status && git log --oneline -5
   ```

2. **Confirm the baseline is clean**
   ```bash
   [test command — e.g., pytest tests/ -v]
   ```
   Do not begin changes if the baseline is red. Fix first.

3. **Read the relevant companion docs**
   From the Ecosystem Map above, identify which files apply to this session's task.
   Read those before writing any code.

4. **Check institutional memory**
   Scan `docs/decision-log.md` and `docs/discovery-log.md` for entries affecting the
   current task. If something was decided before, honor the decision or explicitly reverse it.

5. **Optional — ingest LLM engineering foundations**
   If working on AI/LLM components or debugging model behavior, read:
   - Karpathy's LLM Wiki: `https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f`
   This establishes shared vocabulary for reasoning about neural network engineering.

---

## 5. Definition of Done

*A task is not complete until every applicable box is checked. Binary — not negotiable.*

**Code**
- [ ] Tests pass; new code has at least one happy-path and one failure-path test
- [ ] No new linting warnings introduced
- [ ] No hardcoded secrets, credentials, or API keys
- [ ] External content sanitized before any LLM prompt inclusion

**Documentation**
- [ ] Relevant companion docs updated to reflect changed behavior
- [ ] `docs/decision-log.md` updated if an architectural decision was made
- [ ] `docs/lessons-learned.md` updated if something surprising happened
- [ ] ADR filed in `adr/` if a significant architectural choice was locked in

**Hygiene**
- [ ] No unresolved TODOs within the task's stated scope
- [ ] No dead code or commented-out blocks left behind
- [ ] PR / commit description explains *why*, not just *what*

*If a task is too large to satisfy all applicable criteria in one session, split the task.*

---

## 6. Core Anti-Patterns

*These feel correct but are wrong for this codebase. Recognize them. Refuse them.*

| Pattern | The Trap | The Rule |
|---------|----------|----------|
| **Fat orchestrator** | Business logic added to coordination code | Orchestrators move data; they don't transform it |
| **God module** | One class doing crawling + analysis + storage | Single responsibility. Split at the second job |
| **Inline LLM calls** | LLM call buried in a utility or pipeline function | LLM calls belong in agents; inject the client via config |
| **Bare HTTP** | `requests.get()` without rate limiting or UA header | Rate-limit all external calls; use session with standard UA |
| **Credential-dependent tests** | Tests that fail without `.env` present | All tests pass in a clean environment with no secrets |
| **Print debugging** | `print()` in `src/` or equivalent source directories | Structured logging only; remove before commit |
| **Premature abstraction** | Helper class extracted for a single use case | Three similar lines > one leaky abstraction |
| **Sanitization bypass** | "This source is internal, skip sanitize_text()" | Sanitize everything that touches an LLM prompt |
| **Spec fiction** | Referencing an API or package without verifying it exists | Read the source. Cite the version |
| **Ambiguous ownership** | File modified without declaring which task owns it | Every task declares its file scope upfront |

---

## 7. Technology Stack

| Layer | Choice | Rationale | Upgrade Path |
|-------|--------|-----------|--------------|
| Language | [e.g., Python 3.11+] | [reason] | [e.g., 3.12 when stable] |
| Structured store | [e.g., SQLite] | [reason] | [e.g., Postgres at 10k+ rows] |
| Vector search | [e.g., FAISS local] | [reason] | [e.g., Pinecone for managed] |
| LLM interface | [e.g., Anthropic SDK] | [reason] | [provider-agnostic via config] |
| Testing | [e.g., pytest] | [reason] | — |
| Observability | [e.g., structlog JSON] | [reason] | [e.g., OpenTelemetry at scale] |

*Adding a new dependency requires a reason here and an entry in `docs/decision-log.md`.*

---

## 8. Phase Status

```
Phase 0 — [Foundation]           [✅ COMPLETE / 🔄 IN PROGRESS / ⬜ NOT STARTED]
Phase 1 — [Knowledge Discovery]  [status]
Phase 2 — [Intelligence Layer]   [status]
Phase 3 — [Specialization]       [status]
Phase 4 — [Orchestration]        [status]
Phase 5 — [API & Integration]    [status]
```

**Current phase priorities:**
1. [P-current.1] [Task description]
2. [P-current.2] [Task description]

**Phase discipline:** do not implement features belonging to a later phase until the current
phase's success criteria are met. Phase definitions live in `docs/architecture.md`.

---

*Maintained by: [team/owner]. Last updated: [YYYY-MM-DD].*
*Architecture decisions: `docs/decision-log.md` | Discovery log: `docs/discovery-log.md`*
