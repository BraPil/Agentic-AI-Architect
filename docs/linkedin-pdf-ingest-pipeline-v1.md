# LinkedIn PDF Ingest Pipeline v1

## Purpose

This document defines the repeatable ingest path for LinkedIn reaction/activity exports that have been
copied into the repository as readable PDFs.

The goal is to centralize four outputs in one place:

- per-post summaries
- diagram-intent explanations from OCR
- recurring architecture patterns
- curiosity hooks for deeper research

The ingest should bias toward architecturally useful AI/ML/agentics posts and filter out low-signal social noise.

## Input Contract

The input should be a readable PDF placed in `docs/` with a name like:

- `Agentic_AI_Architect_Ingest_YYYYMMDD.pdf`

This is the manual boundary for now: the user or operator exports the LinkedIn feed into PDF first.

## Pipeline Steps

1. Extract PDF metadata with `pdfinfo`.
2. Extract the text layer with `pdftotext -layout`.
3. Extract embedded visuals with `pdfimages -all`.
4. OCR larger visuals with `tesseract`.
5. Group text into posts using `Feed post number N` markers.
6. Strip embedded repost/profile chrome where possible.
7. Score each post for AI/ML/agentics relevance and architectural insight.
8. Filter out low-signal social posts.
9. Build one centralized report containing:
   - post summaries
   - diagram intent
   - architecture patterns
   - curiosity queue
10. Optionally seed the highest-signal retained posts into `data/knowledge_base.db` as `KnowledgeEntry` records.

## Current Output Location

The pipeline writes its machine-readable bundle to:

- `data/ingests/<pdf-stem>/`

Key artifacts:

- `raw_text.txt`
- `ingest_result.json`
- `centralized_report.md`

The structured artifacts now include:

- retained post count
- filtered-out post count
- per-post namespace
- per-post signal score
- seeded knowledge-entry count

## Current Command

```bash
/home/codespace/.python/current/bin/python -m src.pipeline.linkedin_pdf_ingest \
  docs/Agentic_AI_Architect_Ingest_20260314.pdf

/home/codespace/.python/current/bin/python -m src.pipeline.linkedin_pdf_ingest \
  docs/Agentic_AI_Architect_Ingest_20260314.pdf \
  --seed-knowledge-base \
  --db-path data/knowledge_base.db
```

## Training And Curiosity Role

This ingest pipeline does not fine-tune a model.

For the current phase, `train` means:

- collecting structured post records
- extracting diagram signals and OCR labels
- deriving reusable architecture patterns
- generating curiosity hooks that should trigger focused deep research next
- seeding the strongest retained posts into the knowledge base as durable architecture references

## Next Likely Improvements

- direct rendered-page OCR when embedded-image OCR is insufficient
- better repost and quoted-post separation
- optional LLM-backed post synthesis using sanitized extracted content