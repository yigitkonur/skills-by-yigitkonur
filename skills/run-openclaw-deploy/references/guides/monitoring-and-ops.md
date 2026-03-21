# Monitoring and Operations

This guide covers health monitoring, cost tracking, backup strategies, and operational procedures for production OpenClaw instances.

## Uptime monitoring (essential)

**Uptime monitoring is essential for production.** Community reports consistently note that slow failure (degraded performance, partial outages) is worse than immediate failure because it goes undetected longer.

### External uptime monitoring

Set up external monitoring that checks from outside your network:

| Service | How to configure | Notes |
|---------|-----------------|-------|
| UptimeRobot | HTTP check on `https://your-domain/health` | Free tier available |
| Better Uptime | HTTP check + status page | Includes incident management |
| Pingdom | HTTP check with response validation | Enterprise features |
| Custom | Poll `/health?detail=true` and parse JSON | Most flexible |

**Do not rely only on internal health checks.** If the host or network is down, internal checks cannot alert you.

## Health checks

### Built-in health monitoring

```bash
# Run health check
openclaw skill run healthcheck

# The healthcheck skill verifies:
# - Gateway status and uptime
# - LLM provider connectivity and latency
# - Messaging channel status
# - Disk space and resource utilization
# - Active skill count and status
# - Sandbox container health
```

### Automated health checks

```yaml
monitoring:
  health:
    enabled: true
    interval_seconds: 300
    alert_channels:
      - "slack:#ops-alerts"
      - "telegram:admin-chat"
    checks:
      - gateway_status
      - llm_provider_health
      - channel_connectivity
      - disk_space
      - memory_usage
    thresholds:
      disk_space_min_percent: 20
      memory_max_percent: 85
      llm_latency_max_ms: 5000
      channel_timeout_seconds: 30
```

### HTTP health endpoint

```bash
# Basic health check
curl -f http://localhost:8080/health

# Detailed health check
curl http://localhost:8080/health?detail=true

# Expected response:
# {
#   "status": "healthy",
#   "gateway": "running",
#   "uptime_seconds": 86400,
#   "llm_provider": "connected",
#   "channels": { "slack": "connected", "telegram": "connected" },
#   "disk_space_percent": 65,
#   "memory_percent": 42
# }
```

### RAM monitoring

OpenClaw uses 1.5-2 GB idle. Monitor memory to catch leaks early:

```yaml
monitoring:
  health:
    thresholds:
      # Warn when memory exceeds 85% of available
      memory_max_percent: 85
      # With 4 GB recommended RAM, this triggers at ~3.4 GB
```

If memory consistently exceeds 3 GB, investigate:
- Runaway skills or tool loops consuming memory
- Large conversation contexts not being cleaned up
- Too many concurrent cron jobs

## LLM cost tracking

### API spending caps (set BEFORE connecting channels)

**This is the single most important operational configuration.** Real-world reports document $300-600 bills from retry loops caused by messaging channel reconnections.

```yaml
monitoring:
  cost:
    enabled: true
    # CRITICAL: Set these BEFORE connecting any messaging channel
    daily_limit_usd: 50
    weekly_limit_usd: 250
    monthly_limit_usd: 800
    # Use "stop" not "alert" -- by the time you read an alert, the damage is done
    limit_action: "stop"
    alert_channels:
      - "slack:#ops-alerts"
    per_skill_tracking: true
    per_channel_tracking: true
```

### Using the model-usage skill

```bash
openclaw skill run model-usage

# Output includes:
# - Total tokens used (input/output)
# - Cost breakdown by provider
# - Cost breakdown by skill
# - Cost breakdown by channel
# - Daily/weekly/monthly trends
# - Projected monthly cost
```

### Cost optimization strategies

| Strategy | When to use | How |
|----------|-------------|-----|
| Model routing | Different tasks need different capability levels | Route simple tasks to cheaper models |
| Token limits per session | Prevent runaway sessions | Set `max_tokens_per_session` |
| Skill-level budgets | Some skills are disproportionately expensive | Set per-skill token limits |
| Channel routing | Chat channels produce high volume | Route high-volume channels to cost-effective models |
| Spending caps with stop action | Always | Set `limit_action: "stop"` |

## Maintenance operations

### Updates are manual

OpenClaw does not auto-update. You must manually pull new versions and restart.

**Warning:** Config format changes between versions occasionally break things. Always:

1. Back up the current configuration
2. Read the release notes for breaking changes
3. Update in a staging environment first
4. Apply the update
5. Run health checks
6. Roll back if anything fails

### Update procedure (Docker)

```bash
# Back up first
docker exec openclaw tar -czf /data/backup-pre-update.tar.gz /config

# Pull new version
docker pull openclaw/openclaw:latest

# Stop current container
docker stop openclaw
docker rm openclaw

# Start with new version
docker run -d \
  --name openclaw \
  --restart unless-stopped \
  -v openclaw-data:/data \
  -v openclaw-config:/config \
  -e OPENCLAW_API_KEY="${OPENCLAW_API_KEY}" \
  -p 127.0.0.1:8080:8080 \
  openclaw/openclaw:latest

# Verify
curl -f http://localhost:8080/health
docker exec openclaw node --version  # Must be v22.x.x
```

## Cron subsystem operations

The cron subsystem has its own configuration that affects monitoring and operations:

```yaml
cron:
  enabled: true
  store: "sqlite"
  maxConcurrentRuns: 1
  retry:
    maxAttempts: 3
    backoffMs: 5000
    retryOn: "failure"
  sessionRetention: "24h"
  runLog:
    maxBytes: 1048576
    keepLines: 1000
```

### Disabling cron

Two methods for emergencies:

```yaml
# Method 1: config
cron:
  enabled: false
```

```bash
# Method 2: environment variable (fastest for emergencies)
OPENCLAW_SKIP_CRON=1
```

### Monitoring cron jobs

Use `cron.runs` to review execution history. Watch for:
- Jobs that consistently fail (investigate root cause)
- Jobs that take longer than expected (add timeouts)
- Jobs that overlap (increase interval or reduce `maxConcurrentRuns`)
- Retry storms (reduce `maxAttempts` or increase `backoffMs`)

## Backup and disaster recovery

### What to back up

| Component | Location | Frequency | Priority |
|-----------|----------|-----------|----------|
| Configuration files | `/config/` | After every change | Critical |
| Agent data | `/data/` | Daily | High |
| Skill definitions | `/skills/` | After changes | High |
| Environment variables | Secrets manager | After changes | Critical |
| Gateway state | Gateway export | Daily | Medium |
| Conversation history | `/data/conversations/` | Daily | Medium |

### Automated file backup

```bash
#!/bin/bash
BACKUP_DIR="/backups/openclaw/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

cp -r /config "$BACKUP_DIR/config"
cp -r /data "$BACKUP_DIR/data"
cp -r /skills "$BACKUP_DIR/skills"

openclaw gateway export > "$BACKUP_DIR/gateway-state.json"

tar -czf "$BACKUP_DIR.tar.gz" -C "$(dirname $BACKUP_DIR)" "$(basename $BACKUP_DIR)"
rm -rf "$BACKUP_DIR"

# Rotate: keep last 30 days
find /backups/openclaw/ -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR.tar.gz"
```

### Docker volume backup

```bash
docker stop openclaw

docker run --rm \
  -v openclaw-data:/source:ro \
  -v /backups:/backup \
  alpine tar -czf /backup/openclaw-data-$(date +%Y%m%d).tar.gz -C /source .

docker run --rm \
  -v openclaw-config:/source:ro \
  -v /backups:/backup \
  alpine tar -czf /backup/openclaw-config-$(date +%Y%m%d).tar.gz -C /source .

docker start openclaw
```

### Restore procedure

1. Stop the OpenClaw instance
2. Restore configuration files from backup
3. Restore data from backup
4. Verify environment variables are correct
5. Start the OpenClaw instance
6. Run `healthcheck` to verify restoration
7. Test at least one messaging channel end-to-end

### Disaster recovery planning

- **RTO (Recovery Time Objective):** How fast must the instance be back? Size backup/restore accordingly.
- **RPO (Recovery Point Objective):** How much data loss is acceptable? Set backup frequency accordingly.
- **Test restores regularly.** A backup that has never been tested is not a backup.
- **Store backups off-site.** Local-only backups do not survive disk failure or host compromise.
- **Document the restore procedure** and keep it accessible outside the OpenClaw instance.

## Log management

### Accessing logs

```bash
# Docker logs
docker logs openclaw --tail 100 --follow

# Systemd logs (bare VPS)
journalctl -u openclaw --since "1 hour ago"

# Application logs (inside container)
tail -f /data/logs/openclaw.log
```

### Log configuration

```yaml
logging:
  level: "info"
  format: "json"
  max_size_mb: 100
  max_files: 10
  audit:
    enabled: true
    file: "/data/logs/audit.log"
```

### What to monitor in logs

| Log pattern | Indicates | Action |
|-------------|-----------|--------|
| Repeated authentication failures | Brute-force attempt | Check IP restrictions, rate limiting |
| LLM provider errors | Provider instability | Check failover configuration |
| Exec approval timeouts | Operator not responding | Adjust timeout or alert routing |
| Tool-loop detection triggers | Agent in infinite loop | Review the triggering skill |
| High memory or CPU warnings | Resource exhaustion (need 4 GB RAM) | Scale up or optimize |
| Channel disconnect events | Messaging platform issues | Check credentials, WhatsApp keepalive |
| Cost limit reached | Spending cap triggered | Review what caused the spike |
| Cron retry storms | Jobs failing repeatedly | Reduce maxAttempts, fix root cause |

## Operational runbook

### Daily operations

- Review health check status (automated alerts should cover this)
- Check cost tracking dashboard
- Review audit logs for security anomalies
- Verify WhatsApp session is still connected (if using WhatsApp)

### Weekly operations

- Verify backup integrity (test restore on staging)
- Review tool-loop detection triggers
- Check LLM provider usage trends
- Review and prune old conversation history if needed
- Check for OpenClaw updates and CVE patches

### Monthly operations

- Rotate OAuth2 secrets and API keys
- Update OpenClaw to the latest version (back up first, check release notes)
- Review and update security posture
- Test full disaster recovery procedure
- Review cost trends and adjust provider routing
- Audit installed skills against ClawHub advisories

## Steering experiences

### SE-01: Health checks pass but the instance is degraded
Health checks verify connectivity, not quality. An LLM provider may be responding slowly without triggering alerts. Use `model-usage` skill to track latency trends. Set up external uptime monitoring.

### SE-02: Backups exist but have never been tested
Schedule quarterly restore tests. An untested backup is unreliable.

### SE-03: Cost alerts arrive after the budget is already spent
Use `limit_action: "stop"`, not `"alert"`. Set daily limits, not just monthly ones. A runaway agent can exhaust a monthly budget in hours.

### SE-04: Slow failure goes undetected for days
Internal health checks cannot alert if the host is down. Always use external uptime monitoring (UptimeRobot, Better Uptime, etc.) that checks from outside your network.

### SE-05: Update breaks config format
OpenClaw config format changes between versions without migration tooling. Always back up config, read release notes, and update on staging first.
