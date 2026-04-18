# AAA Wiki Index

> Content catalog for the AAA knowledge wiki.
> Three layers: raw/ (source artifacts) → pages/ (curated synthesis) → schema/ (typed extracts).
> Operations: Ingest, Query, Lint.
> Last rebuilt: 2026-04-18

---

## Personas

| Page | Source Persona | Layer | Status |
|------|---------------|-------|--------|
| [pages/persona_andrej_karpathy.md](pages/persona_andrej_karpathy.md) | Andrej Karpathy | wiki | seed |
| [pages/persona_cole_medin.md](pages/persona_cole_medin.md) | Cole Medin | wiki | seed |

## Architectural Patterns

| Page | Origin | Layer | Status |
|------|--------|-------|--------|
| [pages/pattern_llm_wiki.md](pages/pattern_llm_wiki.md) | Karpathy LLM Wiki gist | wiki | seeded |
| [pages/pattern_dark_factory.md](pages/pattern_dark_factory.md) | Cole Medin dark-factory-experiment | wiki | seed |

## Repositories

| Page | Repo | Persona | Layer | Status |
|------|------|---------|-------|--------|
| [pages/repo_nanogpt.md](pages/repo_nanogpt.md) | karpathy/nanoGPT | Karpathy | wiki | seed |
| [pages/repo_micrograd.md](pages/repo_micrograd.md) | karpathy/micrograd | Karpathy | wiki | seed |
| [pages/repo_makemore.md](pages/repo_makemore.md) | karpathy/makemore | Karpathy | wiki | seed |
| [pages/repo_autoresearch.md](pages/repo_autoresearch.md) | karpathy/autoresearch | Karpathy | wiki | seed |
| [pages/repo_dark_factory.md](pages/repo_dark_factory.md) | coleam00/dark-factory-experiment | Cole Medin | wiki | seed |
| [pages/repo_archon.md](pages/repo_archon.md) | coleam00/Archon | Cole Medin | wiki | seed |
| [pages/repo_adversarial_dev.md](pages/repo_adversarial_dev.md) | coleam00/adversarial-dev | Cole Medin | wiki | seed |
| [pages/repo_second_brain_starter.md](pages/repo_second_brain_starter.md) | coleam00/second-brain-starter | Cole Medin | wiki | seed |

## Raw Sources

| File | Type | Persona | Ingested |
|------|------|---------|---------|
| raw/karpathy/ | github_readme, youtube_transcript | Karpathy | 2026-04-18 |
| raw/cole_medin/ | github_readme, youtube_transcript | Cole Medin | 2026-04-18 |

## Lint Status

Last lint run: not yet run.
Open issues: none recorded.

---

## How to Update This Index

- Add a row when a new wiki page or raw source is ingested.
- Mark status: `seed` (stub created), `draft` (content written), `reviewed` (human verified), `stale` (needs refresh).
- Run Lint after any bulk ingest to detect orphans and contradictions.
