# Phishing Triage and Conditional Escalation

## Workflow Request Specification

---

## 1. Client Request (Verbatim)

> The client wants phishing alerts to be ingested, triaged as thoroughly as possible by automation, and escalated to a human analyst only when specific conditions are met.
>
> Examples include malicious URL clicks, malicious attachment interactions, signs of user account compromise, password attack activity following phishing interaction, and identification of similar emails from the same malicious sender internally.
>
> The goal is for analysts to receive a single, enriched view of the investigation so they do not need to manually query logs or build custom searches before taking action.

---

## 2. Interpreted Intent

The client’s primary intent is to **reduce analyst workload** for high-volume phishing alerts while **improving response speed and consistency**.

Phishing alerts are frequent, noisy, and often arrive in bursts during campaigns. Automating the investigation allows analysts to focus on higher-severity incidents and respond more quickly to confirmed threats.

Secondary goals include:

* Faster containment of phishing campaigns
* Consistent investigation results
* Reduced time spent on repetitive research
* Better handling of burst-style phishing activity without overwhelming analysts
* Meeting SLA expectations during peak alert volume

---

## 3. Scope Definition

### In Scope

* Automated enrichment of phishing alerts into a single investigative view
* Validation of user interaction with phishing content (links or attachments)
* Correlation of email activity with proxy, identity, and sign-in telemetry
* Conditional escalation when confidence thresholds are met
* Automatic actions for high-confidence scenarios (e.g., account reset, endpoint isolation) where permitted
* Identification of potential broader phishing campaigns based on internal email volume

### Out of Scope

* Full malware response workflows beyond phishing detection
* Long-term threat hunting beyond the phishing incident
* Deep forensic investigation
* Remediation actions requiring tooling or permissions not available to the MSSP

Phishing workflows may *trigger* downstream alerts (e.g., malware or password attacks), but those should be handled by **separate workflows** to avoid uncontrolled scope expansion.

---

## 4. Required Inputs

For this workflow to function correctly, the following inputs are required:

* Email security telemetry (e.g., Exchange, Proofpoint, Defender for Office)
* User identity data (Entra ID / Active Directory)
* Proxy or network telemetry to confirm URL connections
* Sign-in and audit logs to detect suspicious authentication activity
* Endpoint telemetry for potential isolation actions
* Alert normalization across sources (direct ingestion or via SIEM)
* OSINT integrations (e.g., VirusTotal, AlienVault OTX, Google Threat Intelligence)

If any of these inputs are missing or inconsistent, the automation must degrade safely and escalate to a human analyst.

---

## 5. Assumptions

* Required security tools are integrated and accessible
* Alert data is accurate and timely
* The client has a baseline level of security maturity
* The MSSP has sufficient permissions for approved response actions
* Email security rules (e.g., direct send handling) are already in place or documented
* Phishing has been identified as a known pain point for the client

---

## 6. Constraints & Limitations

* API rate limits may restrict enrichment depth or frequency
* MSSP permissions may not allow automated destructive actions
* Some clients may require approval before endpoint isolation or password resets
* Telemetry gaps (e.g., log outages) may reduce confidence scoring
* Multi-tenant environments introduce policy variability
* Communication workflows may be required when automation cannot act directly

These constraints may require escalation rather than automation.

---

## 7. High-Level Workflow Design (Tool-Agnostic)

1. **Trigger:** Phishing email released from quarantine and user interaction detected
2. **Validation:** Confirm the interaction was intentional (not cache or preview load)
3. **Normalization:** Normalize alert data across email, proxy, and identity sources
4. **Enrichment:**

   * URL reputation via OSINT
   * Proxy logs confirming domain connection
   * Identity logs for suspicious sign-ins
5. **Decision:** Determine confidence of compromise
6. **Action:**

   * High confidence → account revoke/reset, endpoint isolation, escalate
   * Low confidence → informational close
7. **Escalation:** Human review for destructive or ambiguous cases

---

## 8. Decision Logic

### Evidence Scoring (Default Model)

Each signal contributes to a cumulative confidence score.

- Proxy-confirmed URL access: +40
- OSINT verdict = malicious: +30
- Suspicious sign-in following interaction: +30
- No proxy access detected: −40
- Known benign domain: −30

### Confidence Thresholds (Default)

- ≥ 90: High confidence compromise
- 60–89: Medium confidence
- < 60: Low confidence

### Outcomes

- High confidence (≥ 90):
  - Automated containment actions where permitted
  - Escalation to analyst for confirmation

- Medium confidence (60–89):
  - Escalation to analyst
  - No automated destructive action

- Low confidence (< 60):
  - Close as informational
  - No action required

### Notes

- Thresholds are tunable per client
- Default values are adjusted based on historical alert data,
  false positive rates, and client risk tolerance

---

## 9. Human-in-the-Loop Points

Human approval is required for:

* Endpoint isolation
* Account revocation or password reset below confidence thresholds
* Ambiguous enrichment results (e.g., VPN or shared infrastructure)
* Policy enforcement decisions
* Client-specific exceptions

The analyst’s role is to confirm risk and approve or deny action.

---

## 10. Failure Modes & Safe Handling

Potential failures include:

* API outages
* Missing telemetry
* Partial enrichment
* Identity or proxy log ingestion failures

Safe handling includes:

* Failing closed for destructive actions
* Escalating when confidence cannot be established
* Logging and alerting when required data sources are unavailable
* Pausing workflows during major telemetry outages

---

## 11. Tool-Specific Implementation Notes

* Workflow triggers based on phishing alert ingestion
* Conditional logic implemented via decision blocks
* Reusable subflows for enrichment
* Error handling paths for partial or failed integrations

Tool familiarity will be expanded as platform knowledge increases.

---

## 12. API Integration Notes

Areas requiring further research:

* Email security APIs
* Identity and endpoint management APIs
* OSINT service APIs
* Rate limiting and pagination handling
* Authentication models

This is an identified learning gap.

---

## 13. Scripting or Data Transformation

Custom scripting may be required to:

* Normalize inconsistent alert payloads
* Extract URLs or IOCs
* Generate deduplication keys
* Prepare enrichment data for downstream steps

Scripts may be implemented in Python and stored under `/scripts`.

---

## 14. Testing Strategy

* Simulated phishing URLs with controlled reputation scores
* Test user interactions with and without proxy connections
* Validate escalation paths
* Stress test with high alert volume
* Confirm safe handling during telemetry outages

---

## 15. Operational Considerations

* Monitor alert throughput and workflow latency
* Track escalation rates and false positives
* Identify bottlenecks in enrichment steps
* Version workflows to support incremental improvements

---

## 16. Client Communication Notes

Explain to the client:

* What the workflow automates and why
* Where human approval is required
* What actions are intentionally not automated
* How success is measured (reduced analyst time, faster response, fewer false positives)

Success is measured by:

* Reduced time spent on phishing alerts
* Increased automated resolution
* More meaningful escalations to analysts

---