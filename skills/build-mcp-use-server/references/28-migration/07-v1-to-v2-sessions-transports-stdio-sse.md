# Sessions, Transports, and Stateless Serving

*Read this when migrating stateful v1 servers, session stores, stdio listeners, SSE adapters, or Express routes to mcp-use v2.*

In `mcp-use v1`, the framework included an integrated session-affine runtime: servers maintained state across requests using `sessionStore` options (InMemory, Redis, FileSystem), allowed post-response push notifications via `sendNotificationToSession()`, exposed `ctx.session`, and supported stdio serving.

`mcp-use v2` completely eliminates the stateful transport runtime. The server is strictly **stateless and HTTP-only**: each request executes independently against Streamable HTTP at `basePath: "/mcp"`, stdio listeners and Express adapters are removed, and multi-turn state must be persisted in an external database keyed by user identity (`ctx.auth.user.id`) or cryptographically passed via signed `requestState` tokens.

---

## At a Glance: Sessions & Transports Diff

| Capability / Surface | Legacy v1 (`mcp-use <= 1.34.5`) | Canonical v2 (`mcp-use >= 2.8.2`) | Impact / Action |
|---|---|---|---|
| **Context Model** | Session-affine; `ctx.session` holds persistent data | Stateless per-request; `ctx.session` **removed** | Key application state by `ctx.auth.user.id` or explicit trace tokens |
| **Session Stores** | `InMemorySessionStore`, `RedisSessionStore` | **Removed**; no session store config in `MCPServer` | Remove `sessionStore` and `streamManager` constructor options |
| **HTTP Transport** | Proprietary SSE protocol or Express bridge | MCP Streamable HTTP standard (`basePath: "/mcp"`) | Serves GET (streaming), POST (JSON-RPC), DELETE, OPTIONS |
| **Stdio Serving** | `server.listen({ stdio: true })` | **Removed**; Streamable HTTP only | Connect clients over HTTP or use external stdio-to-HTTP bridge |
| **Framework Bridges**| Express/Connect adapter (`server.listen({ express })`) | **Removed**; native Hono (`server.app`) or `server.fetch` | Migrate to Hono or export standard Web Fetch handler |
| **Post-Response Push**| `sendNotificationToSession(sessionId, ...)` | **Removed**; active request notifications only (`ctx.sendNotification`) | Use long-polling, background workers, or resource subscriptions |
| **Server-Side Sampling**| `await ctx.sample({ prompt })` | **Removed**; model generates on host; server provides tools | Eliminate server LLM calls; return deterministic tool results |
| **Multi-Round Elicit**| Beta `ctx.elicit()` / in-memory wizard sessions | `inputRequired()` + `createRequestStateCodec` | See dedicated guide: `10-elicitation-and-state-evolution.md` |

---

## Session Store Removal & Migration

In v1, tools accessed long-lived session state directly on the context object:

### Before (v1): Stateful Transport Sessions
```typescript
import { MCPServer, InMemorySessionStore, RedisSessionStore } from "mcp-use/server";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  sessionStore: new RedisSessionStore({ client: redisClient }),
  streamManager: new RedisStreamManager({ client: redisClient }),
});

server.tool(
  { name: "track-progress", schema: z.object({ step: z.number() }) },
  async ({ step }, ctx) => {
    // Legacy session access
    const sessionId = ctx.session?.sessionId;
    const previous = await ctx.session?.get("lastStep");
    await ctx.session?.set("lastStep", step);
    return text(`Updated step for session ${sessionId}`);
  }
);
```

### After (v2): Stateless Architecture
```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({
  name: "my-server",
  version: "2.0.0",
  basePath: "/mcp",
  // No sessionStore or streamManager options!
});

export const trackProgress = server.tool(
  {
    name: "track-progress",
    inputSchema: z.object({
      step: z.number(),
      // For unauthenticated clients, pass an explicit durable correlation token:
      correlationId: z.string().optional(),
    }),
    outputSchema: z.object({ success: z.boolean(), lastStep: z.number() }),
  },
  async ({ step, correlationId }, ctx) => {
    // 1. Authenticated: Key state by verified identity
    const userId = ctx.auth?.user?.id;

    // 2. Unauthenticated: Key state by explicit input token
    const stateKey = userId ?? correlationId ?? crypto.randomUUID();

    // Store in application-owned database (Postgres, Redis, DynamoDB)
    const previous = await db.progress.get(stateKey);
    await db.progress.set(stateKey, { step, updatedAt: new Date() });

    return {
      content: [{ type: "text", text: `Updated step to ${step} for key ${stateKey}` }],
      structuredContent: { success: true, lastStep: previous?.step ?? 0 },
    };
  }
);
```

### Distinguishing Protocol Redis from Application Redis
When migrating a codebase using Redis:
- **Delete** `RedisSessionStore` and `RedisStreamManager` that fed `new MCPServer({ ... })`.
- **Keep** your application Redis client (`ioredis`, `@upstash/redis`) outside the server config to store application-level cache, idempotency keys, and rate limits.

---

## State Identity Strategies in a Stateless World

Without transport sessions, choose the appropriate identity model:

| Use Case | Identity Key Strategy | Canonical v2 Implementation |
|---|---|---|
| **Authenticated User** | Verified account identifier | Key database records by `ctx.auth.user.id`. |
| **Anonymous User / Correlation** | Explicit input token | Require or generate a `traceId` / `conversationId` property in `inputSchema`. |
| **Multi-Round Elicitation Form** | Cryptographic state token | Use `createRequestStateCodec` carried in `requestState`. (See `10-elicitation-and-state-evolution.md`). |
| **Truly Anonymous / One-Off** | No storage required | Stateless execution; handler operates purely on inputs and returns results. |

