# Sessions, Transports, and Stateless Model

*Read this when migrating stateful v1 servers, stdio, SSE, or Express adapters to v2.*

v2 is stateless and HTTP-only. Session stores, post-response push, and stdio serving are removed. Each request is independent; state belongs in your application database.

## Session store removal

**v1**:
```typescript
import { MCPServer, InMemorySessionStore, RedisSessionStore } from "mcp-use/server";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  sessionStore: new RedisSessionStore({ client: redis }),
  streamManager: new RedisStreamManager({ client: redis }),
});

server.tool(..., async (input, ctx) => {
  const sessionId = ctx.session?.sessionId;
  const previousState = await ctx.session?.get("state");
});
```

**v2**:
```typescript
import { MCPServer } from "mcp-use";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  // No sessionStore or streamManager options
});

export const tool = server.tool(..., async (input, ctx) => {
  // No ctx.session
  const userId = ctx.auth?.user.id;
  const previousState = userId ? await db.state.findByUserId(userId) : null;
});
```

**Migration rule**: Replace all `ctx.session` reads/writes with application-owned storage keyed by verified identity (`ctx.auth.user.id`) or explicit request parameters.

## State migration patterns

| v1 session use | v2 replacement |
|---|---|
| Wizard step / form progress | `ctx.elicit()` input-required rounds + `createRequestStateCodec` |
| User preferences | Database keyed by `ctx.auth.user.id` |
| Temporary calculation cache | External cache (Redis) keyed by request or user |
| Anonymous session | Client passes state token as tool input |
| Cross-request workflow | Durable workflow engine or DB state machine |
| Post-response notification | Subscription listener active on request; otherwise client polling/webhook |

## Request state codec for elicitation

Use `createRequestStateCodec` to persist state across input-required rounds:

```typescript
import { createRequestStateCodec } from "mcp-use";
import { z } from "zod";

const stateCodec = createRequestStateCodec(
  z.object({ orderId: z.string(), step: z.number() })
);

export const checkout = server.tool(
  { name: "checkout", inputSchema: z.object({ orderId: z.string() }), outputSchema: z.object({ ok: z.boolean() }) },
  async ({ orderId }, ctx) => {
    const state = ctx.requestState
      ? stateCodec.decode(ctx.requestState)
      : { orderId, step: 1 };

    const confirmation = await ctx.elicit(
      "confirm-checkout",
      "Confirm checkout?",
      z.object({ confirmed: z.boolean() })
    );

    if (confirmation.status === "required") {
      return confirmation.result;
    }

    if (confirmation.status !== "accept" || !confirmation.data.confirmed) {
      return { content: [{ type: "text", text: "Cancelled" }], structuredContent: { ok: false } };
    }

    // Side effects only after accept (handler re-runs on input)
    await db.orders.complete(orderId);
    return { content: [{ type: "text", text: "Done" }], structuredContent: { ok: true } };
  }
);
```

**Important**: The handler re-runs when the client supplies input. Make side effects idempotent or execute only after `status === "accept"`.

## Post-response push removal

**v1**:
```typescript
await server.sendNotificationToSession(sessionId, "job/complete", { id });
await server.sendNotification("broadcast/update", { ... });
```

**v2**:
```typescript
// During active request only:
await ctx.sendNotification("job/progress", { id, progress: 50 });

// Resource subscriptions (active listeners only):
await server.notifyResourceUpdated("app://job/123");
await server.notifyToolsChanged();
await server.notifyPromptsChanged();
await server.notifyResourcesChanged();
```

There is no arbitrary broadcast or session-targeted push after a request ends. For long-running jobs:
- Return a job ID immediately.
- Provide a `get-job-status` tool.
- Optionally use resource subscriptions while a client is connected.
- Use external webhooks for out-of-band notifications.

## Transport migration

### v1 stdio → v2 HTTP

**v1**:
```typescript
await server.listen({ stdio: true });
// Or auto-detected when no PORT
```

**v2**:
```typescript
// Node/local
await server.listen(3000);

// Edge/fetch runtimes
export default { fetch: server.fetch };
```

No stdio transport exists in v2. Use HTTP. If a local MCP host requires stdio, run an external stdio-to-HTTP bridge (outside mcp-use) or use raw SDK.

### v1 SSE → v2 Streamable HTTP

v1's proprietary SSE transport is replaced by MCP Streamable HTTP. You do not configure it explicitly:

```typescript
// v2 handles Streamable HTTP automatically
await server.listen(3000);
// MCP endpoint: http://localhost:3000/mcp
```

Streamable HTTP supports:
- POST for JSON-RPC requests
- GET for server-to-client streaming
- DELETE for session termination (stateless v2 treats this as cleanup)
- OPTIONS for CORS preflight

### Express/Connect adapters removed

**v1**:
```typescript
await server.listen({
  express: app,
  router: express.Router(),
});
```

**v2** — Use Hono or Web Fetch:
```typescript
// Option 1: Hono app (available as server.app)
import { serve } from "@hono/node-server";
serve({ fetch: server.app.fetch, port: 3000 });

// Option 2: Standard fetch handler
export default { fetch: server.fetch };

// Option 3: Node adapter
import { toNodeHandler } from "mcp-use/node";
const handler = toNodeHandler(server);
```

## Runtime adapters

| Runtime | v2 serving pattern |
|---|---|
| Node.js | `await server.listen(port)` |
| Vercel/Next.js | `createNextHandler()` from `mcp-use/next` |
| Cloudflare Workers | `export default { fetch: server.fetch }` |
| Deno | `Deno.serve(server.fetch)` |
| Bun | `Bun.serve({ fetch: server.fetch })` |
| Hono | `server.app` (Hono instance) |
| Express | **Not supported**; migrate to Hono or use `toNodeHandler` |

## No server-side sampling

**v1**:
```typescript
const completion = await ctx.sample({
  systemPrompt: "You are a helpful assistant",
  messages: [...],
  maxTokens: 500,
});
return text(completion.content);
```

**v2**: `ctx.sample()` is removed. Redesign:

```typescript
// Server provides deterministic tool
export const preparePrompt = server.tool(
  { name: "prepare-prompt", inputSchema: z.object({ data: z.string() }), outputSchema: z.object({ prompt: z.string() }) },
  async ({ data }) => ({
    content: [{ type: "text", text: `Summarize: ${data}` }],
    structuredContent: { prompt: `Summarize: ${data}` },
  })
);
```

The client/model performs generation and calls tools for deterministic operations. Do not embed LLM generation inside the MCP server.

---

**Next**: See `08-appssdk-to-mcp-apps.md` if migrating OpenAI Apps SDK code; otherwise run the validation checklist in `02-v1-to-v2-overview.md`.
