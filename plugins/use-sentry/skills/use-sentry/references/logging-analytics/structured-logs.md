# Log Management & Analytics: Structured Logs

How to ingest, index, and query application logs alongside Sentry error states using Sentry's modern logging pipeline.

## Why Structured Logs in Sentry?

Historically, developers maintained separate logging infrastructure (Elasticsearch, Datadog) alongside Sentry.
With Sentry Structured Logs:
- Application logs are correlated with distributed `traceId` values automatically.
- Logs and exceptions appear in a unified timeline.
- High-severity log spikes can automatically trigger alerts.

---

## 1. Native Sentry Logger API (`Sentry.logger`)

Modern Sentry JavaScript SDKs (v10+ / v11+) follow an opt-in-by-usage model for logging. Logs are captured whenever you call `Sentry.logger.*` or register a logging integration:

```typescript
import * as Sentry from '@sentry/node';

// Standard structured logging with level functions
Sentry.logger.info('Database connection established', {
  host: 'db.internal',
  port: 5432,
});

Sentry.logger.warn('Rate limit approaching threshold', {
  remaining: 15,
  limit: 100,
});

Sentry.logger.error('Failed to process payment', {
  orderId: 'ord_123',
  reason: 'insufficient_funds',
});

// Parameterized format strings via Sentry.logger.fmt
const user = 'usr_456';
const team = 'core-eng';
Sentry.logger.info(Sentry.logger.fmt`User ${user} joined team ${team}`);
```

---

## 2. Official Pino Integration (`pinoIntegration`)

Instead of writing custom stream parsers, modern Sentry provides native Pino auto-instrumentation via `pinoIntegration()`:

```typescript
import * as Sentry from '@sentry/node';
import pino from 'pino';

// 1. Initialize Sentry with pinoIntegration
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  integrations: [
    Sentry.pinoIntegration(),
  ],
});

// 2. Initialize standard Pino logger
export const logger = pino({
  level: 'info',
});

// Logs emitted via Pino automatically carry active trace IDs, span contexts, and log attributes in Sentry
logger.info({ userId: '123' }, 'User logged in');
logger.error(new Error('Transaction rejected'), 'Payment failure');
```

---

## 3. Querying Structured Logs via Sentry CLI

```bash
# Query recent error logs
sentry log list <org>/<project> -q 'level:error' -t 24h -n 20 --json \
  | jq -r '.data[] | "\(.timestamp) [\(.severity)] \(.message)"'

# Live tail stream logs in terminal
sentry log list <org>/<project> -q 'level:error' -f
```
