# Deploying the Drop-In Server

Ship the colocated MCP server either as a separate Node service or as a stateless fetch handler. Prefer the separate service unless you have verified the tool surface is strictly request/response.

Source note: the TypeScript docs index has no Vercel deployment page; the route-handler pattern below is grounded in `mcp-use@1.26.0`'s `MCPServer.getHandler()` declaration and the docs index at https://mcp-use.com/docs/llms.txt.

---

## Decision Matrix

| Path | Where MCP runs | Sessions | Use when |
|---|---|---|---|
| **Separate Node service** | Standalone Node process, separate port | Stateful by default in Node | Long-lived sessions, notifications, sampling, elicitation, widgets, or streaming. |
| **Next.js route handler** | `app/api/mcp/[...mcp]/route.ts` | Set `stateless: true` | Stateless tools on the same deploy target as the Next.js app. |
| **Edge route handler** | Same route with `runtime = "edge"` | Set `stateless: true` | Stateless tools with no Node-only imports. |

---

## 1. Separate Node Service

Run the MCP server as its own Node process beside Next.js:

```json
{
  "scripts": {
    "build": "next build && mcp-use build --mcp-dir src/mcp",
    "start:web": "next start -p 3000",
    "start:mcp": "mcp-use start --mcp-dir src/mcp -p 3001"
  }
}
```

`mcp-use build --mcp-dir src/mcp` is intentionally lighter than standalone build mode:

- It skips the esbuild transpile step.
- It skips the `tsc --noEmit` typecheck.
- It still builds widgets into `dist/resources/widgets/<name>/`.
- The manifest records the TypeScript source entry, and `mcp-use start` runs it with `tsx`.

Deploy the web app and MCP server as separate services that share the same code and env configuration.

---

## 2. Next.js Route Handler

`MCPServer.getHandler()` is public, but it is **async** and returns a fetch handler. For serverless route handlers, set `stateless: true` explicitly; the package only auto-defaults `stateless` to true in Deno.

```typescript
// app/api/mcp/[...mcp]/route.ts
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";
import { getGreeting } from "@/lib/server-data";

const server = new MCPServer({
  name: "my-app-mcp",
  version: "1.0.0",
  stateless: true,
});

server.tool(
  { name: "greet", schema: z.object({ name: z.string() }) },
  async ({ name }) => text(await getGreeting(name)),
);

const handler = await server.getHandler();

export const GET = handler;
export const POST = handler;
export const DELETE = handler;
```

Use this only when tools do not depend on a persistent SSE connection or cross-request session state.

---

## 3. Edge Route Handler

The Edge shape is the same, with an Edge runtime export and no Node-only transitive imports:

```typescript
// app/api/mcp/[...mcp]/route.ts
export const runtime = "edge";

import { MCPServer, text } from "mcp-use/server";

const server = new MCPServer({
  name: "edge-mcp",
  version: "1.0.0",
  stateless: true,
});

server.tool({ name: "ping" }, async () => text("pong"));

const handler = await server.getHandler();

export const GET = handler;
export const POST = handler;
export const DELETE = handler;
```

Edge runtime constraints are outside mcp-use itself: no Node `fs`, `path`, `child_process`, native modules, or Node-only middleware dependencies.

---

## 4. Stateless Considerations

When `stateless: true`, the server uses JSON request/response mode without session tracking. Avoid features that require a persistent client connection:

| Feature | Why to avoid it in route handlers | Better fit |
|---|---|---|
| `ctx.sample()` | Waits on a client reverse call and progress notifications. | Separate Node service. |
| `ctx.elicit()` | Waits on a client round trip. | Separate Node service or upfront tool input. |
| `ctx.session.sessionId` | No durable session identity in stateless mode. | OAuth `ctx.auth.user.userId` when OAuth is configured. |
| `server.sendNotification()` | Broadcasts to active sessions. | Stateful Node service. |
| Long-running `ctx.reportProgress` work | Function timeouts can cut the request. | Worker plus polling, or a stateful service. |

---

## 5. Hybrid Pattern

Common production layout:

- **Vercel:** the Next.js app and ordinary web routes.
- **Standalone Node:** the MCP server with session features.
- **Same repo:** both deploys import shared `src/lib/*` and shared types.

```bash
next build
mcp-use build --mcp-dir src/mcp
mcp-use start --mcp-dir src/mcp -p 3001
```

Remote MCP clients connect to the MCP server's public URL, not necessarily the Next.js app domain.

---

## 6. See Also

- **What `--mcp-dir` triggers** → `02-mcp-dir-flag.md`
- **Stateless HTTP transport** → `../09-transports/04-stateless-mode.md`
- **Production deploy guide** → `../25-deploy/01-decision-matrix.md`
- **Tunneling for dev-time remote access** → `../21-tunneling/01-overview.md`
