# API Integration Demo

A simple FastAPI-based API that demonstrates common integration failure modes encountered in SOAR/automation environments.

## Purpose

This API is intentionally designed to fail in predictable ways to help understand:
- Authentication failures (401, 403)
- Rate limiting (429)
- Malformed requests (400)
- Not found errors (404)
- Server errors (500)
- Timeout scenarios

## Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
uvicorn main:app --reload
```

API will be available at: http://localhost:8000

Interactive docs at: http://localhost:8000/docs

## Test Scenarios

### 1. Health Check (Always Succeeds)
```bash
curl http://localhost:8000/health
```

### 2. 401 Unauthorized (Missing Auth)
```bash
curl http://localhost:8000/alerts
```

**Expected:** `401 Unauthorized - Missing authentication`

### 3. 403 Forbidden (Invalid Credentials)
```bash
curl -H "X-API-Key: wrong-key" http://localhost:8000/alerts
```

**Expected:** `403 Forbidden - Invalid API key`

### 4. Success (Valid Auth)
```bash
curl -H "X-API-Key: valid-key-123" http://localhost:8000/alerts
```

**Expected:** JSON array of alerts

### 5. 400 Bad Request (Missing Fields)
```bash
curl -X POST http://localhost:8000/alerts \
  -H "X-API-Key: valid-key-123" \
  -H "Content-Type: application/json" \
  -d '{"tenant": "test-only"}'
```

**Expected:** `400 Bad Request - Missing required fields`

### 6. 201 Created (Valid POST)
```bash
curl -X POST http://localhost:8000/alerts \
  -H "X-API-Key: valid-key-123" \
  -H "Content-Type: application/json" \
  -d '{"tenant": "client-a", "alert_type": "TEST_ALERT", "severity": "low"}'
```

**Expected:** `201 Created` with new alert JSON

### 7. 429 Rate Limit (Run This 6 Times Fast)
```bash
for i in {1..6}; do curl -H "X-API-Key: valid-key-123" http://localhost:8000/alerts; done
```

**Expected:** First 5 succeed, 6th returns `429 Too Many Requests`

### 8. 404 Not Found
```bash
curl -H "X-API-Key: valid-key-123" http://localhost:8000/users/999
```

**Expected:** `404 Not Found - User with ID 999 not found`

### 9. 500 Server Error
```bash
curl http://localhost:8000/simulate-server-error
```

**Expected:** `500 Internal Server Error`

## What This Demonstrates

- **Authentication patterns** (header-based API keys)
- **Error response structures** (consistent JSON format)
- **Rate limiting implementation** (time-window based)
- **Input validation** (required fields, valid values)
- **RESTful conventions** (GET vs POST, proper status codes)
- **Pagination basics** (limit parameter)

## Next Steps

Use these error scenarios to populate the `/docs/30-api-integration/api-troubleshooting-scenarios.md` document with real examples.