# Enterprise Overlay Fields v0

## Purpose

This document defines the first structured enterprise overlay carried inside the canonical answer contract.

The system was already segment-aware at the request level, but that was not enough. A durable answer also
needs to say whether the recommendation is enterprise-safe now, what would need to change by segment, and
which future governance hooks must stay intact.

## v0 Overlay Shape

The overlay is stored in `enterprise_overlay` with the following fields:

- `enterprise_safe_now`
- `reasoning`
- `key_requirements`
- `future_alignment_hooks`
- `segment_deltas`

Each `segment_delta` contains:

- `segment`
- `adjustment_summary`
- `key_priorities`

## Why This Exists

The current cycle explicitly asks the system to answer:

- is this enterprise-safe enough to recommend now
- what parts of this recommendation are segment-specific
- what would differ for a startup or smaller company

These fields turn that requirement into machine-readable output instead of leaving it as prose.

## v0 Design Rule

The overlay should stay conservative.

If the answer is built from fallback signals, incomplete provenance, or cross-segment generalization, the
overlay should say so and avoid overstating enterprise readiness.

## Expected v0 Use

The overlay is intended to support:

- enterprise-facing API answers
- evaluation of segment-aware recommendations
- future governance, auditability, and policy systems
- later source and recommendation calibration work