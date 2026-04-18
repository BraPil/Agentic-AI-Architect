---
wiki_id: repo_micrograd
type: repo_page
persona: andrej_karpathy
repo: karpathy/micrograd
foundational: false
raw_source: data/wiki/raw/karpathy/github_karpathy_micrograd_readme.md
status: draft
last_updated: 2026-04-18
aaa_relevance:
  - Education — foundational teaching tool for backpropagation
  - First rung of Karpathy's teaching ladder
---

# karpathy/micrograd

## What It Is

A minimal scalar-valued autograd engine in ~150 lines of Python, plus a small neural network library on top. Implements backpropagation over a dynamically built DAG and a small PyTorch-like neural net API.

The repo is the first step in Karpathy's nn-zero-to-hero course. Purpose: demystify backpropagation by showing the complete implementation in one readable file.

## Teaching Ladder Position

`micrograd` → `makemore` → `nanoGPT` → `nanochat` → `autoresearch`

micrograd teaches: how a Value object tracks gradients, how the chain rule flows backward, why every modern ML framework does what it does.

## Why It Matters for AAA

Context for evaluating claims about gradient-based learning. Also the starting point for anyone learning from Karpathy's material — understanding which repo a learner is at tells you what they understand.
