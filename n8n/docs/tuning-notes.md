# Threat Scoring Tuning Notes

## VirusTotal IP Reputation Thresholds

### Initial Implementation
Originally used a percentage-based threat score:
- `threatScore > 30` = HIGH
- `threatScore > 10` = MEDIUM
- Otherwise = LOW

### Problem Discovered During Testing
The percentage-based approach was not sensitive enough. VirusTotal checks IPs against 80-90+ vendors, so even clearly malicious IPs (like known Tor exit nodes used in attacks) rarely exceed 30% detection rate.

Example: A Tor exit node IP (185.220.101.42) with 8 malicious detections only scored ~10 on the percentage scale, resulting in a LOW risk classification despite being a known threat.

### Tuned Thresholds (Current)
Based on real-world security analyst experience, switched to raw malicious detection counts:

| Malicious Detections | Risk Level | Rationale |
|---------------------|------------|-----------|
| 5+ | HIGH | Multiple vendors flagging = confirmed threat, warrants immediate alert |
| 2-4 | MEDIUM | Some vendor flags = worth investigating |
| 0-1 | LOW | Single flag could be false positive |

### Why This Works Better
- In practice, having 4-5 vendors independently flag an IP as malicious is significant
- Percentage-based scoring gets diluted by the large number of vendors that return "undetected"
- Raw counts better reflect analyst triage decisions

### Future Improvements
Consider adding:
- Weighted scoring based on vendor reputation (some vendors more reliable than others)
- Time-decay factor (recent detections weighted higher)
- Category-specific thresholds (phishing vs malware vs spam)
