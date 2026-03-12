# Transports

Configure how MCP clients connect to your server by choosing the right transport layer.

---

## Transport Overview

Every MCP server communicates over a **transport** — the wire protocol that carries JSON-RPC messages between client and server. Choose based on deployment target, session needs, and client capabilities.

| Transport | Use Case | Session Support | Direction |
|---|---|---|---|
| `stdio` | CLI tools, local servers, Claude Desktop | Single session | Bidirectional |
| `httpStream` | Remote servers, web apps, production | Multi-session | Bidirectional |
| `sse` (legacy) | Backward compatibility | Multi-session | Server→Client SSE, Client→Server POST |

> **Rule of thumb:** Start with `stdio` for local development, switch to `httpStream` for production.

---

## Stdio Transport (Default)

The stdio transport reads JSON-RPC messages from stdin and writes responses to stdout. It requires zero configuration and is the default when no transport is specified.

```typescript
import { MCPServer, text } from "mcp-use/server";

const server = new MCPServer({ name: "my-server", version: "1.0.0" });
server.tool({ name: "hello" }, async () => text("Hello!"));

// Default: stdio transport (no arguments needed)
await server.listen();

// Explicit:
await server.listen({ transportType: "stdio" });
```

### When to Use

- Local CLI tools invoked by a parent process
- Claude Desktop integration (Claude spawns the server as a child process)
- Development and testing
- Single-user, single-machine scenarios

### Pros

- Zero config — works immediately
- Instant startup — no port binding or network stack
- Secure by default — no network exposure
- Simple debugging — pipe stdin/stdout manually

### Cons

- Single client only — one connection at a time
- No remote access — client and server must share the same machine
- No session multiplexing — one session per process lifetime

### Claude Desktop Configuration

Add your stdio server to Claude Desktop's config file:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "npx",
      "args": ["my-mcp-server"]
    }
  }
}
```

---

## Streamable HTTP Transport

The `httpStream` transport runs a full HTTP server that supports bidirectional streaming, session management, and multiple simultaneous clients.

### Basic Usage

```typescript
import { MCPServer, text } from "mcp-use/server";

const server = new MCPServer({ name: "my-server", version: "1.0.0" });
server.tool({ name: "hello" }, async () => text("Hello!"));

await server.listen({
  transportType: "httpStream",
  port: 3000,
});
```

### With Full Options

```typescript
import crypto from "node:crypto";

await server.listen({
  transportType: "httpStream",
  port: 3000,
  hostname: "0.0.0.0",
  path: "/mcp",
  cors: true,

  // Session management — generate unique IDs per connection
  sessionIdGenerator: () => crypto.randomUUID(),

  // Stateless mode (no sessions) — uncomment to disable sessions:
  // sessionIdGenerator: undefined,
});
```

### When to Use

- Production deployments behind a reverse proxy or load balancer
- Remote access from clients on other machines
- Multi-client scenarios (multiple users connecting simultaneously)
- Web applications that need MCP capabilities

### Pros

- Standard HTTP — works with existing infrastructure (proxies, TLS, CDNs)
- Load-balanceable — distribute across multiple server instances
- Session management — track per-client state
- Resumable — clients can reconnect and resume streams

### Cons

- More setup — requires port, hostname, and optional TLS configuration
- Network overhead — HTTP framing adds latency compared to raw stdio
- Firewall considerations — inbound port must be reachable

### HTTP Endpoints

When running with `httpStream`, the server exposes:

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/mcp` (or custom) | Send JSON-RPC requests, receive streamed responses |
| `GET` | `/mcp` (or custom) | Open an SSE stream for server-initiated messages |
| `DELETE` | `/mcp` (or custom) | Terminate a session |

---

## SSE Transport (Legacy)

The SSE (Server-Sent Events) transport uses a dedicated SSE endpoint for server-to-client messages and a separate POST endpoint for client-to-server messages.

```typescript
await server.listen({
  transportType: "sse",
  port: 3000,
  path: "/sse",
});
```

> **Deprecation notice:** SSE is being superseded by Streamable HTTP (`httpStream`). Use `httpStream` for all new servers. SSE remains available for backward compatibility with older clients that do not yet support the streamable HTTP protocol.

### When to Use

- Connecting to clients that only support the legacy SSE transport
- Maintaining existing deployments during migration to `httpStream`

---

## Using with Express/Hono Middleware

The HTTP transports (`httpStream` and `sse`) support middleware for logging, rate limiting, authentication, and custom routes alongside MCP endpoints.

