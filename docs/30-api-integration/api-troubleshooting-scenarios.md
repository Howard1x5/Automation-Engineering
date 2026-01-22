# API Troubleshooting Scenarios - Complete Reference

**Purpose:** Real-world API integration failure diagnosis and resolution guide

**Related Demo:** See `/demos/api-integration-demo/` for a working API that demonstrates these failure modes.

---

---

## Quick Reference: HTTP Status Codes

### Success Codes (2xx)
- **200 OK** - Request succeeded, data returned
- **201 Created** - Resource successfully created (POST/PUT)
- **204 No Content** - Request succeeded, no data to return

### Client Errors (4xx) - "YOU have a problem"
- **400 Bad Request** - Malformed payload, missing fields, invalid data types
- **401 Unauthorized** - Missing or invalid authentication credentials
- **403 Forbidden** - Valid credentials but insufficient permissions/scope
- **404 Not Found** - Endpoint or resource doesn't exist
- **429 Too Many Requests** - Rate limit exceeded

### Server Errors (5xx) - "THEY have a problem"
- **500 Internal Server Error** - Backend crashed or unhandled exception
- **502 Bad Gateway** - Upstream server returned invalid response
- **503 Service Unavailable** - Service temporarily down (maintenance, overload)
- **504 Gateway Timeout** - Upstream server didn't respond in time

### Retryable vs Non-Retryable

**✅ RETRYABLE (might work if you try again):**
- 429 (rate limit - retry after waiting)
- 500/502/503/504 (server issues - retry with exponential backoff)
- Network timeouts

**❌ NOT RETRYABLE (fix the problem first):**
- 401/403 (fix authentication/permissions)
- 400 (fix payload format)
- 404 (verify resource exists)

---

## Scenario 1: Missing Authentication (401 Unauthorized)

### Symptom
Integration fails immediately on first request

### Error Response Example
```json
{
  "detail": "Missing authentication. Include X-API-Key header."
}
```

### HTTP Status Code
**401 Unauthorized**

### What This Means
- API requires authentication but none was provided
- The request doesn't include required credentials at all
- Most common issue: integration configured but credentials never added

### Diagnosis Steps
1. Check SOAR platform integration configuration
2. Verify API key/token field is populated
3. Check if credentials are in correct format (no extra spaces, line breaks)
4. Verify correct authentication method (header vs. query param vs. body)

### Common Causes
- API key field left blank in configuration
- Credentials stored in wrong field
- Wrong authentication header name (e.g., using `Authorization` when API expects `X-API-Key`)
- Credentials not saved after configuration

### Resolution
1. Obtain valid API credentials from service provider
2. Configure credentials in SOAR integration settings
3. Verify header/parameter name matches API documentation
4. Test with simple API call to confirm authentication works

### How to Explain to Client
> "The integration isn't connecting because authentication credentials haven't been configured. We need to add your API key to the integration settings. Once configured, the workflow will authenticate properly with the API."

### Testing Outside Platform
```bash
# This will fail with 401
curl http://localhost:8001/alerts

# This will succeed
curl -H "X-API-Key: valid-key-123" http://localhost:8001/alerts
```

---

## Scenario 2: Invalid Credentials (403 Forbidden)

### Symptom
Integration was working, suddenly starts failing  
OR: Integration never worked despite credentials being configured

### Error Response Example
```json
{
  "detail": "Invalid API key. Access forbidden."
}
```

### HTTP Status Code
**403 Forbidden**

### What This Means
- Authentication credentials were provided (header present)
- Credentials are either invalid, expired, or lack required permissions
- Server recognizes the authentication attempt but rejects it

### Key Difference from 401
- **401** = "Who are you?" (no credentials provided)
- **403** = "I know who you claim to be, but you're not allowed" (credentials provided but invalid/insufficient)

