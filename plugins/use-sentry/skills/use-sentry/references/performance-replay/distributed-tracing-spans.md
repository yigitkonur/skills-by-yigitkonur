# Performance: Distributed Tracing & Spans

How to instrument transactions, trace latency bottlenecks across microservices, and manage span lifecycles.

## The Tracing Model: Traces, Transactions & Spans

- **Trace:** The entire end-to-end journey of a user request across multiple services (identified by a 32-character hex `traceId`).
- **Transaction:** A top-level operation representing a single unit of work (e.g. an HTTP route `POST /api/v1/checkout` or CLI command).
- **Span:** An individual timed operation within a transaction (e.g. `db.query`, `http.client`, `cache.get`).

## 1. Creating Custom Spans with `startSpan`

```typescript
import * as Sentry from '@sentry/node';

export async function executeDatabaseQuery<T>(sql: string, params: any[]): Promise<T> {
  return Sentry.startSpan(
    {
      name: 'db.query',
      op: 'db.query',
      attributes: {
        'db.system': 'postgresql',
        'db.statement': sql,
      },
    },
    async (span) => {
      try {
        const result = await pool.query(sql, params);
        span.setStatus({ code: 1 }); // OK
        return result.rows as unknown as T;
      } catch (err: any) {
        span.setStatus({ code: 2, message: err.message }); // ERROR
        throw err;
      }
    }
  );
}
```

## 2. Propagating Distributed Trace Headers

When making outbound HTTP calls to other internal services or APIs:

```typescript
export function getOutboundTraceHeaders(): Record<string, string> {
  const span = Sentry.getActiveSpan();
  if (!span) return {};

  const headers: Record<string, string> = {};
  
  const sentryTrace = Sentry.spanToTraceHeader(span);
  if (sentryTrace) headers['sentry-trace'] = sentryTrace;

  const baggage = Sentry.spanToBaggageHeader(span);
  if (baggage) headers['baggage'] = baggage;

  return headers;
}
```

Downstream services reading `sentry-trace` will adopt the same `traceId`, linking all spans into a unified waterfall in Sentry.

## 3. Investigating Spans via CLI

```bash
# View complete span tree for a slow trace:
sentry trace view <TRACE_ID>

# List spans in a project matching an operation:
sentry span list <org>/<project>
```
