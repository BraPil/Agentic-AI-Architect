# Source Weighting Model v0

## Purpose

This document defines the first explicit source weighting model for retrieval and evaluation.

The repository previously relied on implicit confidence choices for repo-native fallbacks. That was not
good enough for a durable evaluation module because ranking behavior was partially hidden.

## Current Weighting Factors

The v0 model combines two factors.

### 1. Retrieval source weight

- `knowledge_base`: `1.00`
- `trend_registry`: `0.95`
- `framework_matrix`: `0.90`
- `tool_registry`: `0.85`

### 2. Evidence-tier weight

- `direct`: `1.00`
- `public_companion`: `0.85`
- `user_provided`: `0.80`
- `inferred`: `0.65`

## How It Is Applied

The current retrieval score begins from entry confidence and is then multiplied by:

- retrieval source weight
- evidence-tier weight

After that, query-text relevance bonuses are added.

This means stronger sources still need query relevance, but weaker or inferred sources are penalized
before ranking bonuses are applied.

## Why This Is Good Enough For v0

The goal is not perfect ranking.

The goal is to make source preference explicit and auditable while the system still uses deterministic,
testable heuristics.

## Future Refinements

Likely next steps:

- namespace-specific source weighting
- freshness-aware decay
- enterprise overlay weights
- persisted source-performance feedback from evaluation history