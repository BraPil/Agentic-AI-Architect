---
wiki_id: persona_andrej_karpathy
type: persona_page
persona_id: karpathy
priority_rank: 1
status: draft
last_updated: 2026-04-18
channels:
  youtube: https://www.youtube.com/@AndrejKarpathy
  github: https://github.com/karpathy
  linkedin: https://www.linkedin.com/in/andrej-karpathy-9a650716/
youtube_transcript_status: deferred — cloud IP blocked; run locally
---

# Persona: Andrej Karpathy

## Who He Is

Former OpenAI co-founder and Director of AI at Tesla. Now independent researcher, educator, and builder. One of the most trusted voices on deep learning, LLMs, and AI systems architecture.

Core style: builds things from scratch to understand them. Every repo is a minimal, readable implementation of something that usually takes far more code. Teaches by stripping away until only the essential idea remains.

## Key Intellectual Contributions (from ingested sources)

### Teaching Ladder
`micrograd` → `makemore` → `nanoGPT` → `nanochat` → `autoresearch`

A progressive curriculum from scalar autograd to autonomous research loops. Understanding where someone is on this ladder tells you what they understand about deep learning.

### LLM Wiki Architecture
Three-layer knowledge system (raw / wiki / schema) + Ingest-Query-Lint operations. The foundational architectural spec for AAA's knowledge layer. See [pattern_llm_wiki.md](pattern_llm_wiki.md).

### autoresearch: Autonomous Overnight Research
Give an agent a GPU and a training setup, let it experiment autonomously with a fixed 5-minute budget per experiment, fixed evaluation metric. Human improves `program.md` (the research org instructions), not `train.py` (the code being improved). See [repo_autoresearch.md](repo_autoresearch.md).

## AAA Persona Signal

| Dimension | Signal |
|-----------|--------|
| Architecture stance | Minimal first, then layer complexity. Never FAISS before structured index. |
| Evaluation philosophy | Fixed metrics, fixed budgets, holdout evaluation only. |
| Agent design | Agents edit code; humans edit instructions (program.md = CLAUDE.md analog). |
| Scale thinking | Structured index beats RAG at <500 sources. Graduate to scale incrementally. |
| Self-improvement | Overnight loop with measurable, comparable experiments. |

## Ingestion Status

| Channel | Status | Count |
|---------|--------|-------|
| GitHub READMEs | Complete | 4 repos (nanoGPT, micrograd, makemore, autoresearch) |
| LLM Wiki gist | Complete (foundational seed) | 1 gist |
| YouTube transcripts | Deferred — Codespace IP blocked by YouTube | 10 videos queued |
| LinkedIn posts | Deferred — auth-blocked | Queued |

## YouTube Videos Queued (run locally)

IDs: `EWvNQjAaOHw`, `7xTGNNLPyMI`, `l8pRSuU81PU`, `zduSFxRajkE`, `zjkBMFhNj_g`, `kCc8FmEb1nY`, `t3YJ5hKiMQ0`, `q8SA3rM6ckI`, `P6sfmUTpUmc`, `TCH_1BHY58I`

To run when on a non-cloud IP:
```python
from src.pipeline.youtube_ingest import YouTubeIngestPipeline, VideoTarget
pipeline = YouTubeIngestPipeline(raw_dir="data/wiki/raw", request_delay=1.5)
targets = [VideoTarget(vid, "karpathy") for vid in IDS_ABOVE]
pipeline.run(targets)
```
