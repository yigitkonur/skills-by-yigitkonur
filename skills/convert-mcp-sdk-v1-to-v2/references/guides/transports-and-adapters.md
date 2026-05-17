# Transports and Framework Adapters

Three transports survive the v1→v2 split, one is removed, and the framework adapters move to dedicated packages.

## Transport class renames

| v1 | v2 | Package |
|---|---|---|
| `StdioServerTransport` | `StdioServerTransport` | `@modelcontextprotocol/server` (was deep subpath) |
| `StreamableHTTPServerTransport` | `NodeStreamableHTTPServerTransport` | `@modelcontextprotocol/node` |
| `WebStandardStreamableHTTPServerTransport` | `WebStandardStreamableHTTPServerTransport` | `@modelcontextprotocol/server` (was deep subpath) |
| `SSEServerTransport` | **Removed** | — |

The Node-specific Streamable HTTP transport is renamed to make the platform target explicit (`Node` prefix). Cloudflare Workers, Deno, and Bun should use `WebStandardStreamableHTTPServerTransport` from `@modelcontextprotocol/server`.

## SSE removal: client implications

`SSEServerTransport` is gone in v2. Servers that exposed it must move clients to Streamable HTTP first, then migrate the server. Check whether any of your clients still negotiate the legacy SSE endpoint:

```bash
# Search server logs for SSE-only clients
grep "GET /sse" access.log | head
```

If active SSE clients exist, ship a Streamable-HTTP-capable v1 deploy first, give clients a release cycle to upgrade, then start the v2 migration. Skipping this step strands legacy clients on a dead endpoint.

## Renaming `StreamableHTTPServerTransport`

Mechanical rewrite. Type signature is the same; only the class name and import path change.

```typescript
// v1
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
const transport = new StreamableHTTPServerTransport({
  sessionIdGenerator: () => crypto.randomUUID(),
  onsessioninitialized: (id) => transports.set(id, transport),
});

// v2
import { NodeStreamableHTTPServerTransport } from "@modelcontextprotocol/node";
const transport = new NodeStreamableHTTPServerTransport({
  sessionIdGenerator: () => crypto.randomUUID(),
  onsessioninitialized: (id) => transports.set(id, transport),
});
```

Existing `transport.handleRequest`, `transport.sessionId`, `transport.onclose`, and `EventStore` integration are unchanged.

## Framework adapter packages

In v1, `createMcpExpressApp()` lives at the SDK subpath `@modelcontextprotocol/sdk/server/express.js`. In v2, it moves to a dedicated package — same function name, different import path. Hono is wholly new in v2.

```typescript
// v1 — Express only
import { createMcpExpressApp } from "@modelcontextprotocol/sdk/server/express.js";

// v2 — Express
import { createMcpExpressApp } from "@modelcontextprotocol/express";

// v2 — Hono (new)
import { createMcpHonoApp } from "@modelcontextprotocol/hono";
```

`@modelcontextprotocol/hono` is the official SDK adapter (alpha.2 as of 2026-05-08); `@hono/mcp` is a separate community package — not interchangeable.

## DNS rebinding protection moved out of the transport

In v1, `StreamableHTTPServerTransport` accepts `allowedHosts` / `allowedOrigins` options that perform Host-header validation at the transport layer. In v2 the protection moves into adapter middleware:

```typescript
// v1 — transport-level
const transport = new StreamableHTTPServerTransport({
  allowedHosts: ["127.0.0.1", "localhost"],
});

// v2 — adapter-level (auto-applied for localhost)
const app = createMcpExpressApp({
  host: "127.0.0.1",  // auto-protects 127.0.0.1, localhost, ::1
});

// v2 — explicit middleware for custom hosts
import { hostHeaderValidation } from "@modelcontextprotocol/express";
app.use(hostHeaderValidation({ allowedHosts: ["mcp.example.com"] }));
```

If you bind to `0.0.0.0` you opt out of automatic protection — the adapter logs a warning. Wire `hostHeaderValidation` middleware explicitly for production.

## Hono parsedBody quirk

Hono pre-parses request bodies through its own middleware. The MCP Hono adapter expects to read the JSON body itself, so it stashes the parsed value on the context:

```typescript
import { createMcpHonoApp } from "@modelcontextprotocol/hono";

const app = createMcpHonoApp({ host: "127.0.0.1" });

// If you have your own JSON middleware before MCP, set parsedBody:
app.use("*", async (c, next) => {
  if (c.req.header("content-type")?.includes("json")) {
    c.set("parsedBody", await c.req.json());
  }
  await next();
});
```

Servers that mount MCP under Hono with no other body parser don't need this — the adapter handles parsing itself.

## Stateful HTTP session pattern is unchanged

The session-map pattern (track sessions by `mcp-session-id` header, route POST/GET/DELETE per session, handle initialize as the new-session signal) is the same in both versions. Only the transport class name changes:

```typescript
// Same algorithm, both versions — only the import line and class name differ
const transports: Record<string, Transport> = {};

app.post("/mcp", async (req, res) => {
  const sessionId = req.headers["mcp-session-id"] as string | undefined;
  let transport = sessionId ? transports[sessionId] : undefined;
  if (!transport) {
    if (!isInitializeRequest(req.body)) {
      return res.status(400).json({ error: "no session" });
    }
    transport = new NodeStreamableHTTPServerTransport({  // v2 class name
      sessionIdGenerator: () => crypto.randomUUID(),
      onsessioninitialized: (id) => { transports[id] = transport; },
    });
    await server.connect(transport);
  }
  await transport.handleRequest(req, res, req.body);
});
```

## Pre-flight checklist for this rewrite

- [ ] `StreamableHTTPServerTransport` calls renamed to `NodeStreamableHTTPServerTransport`.
- [ ] `SSEServerTransport` references removed (and client compat verified).
- [ ] `createMcpExpressApp` import moved from SDK subpath to `@modelcontextprotocol/express`.
- [ ] `WebStandardStreamableHTTPServerTransport` (if used) imported from `@modelcontextprotocol/server`.
- [ ] DNS rebinding protection: localhost auto-applied, custom hosts use `hostHeaderValidation` middleware.
- [ ] `0.0.0.0` bindings: explicit `hostHeaderValidation` added (don't rely on the warning).
- [ ] Hono targets: confirm `@modelcontextprotocol/hono` is installed (not `@hono/mcp`).
- [ ] Hono with custom body parser: `c.set("parsedBody", ...)` middleware added.
- [ ] Existing session-map code reviewed — algorithm unchanged, only class name differs.
