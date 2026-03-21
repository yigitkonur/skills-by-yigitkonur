# Cron Scheduling Guide

The `cron` tool is a built-in OpenClaw tool in the `group:automation` group. It manages scheduled jobs that run automatically at specified intervals.

## API reference

### cron.add

Creates a new scheduled job. All fields documented below match the verified schema from docs.openclaw.ai.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Unique job identifier |
| `schedule` | object | Yes | Timing configuration (see schedule kinds below) |
| `sessionTarget` | string | Yes | Where the job runs: `"main"`, `"isolated"`, `"current"`, or `"session:<id>"` |
| `payload` | object | Yes | What the job does (see payload kinds below) |
| `wakeMode` | string | No | `"now"` or `"next-heartbeat"` |
| `deleteAfterRun` | boolean | No | Remove job after first execution |
| `delivery` | object | No | How to deliver results (see delivery below) |
| `agentId` | string | No | Target agent for the job |
| `description` | string | No | Human-readable description |
| `enabled` | boolean | No | Whether the job is active (default `true`) |
| `bestEffort` | boolean | No | Skip if system is busy rather than queue |
| `lightContext` | boolean | No | Use minimal context for the session |

### Schedule kinds

Three schedule formats are supported:

#### kind: "at" -- one-time execution

```json
{
  "kind": "at",
  "at": "2026-04-01T09:00:00Z"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `kind` | string | Yes | Must be `"at"` |
| `at` | string | Yes | ISO 8601 datetime |

#### kind: "every" -- interval-based

```json
{
  "kind": "every",
  "everyMs": 300000
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `kind` | string | Yes | Must be `"every"` |
| `everyMs` | int | Yes | Interval in milliseconds |

#### kind: "cron" -- cron expression

```json
{
  "kind": "cron",
  "expr": "0 9 * * 1-5",
  "tz": "America/New_York"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `kind` | string | Yes | Must be `"cron"` |
| `expr` | string | Yes | 5 or 6-field cron expression |
| `tz` | string | Yes | IANA timezone (e.g. `"America/New_York"`, `"Europe/London"`) |

### Stagger

Top-of-hour and popular schedules automatically get staggered up to 5 minutes (300000ms) to avoid thundering-herd effects.

| Setting | Description |
|---------|-------------|
| `staggerMs: 0` | No stagger (exact timing) |
| `staggerMs: 0-300000` | Random delay up to value |
| CLI: `--stagger 30s` | Set stagger via CLI |
| CLI: `--exact` | Sets `staggerMs: 0` |

### Payload kinds

#### kind: "systemEvent"

Triggers a system-level event:

```json
{
  "kind": "systemEvent",
  "text": "Run daily health check",
  "model": "claude-sonnet-4-20250514",
  "thinking": "low",
  "timeoutSeconds": 120,
  "lightContext": true
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `kind` | string | Yes | Must be `"systemEvent"` |
| `text` | string | Yes | Event description / instruction |
| `model` | string | No | Override LLM model for this job |
| `thinking` | string | No | `"off"`, `"minimal"`, `"low"`, `"medium"`, `"high"`, `"xhigh"` |
| `timeoutSeconds` | int | No | Max execution time |
| `lightContext` | boolean | No | Minimal context mode |

#### kind: "agentTurn"

Sends a message to the agent as if a user sent it:

```json
{
  "kind": "agentTurn",
  "message": "Generate the weekly analytics report and send it to #reports",
  "model": "claude-sonnet-4-20250514",
  "thinking": "medium",
  "timeoutSeconds": 300
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `kind` | string | Yes | Must be `"agentTurn"` |
| `message` | string | Yes | Message to send to the agent |
| `model` | string | No | Override LLM model |
| `thinking` | string | No | `"off"`, `"minimal"`, `"low"`, `"medium"`, `"high"`, `"xhigh"` |
| `timeoutSeconds` | int | No | Max execution time |
| `lightContext` | boolean | No | Minimal context mode |

### Delivery

Controls how job results are delivered:

```json
{
  "mode": "announce",
  "channel": "slack",
  "to": "#ops-alerts",
  "bestEffort": true
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mode` | string | Yes | `"none"`, `"announce"`, or `"webhook"` |
| `channel` | string | No | `"whatsapp"`, `"telegram"`, `"discord"`, `"slack"`, `"mattermost"`, `"signal"`, `"imessage"`, or `"last"` |
| `to` | string | No | Destination within the channel (e.g. channel name, chat ID) |
| `bestEffort` | boolean | No | Skip delivery silently if it fails |

### Complete cron.add example

```json
{
  "name": "daily-health-check",
  "description": "Run health diagnostics every morning",
  "schedule": {
    "kind": "cron",
    "expr": "0 9 * * *",
    "tz": "America/New_York"
  },
  "sessionTarget": "isolated",
  "payload": {
    "kind": "agentTurn",
    "message": "Run a full health check and report any issues.",
    "thinking": "low",
    "timeoutSeconds": 120
  },
  "delivery": {
    "mode": "announce",
    "channel": "slack",
    "to": "#ops-alerts"
  },
  "enabled": true
}
```

## Other cron API operations

| Operation | Description |
|-----------|-------------|
| `cron.list` | List all scheduled jobs |
| `cron.status` | Get status of the cron subsystem |
| `cron.update` | Modify an existing job (partial update) |
| `cron.remove` | Delete a job by name |
| `cron.run` | Manually trigger a job immediately |
| `cron.runs` | View execution history for a job |
| `system.event` | Fire a one-off system event (related but not cron-specific) |

## Cron subsystem configuration

Server-level settings for the cron subsystem:

```yaml
cron:
  enabled: true                    # Master switch for cron subsystem
  store: "sqlite"                  # Job storage backend
  maxConcurrentRuns: 1             # Max simultaneous job executions
  retry:
    maxAttempts: 3                 # Retry failed jobs up to N times
    backoffMs: 5000                # Delay between retries (ms)
    retryOn: "failure"             # When to retry: "failure", "timeout", "any"
  sessionRetention: "24h"          # How long to keep job session data
  runLog:
    maxBytes: 1048576              # Max log size per run
    keepLines: 1000                # Max log lines kept per run
```

### Disabling cron entirely

Two methods:

```yaml
# Method 1: config file
cron:
  enabled: false
```

```bash
# Method 2: environment variable
OPENCLAW_SKIP_CRON=1
```

## Cron expression format

Standard cron expressions use 5 fields (6-field with seconds is also supported):

```
*  *  *  *  *
|  |  |  |  |
|  |  |  |  +-- Day of week (0-7, 0 and 7 = Sunday)
|  |  |  +----- Month (1-12)
|  |  +-------- Day of month (1-31)
|  +----------- Hour (0-23)
+-------------- Minute (0-59)
```

### Common schedules

| Schedule | Expression | Description |
|----------|------------|-------------|
| Every minute | `* * * * *` | Use sparingly -- high resource usage |
| Every 5 minutes | `*/5 * * * *` | Good for frequent checks |
| Every hour | `0 * * * *` | At the top of each hour |
| Every day at midnight | `0 0 * * *` | Daily maintenance tasks |
| Every Monday at 9am | `0 9 * * 1` | Weekly reports |
| First of month at noon | `0 12 1 * *` | Monthly summaries |
| Weekdays at 8am | `0 8 * * 1-5` | Business-hour automation |

## Safety rules for cron jobs

### Before creating any cron job

1. **Confirm the user wants automated execution.** Never create a cron job without explicit consent.
2. **Define the disable path.** Tell the user exactly how to stop the job (`cron.remove` with the job name).
3. **Set reasonable frequency.** Do not create jobs that run every minute unless clearly justified.
4. **Define failure behavior.** Configure retry settings and delivery for failure notification.
5. **Check for existing jobs.** Run `cron.list` to avoid duplicates or conflicts.

### Mandatory safety constraints

- Every cron job MUST have a corresponding disable/delete instruction provided to the user
- Jobs that call exec MUST have `timeoutSeconds` limits in the payload
- Jobs that call external APIs MUST have rate limiting awareness
- Jobs that modify data MUST log what they changed
- Jobs MUST NOT run unbounded loops (set max iterations)
- Jobs MUST NOT contain secrets in their definition (use environment variables)
- Use `sessionTarget: "isolated"` for jobs that should not affect the main session

## Combining cron with other tools

### Cron + Lobster

Use cron to trigger a Lobster workflow on a schedule. The cron payload sends a message that starts the workflow; Lobster manages multi-step execution.

**Warning:** If the Lobster workflow includes approval gates, the cron-triggered instance will pause at the gate and wait for human approval. Design cron-triggered workflows to either skip approval or use `delivery` to alert the human.

### Cron + exec

Use cron to run shell commands on a schedule.

**Warning:** This is the highest-risk combination. Always:

- Use `sessionTarget: "isolated"` to contain damage
- Set `timeoutSeconds` in the payload
- Use `delivery` to report results
- Never include secrets in the payload message
- Use absolute paths in commands

### Cron + LLM Task

Use cron to trigger LLM analysis on a schedule. Good for periodic reports, summarization, or anomaly detection.

**Pattern:** Cron payload sends an `agentTurn` message that invokes the LLM Task. Use `thinking` level appropriate to the task complexity.

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| Job does not run | Wrong schedule expression | Verify `expr` format, check `tz` is correct IANA timezone |
| Job runs at wrong time | Missing or wrong `tz` field | Always specify `tz` with cron kind schedules |
| Job runs too often | Wrong `everyMs` value or cron expression | Check units (everyMs is milliseconds, not seconds) |
| Job fails silently | No `delivery` configured | Add delivery with `mode: "announce"` to a monitoring channel |
| Job conflicts with another | Overlapping schedules | Use `cron.list` to audit, stagger schedules |
| Job runs but no output | Session ended before completion | Increase `timeoutSeconds`, check `sessionRetention` |
| Stagger causes missed window | Auto-stagger pushed job past deadline | Set `staggerMs: 0` or use `--exact` CLI flag |
| Too many concurrent runs | Default `maxConcurrentRuns: 1` | Increase `maxConcurrentRuns` in cron config if needed |

## Community skills

Check if these are available for specialized cron guidance:

| Skill | Focus |
|-------|-------|
| `cron-mastery` | Advanced cron expression patterns |
| `cron-creator` | Interactive cron expression builder |
| `cron-guardrails` | Safety validation for cron jobs |
| `safe-cron-runner` | Sandboxed cron execution |
