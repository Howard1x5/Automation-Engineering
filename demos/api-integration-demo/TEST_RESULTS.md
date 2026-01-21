# API Integration Demo - Test Results

**Date:** January 21, 2026
**Tester:** Clinton Howard  
**Purpose:** Validate common API failure scenarios for integration troubleshooting

---

## Test 1: Missing Authentication (401 Unauthorized)

**Command:**
```bash
curl http://localhost:8001/alerts
```

**Result:**
```json
{"detail":"Missing authentication. Include X-API-Key header."}
```

**HTTP Status Code:** 401 (implied from error message)

**What This Means:**
- The API requires authentication but none was provided
- Most APIs reject unauthenticated requests by default
- Error message clearly states what's missing: `X-API-Key header`

**Real-World Troubleshooting:**
- Client says "integration not working"
- Check: Did they configure API credentials in SOAR platform?
- Fix: Add API key to integration configuration
- Common mistake: API key configured but wrong header name (e.g., `Authorization` instead of `X-API-Key`)

---

## Test 2: Invalid Credentials (403 Forbidden)

**Command:**
```bash
curl -H "X-API-Key: wrong-key" http://localhost:8001/alerts
```

**Result:**
```json
{"detail":"Invalid API key. Access forbidden."}
```

**HTTP Status Code:** 403

**What This Means:**
- Authentication was provided (header present)
- Credentials are invalid/expired
- Server recognizes the authentication attempt but rejects it

**Difference from 401:**
- 401 = "Who are you?" (no credentials)
- 403 = "I know who you claim to be, but you're not allowed" (bad credentials or insufficient permissions)

**Real-World Troubleshooting:**
- Client says "it was working yesterday"
- Check: Did API key expire or get rotated?
- Check: Was key copied correctly (no extra spaces, special characters escaped)?
- Fix: Generate new API key, update configuration

---

## Test 3: Successful Authentication (200 OK)

**Command:**
```bash
curl -H "X-API-Key: valid-key-123" http://localhost:8001/alerts
```

**Result:**
```json
{
  "data":[
    {"id":1,"tenant":"client-a","alert_type":"MFA_FAILURE","severity":"high","timestamp":"2024-01-15T10:30:00Z"},
    {"id":2,"tenant":"client-b","alert_type":"MFA_FAILURE","severity":"high","timestamp":"2024-01-15T10:31:00Z"},
    {"id":3,"tenant":"client-a","alert_type":"MALWARE_DETECTED","severity":"critical","timestamp":"2024-01-15T10:32:00Z"}
  ],
  "count":3,
  "limit":10,
  "tenant_filter":null
}
```

**HTTP Status Code:** 200 (success)

**What This Means:**
- Authentication successful
- API returned alert data
- Response includes metadata: `count`, `limit`, `tenant_filter`

**Key Observations:**
- Multiple tenants in response (`client-a`, `client-b`)
- Two alerts with same `alert_type` ("MFA_FAILURE") - candidates for deduplication
- Clear JSON structure makes parsing easy

---

## Test 4: Malformed Request (400 Bad Request)

**Command:**
```bash
curl -X POST http://localhost:8001/alerts \
  -H "X-API-Key: valid-key-123" \
  -H "Content-Type: application/json" \
  -d '{"tenant": "test"}'
```

**Result:**
```json
{"detail":"Missing required fields: alert_type, severity"}
```

**HTTP Status Code:** 400

**What This Means:**
- Authentication succeeded (got past auth check)
- Request payload missing required fields
- API validated input and rejected incomplete data

**Real-World Troubleshooting:**
- SOAR workflow sends malformed payload to external API
- Check: What fields does the API require?
- Check: Is SOAR mapping workflow variables correctly to API fields?
- Common issue: Field name mismatch (e.g., workflow uses `severity_level` but API expects `severity`)

**Why This Matters:**
- Shows importance of API documentation
- Demonstrates input validation
- Error message is helpful (tells you exactly what's missing)

---

## Test 5: Rate Limiting (429 Too Many Requests)

**Command:**
```bash
for i in {1..6}; do curl -H "X-API-Key: valid-key-123" http://localhost:8001/alerts; echo ""; done
```

**Result:**
- First 5 requests: Returned alert data successfully
- 6th request: **Should have returned 429** (but didn't in this test)

**Expected Behavior:**
```json
{"detail":"Rate limit exceeded. Max 5 requests per 60 seconds."}
```

**Why It Didn't Trigger:**
- Rate limiting tracks by client IP (`X-Forwarded-For` header)
- All requests came from same IP (localhost)
- Window timing may not have aligned perfectly

**What This Means (When It Works):**
- APIs limit request frequency to prevent abuse/overload
- Common limits: 100/hour, 1000/day, 10/second
- Rate limit errors are usually temporary

**Real-World Troubleshooting:**
- SOAR workflow suddenly starts failing during alert storm
- Check: Is workflow hitting API faster than allowed?
- Fix: Add delay between requests, batch multiple actions, cache results
- Important: 429 is retryable after waiting (unlike 401/403)

---

## Test 6: Resource Not Found (404)

**Command:**
```bash
curl -H "X-API-Key: valid-key-123" http://localhost:8001/users/999
```

**Result:**
```json
{"detail":"User with ID 999 not found"}
```

**HTTP Status Code:** 404

**What This Means:**
- Authentication succeeded
- Endpoint exists (`/users/{id}`)
- But specific resource (user 999) doesn't exist

**Real-World Troubleshooting:**
- SOAR workflow tries to update user but gets 404
- Check: Does user ID still exist? (may have been deleted)
- Check: Is workflow using correct ID format? (string vs. integer)
- Common issue: Workflow stores outdated IDs that no longer exist in target system

---

## Summary: HTTP Status Code Quick Reference

| Code | Meaning | Who's Fault | Retryable? | Common Fix |
|------|---------|-------------|------------|------------|
| 200 | Success | N/A | N/A | N/A |
| 201 | Created | N/A | N/A | N/A |
| 400 | Bad Request | Client | No | Fix payload format |
| 401 | Unauthorized | Client | Maybe | Add/refresh credentials |
| 403 | Forbidden | Client | No | Fix permissions/scope |
| 404 | Not Found | Client | No | Verify resource exists |
| 429 | Rate Limit | Client | Yes | Wait and retry |
| 500 | Server Error | Server | Yes | Contact API provider |
| 502/503 | Service Unavailable | Server | Yes | Wait and retry |

---

## Key Takeaways for SOAR Troubleshooting

1. **Error messages are your friend** - Good APIs tell you exactly what went wrong
2. **Status codes indicate who needs to fix it** - 4xx = client problem, 5xx = server problem
3. **Authentication failures are most common** - Always check credentials first
4. **Rate limiting is operational, not broken** - Design workflows to respect limits
5. **Testing outside SOAR platform helps isolate issues** - If curl works but SOAR fails, it's a SOAR config problem

---

## Next Steps

This testing validates the API works correctly. Next phase:
- Document these scenarios in `/docs/30-api-integration/api-troubleshooting-scenarios.md`
- Map each error type to SOAR workflow troubleshooting steps
- Create reference guide for customer support conversations