### Diagnosis Steps
1. Verify API key hasn't expired or been rotated
2. Check if service provider revoked/changed credentials
3. Confirm credentials have required scope/permissions
4. Test credentials outside SOAR platform (curl/Postman) to isolate issue
5. Check for typos in credential (extra spaces, incorrect characters)

### Common Causes
- **API key expired** (many services auto-expire keys after 30/60/90 days)
- **API key rotated** (provider regenerated keys for security)
- **Insufficient scope** (read-only key trying to create/update resources)
- **IP whitelist** (API only accepts requests from specific IPs)
- **Copy/paste error** (extra whitespace, incomplete key)

### Resolution
1. Generate new API key from service provider
2. Update credentials in SOAR configuration
3. Verify new credentials work with test API call
4. If scope issue: request elevated permissions or use different credential

### How to Explain to Client
> "The API credentials are configured but being rejected. This usually means the API key expired or was rotated by the service provider. We need to generate a new API key and update the integration configuration. I can walk you through obtaining new credentials from [Service Provider]."

### Testing Outside Platform
```bash
# This will fail with 403 (wrong key)
curl -H "X-API-Key: wrong-key" http://localhost:8001/alerts

# This will succeed (correct key)
curl -H "X-API-Key: valid-key-123" http://localhost:8001/alerts
```

---

## Scenario 3: Malformed Request (400 Bad Request)

### Symptom
Integration fails when trying to create/update resources  
Error messages reference "missing fields" or "invalid format"

### Error Response Example
```json
{
  "detail": "Missing required fields: alert_type, severity"
}
```

### HTTP Status Code
**400 Bad Request**

### What This Means
- Authentication succeeded (got past auth check)
- Request payload is malformed, incomplete, or contains invalid data
- API performed input validation and rejected the request

### Diagnosis Steps
1. Capture exact JSON payload being sent by workflow
2. Compare against API documentation for required fields
3. Verify field names match exactly (case-sensitive, spelling)
4. Check data types (string vs. integer vs. boolean)
5. Test payload outside SOAR with curl to verify format

### Common Causes

**Missing Required Fields:**
- Workflow doesn't populate all mandatory fields
- Variable mapping incorrect (field exists but is null/empty)

**Field Name Mismatch:**
- API expects `alertType` (camelCase) but workflow sends `alert_type` (snake_case)
- Typo in field name

**Invalid Data Types:**
- API expects integer but workflow sends string: `"severity": "5"` instead of `"severity": 5`
- API expects string but workflow sends number

**Invalid Field Values:**
- API expects specific enum values: `severity` must be `["low", "medium", "high"]` but workflow sends `"critical"`
- Date/time format incorrect (ISO-8601 expected but receives epoch timestamp)

### Resolution
1. Review API documentation for exact field requirements
2. Update workflow variable mapping
3. Add data type conversion if needed (string to int, etc.)
4. Add validation step before API call to ensure required fields populated
5. Test with minimal payload first, then add optional fields

### How to Explain to Client
> "The workflow is sending incomplete or incorrectly formatted data to the API. The API requires specific fields in a specific format. We need to adjust the workflow's data mapping to ensure all required fields are populated correctly. I'll update the field mappings and test to confirm the format matches what the API expects."

### Testing Outside Platform
```bash
# This will fail with 400 (missing fields)
curl -X POST http://localhost:8001/alerts \
  -H "X-API-Key: valid-key-123" \
  -H "Content-Type: application/json" \
  -d '{"tenant": "test"}'

# This will succeed (all required fields present)
curl -X POST http://localhost:8001/alerts \
  -H "X-API-Key: valid-key-123" \
  -H "Content-Type: application/json" \
  -d '{"tenant": "client-a", "alert_type": "TEST", "severity": "low"}'
```

---

## Scenario 4: Rate Limiting (429 Too Many Requests)

### Symptom
Integration works fine during normal operation  
Starts failing during high-volume periods (alert storms, bulk processing)  
May work intermittently (some requests succeed, others fail)

