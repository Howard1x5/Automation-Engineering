"""
Alert Deduplication Key Generator

Purpose:
    Generate deterministic deduplication keys for multi-tenant alert correlation.
    Used to identify when multiple alerts across different tenants represent
    the same underlying event (e.g., service outage, widespread attack).

Use Cases:
    - Microsoft MFA outage causing alerts across 50 tenants
    - Phishing campaign hitting multiple clients simultaneously
    - Vendor service disruption generating duplicate alerts

Author: Clinton Howard
Date: January 2026
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional


def normalize_string(value: Any) -> str:
    """
    Normalize a value for consistent key generation.
    
    Handles:
    - Case normalization (uppercase -> lowercase)
    - Whitespace trimming
    - None/null values
    - Non-string types (convert to string)
    
    Args:
        value: Any value to normalize
    
    Returns:
        Normalized lowercase string
    """
    if value is None:
        return ""
    
    # Convert to string and normalize
    return str(value).lower().strip()


def bucket_timestamp(timestamp_str: str, bucket_minutes: int = 60) -> str:
    """
    Round timestamp down to nearest time bucket.
    
    This groups alerts that occur within the same time window.
    
    Examples (with 60-minute bucket):
        14:23:45 -> 14:00
        14:58:12 -> 14:00
        15:05:33 -> 15:00
    
    Examples (with 15-minute bucket):
        14:23:45 -> 14:15
        14:58:12 -> 14:45
        15:05:33 -> 15:00
    
    Args:
        timestamp_str: ISO format timestamp string
        bucket_minutes: Size of time bucket in minutes (default: 60)
    
    Returns:
        Bucketed timestamp string (YYYY-MM-DDTHH:MM)
    """
    try:
        # Parse timestamp (handle various formats)
        # Remove 'Z' suffix and any timezone info for parsing
        clean_ts = timestamp_str.replace('Z', '').split('+')[0].split('.')[0]
        dt = datetime.fromisoformat(clean_ts)
        
        # Calculate bucket
        # Floor divide minutes to nearest bucket
        bucketed_minute = (dt.minute // bucket_minutes) * bucket_minutes
        
        # Create bucketed datetime
        bucketed_dt = dt.replace(minute=bucketed_minute, second=0, microsecond=0)
        
        # Return as string (without seconds for cleaner keys)
        return bucketed_dt.strftime('%Y-%m-%dT%H:%M')
    
    except (ValueError, AttributeError) as e:
        # If parsing fails, return original (better than crashing)
        print(f"Warning: Could not parse timestamp '{timestamp_str}': {e}")
        return timestamp_str


def generate_dedupe_key(
    alert: Dict[str, Any],
    key_fields: List[str],
    time_field: str = "timestamp",
    bucket_minutes: int = 60,
    include_hash: bool = True
) -> str:
    """
    Generate a deduplication key from alert fields.
    
    The key is deterministic - same input always produces same output.
    Alerts with matching keys are candidates for grouping.
    
    Args:
        alert: Alert dictionary
        key_fields: List of field names to include in key (order matters)
        time_field: Name of timestamp field (will be bucketed)
        bucket_minutes: Time bucket size in minutes
        include_hash: If True, append MD5 hash for shorter keys
    
    Returns:
        Dedupe key string
    
    Example:
        alert = {"alert_type": "MFA_FAILURE", "source": "Defender", "timestamp": "..."}
        key_fields = ["alert_type", "source"]
        
        Result: "mfa_failure|defender|2026-01-22T14:00"
        Or with hash: "mfa_failure|defender|2026-01-22T14:00|a1b2c3d4"
    """
    key_parts = []
    
    # Extract and normalize each key field
    for field in key_fields:
        value = alert.get(field, "")
        normalized = normalize_string(value)
        key_parts.append(normalized)
    
    # Add bucketed timestamp if time_field exists
    if time_field and time_field in alert:
        bucketed_time = bucket_timestamp(alert[time_field], bucket_minutes)
        key_parts.append(bucketed_time)
    
    # Join parts with pipe delimiter
    key_string = "|".join(key_parts)
    
    # Optionally append hash for shorter, fixed-length keys
    if include_hash:
        # MD5 is fine here (not for security, just for key shortening)
        hash_suffix = hashlib.md5(key_string.encode()).hexdigest()[:8]
        key_string = f"{key_string}|{hash_suffix}"
    
    return key_string


def generate_dedupe_key_hash_only(
    alert: Dict[str, Any],
    key_fields: List[str],
    time_field: str = "timestamp",
    bucket_minutes: int = 60
) -> str:
    """
    Generate a short hash-only dedupe key.
    
    Useful when you need fixed-length keys for database storage
    or when human readability isn't needed.
    
    Args:
        alert: Alert dictionary
        key_fields: List of field names to include
        time_field: Name of timestamp field
        bucket_minutes: Time bucket size
    
    Returns:
        32-character MD5 hash string
    """
    # Build the source string
    parts = []
    
    for field in key_fields:
        value = normalize_string(alert.get(field, ""))
        parts.append(f"{field}={value}")
    
    if time_field and time_field in alert:
        bucketed = bucket_timestamp(alert[time_field], bucket_minutes)
        parts.append(f"time={bucketed}")
    
    source_string = "&".join(parts)
    
    # Return full MD5 hash
    return hashlib.md5(source_string.encode()).hexdigest()


def group_alerts_by_dedupe_key(
    alerts: List[Dict[str, Any]],
    key_fields: List[str],
    time_field: str = "timestamp",
    bucket_minutes: int = 60
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group a list of alerts by their dedupe keys.
    
    This is the main function for correlation - takes raw alerts
    and groups them by matching dedupe keys.
    
    Args:
        alerts: List of alert dictionaries
        key_fields: Fields to use for deduplication
        time_field: Timestamp field name
        bucket_minutes: Time bucket size
    
    Returns:
        Dictionary mapping dedupe keys to lists of matching alerts
    """
    groups = {}
    
    for alert in alerts:
        # Generate key for this alert
        key = generate_dedupe_key(
            alert=alert,
            key_fields=key_fields,
            time_field=time_field,
            bucket_minutes=bucket_minutes,
            include_hash=False  # Readable keys for grouping
        )
        
        # Add to appropriate group
        if key not in groups:
            groups[key] = []
        groups[key].append(alert)
    
    return groups


