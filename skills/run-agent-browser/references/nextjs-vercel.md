# Next.js + Vercel Integration

Run agent-browser from Next.js on Vercel using Vercel Sandbox microVMs.

## Setup

```bash
pnpm add @vercel/sandbox
```

## Server Action

```typescript
"use server";

import { Sandbox } from "@vercel/sandbox";

const CHROMIUM_SYSTEM_DEPS = [
  "libasound2t64",
  "libatk-bridge2.0-0t64",
  "libatk1.0-0t64",
  "libatspi2.0-0t64",
  "libcairo2",
  "libcups2t64",
  "libdbus-1-3",
  "libdrm2",
  "libgbm1",
  "libglib2.0-0t64",
  "libnspr4",
  "libnss3",
  "libpango-1.0-0",
  "libx11-6",
  "libxcb1",
  "libxcomposite1",
  "libxdamage1",
  "libxext6",
  "libxfixes3",
  "libxkbcommon0",
  "libxrandr2",
  "libxshmfence1",
];

async function getSandboxCredentials() {
  const sandbox = await Sandbox.create({
    snapshotId: process.env.AGENT_BROWSER_SNAPSHOT_ID,
  });
  return {
    host: sandbox.getHost(9222),
    sandbox,
  };
}

async function withBrowser<T>(
  fn: (browserHost: string) => Promise<T>
): Promise<T> {
  const { host, sandbox } = await getSandboxCredentials();

  // Install agent-browser and dependencies if no snapshot
  if (!process.env.AGENT_BROWSER_SNAPSHOT_ID) {
    await sandbox.commands.run(
      `apt-get update && apt-get install -y ${CHROMIUM_SYSTEM_DEPS.join(" ")}`
    );
    await sandbox.commands.run("npm install -g @anthropic-ai/agent-browser");
    await sandbox.commands.run(
      "agent-browser install && agent-browser --cdp-port 9222 open about:blank"
    );
  }

  try {
    return await fn(host);
  } finally {
    await sandbox.close();
  }
}

export async function screenshotUrl(url: string): Promise<string> {
  return withBrowser(async (host) => {
    const response = await fetch(`http://${host}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        command: `open ${url} && wait --load networkidle && screenshot`,
      }),
    });
    const data = await response.json();
    return data.screenshot;
  });
}

export async function snapshotUrl(url: string): Promise<string> {
  return withBrowser(async (host) => {
    const response = await fetch(`http://${host}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        command: `open ${url} && wait --load networkidle && snapshot -i`,
      }),
    });
    const data = await response.json();
    return data.output;
  });
}
```

## Sandbox Snapshots

- Without optimization: ~30 second install each run
- With snapshot: sub-second startup
- Create: `npx tsx scripts/create-snapshot.ts`
- Set: `AGENT_BROWSER_SNAPSHOT_ID=snap_xxxxxxxxxxxx`
- Different from accessibility snapshots — this is a Vercel VM image

## Authentication

- On Vercel: automatic OIDC
- Local dev: `VERCEL_TOKEN`, `VERCEL_TEAM_ID`, `VERCEL_PROJECT_ID`

## Scheduled Workflows (Cron)

```typescript
// app/api/cron/route.ts
import { withBrowser } from "@/lib/browser";

export async function GET() {
  const result = await withBrowser(async (host) => {
    const response = await fetch(`http://${host}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        command: "open https://example.com && snapshot -i",
      }),
    });
    return response.json();
  });

  return Response.json(result);
}
```

```json
// vercel.json
{
  "crons": [
    {
      "path": "/api/cron",
      "schedule": "0 * * * *"
    }
  ]
}
```

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `AGENT_BROWSER_SNAPSHOT_ID` | Vercel Sandbox snapshot ID for fast startup |
| `VERCEL_TOKEN` | Auth token for local development |
| `VERCEL_TEAM_ID` | Team ID for local development |
| `VERCEL_PROJECT_ID` | Project ID for local development |
