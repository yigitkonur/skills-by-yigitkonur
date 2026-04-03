# Transports

Configure how MCP clients connect to your server — HTTP Streamable for networked services, or serverless handlers for edge platforms.

---

## Transport Decision Matrix

| Transport | Protocol | Use When | Sessions | SSE | Scaling |
|-----------|----------|----------|----------|-----|---------|
| **HTTP Streamable** | HTTP + SSE | Networked servers, multi-client, production APIs | Yes (auto) | Yes | Horizontal (with Redis) |
| **SSE (legacy)** | HTTP + SSE | Backward compatibility with older MCP clients only | Yes | Yes | Same as HTTP Streamable |
| **Serverless** | Platform-specific | Supabase Edge Functions, Cloudflare Workers, Deno Deploy, Vercel | Stateless | No | Platform-managed |

**Quick rule:** Use `server.listen()` or `server.listen(port)` for HTTP, `server.getHandler()` for serverless.

---

## HTTP Streamable Transport

When `server.listen(port)` is called, the server starts an HTTP server using Streamable HTTP transport. This is the primary transport for networked MCP servers.

```typescript
import { MCPServer, text } from "mcp-use/server";

const server = new MCPServer({ name: "my-server", version: "1.0.0" });
server.tool({ name: "hello" }, async () => text("Hello!"));

// Start HTTP server on port 3000
await server.listen(3000);
```

### Port Resolution Order

The port is resolved in this priority:

1. `server.listen(port)` — explicit argument (highest priority)
2. `--port` CLI argument (e.g., `node server.js --port 8080`)
3. `PORT` environment variable
4. Default: `3000`

> **Note:** `server.listen()` called without a port argument starts HTTP on the default port (3000), not stdio. The mcp-use server framework is HTTP-only.

### Host Configuration

The hostname defaults to `"localhost"`. Override it via:

- `host` constructor option: `new MCPServer({ host: "0.0.0.0", ... })`
- `HOST` environment variable

```typescript
const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  host: "0.0.0.0", // Bind to all interfaces (required for Docker/containers)
});

await server.listen(3000);
```

### HTTP Endpoints

The server automatically mounts endpoints at both `/mcp` and `/sse`:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/mcp` | `POST` | Send JSON-RPC requests, receive streamed responses |
| `/mcp` | `GET` | Open an SSE stream for server-initiated messages |
| `/mcp` | `DELETE` | Terminate a session |
| `/mcp` | `HEAD` | Health check / keep-alive |
| `/sse` | Same | Legacy alias — same handler, backward compatible |

### Stateful vs Stateless Auto-Detection

The server auto-detects the mode per request based on the client's `Accept` header:

- `Accept: application/json, text/event-stream` → **Stateful** (sessions, SSE, notifications)
- `Accept: application/json` only → **Stateless** (request-response, no sessions)
- **Deno / edge runtimes** → always stateless (auto-detected)
- `stateless: true` in constructor → forces stateless for all requests

```typescript
// Force stateless mode (useful for serverless/edge)
const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  stateless: true,
});
```

This enables compatibility with `curl`, k6, and HTTP-only clients while maintaining full SSE support for capable clients.

> **Session stores** — See `session-management.md` for session store configuration (in-memory, Redis, filesystem).

---

## SSE Transport (Legacy)

The `/sse` endpoint exists for backward compatibility with older MCP clients that expect the legacy SSE-based protocol. It uses the same handler as `/mcp` — there is no separate SSE-only mode.

**When to use:** Only when connecting to clients that do not support the newer Streamable HTTP transport. All modern MCP clients should use `/mcp`.

---

## Serverless Handlers

For platforms that manage the HTTP server lifecycle (Supabase Edge Functions, Cloudflare Workers, Deno Deploy), use `getHandler()` instead of `listen()`.

```typescript
import { MCPServer, text } from "mcp-use/server";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  stateless: true, // Recommended for serverless
});