def analyze_groups(groups: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Analyze grouped alerts for reporting.
    
    Args:
        groups: Output from group_alerts_by_dedupe_key()
    
    Returns:
        Analysis summary
    """
    total_alerts = sum(len(alerts) for alerts in groups.values())
    multi_tenant_groups = {k: v for k, v in groups.items() if len(v) > 1}
    
    return {
        "total_alerts": total_alerts,
        "unique_events": len(groups),
        "multi_tenant_events": len(multi_tenant_groups),
        "alerts_deduplicated": total_alerts - len(groups),
        "largest_group_size": max(len(v) for v in groups.values()) if groups else 0
    }


def main():
    """
    Example usage demonstrating multi-tenant alert deduplication.
    """
    
    # Simulated alerts from multiple tenants during MFA outage
    alerts = [
        {
            "id": "alert-001",
            "tenant": "ACME Corp",
            "alert_type": "MFA_FAILURE",
            "source": "Microsoft Defender",
            "timestamp": "2026-01-22T14:23:45Z",
            "user": "jsmith@acme.com",
            "severity": "high"
        },
        {
            "id": "alert-002",
            "tenant": "Globex Inc",
            "alert_type": "MFA_FAILURE",
            "source": "Microsoft Defender",
            "timestamp": "2026-01-22T14:24:12Z",
            "user": "bwilson@globex.com",
            "severity": "high"
        },
        {
            "id": "alert-003",
            "tenant": "Initech",
            "alert_type": "MFA_FAILURE",
            "source": "Microsoft Defender",
            "timestamp": "2026-01-22T14:38:58Z",
            "user": "mbolton@initech.com",
            "severity": "high"
        },
        {
            "id": "alert-004",
            "tenant": "ACME Corp",
            "alert_type": "MALWARE_DETECTED",
            "source": "Microsoft Defender",
            "timestamp": "2026-01-22T14:25:00Z",
            "user": "jsmith@acme.com",
            "severity": "critical"
        },
        {
            "id": "alert-005",
            "tenant": "Globex Inc",
            "alert_type": "MFA_FAILURE",
            "source": "Microsoft Defender",
            "timestamp": "2026-01-22T15:15:00Z",  # Different hour
            "user": "cjones@globex.com",
            "severity": "high"
        },
        {
            "id": "alert-006",
            "tenant": "Umbrella Corp",
            "alert_type": "MFA_FAILURE",
            "source": "Okta",  # Different source
            "timestamp": "2026-01-22T14:30:00Z",
            "user": "awesker@umbrella.com",
            "severity": "high"
        }
    ]
    
    print("=" * 70)
    print("ALERT DEDUPLICATION DEMO")
    print("=" * 70)
    
    print("\nINPUT: {} alerts from multiple tenants".format(len(alerts)))
    print("-" * 70)
    for alert in alerts:
        print(f"  [{alert['id']}] {alert['tenant']}: {alert['alert_type']} "
              f"({alert['source']}) at {alert['timestamp']}")
    
    # Define which fields determine "same event"
    # Note: We EXCLUDE tenant and user because those vary per client
    key_fields = ["alert_type", "source"]
    
    print("\n" + "=" * 70)
    print("DEDUPE KEY GENERATION")
    print("=" * 70)
    print(f"\nKey fields: {key_fields}")
    print(f"Time bucket: 60 minutes")
    print("\nGenerated keys:")
    print("-" * 70)
    
    for alert in alerts:
        key = generate_dedupe_key(
            alert=alert,
            key_fields=key_fields,
            time_field="timestamp", 
            bucket_minutes=60,
            include_hash=False
        )
        print(f"  [{alert['id']}] {alert['tenant'][:12]:12} -> {key}")
    
    # Group alerts by dedupe key
    print("\n" + "=" * 70)
    print("GROUPED ALERTS (Same key = Same event)")
    print("=" * 70)
    
    groups = group_alerts_by_dedupe_key(
        alerts=alerts,
        key_fields=key_fields,
        time_field="timestamp",
        bucket_minutes=60
    )
    
    for key, grouped_alerts in groups.items():
        print(f"\nKey: {key}")
        print(f"  Alerts in group: {len(grouped_alerts)}")
        tenants = [a['tenant'] for a in grouped_alerts]
        print(f"  Tenants affected: {', '.join(tenants)}")
        if len(grouped_alerts) > 1:
            print("  ** MULTI-TENANT EVENT - Candidate for correlation **")
    
    # Analysis summary
    print("\n" + "=" * 70)
    print("ANALYSIS SUMMARY")
    print("=" * 70)
    
    analysis = analyze_groups(groups)
    print(f"\n  Total alerts received:     {analysis['total_alerts']}")
    print(f"  Unique events identified:  {analysis['unique_events']}")
    print(f"  Multi-tenant events:       {analysis['multi_tenant_events']}")
    print(f"  Alerts deduplicated:       {analysis['alerts_deduplicated']}")
    print(f"  Largest group size:        {analysis['largest_group_size']}")
    
    print("\n" + "=" * 70)
    print("KEY INSIGHTS")
    print("=" * 70)
    print("""
  1. Alerts are grouped by alert_type + source + time_bucket
  2. Tenant and user are EXCLUDED (they vary per client)
  3. 60-minute bucket groups alerts within same hour
  4. Multi-tenant groups are candidates for service outage investigation
  5. Human validation still required before bulk closure
    """)


if __name__ == "__main__":
    main()