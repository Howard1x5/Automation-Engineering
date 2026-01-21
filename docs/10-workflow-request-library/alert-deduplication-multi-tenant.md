# Workflow Request Specification
## Alert Deduplication Across Multiple Tenants

---

## 1. Client Request (Verbatim)

> "We need to do something about all these duplicate alerts. Our analysts are spending too much time on the same thing across multiple tenants."

The MSSP operations manager describes the pain as:
- Analyst queues filled with what appears to be the same alert repeated across 5, 10, or 20+ tenants
- High-quality analysts wasting time closing duplicates instead of investigating real threats
- Alert volume creating the illusion of workload when much of it is redundant

---

## 2. Interpreted Intent

The client's actual goals are:

**Primary intent:**
- Reduce analyst time spent on redundant work
- Allow high-quality analysts to focus on deep investigation, not duplicate cleanup
- Group correlated alerts so one analyst can work the issue once and close it for all affected tenants

**Secondary intent:**
- Improve analyst morale (less "busy work")
- Better utilize senior analyst time
- Maintain or improve response times without adding headcount

**What this is NOT about:**
- SLA gaming (their metrics already look good from fast duplicate closures)
- Alert suppression that could hide real incidents
- Reducing all alert volume indiscriminately

**The core challenge:**
How do we identify that "Failed MFA - user locked out" firing for 15 different tenants is actually the *same underlying event* (e.g., Microsoft Entra change, MFA service disruption) and should be grouped, rather than 15 separate user account issues that happen to look similar?

---

## 3. Scope Definition

### In Scope

**Phase 1 - Correlation Detection (Primary Automation Goal):**
- Detect when the same alert type fires across multiple tenants within a defined time window
- Group correlated alerts based on:
  - Alert name/type
  - Common trigger source (e.g., Microsoft/Entra service, MFA provider)
  - Similar timing pattern
  - Normalized alert metadata (excluding tenant-specific fields like individual usernames/IPs)

**Phase 2 - Case Hierarchy (After Correlation Confirmed):**
- Create one parent case representing the underlying issue
- Link child cases for each affected tenant
- Validate that children truly match the parent pattern
- Present grouped view to analyst with all tenant context in single pane

**Phase 3 - Enrichment:**
- Pull relevant context for all affected tenants
- Surface commonalities (service disruption, provider issue, configuration change)
- Flag discrepancies that might indicate false grouping

**Time Window:**
- Alerts arriving within [15 minutes / 1 hour / tunable] are candidates for correlation
- Window must account for staggered alert delivery across tenants

### Out of Scope

**Explicitly NOT Automated:**
- Full investigation of the root cause
- Automatic closure/suppression without human review
- Initial determination of "is this a real incident or false positive?"
- SLA management or contractual obligation tracking (analyst responsibility)
- Auto-closing child cases based on parent resolution (requires human confirmation first)

**Only After Human-in-the-Loop Approval:**
- Suppression of future similar alerts (dangerous without analyst validation)
- Bulk closure of child cases
- Changes to detection rules or thresholds

**Not This Workflow:**
- Alert storms from different root causes (separate workflow)
- Predictive grouping before alerts fire
- Cross-client correlation for non-multi-tenant scenarios

---

## 4. Required Inputs

### Mandatory Data Fields (Per Alert)
For correlation logic to function, each alert must contain:

**Core Identifiers:**
- Tenant ID or tenant name (consistent field across all alert sources)
- Alert name/type (normalized)
- Alert source system (e.g., "Microsoft Defender", "Entra ID", "Custom SIEM Rule")
- Timestamp (alert generation time, not ingestion time)
- Source type (authentication, endpoint, network, etc.)

**Correlation Fields:**
- Service/provider involved (e.g., "Microsoft MFA", "Entra ID", "Okta")
- Error type or failure reason (if applicable)
- Alert severity/priority

**Data Quality Requirements:**
- Field names must be consistent across tenants
- Timestamps must be in normalized format (UTC recommended)
- Alert names from custom rules should follow naming conventions similar to vendor alerts

### System Requirements

**SIEM/Log Aggregation:**
- Centralized index or cross-tenant query capability
- Ability to search across multiple tenant indexes simultaneously
- Parsed/normalized logs (not raw, unless normalization can occur in real-time)

**Case Management / Ticketing:**
- API access to create parent/child case relationships
- Field to track "grouped with" or "parent case ID"
- Ability to update case metadata when grouping occurs

