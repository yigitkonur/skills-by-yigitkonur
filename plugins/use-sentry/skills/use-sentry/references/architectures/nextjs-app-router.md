# Architecture: Next.js App Router (14 & 15)

How to configure Sentry in Next.js across Client, Server, and Edge runtimes with automatic tunnel rewrites.

## Installation

```bash
npm install @sentry/nextjs
```

## 1. Client Configuration (`sentry.client.config.ts`)

```typescript
import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  // Use Next.js internal tunnel rewrite to bypass ad-blockers & ISP sinkholes
  tunnel: '/monitoring-tunnel',
  tracesSampleRate: 1.0,
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
});
```

## 2. Server Configuration (`sentry.server.config.ts`)

```typescript
import * as Sentry from '@sentry/nextjs';

const dsn = process.env.SENTRY_DSN;
const projectId = dsn?.trim().match(/\/(\d+)(?:$|[?#])/)?.[1];

Sentry.init({
  dsn,
  tunnel: projectId ? `https://sentry.io/api/${projectId}/envelope/` : undefined,
  tracesSampleRate: 1.0,
});
```

## 3. Edge Configuration (`sentry.edge.config.ts`)

```typescript
import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  tracesSampleRate: 1.0,
});
```

## 4. Next.js Config with Tunnel Rewrite (`next.config.mjs`)

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
  // Automatically rewrites /monitoring-tunnel to Sentry ingest
  tunnelRoute: '/monitoring-tunnel',
  hideSourceMaps: true,
  disableLogger: true,
});
```