### Error Response Example
```json
{
  "detail": "Rate limit exceeded. Max 5 requests per 60 seconds."
}
```

### HTTP Status Code
**429 Too Many Requests**

### What This Means
- API limits request frequency to prevent abuse/overload
- Workflow is calling API faster than allowed rate
- This is an **operational issue**, not a broken integration

### Common Rate Limit Patterns
- **Per-second limits:** 10 requests/second
- **Per-minute limits:** 100 requests/minute
- **Per-hour limits:** 1000 requests/hour
- **Per-day limits:** 10,000 requests/day
- **Concurrent request limits:** Max 5 simultaneous connections

### Diagnosis Steps
1. Check API documentation for published rate limits
2. Review workflow execution logs for request frequency
3. Identify if issue occurs during specific conditions (alert storms)
4. Calculate actual request rate vs. API limit
5. Check if multiple workflows share same API credentials (combined rate)

### Common Causes

**Alert Storm Scenarios:**
- 100 alerts arrive in 1 minute
- Each alert triggers API enrichment call
- 100 API calls in 1 minute exceeds limit of 60/minute

**Inefficient Workflow Design:**
- Workflow calls same API endpoint multiple times for same data
- No caching of repeated lookups
- Parallel execution hitting API simultaneously

**Shared Credentials:**
- Multiple SOAR workflows use same API key
- Combined request rate exceeds limit
- One workflow's traffic impacts another

### Resolution Options

**1. Add Delays Between Requests**
```python
# Instead of rapid-fire requests
for alert in alerts:
    enrich_api_call(alert)

# Add delay between requests
for alert in alerts:
    enrich_api_call(alert)
    time.sleep(1)  # 1 second delay
```

**2. Batch Requests**
```python
# Instead of individual calls
for alert in alerts:
    api.get_user(alert.user_id)

# Batch into single call
user_ids = [alert.user_id for alert in alerts]
api.get_users_batch(user_ids)  # One API call
```

**3. Cache Results**
```python
# Cache repeated lookups
cache = {}

for alert in alerts:
    if alert.domain not in cache:
        cache[alert.domain] = reputation_api.check(alert.domain)
    
    reputation = cache[alert.domain]
```

**4. Implement Exponential Backoff**
```python
def api_call_with_retry(endpoint):
    max_retries = 5
    wait_time = 1
    
    for attempt in range(max_retries):
        try:
            return api.call(endpoint)
        except RateLimitError:
            if attempt < max_retries - 1:
                time.sleep(wait_time)
                wait_time *= 2  # Exponential backoff: 1s, 2s, 4s, 8s, 16s
            else:
                raise
```

**5. Request Rate Limit Increase**
- Contact API provider
- Explain use case and volume
- May require paid tier or enterprise plan

### How to Explain to Client
> "During high-volume periods, we're hitting the API's rate limit. This isn't a failure - it's the API protecting itself from overload. We have several options: we can add small delays between requests, batch multiple lookups into single calls, or cache repeated data. For your alert volume, I recommend [specific solution]. This will prevent rate limit errors while maintaining the enrichment you need."

### Testing Outside Platform
```bash
# Run this 6 times rapidly - 6th request should fail with 429
for i in {1..6}; do 
  curl -H "X-API-Key: valid-key-123" http://localhost:8001/alerts
  echo ""
done
```

---

## Scenario 5: Resource Not Found (404)

### Symptom
Workflow fails when trying to retrieve/update specific resources  
Works for some items but fails for others

### Error Response Example
```json
{
  "detail": "User with ID 999 not found"
}
```

### HTTP Status Code
**404 Not Found**

### What This Means
- Authentication succeeded
- API endpoint exists and is accessible
- Specific resource (user, ticket, device) doesn't exist

