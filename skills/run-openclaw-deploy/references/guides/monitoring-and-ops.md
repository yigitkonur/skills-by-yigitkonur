# Monitoring and Operations

This guide covers health monitoring, cost tracking, backup strategies, and operational procedures for production OpenClaw instances.

## Health checks

### Built-in health monitoring

OpenClaw provides the `healthcheck` skill for comprehensive instance health assessment.

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

Configure automated health checks for continuous monitoring:

```yaml
monitoring:
  health:
    enabled: true
    interval_seconds: 300  # Check every 5 minutes
    # Alert channels (uses configured messaging channels)
    alert_channels:
      - "slack:#ops-alerts"
      - "telegram:admin-chat"
    # What to check
    checks:
      - gateway_status
      - llm_provider_health
      - channel_connectivity
      - disk_space
      - memory_usage
    # Thresholds
    thresholds:
      disk_space_min_percent: 20
      memory_max_percent: 85
      llm_latency_max_ms: 5000
      channel_timeout_seconds: 30
```

### HTTP health endpoint

The gateway exposes a health endpoint for external monitoring:

```bash
# Basic health check
curl -f http://localhost:8080/health

# Detailed health check (includes component status)
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

### Integrating with external monitoring

Use the HTTP health endpoint with external monitoring tools:

- **Uptime monitoring** (UptimeRobot, Pingdom, Better Uptime): Point at `/health`
- **Prometheus/Grafana**: Scrape the `/metrics` endpoint if available
- **Custom alerting**: Poll `/health?detail=true` and parse the JSON response

## LLM cost tracking

### Using the model-usage skill

The `model-usage` skill tracks LLM API consumption and costs:

```bash
# View current usage
openclaw skill run model-usage

# Output includes:
# - Total tokens used (input/output)
# - Cost breakdown by provider
# - Cost breakdown by skill
# - Cost breakdown by channel
# - Daily/weekly/monthly trends
# - Projected monthly cost
```

### Cost alert configuration

```yaml
monitoring:
  cost:
    enabled: true
    # Alert thresholds
    daily_limit_usd: 50
    weekly_limit_usd: 250
    monthly_limit_usd: 800
    # Action when limit is reached: "alert", "throttle", "stop"
    limit_action: "alert"
    # Alert channels
    alert_channels:
      - "slack:#ops-alerts"
    # Track per-skill costs
    per_skill_tracking: true
    # Track per-channel costs
    per_channel_tracking: true
```

### Cost optimization strategies

| Strategy | When to use | How |
|----------|-------------|-----|
| Model routing | Different tasks need different capability levels | Route simple tasks to cheaper models via gateway-management.md |
| Token limits per session | Prevent runaway sessions | Set `max_tokens_per_session` in agent defaults |
| Skill-level budgets | Some skills are disproportionately expensive | Set per-skill token limits |
| Channel routing | Chat channels produce high volume | Route high-volume channels to cost-effective models |
| Community skill: `openclaw-cost-guardian` | Comprehensive cost governance | Install and configure for automated cost management |

## Backup and disaster recovery

### What to back up

| Component | Location | Frequency | Priority |
|-----------|----------|-----------|----------|
| Configuration files | `/config/` | After every change | Critical |
| Agent data | `/data/` | Daily | High |
| Skill definitions | `/skills/` (custom skills) | After changes | High |
| Environment variables | Secrets manager | After changes | Critical |
| Gateway state | Gateway export | Daily | Medium |
| Conversation history | `/data/conversations/` | Daily | Medium |

### Backup methods

#### Automated file backup

```bash
#!/bin/bash
# backup-openclaw.sh
BACKUP_DIR="/backups/openclaw/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Back up configuration
cp -r /config "$BACKUP_DIR/config"

# Back up data
cp -r /data "$BACKUP_DIR/data"

# Back up custom skills
cp -r /skills "$BACKUP_DIR/skills"

# Export gateway state
openclaw gateway export > "$BACKUP_DIR/gateway-state.json"

