"""
Simple API Demo for Understanding Integration Failure Modes

This API intentionally includes common failure scenarios that occur
in production integrations. Used to demonstrate troubleshooting skills.

Run with: uvicorn main:app --reload
Test with: curl http://localhost:8000/health
"""

from fastapi import FastAPI, HTTPException, Header, Query
from typing import Optional
import time
from datetime import datetime

app = FastAPI(title="Alert Integration Demo API")

# Simulated rate limiting
request_counts = {}
RATE_LIMIT = 5
RATE_WINDOW = 60  # seconds

# Simulated database
alerts_db = [
    {"id": 1, "tenant": "client-a", "alert_type": "MFA_FAILURE", "severity": "high", "timestamp": "2024-01-15T10:30:00Z"},
    {"id": 2, "tenant": "client-b", "alert_type": "MFA_FAILURE", "severity": "high", "timestamp": "2024-01-15T10:31:00Z"},
    {"id": 3, "tenant": "client-a", "alert_type": "MALWARE_DETECTED", "severity": "critical", "timestamp": "2024-01-15T10:32:00Z"},
]

users_db = [
    {"id": 1, "username": "analyst1", "role": "soc_analyst", "tenant": "client-a"},
    {"id": 2, "username": "analyst2", "role": "soc_lead", "tenant": "client-b"},
]


def check_rate_limit(client_ip: str):
    """Simulate rate limiting (429 errors)"""
    now = time.time()
    
    if client_ip not in request_counts:
        request_counts[client_ip] = []
    
    # Remove old requests outside the window
    request_counts[client_ip] = [
        req_time for req_time in request_counts[client_ip] 
        if now - req_time < RATE_WINDOW
    ]
    
    if len(request_counts[client_ip]) >= RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {RATE_LIMIT} requests per {RATE_WINDOW} seconds."
        )
    
    request_counts[client_ip].append(now)


@app.get("/health")
async def health_check():
    """
    Health check endpoint - always succeeds
    Example: curl http://localhost:8000/health
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "alert-integration-api"
    }


@app.get("/alerts")
async def get_alerts(
    tenant: Optional[str] = None,
    limit: int = Query(default=10, le=100),
    api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """
    Get alerts with authentication and pagination
    
    Demonstrates:
    - 401 Unauthorized (missing API key)
    - 403 Forbidden (invalid API key)
    - Pagination with limit parameter
    - Filtering by tenant
    
    Examples:
    - curl http://localhost:8000/alerts
      (fails with 401)
    
    - curl -H "X-API-Key: valid-key-123" http://localhost:8000/alerts
      (succeeds)
    
    - curl -H "X-API-Key: wrong-key" http://localhost:8000/alerts
      (fails with 403)
    
    - curl -H "X-API-Key: valid-key-123" "http://localhost:8000/alerts?tenant=client-a"
      (filtered results)
    """
    
    # Simulate 401 - Missing authentication
    if api_key is None:
        raise HTTPException(
            status_code=401,
            detail="Missing authentication. Include X-API-Key header."
        )
    
    # Simulate 403 - Invalid credentials (valid format but wrong key)
    if api_key != "valid-key-123":
        raise HTTPException(
            status_code=403,
            detail="Invalid API key. Access forbidden."
        )
    
    # Filter by tenant if provided
    results = alerts_db
    if tenant:
        results = [alert for alert in alerts_db if alert["tenant"] == tenant]
    
    # Apply limit (pagination simulation)
    results = results[:limit]
    
    return {
        "data": results,
        "count": len(results),
        "limit": limit,
        "tenant_filter": tenant
    }


@app.post("/alerts")
async def create_alert(
    alert_data: dict,
    api_key: Optional[str] = Header(None, alias="X-API-Key"),
    client_ip: str = Header(default="127.0.0.1", alias="X-Forwarded-For")
):
    """
    Create a new alert
    
    Demonstrates:
    - 401/403 authentication errors
    - 400 Bad Request (malformed payload)
    - 429 Rate limiting
    - 201 Created (success)
    
    Examples:
    - curl -X POST http://localhost:8000/alerts -H "Content-Type: application/json" -d '{}'
      (fails with 401)
    
    - curl -X POST http://localhost:8000/alerts -H "X-API-Key: valid-key-123" -H "Content-Type: application/json" -d '{"tenant": "test"}'
      (fails with 400 - missing required fields)
    
    - curl -X POST http://localhost:8000/alerts -H "X-API-Key: valid-key-123" -H "Content-Type: application/json" -d '{"tenant": "client-a", "alert_type": "TEST", "severity": "low"}'
      (succeeds with 201)
    """
    
    # Check authentication
    if api_key is None:
        raise HTTPException(status_code=401, detail="Missing authentication")
    
    if api_key != "valid-key-123":
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    # Check rate limiting
    check_rate_limit(client_ip)
    
    # Validate required fields (400 Bad Request)
    required_fields = ["tenant", "alert_type", "severity"]
    missing_fields = [field for field in required_fields if field not in alert_data]
    
    if missing_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required fields: {', '.join(missing_fields)}"
        )
    
    # Validate field values
    valid_severities = ["low", "medium", "high", "critical"]
    if alert_data["severity"] not in valid_severities:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid severity. Must be one of: {', '.join(valid_severities)}"
        )
    
    # Create the alert
    new_alert = {
        "id": len(alerts_db) + 1,
        "tenant": alert_data["tenant"],
        "alert_type": alert_data["alert_type"],
        "severity": alert_data["severity"],
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    alerts_db.append(new_alert)
    
    return {
        "message": "Alert created successfully",
        "alert": new_alert
    }, 201


@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """
    Get user by ID
    
    Demonstrates:
    - 404 Not Found (user doesn't exist)
    - Path parameters
    
    Examples:
    - curl -H "X-API-Key: valid-key-123" http://localhost:8000/users/1
      (succeeds)
    
    - curl -H "X-API-Key: valid-key-123" http://localhost:8000/users/999
      (fails with 404)
    """
    
    if api_key != "valid-key-123":
        raise HTTPException(status_code=401, detail="Missing or invalid API key")
    
    user = next((u for u in users_db if u["id"] == user_id), None)
    
    if user is None:
        raise HTTPException(
            status_code=404,
            detail=f"User with ID {user_id} not found"
        )
    
    return {"user": user}


@app.get("/simulate-timeout")
async def simulate_timeout():
    """
    Simulates a slow/timeout scenario (5xx errors)
    WARNING: This will actually sleep for 10 seconds
    
    Example:
    - curl http://localhost:8000/simulate-timeout
      (takes 10 seconds, may timeout depending on client settings)
    """
    time.sleep(10)  # Simulate slow backend
    return {"message": "This took way too long"}


@app.get("/simulate-server-error")
async def simulate_server_error():
    """
    Simulates a 500 Internal Server Error
    
    Example:
    - curl http://localhost:8000/simulate-server-error
      (always fails with 500)
    """
    raise HTTPException(
        status_code=500,
        detail="Internal server error - something went wrong on our end"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)