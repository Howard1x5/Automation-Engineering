"""
Alert Payload Transformation Script

Purpose:
    Normalize messy SIEM alert JSON into standardized format for case management.
    Common use case: Different SIEMs (Splunk, Microsoft, QRadar) send alerts in 
    different formats. This script converts them to a common schema.

Author: Clinton Howard
Date: January 2026
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional


# Valid severity levels accepted by case management system
VALID_SEVERITIES = ["low", "medium", "high", "critical"]
DEFAULT_SEVERITY = "medium"


def normalize_timestamp(timestamp_str: str) -> str:
    """
    Convert timestamp to ISO-8601 format without milliseconds.
    
    Input:  "2024-01-22T14:23:45.123Z"
    Output: "2024-01-22T14:23:45Z"
    
    Args:
        timestamp_str: ISO timestamp string (may include milliseconds)
    
    Returns:
        Normalized timestamp string without milliseconds
    """
    try:
        # Parse the timestamp (handles with or without milliseconds)
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        
        # Format without milliseconds
        return dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    except (ValueError, AttributeError):
        # If parsing fails, return original
        print(f"Warning: Could not parse timestamp '{timestamp_str}'")
        return timestamp_str


def normalize_severity(severity_str: Optional[str]) -> str:
    """
    Normalize severity to lowercase and validate against allowed values.
    
    Input:  "HIGH" or "high" or "5" or "SUPER_CRITICAL"
    Output: "high" or DEFAULT_SEVERITY if invalid
    
    Args:
        severity_str: Severity string from alert (can be any format)
    
    Returns:
        Normalized, validated severity level
    """
    if not severity_str:
        return DEFAULT_SEVERITY
    
    # Convert to lowercase
    normalized = severity_str.lower().strip()
    
    # Validate against allowed values
    if normalized in VALID_SEVERITIES:
        return normalized
    
    # Invalid severity - log warning and use default
    print(f"Warning: Invalid severity '{severity_str}', using '{DEFAULT_SEVERITY}'")
    return DEFAULT_SEVERITY


def transform_alert(raw_alert: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform raw SIEM alert into standardized case management format.
    
    This handles:
    - Field name mapping (EventTime -> timestamp)
    - Data type normalization (uppercase -> lowercase)
    - Missing field handling (set to None)
    - Nested data restructuring (RawData -> metadata)
    
    Args:
        raw_alert: Raw alert dictionary from SIEM
    
    Returns:
        Transformed alert dictionary ready for case creation
    """
    
    # Initialize output structure
    transformed = {}
    
    # --- Required Fields (with safe defaults) ---
    
    # Timestamp: normalize format
    # Get EventTime or generate current UTC timestamp as default
    event_time = raw_alert.get("EventTime")
    if event_time is None:
        event_time = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    
    transformed["timestamp"] = normalize_timestamp(event_time)
    
    # Source system: use as-is (preserve original casing for vendor names)
    transformed["source_system"] = raw_alert.get("EventSource", "Unknown")
    
    # Alert ID: critical for tracking
    transformed["alert_id"] = raw_alert.get("EventID", None)
    
    # Tenant: preserve original casing (company names)
    transformed["tenant"] = raw_alert.get("Customer", None)
    
    # Severity: normalize and validate
    transformed["severity"] = normalize_severity(
        raw_alert.get("Alert_Severity")
    )
    
    # --- Optional Fields (may be missing) ---
    
    # User: convert field name, preserve value
    transformed["user"] = raw_alert.get("affected_user", None)
    
    # Source IP: convert field name
    transformed["source_ip"] = raw_alert.get("SourceIP", None)
    
    # Description: keep verbatim (important for analyst context)
    transformed["description"] = raw_alert.get("Description", None)
    
    # --- Nested Metadata Transformation ---
    
    # Transform RawData -> metadata with field name changes
    raw_data = raw_alert.get("RawData", {})
    
    if raw_data:
        transformed["metadata"] = {
            "login_attempts": raw_data.get("LoginAttempts", None),
            "geo_location": raw_data.get("Country", None)
        }
    else:
        transformed["metadata"] = {}
    
    return transformed


def main():
    """
    Example usage with test data.
    
    Run this script directly to see transformation in action:
        python transform_alert_payload.py
    """
    
    # Example raw alert from SIEM
    raw_alert = {
        "EventTime": "2024-01-22T14:23:45.123Z",
        "EventSource": "Microsoft Defender",
        "EventID": "def-12345",
        "Customer": "ACME Corp",
        "Alert_Severity": "HIGH",
        "affected_user": "jsmith@acme.com",
        "SourceIP": "192.168.1.50",
        "Description": "Multiple failed login attempts detected from unusual location",
        "RawData": {
            "LoginAttempts": 15,
            "Country": "Unknown"
        }
    }
    
    print("=" * 60)
    print("ALERT PAYLOAD TRANSFORMATION DEMO")
    print("=" * 60)
    print("\nRAW INPUT (from SIEM):")
    print(json.dumps(raw_alert, indent=2))
    
    # Transform the alert
    transformed = transform_alert(raw_alert)
    
    print("\nTRANSFORMED OUTPUT (for case management):")
    print(json.dumps(transformed, indent=2))
    
    print("\n" + "=" * 60)
    print("TESTING MISSING FIELDS")
    print("=" * 60)
    
    # Test with missing fields
    incomplete_alert = {
        "EventTime": "2024-01-22T15:00:00Z",
        "EventID": "def-67890",
        "Alert_Severity": "INVALID_SEVERITY"  # This will trigger validation
    }
    
    print("\nINCOMPLETE INPUT:")
    print(json.dumps(incomplete_alert, indent=2))
    
    transformed_incomplete = transform_alert(incomplete_alert)
    
    print("\nTRANSFORMED OUTPUT (with defaults):")
    print(json.dumps(transformed_incomplete, indent=2))
    
    print("\nTransformation complete!")
    print("\nKey observations:")
    print("  - Missing fields set to null")
    print("  - Invalid severity defaulted to 'medium'")
    print("  - Timestamp normalized")


if __name__ == "__main__":
    main()