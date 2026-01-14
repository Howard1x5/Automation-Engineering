# Process Improvement: API Integration Mental Models

## What an API is (in one sentence)
An API (Application Programming Interface) is a programmatic way for one system to read data from, or take action in, another system using structured requests (usually over HTTP).

---

## Why SOAR uses APIs
SOAR platforms rely on APIs to integrate with other security and IT tools in order to:

- Pull context and enrichment data (logs, reputation, metadata)
- Search historical activity across systems
- Take response actions (isolate endpoints, reset accounts, quarantine emails)
- Create operational records (tickets, notifications, audit entries)

Without APIs, automation platforms cannot investigate or respond across multiple tools.

---

## The 7 things you must know about any API integration

1. **Endpoint**
   - The specific API URL being called (what resource you are interacting with)

2. **Method**
   - GET = read data  
   - POST = create or take action  
   - PUT / PATCH = modify existing data  
   - DELETE = remove data

3. **Authentication**
   - How the automation proves it is allowed to call the API  
   - Common models: API keys, OAuth tokens, client credentials

4. **Permissions / Scope**
   - Even with valid authentication, the API may restrict what actions are allowed
   - Lack of scope commonly causes authorization failures

5. **Required Inputs**
   - Identifiers needed for the request (message ID, user ID, device ID, time window)

6. **Response Shape**
   - What data is returned and which fields must be stored for downstream steps

7. **Limits**
   - Rate limits, pagination, and timeouts  
   - Most automation reliability issues occur here

---

## Common failure modes and what they look like

### Authentication failures
- **401 Unauthorized**: invalid credentials or expired token  
- **403 Forbidden**: credentials valid but insufficient permissions

### Pagination issues
- Only partial results returned (e.g., first 100 records)
- Additional pages must be explicitly requested

### Rate limiting
- **429 Too Many Requests**
- Occurs when APIs are called too frequently

### Transient/server errors
- **500 / 502 / 503**
- Service instability, backend load, or temporary outages

### Idempotency issues
- Duplicate actions (multiple quarantines, repeated disables)
- Caused by retries without state checks

---

## Pagination mental model (with examples)
Many APIs return results in pages rather than all at once.

Common patterns:
- Page + limit (page=1, page=2, etc.)
- Cursor or next-page token returned in the response

Automation must:
- Capture the next-page indicator
- Loop until no additional pages exist

Failing to do this results in incomplete investigations.

---

## Rate limiting mental model (with examples)
APIs protect themselves by limiting request volume.

When limits are exceeded:
- API returns **429 Too Many Requests**

Automation should respond by:
- Retrying with exponential backoff
- Batching requests where possible
- Caching repeated lookups to reduce load

Rate limits are a reliability constraint, not an error condition.

---

## Authentication mental model (high level)

Common authentication models:
- **API Key**: static secret
- **OAuth Token**: short-lived token that expires
- **Client Credentials**: service-to-service OAuth authentication

Important considerations:
- Tokens can expire and require refresh
- Scope determines allowed actions
- Least privilege access is preferred

---

## Troubleshooting checklist
When an API step fails, check:

1. HTTP status code (401, 403, 429, 5xx)
2. Token validity or expiration
3. Permissions and scope
4. Pagination completeness
5. Rate limiting behavior
6. Service availability
7. Duplicate action protection (idempotency)
