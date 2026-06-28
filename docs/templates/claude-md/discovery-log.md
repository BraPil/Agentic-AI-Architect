# Discovery Log — [PROJECT NAME]

> Important findings that affect future work.
> Not decisions (those go in decision-log.md) — discoveries: things we learned that changed
> how we think about the problem.
> Append only. Include the date so findings can be evaluated for staleness later.

---

## Format

```markdown
### [YYYY-MM-DD] — [Finding Title]

**What we found:** [The specific discovery]
**Why it matters:** [How this changes future work or our understanding]
**Source:** [Where we learned this — experiment, external source, incident, etc.]
**Follow-up:** [What this means we should do, test, or change]
**Status:** [active / superseded / implemented]
```

---

## Log

### [YYYY-MM-DD] — [Example: TF-IDF vector fallback preserves 70% retrieval quality vs. embeddings]

**What we found:** When sentence-transformers is unavailable, TF-IDF hash vectors retrieve the
correct answer in 70% of test cases (vs. 89% with full embeddings).
**Why it matters:** Justifies the graceful degradation approach. The fallback is good enough
to provide value even in zero-dependency environments.
**Source:** Evaluation run 2024-XX-XX, 20 test queries.
**Follow-up:** Document this in `docs/evaluation.md`. Do not remove the fallback path.
**Status:** active

---

*Add new entries above this line. Newest first.*
