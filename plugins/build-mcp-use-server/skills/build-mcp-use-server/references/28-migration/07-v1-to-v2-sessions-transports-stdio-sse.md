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

## The full v1 session-runtime family is removed (no v2 equivalent)

beta.66 ships **none** of v1's stateful transport. Every one of these is gone — there is no renamed import, only a redesign:

- `InMemorySessionStore`, `FileSystemSessionStore`, `RedisSessionStore`
- `RedisStreamManager`
- `MCPServer` config keys `sessionStore`, `streamManager`, `stateless: false`, `sessionIdleTimeoutMs`
- `ctx.session` (and `ctx.session.sessionId`)
- Session introspection: `server.getActiveSessions()`, `server.getServerForSession()`
- Per-session capability injection: `server.registerCapabilities(...)` / runtime capability patching

Check for all of them during migration — they fail as **type/config errors**, not imports, so an import scan alone will miss them:

```bash
grep -rnE 'stateless|sessionStore|streamManager|sessionIdleTimeout|RedisSessionStore|RedisStreamManager|InMemorySessionStore|FileSystemSessionStore|ctx\.session|getActiveSessions|getServerForSession|registerCapabilities' src/ index.ts
```

**Distinguish two uses of Redis before deleting anything.** v1 protocol state (sessions, stream resume) is obsolete in v2 — remove the `RedisSessionStore`/`RedisStreamManager` that fed `MCPServer`. But an **application** Redis store (a resume cache, ledger, or idempotency store keyed by your own ID) is still valid — keep it as ordinary application state outside the server config. Do not conflate the two.

**Identity key when there is no OAuth.** The rule "key storage by `ctx.auth.user.id`" only works if your server authenticates. A v1 project that used a transport session ID as its identity for unauthenticated clients needs a replacement identity:

| v1 identity | v2 replacement |
|---|---|
| Authenticated user | `ctx.auth.user.id` (unchanged pattern) |
| Unauthenticated, correlation needed | Client passes a durable trace/session token as a tool **input parameter** (or mint one server-side and return it; client echoes it back). Validate/sanitize like any input. |
| Multi-round wizard state | `createRequestStateCodec` + `requestState` (signed, tamper-evident) — see below |
| Anonymous + no correlation | Stateless — no storage |

```typescript
// Unauthenticated correlation via explicit input token
export const run = server.tool(
  { name: "run", inputSchema: z.object({ task: z.string(), traceId: z.string().optional() }), outputSchema: ... },
  async ({ task, traceId }, ctx) => {
    const id = traceId ?? crypto.randomUUID();
    await db.ledger.append(id, task);       // application store, not a session store
    return { content: [...], structuredContent: { traceId: id, ... } };
  }
);
```

If you patched internal session factories (`getServerForSession`) or called `registerCapabilities()` at runtime, that behavior **cannot be ported** — v2 builds the per-request MCP instance from the registry and exposes no public hook. Expose the same information through tools/resources, set static capability text via the `instructions` constructor field, or drop to the low-level `@modelcontextprotocol/server` SDK only if you own the whole handler.


## State migration patterns

| v1 session use | v2 replacement |
|---|---|
| Wizard step / form progress | `input_required` rounds (`inputRequired()`/`inputResponse()`/`acceptedContent()`) + `createRequestStateCodec` |
| User preferences | Database keyed by `ctx.auth.user.id` |
| Temporary calculation cache | External cache (Redis) keyed by request or user |
| Anonymous session | Client passes state token as tool input |
| Cross-request workflow | Durable workflow engine or DB state machine |
| Post-response notification | Subscription listener active on request; otherwise client polling/webhook |

## Request state codec for elicitation

> **`ctx.elicit(key, message, schema)` is documented in some v2 docs but not shipped in 2.0.0-beta.66.** `RequestContextBase` in the shipped `dist/context.d.ts` has no `elicit` field. Use the real, shipped primitives below — `inputRequired()`, `inputResponse()`, `acceptedContent()` — re-exported from `mcp-use` root (originally from `@modelcontextprotocol/server`). See `../12-elicitation/01-overview.md` for the full elicitation model.

Use `createRequestStateCodec` to persist state across input-required rounds. It mints an HMAC-signed wire string in `inputRequired({ requestState })` and verifies it on the client's retry via `ServerOptions.requestState.verify`:

```typescript
import { MCPServer, createRequestStateCodec, inputRequired, inputResponse, acceptedContent } from "mcp-use";
import { z } from "zod";

const stateCodec = createRequestStateCodec<{ orderId: string; step: number }>({
  key: process.env.REQUEST_STATE_SECRET!, // >= 32 bytes; throws RangeError otherwise
  ttlSeconds: 600, // defaults to 600 if omitted
});

const server = new MCPServer({
  name: "checkout-server",
  version: "1.0.0",
  requestState: { verify: stateCodec.verify }, // wire the verify hook in
});

const confirmSchema = z.object({ confirmed: z.boolean() });

export const checkout = server.tool(
  { name: "checkout", inputSchema: z.object({ orderId: z.string() }), outputSchema: z.object({ ok: z.boolean() }) },
  async ({ orderId }, ctx) => {
    const state = ctx.requestState<{ orderId: string; step: number }>() ?? { orderId, step: 1 };
    const response = inputResponse(ctx.inputResponses, "confirm-checkout");
    if (response.kind === "elicit" && response.action !== "accept") {
      return { content: [{ type: "text", text: "Cancelled" }], structuredContent: { ok: false } };
    }

    const confirmation = acceptedContent(ctx.inputResponses, "confirm-checkout", confirmSchema);
    if (confirmation === undefined) {
      return inputRequired({
        inputRequests: {
          "confirm-checkout": inputRequired.elicit({
            message: "Confirm checkout?",
            requestedSchema: confirmSchema,
          }),
        },
        requestState: await stateCodec.mint(state),
      });
    }

    if (!confirmation.confirmed) {
      return { content: [{ type: "text", text: "Cancelled" }], structuredContent: { ok: false } };
    }

    // Side effects only after accept (handler re-runs from the top on input)
    await db.orders.complete(state.orderId);
    return { content: [{ type: "text", text: "Done" }], structuredContent: { ok: true } };
  }
);
```

`stateCodec.mint(payload)` returns `Promise<string>`; the verified payload is read back inside the handler as `ctx.requestState<{ orderId: string; step: number }>()` (called as a generic function, not `.decode()`/`.parse()`). A tampered or expired `requestState` fails `verify` and is rejected before your handler runs. The codec is signed, not encrypted: clients can read its payload. Signing prevents tampering but does not by itself bind a token to one authenticated user, so never use request state alone as an authorization boundary; re-check `ctx.auth` and durable ownership before side effects.

**Important**: The handler re-runs from the top when the client supplies input — there is no suspended stack frame. Make side effects idempotent or execute only after `acceptedContent()` returns validated data.

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
