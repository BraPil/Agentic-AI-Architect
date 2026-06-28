# Incident Report — [INCIDENT NAME]

**Date:** [YYYY-MM-DD]  
**Severity:** [P0 (total outage) | P1 (major degradation) | P2 (minor) | P3 (cosmetic)]  
**Duration:** [HH:MM] — from [HH:MM UTC] to [HH:MM UTC]  
**Responders:** [names]  
**Status:** [Open | Resolved | Monitoring]

---

## Summary

[Three sentences: what happened, who was affected, and how it was resolved.]

---

## Timeline

*All times in UTC.*

| Time | Event |
|------|-------|
| HH:MM | [First alert / detection] |
| HH:MM | [Response begins] |
| HH:MM | [Diagnosis] |
| HH:MM | [Mitigation applied] |
| HH:MM | [Issue resolved / service restored] |
| HH:MM | [Monitoring confirmed stable] |

---

## Root Cause

[What was the fundamental cause? Not "it broke" — the mechanism. Was it a missing guard?
A race condition? An upstream API change? A configuration error?]

**Contributing factors:**
- [Factor 1 — something that made the root cause possible or harder to detect]
- [Factor 2]

---

## Impact

| Dimension | Detail |
|-----------|--------|
| Services affected | [list] |
| Users affected | [count or percentage] |
| Data affected | [describe any data integrity issues] |
| Revenue / SLA impact | [if applicable] |

---

## Detection

**How was the issue detected?** [Alert / user report / manual check / monitoring]

**How long until detection?** [From the first anomalous event to detection]

**Could it have been detected earlier?** [Yes/No — if yes, what would have caught it?]

---

## Resolution

**What fixed it?** [Specific action(s) taken]

**Runbook followed?** [Yes (link) / No — if no, does a runbook need to be created?]

**Was the fix a workaround or a root cause fix?** [Workaround / Root cause / Both]

---

## Action Items

| Action | Owner | Due Date | Priority |
|--------|-------|----------|----------|
| [Preventive action 1] | [name] | [YYYY-MM-DD] | [H/M/L] |
| [Monitoring improvement] | [name] | [YYYY-MM-DD] | [H/M/L] |
| [Runbook created/updated] | [name] | [YYYY-MM-DD] | [H/M/L] |
| [Test added] | [name] | [YYYY-MM-DD] | [H/M/L] |

---

## Lessons Learned

[What should never happen again, and what specific change prevents it? This section feeds
`docs/lessons-learned.md` — copy the key lesson there after this is filed.]

---

## References

- [Monitoring link]
- [Relevant PR or commit that caused or fixed the issue]
- [Related ADR or runbook]

---

*Blame-free. The goal is system improvement, not individual accountability.*
*File within 48 hours of resolution. Action items have owners and due dates.*
