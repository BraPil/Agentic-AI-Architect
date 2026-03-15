# Source Weighting Model v2

## Purpose

This document defines the second retrieval-weighting model.

The v1 model made source preferences explicit. The v2 model keeps that explicit base but adds two new
signals:

- learned multipliers from persisted evaluation outcomes
- freshness-aware decay tied to the requested time horizon

## v2 Weighting Components

The ranking score now combines four factors before text-match bonuses are added:

- base source weight
- evidence-tier weight
- learned source multiplier
- freshness multiplier

## Learned Source Multipliers

Recent persisted evaluation runs are flattened into observations of:

- normalized score
- answer segment
- retrieval sources used by that answer

Each retrieval source receives a conservative multiplier based on recent normalized scores. The model is
intentionally modest and bounded so one or two runs cannot produce unstable jumps.

### Range

- minimum multiplier: `0.85`
- neutral multiplier: `1.00`
- maximum multiplier: `1.15`

## Segment-Aware Learning

When enough history exists, the system prefers segment-specific learned multipliers over global ones.

That means enterprise queries can learn a different source preference than startup queries without needing
separate hard-coded tables.

## Freshness Decay

Freshness decay is applied from the entry `updated_at` timestamp.

The floor and half-life depend on the requested time horizon:

- `now`: strongest recency pressure
- `4-weeks`: moderate recency pressure
- `quarter`: light recency pressure

This prevents stale high-confidence entries from dominating current decisions when fresher evidence exists.

## Why This Is Good Enough For v2

The goal is still not perfect retrieval.

The goal is to make ranking adapt to observed answer quality while keeping the system deterministic,
auditable, and cheap to evaluate.