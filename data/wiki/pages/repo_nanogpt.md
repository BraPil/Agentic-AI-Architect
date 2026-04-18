---
wiki_id: repo_nanogpt
type: repo_page
persona: andrej_karpathy
repo: karpathy/nanoGPT
foundational: false
raw_source: data/wiki/raw/karpathy/github_karpathy_nanoGPT_readme.md
status: draft
last_updated: 2026-04-18
aaa_relevance:
  - Education — canonical GPT-2 teaching baseline; referenced across the field
  - P2 — understanding transformer architecture for knowledge extraction
  - Note: deprecated Nov 2025 in favor of nanochat
---

# karpathy/nanoGPT

## What It Is

The simplest, fastest repository for training/finetuning medium-sized GPTs. A rewrite of minGPT that prioritizes practicality over education. ~300-line `train.py` + ~300-line `model.py`. Can reproduce GPT-2 (124M) on a single 8×A100 node in ~4 days.

**Status (Nov 2025):** Deprecated in favor of [nanochat](https://github.com/karpathy/nanochat). The repo stays up for posterity but active development has moved to nanochat.

## Key Design Choice

> "prioritizes teeth over education"

Unlike minGPT (which was written to be read), nanoGPT was written to be used and hacked. The simplicity is intentional — every line is there because it has to be.

## Why It Matters for AAA

- **Canonical reference**: nanoGPT is cited as a baseline in nearly every GPT-2-scale experiment. Understanding its structure helps evaluate research claims about model changes.
- **Karpathy's teaching ladder**: micrograd → makemore → nanoGPT → nanochat is a progressive curriculum. AAA's education namespace should map this ladder explicitly.
- **autoresearch uses nanochat** (nanoGPT's successor) as its training target — the two repos are connected.