---

## Transport Migration: From Stdio & Proprietary SSE to Streamable HTTP

### 1. Stdio Serving Removed
In v1, calling `server.listen({ stdio: true })` bound the server to process standard input/output. In v2, **stdio is completely removed**:

```typescript
// v1 (Removed)
await server.listen({ stdio: true });

// v2 (Canonical): Node.js standalone HTTP server
await server.listen(3000); // Listens at http://localhost:3000/mcp
```

If you must connect a legacy client that only speaks stdio (such as older Claude Desktop versions that cannot connect to HTTP endpoints), use an external stdio-to-HTTP proxy (e.g. `mcp-proxy` or `@modelcontextprotocol/sdk` CLI bridge) outside `mcp-use`.

### 2. Proprietary SSE Replaced by Streamable HTTP
In v1, servers ran proprietary Server-Sent Events endpoints. In v2, the server automatically mounts the official **MCP Streamable HTTP protocol** at `basePath` (default `/mcp`):
- **POST `/mcp`**: Handles standard JSON-RPC requests (`tools/call`, `tools/list`, etc.).
- **GET `/mcp`**: Establishes streaming event transport (`text/event-stream`).
- **DELETE `/mcp`**: Handles session teardown signals gracefully.
- **OPTIONS `/mcp`**: Manages CORS preflight handshakes.

### 3. Express and Connect Adapters Removed
In v1, servers could attach directly to an Express app. In v2, Express adapters are removed. Deploy via **Hono**, **Node HTTP adapter**, or standard **Web Fetch**:

```typescript
// Option A: Standalone Node.js HTTP server (built-in)
await server.listen(3000);

// Option B: Standard Web Fetch handler (Cloudflare Workers, Edge runtimes)
export default { fetch: server.fetch };

// Option C: Hono application instance (server.app is a pre-configured Hono app)
import { serve } from "@hono/node-server";
serve({ fetch: server.app.fetch, port: 3000 });

// Option D: Node.js http.createServer adapter
import { toNodeHandler } from "mcp-use/node";
import http from "node:http";
const httpServer = http.createServer(toNodeHandler(server));
httpServer.listen(3000);
```

---

## Post-Response Notifications Removed

In v1, servers could push out-of-band notifications to specific sessions long after an HTTP request completed:

```typescript
// v1 (Removed)
await server.sendNotificationToSession(sessionId, "job/complete", { jobId: "123" });
await server.sendNotification("broadcast/update", { data: [...] });
```

In v2, all notifications are strictly scoped:
- **During an active request**: Call `await ctx.sendNotification("progress", { percent: 50 })` or `await ctx.sendLog("info", { stage: "processing" })`.
- **Resource Subscriptions**: Clients actively subscribed to a resource receive change notifications when you call `await server.notifyResourceUpdated("app://record/123")`.
- **Tool/Prompt Updates**: Broadcast metadata changes via `await server.notifyToolsChanged()`.

For long-running asynchronous tasks (e.g. 5-minute batch jobs):
1. Tool returns immediately with `{ status: "queued", jobId: "job_99" }`.
2. Provide a companion query tool: `get-job-status({ jobId })`.
3. Use external webhooks for out-of-band notifications.

---

## Multi-Round Elicitation & State Evolution

> **Notice**: While experimental v2 notes referenced `ctx.elicit()`, `ctx.elicit()` was **permanently removed in v2.4.3 (#2409)**. 

For interactive multi-round workflows (such as confirmation dialogs or multi-step wizards), canonical `mcp-use v2` uses:
1. `inputRequired({ inputRequests: { key: inputRequired.elicit(...) }, requestState })`
2. `inputResponse(ctx.inputResponses, key)`
3. `acceptedContent(ctx.inputResponses, key, schema)`
4. `createRequestStateCodec<T>({ key: SECRET, ttlSeconds: 300 })`

For the complete guide and runnable code transformations, see dedicated guide:  
👉 **`10-elicitation-and-state-evolution.md`**

---

## Anti-Patterns and Common Traps

| Anti-Pattern | Root Mechanism & Failure Mode | Canonical v2 Fix |
|---|---|---|
| **Passing `sessionStore` to `MCPServer`** | Option removed from `ServerConfig`. Fails TypeScript compilation. | Store state in application database keyed by `ctx.auth.user.id`. |
| **Calling `server.listen({ stdio: true })`** | Stdio transport removed. Method throws or option is ignored. | Call `server.listen(port)` to serve over Streamable HTTP. |
| **Attempting to Read `ctx.session`** | `ctx.session` is undefined in v2. Accessing properties throws `TypeError: Cannot read properties of undefined`. | Read identity from `ctx.auth.user.id` or input arguments. |
| **Passing Express App to `server.listen`** | Express adapter removed in v2. | Use `server.app` (Hono), `server.fetch`, or `toNodeHandler(server)`. |
| **Relying on `sendNotificationToSession`** | Out-of-band session push deleted. | Send progress during request via `ctx.sendNotification()`, or return a job ID and poll. |

---

## Next Steps & Cross-References

- **Interactive Elicitation**: See `10-elicitation-and-state-evolution.md` for multi-round input forms and cryptographic request state.
- **Master Overview**: See `02-v1-to-v2-overview.md` for the full migration checklist and exit gate.
- **Production Deployment**: See `references/25-deploy/02-pre-deploy-checklist.md` for cloud environment hardening.