### Diagnosis Steps
1. Verify resource ID/identifier is correct
2. Check if resource was deleted or archived
3. Confirm ID format matches API expectations (string vs. integer)
4. Test with known-good resource ID to verify endpoint works
5. Check for case-sensitivity in identifiers

### Common Causes

**Resource Deleted:**
- User account deactivated since workflow stored ID
- Ticket closed and purged from system
- Device removed from inventory

**ID Format Mismatch:**
- API expects integer: `user_id: 123`
- Workflow sends string: `user_id: "123"`
- Or vice versa

**Stale Data:**
- Workflow stores resource ID from previous step
- Resource deleted between storage and lookup
- Time delay in data synchronization

**Wrong Environment:**
- Using production resource ID in test environment
- Resource exists in one tenant but not another (multi-tenant)

### Resolution
1. Add existence check before main action
2. Handle 404 gracefully (skip or log, don't fail entire workflow)
3. Implement fallback logic (create if not found)
4. Add validation: "Does this resource still exist before we try to update it?"

### Example: Safe Resource Update Pattern
```python
def safe_update_user(user_id, data):
    # First check if user exists
    try:
        user = api.get_user(user_id)
    except NotFoundError:
        # Handle gracefully - don't fail workflow
        log.warning(f"User {user_id} not found, skipping update")
        return None
    
    # User exists, safe to update
    return api.update_user(user_id, data)
```

### How to Explain to Client
> "The workflow is trying to update a resource that no longer exists in the system. This can happen if the user account was deleted or the ticket was closed between when we captured the ID and when we tried to act on it. We can add a check to verify the resource exists before attempting the update, and handle cases where it's already been removed."

### Testing Outside Platform
```bash
# This will fail with 404 (user doesn't exist)
curl -H "X-API-Key: valid-key-123" http://localhost:8001/users/999

# This will succeed (user exists)
curl -H "X-API-Key: valid-key-123" http://localhost:8001/users/1
```

---

## Scenario 6: Server Error (500 Internal Server Error)

### Symptom
Integration was working fine, suddenly all requests fail  
OR: Specific API calls fail consistently while others work

### Error Response Example
```json
{
  "detail": "Internal server error - something went wrong on our end"
}
```

### HTTP Status Code
**500 Internal Server Error**

### What This Means
- Problem is on API provider's side (their backend)
- Your request may be valid, but their server couldn't process it
- Could be: unhandled exception, database error, backend crash

### Key Understanding
**This is NOT your fault.** 500 means their code has a bug or their infrastructure has an issue.

### Diagnosis Steps
1. Check if error is consistent or intermittent
2. Try same request again after brief wait (could be transient)
3. Check API provider's status page (status.servicename.com)
4. Test with different request parameters (may be specific-input triggered bug)
5. Check if issue affects all endpoints or just specific ones

### Common Causes (Provider Side)

**Temporary Issues:**
- Database connection timeout
- Memory exhaustion during high load
- Unhandled exception in edge case

**Persistent Issues:**
- Backend deployment broke something
- Database corruption
- Integration with their dependencies failed

**Input-Triggered Bugs:**
- Specific data value triggers unhandled exception
- Null pointer/reference error
- SQL injection vulnerability exposed (their problem)

### Resolution Strategy

**Immediate Response:**
- Implement retry logic with exponential backoff
- Don't retry indefinitely (set max attempts)
- **This error IS retryable** (unlike 4xx errors)

**Retry Pattern Example:**
```python
def api_call_with_retry(endpoint, max_retries=3):
    wait_time = 2  # Start with 2 seconds
    
    for attempt in range(max_retries):
        try:
            return api.call(endpoint)
        except ServerError as e:
            if e.status_code >= 500 and attempt < max_retries - 1:
                # Server error - worth retrying
                time.sleep(wait_time)
                wait_time *= 2  # Exponential: 2s, 4s, 8s
            else:
                # Max retries reached or non-retryable error
                raise
```

**If Persistent:**
1. Check provider status page
2. Contact provider support with:
   - Exact timestamp of failure
   - Request ID (if provided in error response)
   - Payload being sent (sanitize sensitive data)
3. Implement circuit breaker (stop hitting broken API)

### Circuit Breaker Pattern
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5):
        self.failures = 0
        self.threshold = failure_threshold
        self.open = False
    
    def call_api(self, endpoint):
        if self.open:
            raise Exception("Circuit breaker open - API is down")
        
        try:
            result = api.call(endpoint)
            self.failures = 0  # Reset on success
            return result
        except ServerError:
            self.failures += 1
            if self.failures >= self.threshold:
                self.open = True  # Stop hammering broken API
            raise