```typescript
import { MCPServer, text } from "mcp-use/server";
import morgan from "morgan";
import rateLimit from "express-rate-limit";

const server = new MCPServer({ name: "my-server", version: "1.0.0" });

// Attach middleware
server.use(morgan("combined"));
server.use(
  "/api",
  rateLimit({ windowMs: 15 * 60 * 1000, max: 100 })
);

// Custom routes alongside MCP
server.get("/health", (c) => c.json({ status: "ok" }));
server.post("/webhook", async (c) => {
  const body = await c.req.json();
  // handle webhook payload
  return c.json({ received: true });
});

// Define tools as usual
server.tool({ name: "hello" }, async () => text("Hello!"));

// Start with HTTP transport
await server.listen({ transportType: "httpStream", port: 3000 });
```

### Middleware Execution Order

1. Global middleware (added via `server.use(...)`) runs first, in registration order.
2. Path-scoped middleware (e.g., `server.use("/api", ...)`) runs only on matching paths.
3. MCP handler processes the request if the path matches the MCP endpoint.
4. Custom route handlers run if the path matches a registered route.

---

## Transport Selection Decision Tree

Use this flowchart to pick the right transport:

```
Is this a local CLI tool or Claude Desktop integration?
  → Yes: Use stdio

Do you need remote access from other machines?
  → Yes: Use httpStream

Do you need multiple simultaneous clients?
  → Yes: Use httpStream with session management
  → No: stdio is simpler

Do you need backward compatibility with SSE-only clients?
  → Yes: Use sse (but plan migration to httpStream)

Still unsure?
  → Start with stdio for development, switch to httpStream for production
```

---

## Session Management

HTTP transports support session tracking to maintain per-client state across requests.

### In-Memory Sessions (Default)

Simple and zero-config. Suitable for single-process deployments.

```typescript
await server.listen({
  transportType: "httpStream",
  port: 3000,
  sessionIdGenerator: () => crypto.randomUUID(),
});
```

- **Pros:** No external dependencies, instant setup.
- **Cons:** Sessions lost on restart, cannot share across processes.

### Redis Sessions

Persist sessions across restarts and share state across multiple server instances.

```typescript
import { MCPServer, RedisSessionStore } from "mcp-use/server";
import { createClient } from "redis";

const redisClient = createClient({ url: process.env.REDIS_URL });
await redisClient.connect();

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  sessionStore: new RedisSessionStore({
    client: redisClient,
    prefix: "mcp:session:",
    defaultTTL: 3600, // seconds
  }),
});

await server.listen({ transportType: "httpStream", port: 3000 });
```

- **Pros:** Survives restarts, works with horizontal scaling.
- **Cons:** Requires a running Redis instance.

### Stateless Mode

Disable sessions entirely. Each request is processed independently with no shared state.

```typescript
await server.listen({
  transportType: "httpStream",
  port: 3000,
  sessionIdGenerator: undefined, // explicitly stateless
});
```

- **Pros:** Simplest scaling model, no session storage needed.
- **Cons:** No per-client context, every request starts fresh.

---

## DNS Rebinding Protection (HTTP)

When running an HTTP transport on `localhost`, protect against DNS rebinding attacks by restricting allowed origins.

```typescript
const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  allowedOrigins: [
    "http://localhost:3000",
    "https://myapp.com",
  ],
});

await server.listen({
  transportType: "httpStream",
  port: 3000,
  cors: true,
});
```

The server rejects requests whose `Origin` header does not match the allow list. Always set `allowedOrigins` when the server is accessible from a browser context.

---

## Common Transport Issues

| Issue | Cause | Fix |
|---|---|---|
| "Connection refused" on stdio | Server crashed on startup | Check for errors before `listen()`. Run manually to see stack trace. |
| CORS errors on HTTP | Missing CORS configuration | Set `cors: true` or configure `allowedOrigins`. |
| Session lost between requests | Stateless mode or missing session store | Add `sessionIdGenerator` and optionally a persistent session store. |
| SSE disconnects unexpectedly | Network timeout or proxy buffering | Switch to `httpStream` with event store for resumability. Configure proxy timeouts. |
| Port already in use | Another process on the same port | Change `port` or stop the conflicting process. |
| Slow stdio responses | Large payloads on stdout | Keep tool responses concise. Stream large data via references instead. |

---

## Transport Comparison Summary

| Feature | stdio | httpStream | sse (legacy) |
|---|---|---|---|
| Setup complexity | None | Low | Low |
| Network required | No | Yes | Yes |
| Multiple clients | No | Yes | Yes |
| Session management | N/A | Built-in | Built-in |
| Resumability | No | Yes (event store) | No |
| Middleware support | No | Yes | Yes |
| Claude Desktop | ✅ | ✅ (via URL) | ✅ (via URL) |
| Production ready | Local only | Yes | Deprecated |
