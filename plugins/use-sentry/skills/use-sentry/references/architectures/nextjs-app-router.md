# Architecture: Next.js App Router (14 & 15)

How to configure Sentry in Next.js across Client, Server, and Edge runtimes with automatic tunnel rewrites and proper `instrumentation.ts` registration.

## Installation

```bash
npm install @sentry/nextjs
```

## 1. Instrumentation Hook (`instrumentation.ts`)

Next.js 14 and 15 require an `instrumentation.ts` (or `instrumentation.js`) in the root (or `src/` directory) to initialize Sentry before any server code runs:

```typescript
export async function register() {
  if (process.env.NEXT_RUNTIME === 'nodejs') {
    await import('./sentry.server.config');
  }

  if (process.env.NEXT_RUNTIME === 'edge') {
    await import('./sentry.edge.config');
  }
}
```

## 2. Client Configuration (`sentry.client.config.ts`)

```typescript
import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  // Note: If tunnelRoute is defined in next.config.mjs, the SDK routes through it automatically.
  // Explicitly specifying tunnel here is optional or can override:
  tunnel: '/monitoring-tunnel',
  tracesSampleRate: 1.0,
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
  spotlight: process.env.NODE_ENV === 'development',
});
```

## 3. Server Configuration (`sentry.server.config.ts`)

```typescript
import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  // Note: Backend server code does NOT need ad-blocker tunneling and communicates
  // server-to-server directly to the DSN host.
  tracesSampleRate: 1.0,
  spotlight: process.env.NODE_ENV === 'development',
});
```

## 4. Edge Configuration (`sentry.edge.config.ts`)

```typescript
import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  tracesSampleRate: 1.0,
});
```

## 5. Next.js Config with Tunnel Rewrite (`next.config.mjs`)

```javascript
import { withSentryConfig } from '@sentry/nextjs';

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Standard Next.js config
};

export default withSentryConfig(nextConfig, {
  org: process.env.SENTRY_ORG,
  project: process.env.SENTRY_PROJECT,
  silent: !process.env.CI,
  widenClientFileUpload: true,
  // Automatically rewrites /monitoring-tunnel to Sentry ingest at the edge
  tunnelRoute: '/monitoring-tunnel',
  hideSourceMaps: true,
  disableLogger: true,
});
```
