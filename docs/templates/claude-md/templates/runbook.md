# Runbook — [OPERATION NAME]

**Version:** 1.0  
**Last Tested:** [YYYY-MM-DD]  
**Owner:** [name or team]  
**Estimated Duration:** [N minutes]  
**Risk Level:** [Low / Medium / High]

---

## Purpose

[One paragraph: what operation this runbook covers, when to use it, and what it achieves.]

---

## Prerequisites

- [ ] [Required access or permission 1]
- [ ] [Required tool or credential 2]
- [ ] [System state precondition — e.g., "service is not receiving traffic"]
- [ ] [Verification command and expected output]

---

## Steps

### Step 1 — [Name]

**What:** [What this step does]

```bash
[command or action]
```

**Expected output:**
```
[what success looks like]
```

**If it fails:** [what to do; link to Troubleshooting section]

---

### Step 2 — [Name]

**What:** [What this step does]

```bash
[command or action]
```

**Expected output:**
```
[what success looks like]
```

**If it fails:** [what to do]

---

## Verification

After all steps are complete, confirm success:

```bash
[verification command]
```

**Expected output:**
```
[what a successful completion looks like]
```

---

## Rollback

If the operation must be reversed:

```bash
[rollback command]
```

**Rollback verification:**
```bash
[verify rollback succeeded]
```

**Note:** [anything that cannot be rolled back, and what to do about it]

---

## Troubleshooting

### Problem: [Common failure mode 1]

**Symptom:** [what you see]
**Cause:** [why it happens]
**Fix:** 
```bash
[resolution command]
```

### Problem: [Common failure mode 2]

**Symptom:** [what you see]
**Cause:** [why it happens]
**Fix:** [resolution steps]

---

## Escalation

If this runbook doesn't resolve the problem:

1. **[Step 1]** — [action, e.g., "Post in #incidents Slack channel with runbook link"]
2. **[Step 2]** — [action, e.g., "Page the on-call engineer"]
3. **[Step 3]** — [action, e.g., "Contact [external team/vendor]"]

---

## References

- [Related runbook or ADR]
- [Documentation link]
- [Monitoring dashboard]

---

*Test this runbook in a non-production environment before the first live use.*
*Update "Last Tested" field after each successful run.*