```

### How to Explain to Client
> "The API provider is experiencing a server-side issue. This isn't a problem with our integration - their backend is having trouble processing requests. I've implemented retry logic so the workflow will automatically retry if the issue is temporary. If it persists, I'll contact their support team. In the meantime, I'm monitoring their status page for updates."

### When to Escalate to Provider
- Error persists for > 15-30 minutes
- Affects critical workflow
- No status page update from provider
- Errors correlate with specific input (might be a bug you discovered)

### Testing Outside Platform
```bash
# This will always return 500
curl http://localhost:8001/simulate-server-error
```

---

## Scenario 7: Service Unavailable (502/503)

### Symptom
Intermittent failures  
"Connection refused" or "Service temporarily unavailable"  
Works after waiting and retrying

### Error Response Example
```json
{
  "detail": "Service temporarily unavailable. Please try again later."
}
```

### HTTP Status Codes
- **502 Bad Gateway** - Load balancer/proxy couldn't reach backend
- **503 Service Unavailable** - Service intentionally down (maintenance, overload)

### What This Means
- API infrastructure is having issues (load balancer, gateway, backend servers)
- Usually temporary (minutes to hours, rarely longer)
- Different from 500 (which is a code bug)

### Common Causes
- **Planned maintenance** - Provider taking service down for updates
- **Deployment in progress** - New version being rolled out
- **Overload** - Too much traffic, service shedding load
- **Upstream dependency failure** - API depends on another service that's down

### Resolution
- **Retry with backoff** (same as 500)
- These errors are almost always transient
- Provider should publish maintenance windows

### How to Explain to Client
> "The API service is temporarily unavailable, likely due to maintenance or high load. This is typically brief. I've configured the workflow to automatically retry with delays. If this becomes frequent, we can discuss implementing a fallback mechanism or alternative data source."

---

## Scenario 8: Timeout (504 Gateway Timeout)

### Symptom
Requests hang for long time (30s, 60s) then fail  
No response received

### Error Response
May not receive JSON error - connection times out

### HTTP Status Code
**504 Gateway Timeout**

### What This Means
- Request reached API gateway/load balancer
- Backend server didn't respond within timeout window
- Gateway gave up waiting

### Common Causes
- Backend processing slow query (large dataset)
- Database deadlock
- Backend server unresponsive/crashed
- Network issue between gateway and backend

### Resolution
- Reduce payload size (request less data)
- Add pagination (retrieve in smaller chunks)
- Increase client-side timeout setting
- Contact provider if timeouts are consistent

---

## The One Diagnostic Flow to Remember

When **any** integration fails, follow this sequence:

```
1. Check status code
   ├─ 4xx → Problem is on my side
   │  ├─ 401/403 → Fix authentication
   │  ├─ 400 → Fix payload
   │  └─ 429 → Add delays/caching
   │
   └─ 5xx → Problem is on their side
      ├─ Retry with backoff (it's temporary)
      └─ If persistent → Contact provider

2. Read the error message
   └─ APIs usually tell you exactly what's wrong

3. Test outside the platform
   ├─ curl/Postman with same credentials
   └─ If external test works but SOAR fails → SOAR config issue
   └─ If external test also fails → API issue
```