**Workflow Platform (Torq/SOAR):**
- Access to alert stream in near-real-time
- State storage to track which alerts have been evaluated for grouping
- Time-window tracking (which alerts are still eligible for correlation)

### Optional but Recommended

**External Service Status:**
- Microsoft Service Health API (enrichment for Microsoft-related alerts)
- MFA provider status pages (Okta, Duo, etc.)
- Helps confirm "this is a provider issue" vs. "this is targeted activity"
- Used for enrichment only, not primary correlation logic

### Known Challenges / Normalization Requirements

**Cross-Source Alert Normalization:**
If alerts originate from different systems (EDR, email gateway, SIEM correlation rules), normalization must occur either:
- At SIEM ingestion (preferred)
- Via SOAR data transformation step (adds complexity)
- Through standard field mapping maintained by MSSP

**Custom vs. Vendor Alerts:**
- Custom SIEM correlation rules may have different naming patterns than vendor alerts
- Correlation logic must accommodate variations (fuzzy matching, keyword extraction)
- Example: "MFA Authentication Failure - Multiple Attempts" (vendor) vs. "Failed_MFA_Custom" (custom rule)

**Tenant Identifier Consistency:**
Critical assumption: tenant ID/name field must be:
- Present in every alert
- Spelled/formatted identically across all sources
- Not subject to case sensitivity issues

---

## 6. Constraints & Limitations

### Performance Constraints

**Query Performance:**
- Cross-tenant SIEM queries (index=* style searches) may be slow or resource-intensive
- Alert correlation must complete within reasonable time window (seconds, not minutes)
- SOAR platform may have limits on concurrent API calls or query complexity

**Scaling Constraints:**
- During actual widespread incidents (e.g., Microsoft outage), alert volume may overwhelm correlation logic
- Time-window correlation becomes harder with 1000+ alerts in 15 minutes
- Memory/state management for tracking "alerts eligible for grouping" at scale

### Design Compromises Due to Constraints

**Rather than querying SIEM repeatedly:**
- Preferred approach: SOAR ingests alert stream directly from SIEM
- Correlation happens on SOAR side using in-memory state tracking
- Or: Create dedicated SIEM index/saved search optimized for multi-tenant correlation

**Time Window Trade-offs:**
- Shorter window (5-15 min) = faster grouping, but may miss late-arriving alerts
- Longer window (1 hour) = better correlation, but delays analyst visibility
- Must be tunable based on MSSP operational reality

### Data Quality Constraints

**Normalization is not SOAR's job:**
- If field names vary (e.g., "TenantID" vs. "tenant_name" vs. "ClientID"), SOAR cannot reliably correlate
- Custom scripting to "fix" bad data adds fragility and maintenance burden
- **Strong recommendation:** Data normalization happens at SIEM ingestion, not in workflow

**Client-Specific Variations:**
- Some tenants may have custom alert naming that breaks pattern matching
- Some tenants may have different log verbosity (missing fields)
- Correlation logic must gracefully handle missing data without failing

### Operational Constraints

**SLA Heterogeneity:**
- Grouped alerts may contain mix of high-priority and low-priority tenants
- Analysts must see SLA requirements clearly in parent case view
- Cannot auto-close all children based on parent resolution (contracts may require individual review)

**Human-in-the-Loop Requirement:**
- First instance of any correlation pattern requires human validation
- Suppression/auto-closure only after analyst confirms pattern is benign
- Must track "have we seen this pattern before?" state

---

## 7. High-Level Workflow Design (Tool-Agnostic)

1. Trigger condition
2. 
3. 
4. 
5. 
6. 
7. 

---

## 8. Decision Logic

### Deduplication Key Strategy
[How do you determine "these alerts are the same event"?]

### Time Window
[How long do you wait before deciding to dedupe/suppress?]

### Thresholds
[When do you create one parent case vs. individual cases?]

---

## 9. Human-in-the-Loop Points
[When does an analyst need to be involved?]

---

## 10. Failure Modes & Safe Handling
[What breaks? What happens if dedup logic fails?]

---

## 11. Tool-Specific Implementation Notes
[Torq/SOAR platform considerations]

---

## 12. API Integration Notes
[What systems need to be queried? What state needs to be tracked?]

---

## 13. Scripting or Data Transformation
[Any normalization needed across tenant alert formats?]

---

## 14. Testing Strategy
[How do you test multi-tenant dedup without impacting production?]

---

## 15. Operational Considerations
[Logging, metrics, what could go wrong in production?]

---

## 16. Client Communication Notes
[How do you explain this to MSSP leadership and individual tenant clients?]

---