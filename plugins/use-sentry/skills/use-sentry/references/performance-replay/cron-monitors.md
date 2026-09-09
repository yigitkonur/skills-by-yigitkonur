# Cron Monitors & Background Job Heartbeats

How to monitor recurring cron jobs, BullMQ workers, and scheduled pipelines to alert on silent failures and missed executions.

## The Silent Cron Failure Trap

Scheduled background jobs (e.g. nightly backups, daily billing runs, sitemap updates) often fail silently:
- If a cron job crashes before sending an exception, nothing is reported.
- If the server hosting the cron job stalls or reboots, no alert fires.
- If an infinite loop occurs, the process hangs indefinitely.

Sentry Cron Monitors solve this via bidirectional check-in heartbeats.

## 1. Instrumenting a Scheduled Task in Node.js

Use `Sentry.withMonitor` to automatically track start, completion, and duration:

```typescript
import * as Sentry from '@sentry/node';

export async function runDailyBillingSync() {
  return Sentry.withMonitor('daily-billing-sync', async () => {
    // Everything inside this callback is tracked
    await executeBillingSteps();
  }, {
    schedule: {
      type: 'crontab',
      value: '0 2 * * *', // Daily at 02:00 AM UTC
    },
    checkinMargin: 10,     // Allow 10 minutes grace window
    maxRuntime: 60,        // Alert if execution takes longer than 60 minutes
    timezone: 'UTC',
  });
}
```

## 2. Manual Check-in Lifecycle (Custom Transports / Bash)

For external bash scripts or distributed worker queues:

```bash
# 1. Send IN_PROGRESS check-in at start
CHECK_IN_ID=$(curl -s -X POST \
  -H "Authorization: DSN ${SENTRY_DSN}" \
  -H "Content-Type: application/json" \
  -d '{"status":"in_progress"}' \
  "https://sentry.io/api/0/monitors/daily-backup/check-ins/" | jq -r .id)

# 2. Execute workload
if ./run-backup.sh; then
  # 3. Send OK check-in
  curl -s -X PUT \
    -H "Authorization: DSN ${SENTRY_DSN}" \
    -H "Content-Type: application/json" \
    -d '{"status":"ok"}' \
    "https://sentry.io/api/0/monitors/daily-backup/check-ins/${CHECK_IN_ID}/"
else
  # 4. Send ERROR check-in
  curl -s -X PUT \
    -H "Authorization: DSN ${SENTRY_DSN}" \
    -H "Content-Type: application/json" \
    -d '{"status":"error"}' \
    "https://sentry.io/api/0/monitors/daily-backup/check-ins/${CHECK_IN_ID}/"
  exit 1
fi
```

Sentry alerts automatically if:
- The job does not check in within the scheduled window (missed).
- The job runs longer than `maxRuntime` (timed out).
- The check-in status is `error`.
