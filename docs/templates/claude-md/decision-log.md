# Decision Log — [PROJECT NAME]

> Chronological record of significant architectural and engineering decisions.
> Append only. Never edit past entries. If a decision is reversed, add a new entry.
> Full context lives in `adr/`. This log is the summary index.

---

## Format

```markdown
### [YYYY-MM-DD] — [Decision Title]

**Context:** [What situation prompted this decision]
**Decision:** [What was chosen]
**Rejected:** [What was not chosen and why]
**Consequences:** [What this makes easier, what it makes harder]
**Owner:** [Who made this call]
**ADR:** [adr/NNNN-filename.md] (if filed)
```

---

## Log

### [YYYY-MM-DD] — [Example: Chose SQLite over PostgreSQL for initial storage]

**Context:** Needed a structured store for Phase 0. No infrastructure available; wanted zero-config start.
**Decision:** SQLite via `sqlite3` stdlib. No ORM.
**Rejected:** PostgreSQL (requires server), DynamoDB (AWS dependency), Redis (wrong data model).
**Consequences:** Zero setup cost; easy to migrate later; 10k+ row performance not validated yet.
**Owner:** [name]
**ADR:** [adr/0001-storage-sqlite.md]

---

*Add new entries above this line, newest first.*
*Or append chronologically — choose one convention and keep it.*