server.tool({ name: "hello" }, async () => text("Hello!"));
```

### Supabase Edge Functions

```typescript
const handler = await server.getHandler({ provider: "supabase" });
Deno.serve(handler);
```

Pass `{ provider: "supabase" }` to enable automatic Supabase path rewriting.

### Cloudflare Workers

```typescript
const handler = await server.getHandler();
export default { fetch: handler };
```

### Deno Deploy

```typescript
const handler = await server.getHandler();
Deno.serve(handler);
```

### Vercel (Serverless Functions)

```typescript
// api/mcp.ts
const handler = await server.getHandler();
export default { fetch: handler };
```

> **Note:** `MCPServer` wraps a Hono app internally — it does not extend Hono directly. `getHandler()` returns a standard `fetch`-compatible handler. Stateless mode is recommended for serverless since there is no persistent session storage between invocations.

---

## Proxy / Aggregator Transport

The `server.proxy()` method composes multiple upstream MCP servers into a single unified server. All tools, resources, and events from child servers are namespaced and forwarded automatically.

### High-Level Proxy (Recommended)

```typescript
import { MCPServer } from "mcp-use/server";
import path from "node:path";

const server = new MCPServer({ name: "UnifiedServer", version: "1.0.0" });

await server.proxy({
  // Local TypeScript server (tsx runner)
  database: {
    command: "tsx",
    args: [path.resolve(__dirname, "./db-server.ts")],
  },

  // Local Python FastMCP server
  weather: {
    command: "uv",
    args: ["run", "weather_server.py"],
    env: { ...process.env, FASTMCP_LOG_LEVEL: "ERROR" },
  },

  // Remote HTTP MCP server
  manufact: {
    url: "https://manufact.com/docs/mcp",
  },
});

// Tools from "database" become "database_<toolName>", etc.
server.tool(
  { name: "aggregator_status", description: "Check aggregator status" },
  async () => ({ content: [{ type: "text", text: "All systems operational" }] })
);

await server.listen(3000);
```

### Low-Level Proxy (Custom Sessions)

Use the low-level form for custom authentication, dynamic headers, or per-request session control:

```typescript
import { MCPServer } from "mcp-use/server";
import { MCPClient } from "mcp-use/client";

const server = new MCPServer({ name: "UnifiedServer", version: "1.0.0" });

const customClient = new MCPClient({
  mcpServers: {
    secure_db: { url: "https://secure-db.example.com/mcp" },
  },
});

const dbSession = await customClient.createSession("secure_db");

// Explicitly proxy the session under a chosen namespace
await server.proxy(dbSession, { namespace: "secure_db" });

await server.listen(3000);
```

### Proxy Configuration Types

| Type | Shape | Notes |
|------|-------|-------|
| `ProxyConfig` | `{ [namespace: string]: ProxyTarget }` | Keys become tool/resource namespaces |
| `ProxyTarget` (local) | `{ command: string; args?: string[]; env?: Record<string, string> }` | Spawn a local process |
| `ProxyTarget` (remote) | `{ url: string }` | Connect to a remote HTTP MCP server |

### Proxy Namespace Behavior

- **Tools:** `database_<toolName>` (namespace + underscore + tool name)
- **Resource URIs:** `weather://app://settings` (namespace + `://` + original URI)
- **Events:** All `list_changed` and `progress` notifications from child servers are forwarded to connected clients automatically

### Proxy Event Forwarding

1. Child tool emits `notifications/progress/report`
2. Aggregator receives the event via its internal listener
3. Aggregator forwards it through the originating `ToolContext` back to the invoking client
4. `notifications/tools/list_changed`, `notifications/resources/list_changed`, and `notifications/prompts/list_changed` are forwarded to all connected clients

---

## DNS Rebinding Protection

When running on `localhost`, protect against DNS rebinding attacks by restricting allowed origins. Set `allowedOrigins` in the constructor to enable Host header validation.

```typescript
const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  allowedOrigins: [
    "http://localhost:3000",
    "https://myapp.com",
  ],
});
```

### How Validation Works

1. **Hostname extraction** — Each origin URL is parsed to extract its hostname (e.g., `"http://localhost:3000"` → `"localhost"`).
2. **Host header check** — A global middleware checks every incoming request's `Host` header against the extracted hostnames.
3. **Rejection** — If the `Host` header does not match any allowed hostname, the server returns a JSON-RPC error with HTTP **403 Forbidden**.

| `allowedOrigins` value | Behavior |
|------------------------|----------|
| Not set (default) | No host validation — all `Host` values accepted |
| `[]` (empty array) | No host validation (same as not set) |
| `["https://myapp.com"]` | Host header must match a configured hostname |

```typescript
// Load from environment for production
const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  allowedOrigins: process.env.ALLOWED_ORIGINS?.split(","),
});
```

> **Always set `allowedOrigins`** when the server is accessible from a browser context. Without it, a malicious webpage could exploit DNS rebinding to send requests to your local MCP server.

---

## CORS Configuration

By default, CORS is permissive (`origin: "*"`) for developer ergonomics. Set `cors` in the constructor to restrict it.

