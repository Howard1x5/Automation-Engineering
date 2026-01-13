# Process Improvement: Deterministic Decision Logic

## Context
During the initial workflow specification, decision logic was described
conceptually but lacked deterministic thresholds. This document captures
the approach used to make automation decisions explicit, tunable, and
executable.

---

## Why Deterministic Decision Logic Matters

Automation systems must make decisions that are:
- Explainable
- Repeatable
- Auditable

Vague logic increases analyst confusion and automation risk.
Explicit thresholds allow safe iteration and client-specific tuning.

---

## Example Threshold Models

### Confidence-Based Thresholds
- High confidence: ≥ 90
- Medium confidence: 60–89
- Low confidence: < 60

These values act as **defaults**, not absolutes.

---

## Why Placeholder Thresholds Are Acceptable

- Initial values establish decision shape
- Thresholds are tuned using:
  - Historical alert data
  - False positive rates
  - Client risk tolerance
- Explicit placeholders are safer than implicit assumptions

Incorrect numbers can be adjusted.
Ambiguous logic cannot.

---

## How Thresholds Are Tuned Per Client

Thresholds are refined based on:
- Client security maturity
- Business impact tolerance
- Alert volume
- Tool coverage and telemetry quality
- Regulatory or compliance constraints

All thresholds must be:
- Documented
- Reviewed
- Versioned
