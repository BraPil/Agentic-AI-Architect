# OAA Patches

Changes to `BraPil/Organic_Agentic_AutoDev` developed from AAA but not pushable
from this Codespace (its `GITHUB_TOKEN` is scoped to AAA only — pushing to OAA
returns 403). Preserved here as git patches so the work isn't lost and you can
apply + push from a checkout that has OAA write access.

## Apply

```bash
git clone https://github.com/BraPil/Organic_Agentic_AutoDev.git
cd Organic_Agentic_AutoDev
git checkout -b feat/cognition-bridge
git am /path/to/Agentic-AI-Architect/docs/oaa-patches/0001-feat-cognition-bridge.patch
git push -u origin feat/cognition-bridge
```

## Patches

| Patch | Summary |
|-------|---------|
| `0001-feat-cognition-bridge.patch` | `src/cognition/` — LLM cognition bridge (Researcher → Critic → Synthesizer cycle, `KnowledgeRecordV0` emitter, CLI). Validated live with AAA: promoted artifact raised answer relevance 0.669 → 0.777. |

## Status — RESOLVED upstream (2026-06-28)

The OAA team (Opus) ran the integration prompt and went further than this patch:
**PR #1 `feat/cognition-bridge → main`** ("Cognition bridge + src-layout packaging fix")
applies the cognition bridge AND fixes packaging (src-layout as `organic_agentic_autodev`,
console entry point `oaa-learning-cycle`), plus adds autoresearch, a dashboard, distributed
support, and multiple cognition providers (anthropic/openai/mock).

Verified from AAA:
- `pip install git+…@<PR#1 head>` succeeds; `import organic_agentic_autodev` works with
  no collision against AAA's `src/`.
- The run-cycle CLI contract is unchanged (`--seed/--out/--model`, KnowledgeRecordV0 JSONL),
  so AAA's harvester/seeder are compatible as-is.
- Loop re-proven against the installed package: a fresh cycle's synthesis earned 0.703,
  was promoted, and raised AAA's answer relevance 0.4617 → 0.7229.

So `0001-feat-cognition-bridge.patch` is now historical (superseded by PR #1). Action:
**merge OAA PR #1 to main**, then change AAA's `requirements.txt` pin from the PR-head SHA
to `@main` (or a release tag).
