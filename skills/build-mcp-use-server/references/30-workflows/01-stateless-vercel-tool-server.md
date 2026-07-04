# Workflow: Stateless Vercel Edge Tool Server

**Goal:** deploy a pure tool server (no sessions, no widgets) to Vercel Edge functions. Cold starts <100 ms, free tier friendly.

## Prerequisites

- Vercel account, `npm i -g vercel` logged in.
- Node 22+ locally for development.
- Project structure: a Next.js or plain Vercel project with an Edge route.

## Layout

```
my-edge-mcp/
├── package.json
├── vercel.json
├── api/
│   └── mcp.ts             # Vercel Edge route
└── tsconfig.json
```

## `package.json`

```json
{
  "name": "my-edge-mcp",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vercel dev",
    "deploy": "vercel deploy --prod"
  },
  "dependencies": {
    "mcp-use": "^1.26.0",
    "zod": "^4.0.0"
  }
}
```

## `vercel.json`

```json
{
  "functions": {
    "api/mcp.ts": {
      "runtime": "edge",
      "memory": 128,
      "maxDuration": 30
    }
  },
  "rewrites": [
    { "source": "/mcp", "destination": "/api/mcp" },
    { "source": "/mcp/:path*", "destination": "/api/mcp" }
  ]
}
```

## `api/mcp.ts`

```typescript
import { MCPServer, text, object } from "mcp-use/server";
import { z } from "zod";

export const config = { runtime: "edge" };

const server = new MCPServer({
  name: "edge-tools",
  version: "1.0.0",
  description: "Pure tool server on Vercel Edge",
  stateless: true,
});

server.tool(
  {
    name: "echo",
    description: "Echo a message back",
    schema: z.object({
      message: z.string().min(1).describe("Text to echo"),
    }),
  },
  async ({ message }) => text(message)
);

server.tool(
  {
    name: "geo-from-headers",
    description: "Read Vercel-injected geo headers (no external API needed)",
    schema: z.object({}),
  },
  async (_, ctx) => {
    // ctx.req.raw gives access to the incoming Request — Vercel adds geo headers.
    const h = ctx.req.raw.headers;
    return object({
      country: h?.get("x-vercel-ip-country") ?? null,
      city: h?.get("x-vercel-ip-city") ?? null,
      region: h?.get("x-vercel-ip-country-region") ?? null,
    });
  }
);

server.tool(
  {
    name: "fetch-json",
    description: "Fetch a JSON URL and return the parsed body",
    schema: z.object({
      url: z.string().url(),
    }),
  },
  async ({ url }) => {
    const res = await fetch(url, { headers: { Accept: "application/json" } });
    if (!res.ok) return text(`HTTP ${res.status}`);
    return object(await res.json() as Record<string, unknown>);
  }
);

// Edge runtime: await and export the request handler instead of calling listen().
const handler = await server.getHandler();
export default handler;
```

## Deploy

```bash
vercel link         # one-time
vercel deploy --prod
```

The MCP endpoint will be `https://<project>.vercel.app/mcp`.

## Test

```bash
# tools/list
curl -N -X POST https://<project>.vercel.app/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

# tools/call
curl -N -X POST https://<project>.vercel.app/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"echo","arguments":{"message":"hello"}}}'
```

## Constraints

- Stateless. Each request is a fresh isolate. Do not use module-scope mutable state — it survives only as long as the warm instance lives.
- No `setInterval`, no long-lived sessions, no `sendNotificationToSession`. For those, see `02-stateful-redis-streaming-server.md`.
- No filesystem write. Read external data only via `fetch`.
- `maxDuration: 30` for hobby tier; bump for Pro.

## See also

- Edge auto-detection details: `../09-transports/`
- Per-request auth: `../11-auth/`
- Connect to a chat client: `../25-deploy/`
