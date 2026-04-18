---
wiki_id: repo_makemore
type: repo_page
persona: andrej_karpathy
repo: karpathy/makemore
foundational: false
raw_source: data/wiki/raw/karpathy/github_karpathy_makemore_readme.md
status: draft
last_updated: 2026-04-18
aaa_relevance:
  - Education — character-level language model series; companion to nn-zero-to-hero
  - Teaching ladder: builds from bigram → MLP → CNN → RNN → Transformer
---

# karpathy/makemore

## What It Is

A character-level autoregressive language model that "makes more" of things. Given a list of words (names, cities, etc.) it learns to generate more in the same style. Companion repo to the nn-zero-to-hero YouTube series.

Implements a progressive series of models in increasing complexity: bigram → MLP → CNN → RNN/LSTM → Transformer. Each is implemented from scratch in a single Jupyter notebook with full explanation.

## Teaching Ladder Position

`micrograd` → **`makemore`** → `nanoGPT` → `nanochat` → `autoresearch`

makemore bridges: raw probability tables → learned representations → sequence modeling → transformers.

## Why It Matters for AAA

The progression from bigram to transformer in one repo is the best compact explanation of why transformers win. Useful context for evaluating architecture claims in papers and tools.
