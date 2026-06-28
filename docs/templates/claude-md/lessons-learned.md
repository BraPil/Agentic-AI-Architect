# Lessons Learned — [PROJECT NAME]

> Mistakes, surprises, and preventive lessons from real development.
> The most valuable content in this file is what no one wants to write.
> Read this before starting a new session to avoid repeating known mistakes.

---

## Format

```markdown
### [YYYY-MM-DD] — [Lesson Title]

**What happened:** [Brief description of the incident or surprise]
**Root cause:** [Why it happened — not blame, but mechanism]
**Impact:** [What broke, what was delayed, what confusion was caused]
**Prevention:** [What check, test, or practice would have caught this earlier]
**Status:** [monitoring / resolved / permanent-risk / incorporated-into-standards]
```

---

## Lessons

### [YYYY-MM-DD] — [Example: Mocked database tests passed while prod migration failed]

**What happened:** Integration tests used a mock database that didn't validate column constraints.
A migration adding a NOT NULL column without a default value passed all tests but failed on
the production database with existing rows.
**Root cause:** Mocks were too permissive. They validated the ORM layer but not the database engine.
**Impact:** 45 minutes of production downtime. Manual rollback required.
**Prevention:** Integration tests now hit a real database (SQLite in-memory for tests, same engine
as production). Mocks are no longer used for tests that exercise persistence logic.
**Status:** incorporated-into-standards (see `docs/workflows.md` testing section)

---

### [YYYY-MM-DD] — [Example: Inlining sanitize_text() in two places caused drift]

**What happened:** A new injection pattern was added to `helpers.py` but two agents had their
own inline sanitization that didn't get updated. One was discovered via an audit 3 weeks later.
**Root cause:** Duplicated logic with no enforcement of the canonical location.
**Prevention:** Only one sanitize function. Linter rule to flag any new inline sanitization.
Any sanitization code outside `helpers.py` fails review.
**Status:** incorporated-into-standards (see `CLAUDE.md` §6 anti-patterns)

---

*Add new entries above this line. Oldest lessons stay — they're the hardest-won.*
