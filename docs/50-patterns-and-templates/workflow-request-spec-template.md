# Workflow Request Specification

## 1. Client Request (Verbatim)
> What the client says they want, written as close to their own words as possible.

---

## 2. Interpreted Intent
What the client is usually trying to achieve:
- Reduce analyst workload?
- Improve response time?
- Enforce consistency?
- Reduce risk?
- Meet compliance or SLA goals?

This section translates *words* into *intent*.

---

## 3. Scope Definition
Clearly define what is **in scope** and **out of scope**.

**In scope:**
- 

**Out of scope:**
- 

This prevents scope creep and misaligned expectations.

---

## 4. Required Inputs
What data must exist for this automation to function correctly.

Examples:
- Alert source(s)
- Required fields
- Normalized data expectations
- Tenant context
- Identity of requesting user/system

If inputs are missing or unreliable, automation must degrade safely.

---

## 5. Assumptions
Explicit assumptions being made:
- Data accuracy
- Tool availability
- Permissions
- Timing
- Client maturity

Assumptions should always be documented, never implied.

---

## 6. Constraints & Limitations
Technical or operational limits that affect the design.

Examples:
- API rate limits
- Authentication model limitations
- Tool latency
- Field inconsistencies across tenants
- Regulatory or compliance constraints

This section justifies design decisions later.

---

## 7. High-Level Workflow Design (Tool-Agnostic)
Describe the workflow logically, without referencing a specific platform.

1. Trigger condition
2. Initial validation
3. Data normalization
4. Enrichment steps
5. Decision points
6. Action(s)
7. Escalation or closure

This section should read like a flowchart in text form.

---

## 8. Decision Logic
Explicitly define how decisions are made.

Examples:
- Conditional thresholds
- Boolean logic
- Risk scoring
- Confidence levels
- Required approvals

Avoid vague language. Decisions must be deterministic.

---

## 9. Human-in-the-Loop Points
Identify where and why a human must be involved.

Examples:
- Approval before destructive action
- Ambiguous results
- Policy enforcement

Explain what the human is expected to decide.

---

## 10. Failure Modes & Safe Handling
What can go wrong, and how the workflow should respond.

Examples:
- API failure
- Timeout
- Partial enrichment
- Invalid input
- Tool outage

Describe:
- Fail-open vs fail-closed behavior
- Alerting/logging expectations

---

## 11. Tool-Specific Implementation Notes
Platform-specific considerations (e.g., Torq).

Examples:
- Trigger configuration
- Variable handling
- Conditional blocks
- Error handling constructs
- Reusability (subflows, templates)

This is where tool familiarity is demonstrated.

---

## 12. API Integration Notes
If APIs are involved, document:

- Endpoints used
- Authentication method
- Pagination handling
- Rate limiting strategy
- Idempotency considerations
- Retry logic

Even high-level notes are acceptable here.

---

## 13. Scripting or Data Transformation (If Applicable)
Describe any custom logic required.

Examples:
- Parsing
- Normalization
- Regex extraction
- Deduplication key generation

Reference scripts if they exist in `/scripts`.

---

## 14. Testing Strategy
How this workflow should be tested before production.

Examples:
- Test inputs
- Expected outputs
- Edge cases
- Failure simulations

---

## 15. Operational Considerations
How this workflow behaves in production.

Examples:
- Logging
- Metrics
- Alert fatigue
- Maintenance
- Versioning

---

## 16. Client Communication Notes
How this workflow should be explained to a client.

Examples:
- What it does
- What it does not do
- Why certain limitations exist
- How success is measured

This section demonstrates customer-facing maturity.

---
