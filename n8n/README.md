# n8n Phishing Triage Automation

Automated phishing email analysis workflow that enriches suspicious emails with threat intelligence and routes them based on risk score.

## Why I Built This

SOC analysts spend a lot of time on repetitive triage work - checking URLs against VirusTotal, looking up sender IPs, copy-pasting into ticketing systems. Most of this can be automated while keeping humans in the loop for actual decision-making.

I wanted to understand how modern SOAR platforms handle this, so I built a working version using n8n. It's not production-ready (no email ingestion, simplified scoring), but it demonstrates the core patterns.

## What It Does

```
[Webhook: Email Data]
    ↓
[Extract URLs and IPs]
    ↓
[VirusTotal Lookup] → [Handle Errors/Rate Limits]
    ↓
[AbuseIPDB Lookup] → [Handle Errors/Rate Limits]
    ↓
[Calculate Threat Score]
    ↓
[Route by Risk Level]
    ├─ High (>80)   → Urgent Jira ticket + Slack alert
    ├─ Medium (40-80) → Standard ticket + notification
    └─ Low (<40)    → Log only
```

## Technical Stack

- **n8n** - Self-hosted workflow automation (similar to Zapier/Make but open source)
- **VirusTotal API** - URL and IP reputation
- **AbuseIPDB API** - IP abuse confidence scoring
- **Jira** - Ticket creation (could swap for GitHub Issues)
- **Slack** - Notifications

## Design Decisions

**Why n8n over building from scratch?**
Workflow orchestration is a solved problem. n8n gives me visual debugging, credential management, and a node ecosystem. I can focus on the security logic instead of building an execution engine.

**Why these specific APIs?**
VirusTotal and AbuseIPDB have generous free tiers and are industry standard for threat intel. The workflow is designed to degrade gracefully if one API fails - partial enrichment is better than no enrichment.

**Why conditional routing instead of just alerting everything?**
Alert fatigue is real. Low-risk items don't need human attention. The scoring threshold is configurable, and the workflow logs everything so nothing is truly "ignored."

**Error handling approach:**
APIs fail. Rate limits happen. The workflow catches these and either retries, uses cached data, or marks the enrichment as incomplete rather than crashing. A failed VirusTotal lookup shouldn't block the entire triage.

## Setup

### Prerequisites
- Docker and Docker Compose
- API keys for VirusTotal, AbuseIPDB (free tiers work fine)
- Optional: Jira account, Slack workspace

### Quick Start

```bash
# Clone and enter directory
cd n8n

# Copy environment template
cp .env.example .env

# Add your API keys to .env
nano .env

# Start n8n
docker compose up -d

# Open browser
open http://localhost:5678
```

Default login: `admin` / `changeme` (change these in docker-compose.yml)

### Import the Workflow

1. Open n8n at http://localhost:5678
2. Go to Workflows → Import from File
3. Select `workflows/phishing-triage.json`
4. Configure credentials for each service
5. Activate the workflow

## Testing

Send a test payload to the webhook:

```bash
curl -X POST http://localhost:5678/webhook/phishing-triage \
  -H "Content-Type: application/json" \
  -d @examples/sample-payloads/suspicious-email.json
```

## What I Learned

**API integration is 80% data wrangling.** The actual HTTP request is trivial. Understanding response schemas, handling edge cases, and transforming data between services is where the real work happens.

**Rate limits require architectural thinking.** Free tier APIs have tight limits. The workflow needs queuing, backoff, and graceful degradation - not just "retry 3 times."

**Observability matters.** When a workflow fails at 3am, you need to know why. n8n's execution logs are decent, but I added extra logging nodes at key decision points.

## Future Improvements

- [ ] Add email ingestion (IMAP polling or O365/Gmail API)
- [ ] Implement proper rate limit queuing with Redis
- [ ] Add more enrichment sources (Shodan, URLScan.io)
- [ ] Build a simple dashboard for metrics
- [ ] Add ML-based scoring as a comparison to rule-based

## Project Structure

```
n8n/
├── docker-compose.yml      # n8n container configuration
├── .env.example            # Environment template
├── workflows/              # Exported n8n workflows
├── docs/                   # Setup and API guides
├── examples/               # Sample payloads and responses
└── data/                   # n8n persistent data (gitignored)
```

## License

MIT - do whatever you want with it.
