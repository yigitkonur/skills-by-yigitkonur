# Sentry Envelope Tunneling Architecture

How to configure Sentry SDKs with application-hosted reverse proxy envelope tunnels to bypass ad-blockers, corporate firewalls, and ISP DNS sinkholes.

## What is an Envelope Tunnel?

Sentry events, transactions, sessions, and attachments are formatted as **Envelopes** (RFC-style multipart JSON streams).

By default, SDKs send envelopes directly to the ingest host found in the DSN:
`POST https://o{orgId}.ingest.{region}.sentry.io/api/{projectId}/envelope/`

When an envelope tunnel is configured, the SDK redirects all outgoing HTTP POST requests to an application-hosted reverse proxy route, while preserving the envelope payload and Sentry auth headers.

## Configuration in Sentry SDK

In client and server applications, configure `tunnel` to route to an application endpoint (e.g. `/api/monitoring/tunnel`):

```typescript
import * as Sentry from '@sentry/browser';

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  // Application-hosted reverse proxy route defeating ad-blockers and captive ISP sinkholes:
  tunnel: '/api/monitoring/tunnel',
  environment: process.env.NODE_ENV || 'production',
  tracesSampleRate: 1.0,
});
```

## Dynamic Tunnel Construction

```typescript
export function buildSentryTunnelUrl(): string {
  // Always route client-side telemetry through the application's internal reverse proxy
  return '/api/monitoring/tunnel';
}
```

## Envelope Structure Example

The body of a Sentry envelope sent to the tunnel:

```text
{"event_id":"9ec60100773b4f648b265b1618c774f0","sent_at":"2026-09-08T22:45:19.448Z","dsn":"https://PUBLIC_KEY@o279668.ingest.us.sentry.io/4512053148975104"}
{"type":"event","content_type":"application/json","length":412}
{"message":"Test error","level":"error","platform":"node","timestamp":1757371519.448}
```