### Default CORS Headers

```typescript
// These are the defaults — you only need to set `cors` to override them
{
  origin: "*",
  allowMethods: ["GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS"],
  allowHeaders: [
    "Content-Type", "Accept", "Authorization",
    "mcp-protocol-version", "mcp-session-id",
    "X-Proxy-Token", "X-Target-URL",
  ],
  exposeHeaders: ["mcp-session-id"],
}
```

### Custom CORS

```typescript
const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  cors: {
    origin: ["https://app.example.com"],
    allowMethods: ["GET", "POST", "DELETE", "OPTIONS"],
    allowHeaders: ["Content-Type", "Authorization", "mcp-protocol-version", "mcp-session-id"],
    exposeHeaders: ["mcp-session-id"],
  },
});
```

> **Warning:** The `cors` option **replaces** the default CORS configuration entirely — there is no merge. If you override `cors`, include all headers your clients need (e.g., `mcp-session-id` in `exposeHeaders`).

---

## Base URL Configuration

The `baseUrl` controls the public URL used for widget assets, CSP configuration, and reverse proxy setups. This is critical when the server runs behind a proxy or on a different domain than the public URL.

```typescript
const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  baseUrl: "https://mcp.example.com", // Public URL for clients
});
```

### Resolution Order

1. `baseUrl` constructor option (highest priority)
2. `MCP_URL` environment variable
3. `http://{host}:{port}` (auto-generated from host and port)

### Environment Variables

| Variable | Effect | Default |
|----------|--------|---------|
| `PORT` | HTTP server port | `3000` |
| `HOST` | Bind hostname | `localhost` |
| `MCP_URL` | Full public base URL (widget/asset URLs, CSP) | `http://{HOST}:{PORT}` |
| `CSP_URLS` | Comma-separated extra URLs added to widget CSP | — |

When `baseUrl` (or `MCP_URL`) is set, the server origin is auto-injected into each widget's CSP `connectDomains`, `resourceDomains`, and `baseUriDomains`.

---

## Custom HTTP Routes and Middleware

`MCPServer` wraps Hono internally and proxies all standard Hono request-handling methods, enabling custom routes, middleware, static file serving, etc.:

```typescript
const server = new MCPServer({ name: "my-server", version: "1.0.0" });

// Custom HTTP GET endpoint
server.get("/api/status", (c) => {
  return c.json({ status: "ok", sessions: server.getActiveSessions().length });
});

// Custom middleware
server.use("*", async (c, next) => {
  console.log(`${c.req.method} ${c.req.path}`);
  await next();
});

await server.listen(3000);
```

Available Hono proxy methods: `get()`, `post()`, `put()`, `delete()`, `use()`, `route()`, and all other standard Hono methods.

---

## Common Transport Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| "Connection refused" | Server crashed on startup | Check for errors before `listen()`. Run manually to see stack trace. |
| CORS errors | Missing CORS configuration | CORS is enabled by default (`origin: "*"`). Customize via `cors` constructor option. |
| Port already in use | Another process on the same port | Change port or stop the conflicting process. |
| SSE disconnects | Network timeout or proxy buffering | Configure proxy timeouts. Server supports session recovery on reconnect. |
| 403 Forbidden | `allowedOrigins` rejecting `Host` header | Add the request's origin to `allowedOrigins` array. |
| Stateless mode, notifications not working | Serverless / stateless transport | Notifications require stateful sessions; switch to `server.listen()` transport. |

---

## Summary

| Feature | Details |
|---------|---------|
| **HTTP Streamable** | `server.listen()` or `server.listen(port)` — primary networked transport |
| **SSE (legacy)** | `/sse` endpoint — backward compatible alias for `/mcp` |
| **Serverless** | `server.getHandler()` — Supabase, Cloudflare, Deno, Vercel |
| **Proxy / Aggregator** | `server.proxy(config)` or `server.proxy(session, opts)` — compose multiple upstream servers |
| **Session mode** | Auto-detected per request (stateful for SSE, stateless for HTTP-only) |
| **DNS protection** | `allowedOrigins` constructor option |
| **CORS** | Permissive by default; override via `cors` constructor option |
| **Base URL** | `baseUrl` config or `MCP_URL` env var |
| **Custom routes** | Hono methods proxied directly on `MCPServer` |

> **See also:** `session-management.md` for session stores (in-memory, Redis, filesystem) and stream managers. `server-configuration.md` for middleware and custom routes.