# Compress
tar -czf "$BACKUP_DIR.tar.gz" -C "$(dirname $BACKUP_DIR)" "$(basename $BACKUP_DIR)"
rm -rf "$BACKUP_DIR"

# Rotate: keep last 30 days
find /backups/openclaw/ -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR.tar.gz"
```

#### Docker volume backup

```bash
# Stop the container for consistent backup
docker stop openclaw

# Back up volumes
docker run --rm \
  -v openclaw-data:/source:ro \
  -v /backups:/backup \
  alpine tar -czf /backup/openclaw-data-$(date +%Y%m%d).tar.gz -C /source .

docker run --rm \
  -v openclaw-config:/source:ro \
  -v /backups:/backup \
  alpine tar -czf /backup/openclaw-config-$(date +%Y%m%d).tar.gz -C /source .

# Restart
docker start openclaw
```

#### Community backup skill

The `finn-openclaw-backup` community skill provides automated backup management:
- Scheduled backups with configurable retention
- Remote backup destinations (S3, GCS, SFTP)
- Backup verification and integrity checks
- One-command restore

### Restore procedure

1. Stop the OpenClaw instance
2. Restore configuration files from backup
3. Restore data from backup
4. Verify environment variables are correct
5. Start the OpenClaw instance
6. Run `healthcheck` to verify restoration
7. Test at least one messaging channel end-to-end

```bash
# Example restore
docker stop openclaw

# Restore volumes
docker run --rm \
  -v openclaw-config:/target \
  -v /backups:/backup:ro \
  alpine sh -c "rm -rf /target/* && tar -xzf /backup/openclaw-config-20240115.tar.gz -C /target"

docker run --rm \
  -v openclaw-data:/target \
  -v /backups:/backup:ro \
  alpine sh -c "rm -rf /target/* && tar -xzf /backup/openclaw-data-20240115.tar.gz -C /target"

docker start openclaw

# Verify
openclaw skill run healthcheck
```

### Disaster recovery planning

- **RTO (Recovery Time Objective):** How fast must the instance be back? Size backups and restore procedures accordingly.
- **RPO (Recovery Point Objective):** How much data loss is acceptable? Set backup frequency accordingly.
- **Test restores regularly.** A backup that has never been tested is not a backup.
- **Store backups off-site.** Local-only backups do not survive disk failure or host compromise.
- **Document the restore procedure** and keep it accessible outside the OpenClaw instance itself.

## Log management

### Accessing logs

```bash
# Docker logs
docker logs openclaw --tail 100 --follow

# Systemd logs (bare VPS)
journalctl -u openclaw --since "1 hour ago"

# Application logs (inside container or on host)
tail -f /data/logs/openclaw.log
```

### Log levels

```yaml
logging:
  level: "info"  # debug, info, warn, error
  # Structured JSON logging for machine parsing
  format: "json"
  # Log rotation
  max_size_mb: 100
  max_files: 10
  # Separate security audit log
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
| High memory or CPU warnings | Resource exhaustion | Scale up or optimize skill workloads |
| Channel disconnect events | Messaging platform issues | Check credentials and network |

## Operational runbook

### Daily operations

- Review health check status (automated alerts should cover this)
- Check cost tracking dashboard
- Review audit logs for security anomalies

### Weekly operations

- Verify backup integrity (test restore on a staging instance)
- Review tool-loop detection triggers
- Check LLM provider usage trends
- Review and prune old conversation history if needed

### Monthly operations

- Rotate OAuth2 secrets and API keys
- Update OpenClaw to the latest version
- Review and update security posture
- Test full disaster recovery procedure
- Review cost trends and adjust provider routing

## Steering experiences

### SE-01: Health checks pass but the instance is degraded
Health checks verify connectivity, not quality. An LLM provider may be responding slowly or producing poor results without triggering health alerts. Use `model-usage` skill to track latency trends.

### SE-02: Backups exist but have never been tested
Schedule quarterly restore tests. An untested backup is unreliable.

### SE-03: Cost alerts arrive after the budget is already spent
Set daily limits, not just monthly ones. A runaway agent can exhaust a monthly budget in hours.
