---
wiki_id: persona_cole_medin
type: persona_page
persona_id: cole_medin
priority_rank: 2
status: draft
last_updated: 2026-04-18
channels:
  youtube: https://www.youtube.com/@ColeMedin
  github: https://github.com/coleam00
  linkedin: https://www.linkedin.com/in/cole-medin-727752184/
youtube_transcript_status: deferred — cloud IP blocked; run locally
---

# Persona: Cole Medin

## Who He Is

Practitioner and open-source builder in agentic AI. Known for translating cutting-edge patterns (dark factories, adversarial harnesses, autonomous pipelines) into working, reproducible implementations. Strong focus on making AI coding deterministic and trustworthy at production scale.

Core style: builds things that actually run, documents the failure modes from prior attempts, shares everything as open source.

## Key Intellectual Contributions (from ingested sources)

### Dark Factory Pattern
Autonomous software factory using GitHub as state machine, Archon as workflow engine, Claude Code as coding agent. Non-negotiable rules from real failure history (StrongDM, Spotify Honk). See [pattern_dark_factory.md](pattern_dark_factory.md) and [repo_dark_factory.md](repo_dark_factory.md).

### Archon: Deterministic AI Coding Harness
YAML-defined workflow engine. Deterministic scaffolding + AI fill. Makes "AI can sometimes do this" into "the factory does this on schedule, reliably." See [repo_archon.md](repo_archon.md).

### Adversarial Dev: GAN-inspired Evaluation
Planner / Generator / Evaluator triad. Evaluator actively tries to break what the Generator built. Eliminates self-evaluation bias. See [repo_adversarial_dev.md](repo_adversarial_dev.md).

### Second Brain Starter: Persistent Proactive AI
SOUL.md / USER.md / MEMORY.md memory architecture. Proactive 30-minute heartbeat. Hybrid keyword + semantic memory search. See [repo_second_brain_starter.md](repo_second_brain_starter.md).

## AAA Persona Signal

| Dimension | Signal |
|-----------|--------|
| Architecture stance | Deterministic scaffolding first, AI inside. Never trust a single agent to plan + build + evaluate its own work. |
| Evaluation philosophy | Holdout validation: evaluator never reads the implementation. Binary verdicts. |
| Agent design | Specialized agents with separate context windows. Adversarial tension drives quality. |
| Orchestration | YAML-defined workflows (Archon) for coding tasks; GitHub labels as state for long-running pipelines. |
| Memory | Markdown-file memory (SOUL/USER/MEMORY) over vector DB at personal scale. |

## Repo Ingestion Status

| Repo | Status | Chars |
|------|--------|-------|
| dark-factory-experiment | Complete | 10,528 |
| Archon | Complete | 13,784 |
| adversarial-dev | Complete | 10,363 |
| second-brain-starter | Complete | 5,854 |
| claude-memory-compiler | Not yet ingested | — |

## YouTube Videos Queued (run locally)

IDs: `6woc6ii-zoE`, `qMnClynCAmM`, `7huCP6RkcY4`, `1FiER-40zng`, `HAkSUBdsd6M`, `gmaHRwijOXs`, `uegyRTOrXSU`, `GX_EsbcXfw8`, `nxHKBq5ZU9U`, `NMWgXvm--to`

To run when on a non-cloud IP:
```python
from src.pipeline.youtube_ingest import YouTubeIngestPipeline, VideoTarget
pipeline = YouTubeIngestPipeline(raw_dir="data/wiki/raw", request_delay=1.5)
targets = [VideoTarget(vid, "cole_medin") for vid in IDS_ABOVE]
pipeline.run(targets)
```
