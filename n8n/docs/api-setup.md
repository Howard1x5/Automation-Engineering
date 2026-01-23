# API Setup Guide

This guide walks through getting API credentials for each service.

## 1. VirusTotal

**Purpose:** URL and IP reputation checking

### Get API Key
1. Go to https://www.virustotal.com
2. Create free account
3. Click your profile icon → API key
4. Copy your API key

### Free Tier Limits
- 4 requests/minute
- 500 requests/day
- 15.5K requests/month

### Test Your Key
```bash
curl -s "https://www.virustotal.com/api/v3/ip_addresses/8.8.8.8" \
  -H "x-apikey: YOUR_API_KEY" | jq '.data.attributes.last_analysis_stats'
```

---

## 2. AbuseIPDB

**Purpose:** IP abuse confidence scoring

### Get API Key
1. Go to https://www.abuseipdb.com
2. Create free account
3. Go to Account → API
4. Create new API key

### Free Tier Limits
- 1,000 checks/day
- 5 reports/day

### Test Your Key
```bash
curl -s "https://api.abuseipdb.com/api/v2/check" \
  -H "Key: YOUR_API_KEY" \
  -H "Accept: application/json" \
  -d "ipAddress=8.8.8.8" | jq '.data.abuseConfidenceScore'
```

---

## 3. Jira (Optional - can use GitHub Issues instead)

**Purpose:** Ticket creation for escalation

### Get API Token
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Name it "n8n-integration"
4. Copy the token (shown only once)

### Required Info
- Jira URL: `https://your-domain.atlassian.net`
- Email: Your Atlassian account email
- Project Key: The short code for your project (e.g., "PHISH")

### Test Your Token
```bash
curl -s "https://your-domain.atlassian.net/rest/api/3/myself" \
  -u "your-email@example.com:YOUR_API_TOKEN" | jq '.displayName'
```

---

## 4. Slack

**Purpose:** Notifications and alerts

### Create Webhook
1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name: "n8n-security-alerts"
4. Select your workspace
5. Go to "Incoming Webhooks" → Enable
6. Click "Add New Webhook to Workspace"
7. Select channel (e.g., #security-alerts)
8. Copy webhook URL

### Test Your Webhook
```bash
curl -X POST YOUR_WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -d '{"text": "Test from n8n setup!"}'
```

---

## Adding Credentials to n8n

1. Open n8n at http://localhost:5678
2. Go to Settings → Credentials
3. Click "Add Credential"
4. Select the service type
5. Enter your API key/token
6. Save

### Credential Types in n8n
- **VirusTotal**: Header Auth (x-apikey)
- **AbuseIPDB**: Header Auth (Key)
- **Jira**: Basic Auth (email + API token)
- **Slack**: Webhook URL (in node config, not credentials)

---

## Security Notes

- Never commit API keys to git
- Use `.env` file for local development
- Rotate keys if accidentally exposed
- Use minimum required permissions
- Monitor API usage for anomalies
