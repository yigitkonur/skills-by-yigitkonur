# Application-Level Sentry Proxy Routes

How to implement an internal tunnel proxy route in Fastify, Next.js, and Express to relay envelopes securely from frontend or backend clients.

## Why Use an Internal Proxy Route?

1. **Circumvents Client-Side Ad-Blockers:** UBlock Origin and Brave Shields block `*.sentry.io`. Forwarding through `/api/sentry-tunnel` looks like first-party traffic.
2. **Defeats ISP Filtering:** Ensures browsers and backend workers send telemetry only to your trusted server domain.
3. **Validates Project Destination:** Prevents malicious actors from using your proxy to send arbitrary envelopes to other Sentry projects.

## 1. Next.js App Router Proxy Route (`app/api/sentry-tunnel/route.ts`)

```typescript
import { NextRequest, NextResponse } from 'next/server';

const ALLOWED_PROJECT_IDS = new Set(['4512053148975104']);

export async function POST(req: NextRequest) {
  try {
    const rawEnvelope = await req.text();
    const headerLine = rawEnvelope.split('\n')[0];
    if (!headerLine) {
      return NextResponse.json({ error: 'Empty envelope' }, { status: 400 });
    }

    const header = JSON.parse(headerLine);
    const dsn = new URL(header.dsn);
    const projectId = dsn.pathname.replace('/', '');

    if (!ALLOWED_PROJECT_IDS.has(projectId)) {
      return NextResponse.json({ error: 'Invalid project destination' }, { status: 403 });
    }

    const sentryUrl = `https://sentry.io/api/${projectId}/envelope/`;
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

export const sentryTunnelPlugin: FastifyPluginAsync<{ allowedProjectIds: string[] }> = async (
  fastify,
  opts
) => {
  const allowed = new Set(opts.allowedProjectIds);

  fastify.addContentTypeParser(
    ['application/x-sentry-envelope', 'text/plain'],
    { parseAs: 'string' },
    (_req, body, done) => {
      done(null, body);
    }
  );

  fastify.post('/api/sentry-tunnel', async (request, reply) => {
    const rawEnvelope = request.body as string;
    if (!rawEnvelope) {
      return reply.code(400).send({ error: 'Empty envelope' });
    }

    const firstLine = rawEnvelope.split('\n')[0];
    const header = JSON.parse(firstLine);
    const dsn = new URL(header.dsn);
    const projectId = dsn.pathname.replace('/', '');

    if (!allowed.has(projectId)) {
      return reply.code(403).send({ error: 'Unauthorized project' });
    }

    const sentryRes = await fetch(`https://sentry.io/api/${projectId}/envelope/`, {
      method: 'POST',
      body: rawEnvelope,
      headers: { 'Content-Type': 'application/x-sentry-envelope' },
    });

    reply.code(sentryRes.status).send(await sentryRes.text());
  });
};
```
