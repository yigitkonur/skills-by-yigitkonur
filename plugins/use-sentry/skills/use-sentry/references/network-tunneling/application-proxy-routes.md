# Application-Level Sentry Proxy Routes

How to implement an internal tunnel proxy route in Next.js, Fastify, and Express to relay frontend envelopes securely from client browsers.

## Why Use an Internal Proxy Route?

1. **Circumvents Client-Side Ad-Blockers:** UBlock Origin, Brave Shields, and privacy extensions block requests to `*.sentry.io`. Forwarding through `/api/monitoring/tunnel` on your own domain looks like first-party traffic.
2. **Defeats ISP DNS Interception:** Prevents captive ISP DNS hijacking (e.g. TTNet returning self-signed certificates) from failing client TLS connections.
3. **Validates Project Destination:** Prevents malicious actors from using your server as an open proxy to send arbitrary envelopes to other Sentry projects.

## 1. Next.js App Router Proxy Route (`app/api/monitoring/tunnel/route.ts`)

```typescript
import { NextRequest, NextResponse } from 'next/server';

// Read allowed project IDs and hosts from environment or config
const SENTRY_PROJECT_ID = process.env.SENTRY_PROJECT_ID || process.env.NEXT_PUBLIC_SENTRY_PROJECT_ID;
const ALLOWED_PROJECT_IDS = new Set(
  (process.env.SENTRY_ALLOWED_PROJECT_IDS || SENTRY_PROJECT_ID || '').split(',').map((id) => id.trim()).filter(Boolean)
);

// Allow valid Sentry SaaS hosts (US, EU, and custom ingest domains)
const ALLOWED_HOST_PATTERN = /^([a-zA-Z0-9-]+\.)?(ingest(\.[a-z]{2})?\.sentry\.io|sentry\.io)$/;

export async function POST(req: NextRequest) {
  try {
    const rawEnvelope = await req.text();
    const headerLine = rawEnvelope.split('\n')[0];
    if (!headerLine) {
      return NextResponse.json({ error: 'Empty envelope' }, { status: 400 });
    }

    const header = JSON.parse(headerLine);
    if (!header.dsn) {
      return NextResponse.json({ error: 'Missing DSN in envelope header' }, { status: 400 });
    }

    const dsn = new URL(header.dsn);
    const projectId = dsn.pathname.replace(/^\//, '');

    // 1. Destination project validation
    if (ALLOWED_PROJECT_IDS.size > 0 && !ALLOWED_PROJECT_IDS.has(projectId)) {
      return NextResponse.json({ error: 'Unauthorized project destination' }, { status: 403 });
    }

    // 2. Destination host validation (prevent open proxy relay)
    if (!ALLOWED_HOST_PATTERN.test(dsn.host)) {
      return NextResponse.json({ error: 'Unauthorized Sentry host' }, { status: 403 });
    }

    // 3. Relay to regional Sentry ingest endpoint dynamically
    const sentryUrl = `https://${dsn.host}/api/${projectId}/envelope/`;
    const response = await fetch(sentryUrl, {
      method: 'POST',
      body: rawEnvelope,
      headers: { 'Content-Type': 'application/x-sentry-envelope' },
    });

    return new NextResponse(response.body, { status: response.status });
  } catch (err: any) {
    return NextResponse.json({ error: 'Tunnel forwarding failed', message: err.message }, { status: 500 });
  }
}
```

## 2. Fastify 5 Proxy Route Plugin

```typescript
import type { FastifyPluginAsync } from 'fastify';

export const sentryTunnelPlugin: FastifyPluginAsync<{ allowedProjectIds?: string[] }> = async (
  fastify,
  opts
) => {
  const allowed = new Set(opts.allowedProjectIds || [process.env.SENTRY_PROJECT_ID || '']);
  const allowedHostPattern = /^([a-zA-Z0-9-]+\.)?(ingest(\.[a-z]{2})?\.sentry\.io|sentry\.io)$/;

  fastify.addContentTypeParser(
    ['application/x-sentry-envelope', 'text/plain'],
    { parseAs: 'string' },
    (_req, body, done) => {
      done(null, body);
    }
  );

  fastify.post('/api/monitoring/tunnel', async (request, reply) => {
    const rawEnvelope = request.body as string;
    if (!rawEnvelope) {
      return reply.code(400).send({ error: 'Empty envelope' });
    }

    const firstLine = rawEnvelope.split('\n')[0];
    const header = JSON.parse(firstLine);
    if (!header.dsn) {
      return reply.code(400).send({ error: 'Missing DSN' });
    }

    const dsn = new URL(header.dsn);
    const projectId = dsn.pathname.replace(/^\//, '');

    if (allowed.size > 0 && !allowed.has(projectId)) {
      return reply.code(403).send({ error: 'Unauthorized project' });
    }

    if (!allowedHostPattern.test(dsn.host)) {
      return reply.code(403).send({ error: 'Unauthorized host' });
    }

    const sentryRes = await fetch(`https://${dsn.host}/api/${projectId}/envelope/`, {
      method: 'POST',
      body: rawEnvelope,
      headers: { 'Content-Type': 'application/x-sentry-envelope' },
    });

    reply.code(sentryRes.status).send(await sentryRes.text());
  });
};
```
