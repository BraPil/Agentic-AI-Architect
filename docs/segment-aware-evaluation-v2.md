# Segment-Aware Evaluation v2

## Purpose

This document defines the first explicit segment-comparison evaluation path.

The contract already carried segment metadata and enterprise overlay fields, but v1 could not compare how
the same query behaved across startup, small-company, and enterprise contexts.

## New Capability

The API now supports evaluating the same query across multiple requested segments and summarizing:

- compared segments
- average normalized score
- verdict counts
- best segment for the current answer shape
- score spread across segments

## Why This Matters

Segment-awareness only becomes operational when it is measurable.

This comparison path makes it possible to detect:

- when one answer is too enterprise-biased
- when startup and small-company recommendations collapse into the same generic output
- when retrieval and overlays are not actually differentiating segment behavior

## Current Limitation

The v2 comparison path still reuses the shared evaluation question set and adapts the segment at scoring
time.

That is good enough for v2, but a future version may want a dedicated segment-native evaluation subset.