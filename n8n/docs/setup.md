# n8n Setup Guide

## Prerequisites

- Docker and Docker Compose installed
- User added to `docker` group

## Quick Start

```bash
cd ~/Documents/Projects/Automation-Engineering/n8n

# Start n8n
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f n8n
```

## Access n8n

Open http://localhost:5678 in your browser.

**Default credentials:**
- Username: `admin`
- Password: `changeme`

## Common Commands

```bash
# Start n8n
docker compose up -d

# Stop n8n
docker compose down

# Restart n8n
docker compose restart

# View logs
docker compose logs -f n8n

# Check health
docker compose ps
```

## Data Persistence

All n8n data is stored in `./data/` directory:
- Workflows
- Credentials
- Settings
- Execution history

**Important:** Back up this directory to preserve your work.

## Troubleshooting

### Port 5678 already in use
```bash
# Find what's using the port
sudo lsof -i :5678

# Or change port in docker-compose.yml
ports:
  - "5679:5678"  # Access at localhost:5679
```

### Permission denied on data directory
```bash
# Fix permissions
sudo chown -R 1000:1000 ./data
```

### Container won't start
```bash
# Check logs
docker compose logs n8n

# Remove and recreate
docker compose down
docker compose up -d
```

### Can't access web UI
1. Check container is running: `docker compose ps`
2. Check logs for errors: `docker compose logs n8n`
3. Verify port mapping: `docker port n8n`
4. Try http://127.0.0.1:5678 instead of localhost

## Changing Credentials

Edit `docker-compose.yml`:
```yaml
environment:
  - N8N_BASIC_AUTH_USER=your_username
  - N8N_BASIC_AUTH_PASSWORD=your_secure_password
```

Then restart: `docker compose down && docker compose up -d`

## Next Steps

1. Create your first workflow in n8n UI
2. Set up API credentials (see `api-setup.md`)
3. Import the phishing triage workflow
