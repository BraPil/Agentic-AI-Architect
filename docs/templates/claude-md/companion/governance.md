# Governance — [PROJECT NAME]

> Protected paths, approval policies, file ownership, and escalation paths.
> This file answers: "Can I change X?" and "Who do I ask if I can't?"

---

## Protected Files

*These files must not be modified without explicit instruction from the project owner.*

| File / Path | Why Protected | Who Can Approve |
|-------------|---------------|-----------------|
| `[src/core/base.py]` | [e.g., Lifecycle contract; changes break all agents] | [owner name/role] |
| `[src/utils/sanitize.py]` | [e.g., Security firewall; removals create injection vectors] | [security lead] |
| `[config/settings.py]` — env var names | [Breaking change for all deployments] | [owner] |
| `[tests/]` — existing passing tests | [Deleting tests is not fixing failures] | [owner] |
| `[.github/workflows/]` | [Affects CI for all contributors] | [DevOps lead] |

---

## Approval Matrix

| Action | Approval Required | Method |
|--------|------------------|--------|
| New dependency added | Project owner | Comment in PR + decision-log entry |
| Public interface changed | Project owner + consumers | RFC filed before implementation |
| Schema version bumped | Project owner | ADR filed, consumers notified |
| New agent or module introduced | Project owner | Design doc filed and approved |
| Production deployment | Project owner + ops | Runbook executed, checklist complete |
| Data migration or schema change | Project owner | Runbook filed, rollback plan documented |
| Third-party integration added | Security review | Threat model entry added |

---

## File Ownership

*Who to consult before modifying key files. Not gatekeeping — just "who knows this best."*

| Area | Owner | Backup |
|------|-------|--------|
| Core agents (`src/agents/`) | [name] | [name] |
| Knowledge layer (`src/knowledge/`) | [name] | [name] |
| Pipeline (`src/pipeline/`) | [name] | [name] |
| Configuration (`config/`) | [name] | [name] |
| Tests (`tests/`) | [name] | [name] |
| CI/CD (`.github/`) | [name] | [name] |

---

## Escalation Path

When blocked on a decision that isn't covered by CLAUDE.md or companions:

1. **Check `docs/decision-log.md`** — has this been decided before?
2. **Check `adr/`** — is there an Architecture Decision Record covering this area?
3. **Default to the simpler option** — document the choice and the reason in the PR
4. **File a new ADR** — if the decision is significant and general, write it down for next time
5. **Ask the project owner** — if the risk of the wrong choice is high and you can't determine it

---

## Branch and Release Policy

| Branch | Purpose | Who Pushes | Protection |
|--------|---------|-----------|------------|
| `main` | Production-ready code | Project owner only | Required: CI pass + review |
| `feature/p[N]-*` | Phase-level feature work | Any contributor | Required: CI pass |
| `task/p[N.N]-*` | Task-level branches | Any contributor | Recommended: CI pass |
| `fix/*` | Bug fixes | Any contributor | Required: CI pass |
| `docs/*` | Documentation only | Any contributor | None |

**Merge to main:** squash or merge commit; no force push; tag releases with `v[major].[minor].[patch]`.

---

## Change Management for AI-Generated Code

*Additional governance for code generated or modified by AI coding assistants:*

- AI-generated code follows the same standards as human-written code. No exceptions.
- AI must not modify protected files unless explicitly instructed.
- AI must not push to main or release branches under any circumstance.
- AI must pause and ask when an action has high blast radius or is irreversible.
- AI-generated PRs include: which assistant generated it, the prompt used (brief), and human review status.
- If AI-generated code breaks production, treat it as any other incident — no special blame, same postmortem.

---

*Last updated: [YYYY-MM-DD]*
