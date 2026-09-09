# Sentry Envelope Tunneling Architecture

How to configure Sentry SDKs with official envelope tunnels to bypass ad-blockers, corporate firewalls, and ISP DNS sinkholes.

## What is an Envelope Tunnel?

Sentry events, transactions, sessions, and attachments are formatted as **Envelopes** (RFC-style multipart JSON streams).

By default, SDKs send envelopes directly to the ingest host found in the DSN:
`POST https://o{orgId}.ingest.{region}.sentry.io/api/{projectId}/envelope/`

When an envelope tunnel is configured, the SDK redirects all outgoing HTTP POST requests to an alternative URL, while preserving the envelope payload and Sentry auth headers.

## Configuration in Sentry SDK

Most modern Sentry SDKs support the `tunnel` configuration option:

```typescript
import * as Sentry from '@sentry/node';

const projectId = '4512053148975104';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  // Direct Sentry tunnel bypassing *.ingest.* sinkholes:
  tunnel: `https://sentry.io/api/${projectId}/envelope/`,
  environment: process.env.NODE_ENV || 'production',
  tracesSampleRate: 1.0,
});
```

## Dynamic Tunnel Construction from DSN

```typescript
export function buildSentryTunnelUrl(dsn: string | undefined): string | undefined {
  if (!dsn) return undefined;
  
  const match = dsn.trim().match(/\/(\d+)(?:$|[?#])/);
  if (!match || !match[1]) return undefined;

  const projectId = match[1];
  return `https://sentry.io/api/${projectId}/envelope/`;
}
```

## Envelope Structure Example

The body of a Sentry envelope sent to the tunnel:

```text
{"event_id":"9ec60100773b4f648b265b1618c774f0","sent_at":"2026-09-08T22:45:19.448Z","dsn":"https://PUBLIC_KEY@o279668.ingest.us.sentry.io/4512053148975104"}
{"type":"event","content_type":"application/json","length":412}
{"message":"Test error","level":"error","platform":"node","timestamp":1757371519.448}
```
