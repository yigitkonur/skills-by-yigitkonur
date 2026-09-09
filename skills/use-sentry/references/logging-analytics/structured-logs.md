# Log Management & Analytics: Structured Logs

How to ingest, index, and query application logs alongside Sentry error states using Sentry's modern logging pipeline.

## Why Structured Logs in Sentry?

Historically, developers maintained separate logging infrastructure (Elasticsearch, Datadog) alongside Sentry.
With Sentry Structured Logs:
- Application logs are correlated with distributed `traceId` values automatically.
- Logs and exceptions appear in a unified timeline.
- High-severity log spikes can automatically trigger alerts.

## 1. Sending Structured Logs via Sentry SDK

In modern `@sentry/node`:

```typescript
import * as Sentry from '@sentry/node';

// Sentry structured logger integration
export const sentryLogger = {
  info(message: string, attributes?: Record<string, any>) {
    Sentry.logger.info(message, {
      ...attributes,
      timestamp: new Date().toISOString(),
    });
  },

  warn(message: string, attributes?: Record<string, any>) {
    Sentry.logger.warn(message, {
      ...attributes,
      timestamp: new Date().toISOString(),
    });
  },

  error(message: string, error?: unknown, attributes?: Record<string, any>) {
    Sentry.logger.error(message, {
      ...attributes,
      error: error instanceof Error ? error.message : String(error),
      timestamp: new Date().toISOString(),
    });
  },
};
```

## 2. Pino & Winston Integration

If using Pino, forward logs using the official Sentry transport:

```typescript
import pino from 'pino';

export const logger = pino({
  transport: {
    target: '@sentry/pino-transport',
    options: {
      sentry: {
        dsn: process.env.SENTRY_DSN,
      },
      minLevel: 30, // 30 = info, 40 = warn, 50 = error
    },
  },
});
```

## 3. Querying Structured Logs via Sentry CLI

```bash
# Query recent error logs
sentry log list <org>/<project> -q 'level:error' -t 24h -n 20 --json \
  | jq -r '.data[] | "\(.timestamp) [\(.severity)] \(.message)"'

# Live tail stream logs in terminal
sentry log list <org>/<project> -q 'level:error' -f
```
