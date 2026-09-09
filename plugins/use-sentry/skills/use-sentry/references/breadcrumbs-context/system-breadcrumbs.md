# Contextual Breadcrumbs: System Breadcrumbs

How to record HTTP calls, database transactions, RPC messages, and filesystem events as breadcrumbs to reconstruct crash timelines.

## The Role of System Breadcrumbs

An unhandled exception only reveals the final line of failure. System breadcrumbs reconstruct the chronological sequence of system state leading up to that failure.

## 1. Outbound HTTP Request Breadcrumbs

When using `fetch`, `axios`, or `undici`:

```typescript
import * as Sentry from '@sentry/node';

export function addHttpBreadcrumb(params: {
  method: string;
  url: string;
  statusCode?: number;
  durationMs?: number;
}) {
  const cleanUrl = params.url.replace(/([?&](?:jwt|token|key|secret)=)[^&#\s]+/gi, '$1[Filtered]');

  Sentry.addBreadcrumb({
    category: 'http',
    type: 'http',
    level: params.statusCode && params.statusCode >= 400 ? 'warning' : 'info',
    message: `${params.method} ${cleanUrl} (${params.statusCode || 'in-flight'})`,
    data: {
      method: params.method,
      url: cleanUrl,
      status_code: params.statusCode,
      duration_ms: params.durationMs,
    },
    timestamp: Date.now() / 1000,
  });
}
```

## 2. Database Query Breadcrumbs

Record SQL or ORM operations:

```typescript
export function addDbBreadcrumb(params: {
  table: string;
  operation: 'SELECT' | 'INSERT' | 'UPDATE' | 'DELETE' | 'TRANSACTION';
  durationMs?: number;
  rowCount?: number;
}) {
  Sentry.addBreadcrumb({
    category: 'db.query',
    message: `${params.operation} ${params.table} (${params.durationMs}ms)`,
    level: 'info',
    data: {
      table: params.table,
      op: params.operation,
      duration_ms: params.durationMs,
      rows: params.rowCount,
    },
    timestamp: Date.now() / 1000,
  });
}
```

## 3. Cache Transaction Breadcrumbs

```typescript
export function addCacheBreadcrumb(key: string, hit: boolean) {
  Sentry.addBreadcrumb({
    category: 'cache',
    message: `Cache ${hit ? 'HIT' : 'MISS'}: ${key}`,
    level: 'info',
    data: { key, hit },
  });
}
```
