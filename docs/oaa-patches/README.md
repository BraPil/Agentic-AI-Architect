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

## Still TODO in OAA (not yet patched)

- **Packaging fix**: OAA installs as top-level `src/` (`[tool.setuptools.packages.find] include = ["src*"]`), which collides with AAA's `src/`. Rename to `organic_agentic_autodev` (src-layout) or add a console entry point so AAA can depend on it via pip-from-git instead of running it as a hand-cloned subprocess. Until then the loop runs OAA from a local checkout via `python -m src.cognition.run_cycle` (process isolation), which works but isn't pip-installable.
