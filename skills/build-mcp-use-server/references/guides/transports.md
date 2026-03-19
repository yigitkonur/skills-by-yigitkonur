# Transports

Configure how MCP clients connect to your server — Streamable HTTP for networked services, stdio for local integrations, or serverless handlers for edge platforms.

---

## Transport Decision Matrix

| Transport | How to start | Use When | Sessions | SSE | Scaling |
|---|---|---|---|---|---|
| **HTTP Streamable** | `server.listen(port)` | Networked servers, multi-client, production APIs | Yes (auto-detected) | Yes | Horizontal (with Redis) |
| **stdio** | `server.listen()` (no port) | Local tools, desktop connectors, CLI integrations | N/A | No | Single process |
| **SSE `/sse` alias** | Automatic (same as HTTP Streamable) | Backward compatibility with older MCP clients only | Yes | Yes | Same as HTTP Streamable |
| **Serverless** | `server.getHandler()` | Supabase Edge Functions, Cloudflare Workers, Deno Deploy, Vercel | Stateless | No | Platform-managed |

**Quick rule:** Use `server.listen(port)` for HTTP, `server.listen()` (no port) for stdio, `server.getHandler()` for serverless.

---

## HTTP Streamable Transport

When `server.listen(port)` is called **with a port**, the server starts an HTTP server using Streamable HTTP transport. This is the primary transport for networked MCP servers.

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

> **Note:** Prefer explicit transport configuration in examples. Use stdio for local desktop integrations and Streamable HTTP for remote/networked deployments.

### Host Configuration

The hostname defaults to `"localhost"`. Override it via:

- `host` constructor option (e.g., `host: '0.0.0.0'`)
- `HOST` environment variable
- `baseUrl` constructor option — sets the full public base URL (e.g., `baseUrl: 'https://mcp.example.com'`); also read from `MCP_URL` env var; overrides `host:port` for widget and asset URL generation

```typescript
const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
});

await server.listen(3000);
```

### HTTP Endpoints

The server automatically mounts endpoints at both `/mcp` and `/sse`:

| Endpoint | Method | Purpose |
|---|---|---|
| `/mcp` | `POST` | Send JSON-RPC requests, receive streamed responses |
| `/mcp` | `GET` | Open an SSE stream for server-initiated messages |
| `/mcp` | `DELETE` | Terminate a session |
| `/mcp` | `HEAD` | Health check / keep-alive |
| `/sse` | Same | Legacy alias — same handler, backward compatible |

### Stateful vs Stateless Mode

The `stateless` option in `ServerConfig` controls session behavior. Leave it unset to use auto-detection.

**Auto-detection (default behavior):**

- **Deno / edge runtimes** → always stateless
- **Node.js** → detected per-request from the `Accept` header:
  - `Accept: application/json, text/event-stream` → **Stateful** (sessions, SSE, notifications)
  - `Accept: application/json` only → **Stateless** (request-response, no sessions)

```typescript
// Force stateless mode (ignores Accept header)
const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  stateless: true,
});

// Force stateful mode
const server2 = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  stateless: false,
});
```

Auto-detection (leaving `stateless` unset) lets the same server handle both SSE-capable and HTTP-only clients transparently. This enables compatibility with `curl`, k6, and HTTP-only clients while maintaining full SSE support for capable clients.

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

## DNS Rebinding Protection

When running on `localhost`, protect against DNS rebinding attacks by restricting allowed origins. Set `allowedOrigins` in the constructor to enable Host header validation.

```typescript
const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  allowedOrigins: [
    "https://myapp.com",
  ],
});
```

### How Validation Works

2. **Host header check** — A global middleware checks every incoming request's `Host` header against the extracted hostnames.
3. **Rejection** — If the `Host` header does not match any allowed hostname, the server returns a JSON-RPC error with HTTP **403 Forbidden**.

| `allowedOrigins` value | Behavior |
|---|---|
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

## Public URL Notes

Public asset/widget URLs are deployment concerns. They should be documented at the reverse-proxy or platform layer rather than as `ServerConfig` properties.

```typescript
const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
});
```

### Resolution Order

1. Deployment platform / reverse proxy
2. Environment variables used by your app
3. Runtime defaults for local development

### Environment Variables

| Variable | Effect | Default |
|---|---|---|
| `PORT` | HTTP server port | `3000` |
| `HOST` | Bind hostname | `localhost` |
| `MCP_URL` | Full public base URL (widget/asset URLs, CSP) | `http://{HOST}:{PORT}` |
| `CSP_URLS` | Comma-separated extra URLs added to widget CSP | — |

When you publish widgets, document the public origin explicitly alongside your deployment configuration.

---

## Common Transport Issues

| Issue | Cause | Fix |
|---|---|---|
| "Connection refused" | Server crashed on startup | Check for errors before `listen()`. Run manually to see stack trace. |
| CORS errors | Missing CORS configuration | CORS is enabled by default (`origin: "*"`). Customize via `cors` constructor option. |
| Port already in use | Another process on the same port | Change port or stop the conflicting process. |
| SSE disconnects | Network timeout or proxy buffering | Configure proxy timeouts. Server supports session recovery on reconnect. |
| 403 Forbidden | `allowedOrigins` rejecting `Host` header | Add the request's origin to `allowedOrigins` array. |

---

## Summary

| Feature | Details |
|---|---|
| **HTTP Streamable** | `server.listen()` or `server.listen(port)` — primary networked transport |
| **SSE (legacy)** | `/sse` endpoint — backward compatible alias for `/mcp` |
| **Serverless** | `server.getHandler()` — Supabase, Cloudflare, Deno, Vercel |
| **Session mode** | Auto-detected per request (stateful for SSE, stateless for HTTP-only) |
| **DNS protection** | `allowedOrigins` constructor option |
| **CORS** | Permissive by default; override via `cors` constructor option |
| **Public origin** | Set via deployment / reverse-proxy configuration |

> **See also:** `session-management.md` for session stores (in-memory, Redis, filesystem) and stream managers. `server-configuration.md` for middleware and custom routes.

---

## Streamable HTTP in MCP Spec 2025-11-25

The current MCP transport story centers on **Streamable HTTP**: one canonical endpoint, one transport family, and one session model. In the latest spec, the same endpoint handles request/response RPC, streaming responses, session lifecycle, and server-initiated events.

### What changed from older deployments?

| Era | Write endpoint | Stream endpoint | Session lifecycle | Recommendation |
|---|---|---|---|---|
| Older SSE deployments | `POST /messages` | `GET /sse` | Separate route handling | Migrate |
| Transitional deployments | `POST /mcp` | `GET /mcp` plus `/sse` alias | Unified logic, legacy alias | Acceptable during migration |
| Current spec-aligned deployments | `POST /mcp` | `GET /mcp` | Unified `/mcp` endpoint | Preferred |

### Unified endpoint behavior

| Method | Path | Meaning | Notes |
|---|---|---|---|
| `POST` | `/mcp` | Send JSON-RPC requests | Supports normal and streamed responses |
| `GET` | `/mcp` | Open server-to-client stream | Used for notifications, progress, and resumable stateful sessions |
| `DELETE` | `/mcp` | Close an active session | Client should include `Mcp-Session-Id` |
| `HEAD` | `/mcp` | Cheap health check | Useful behind load balancers |

```typescript
import { MCPServer, text } from 'mcp-use/server'
import { z } from 'zod'

const server = new MCPServer({
  name: 'inventory-server',
  version: '1.0.0',
  allowedOrigins: ['https://app.example.com'],
})

server.tool(
  {
    name: 'inventory-status',
    description: 'Summarize current inventory health.',
    schema: z.object({
      warehouseId: z.string().describe('Warehouse to inspect'),
    }),
  },
  async ({ warehouseId }) => text(`Inventory is healthy for ${warehouseId}.`)
)

await server.listen(3000)
```

### Why the unified endpoint matters

- **Simpler proxies** — one route to expose, secure, and log.
- **Cleaner clients** — no split discovery logic between message and stream URLs.
- **Better compatibility** — POST, GET, DELETE, and HEAD semantics map to a single session contract.
- **Easier observability** — one route for metrics, tracing, WAF rules, and rate limiting.

### `listen()` API reference

The official API signature is:

```typescript
listen(port?: number): Promise<void>
```

Port resolution order: explicit `listen(port)` argument → `--port` CLI flag → `PORT` env var → `3000`.

❌ **BAD** — Keep the legacy split routes in new deployments:

```typescript
await app.post('/messages', legacyMessagesHandler)
await app.get('/sse', legacySseHandler)
```

✅ **GOOD** — Start the server on the unified `/mcp` endpoint:

```typescript
await server.listen(3000)
```

❌ **BAD** — Assume GET `/mcp` is optional for stateful clients:

```typescript
app.post('/mcp', postOnlyHandler)
```

✅ **GOOD** — `listen()` automatically mounts all required methods (POST, GET, DELETE, HEAD) on `/mcp`:

```typescript
await server.listen(3000)
```

---

## SSE to Streamable HTTP Migration Guide

If you already run an older MCP server using a dedicated SSE endpoint, migrate in controlled stages. The goal is to move clients from the **split-route model** to the **unified `/mcp` model** without breaking active integrations.

### Migration checklist

1. **Add `/mcp` first** while keeping `/sse` working.
2. **Switch documentation and examples** to `POST /mcp` and `GET /mcp`.
3. **Update client configs** to point at the new endpoint.
4. **Keep a compatibility window** with a `/sse` alias if you have older clients.
5. **Log usage by route** so you know when legacy traffic is gone.
6. **Remove `/messages` and `/sse` only after the compatibility window closes.**

### Compatibility strategy table

| Strategy | Pros | Cons | Use when |
|---|---|---|---|
| Immediate cutover | Simplest server config | Breaks old clients | Internal-only environments |
| Dual-route compatibility | Safe migration | More proxy/app config | Most production systems |
| Reverse-proxy rewrite | No app code changes for legacy clients | Harder to observe | Short transition periods |

### Example: dual-route migration

```typescript
import { MCPServer, text } from 'mcp-use/server'

const server = new MCPServer({
  name: 'migration-safe-server',
  version: '1.0.0',
})

server.tool({
  name: 'ping',
  description: 'Return a ping response.',
}, async () => text('pong'))

// Start the server — /mcp is the canonical endpoint, /sse alias is mounted automatically
await server.listen(3000)
```

### Proxy rewrite example

```nginx
location = /messages {
  proxy_pass http://127.0.0.1:3000/mcp;
  proxy_set_header X-Legacy-Mcp-Route messages;
}

location = /sse {
  proxy_pass http://127.0.0.1:3000/mcp;
  proxy_set_header Accept "text/event-stream";
  proxy_set_header X-Legacy-Mcp-Route sse;
}
```

### Migration verification questions

| Question | Why it matters |
|---|---|
| Do new clients use `POST /mcp`? | Confirms request path migration |
| Do stateful clients still open `GET /mcp`? | Confirms streaming path is healthy |
| Do load balancers allow long-lived GETs? | Prevents silent disconnects |
| Are legacy `/sse` requests still arriving? | Tells you whether removal is safe |
| Are 404s on `Mcp-Session-Id` recoverable? | Ensures compliant re-initialize behavior |

### Backward compatibility notes

- Keep **legacy docs clearly labeled** as transitional.
- Avoid publishing new snippets with `/messages` or `/sse` unless you are explicitly documenting migration.
- If you must keep `/sse`, ensure it points at the same session and auth logic as `/mcp`.
- Log the `User-Agent` or client metadata when possible so you know which clients still rely on legacy flows.

---

## STDIO Transport

STDIO remains the best transport for **local tools, desktop connectors, and CLI-driven integrations**. It avoids network exposure entirely and works especially well with developer tools such as Claude Desktop, local inspectors, or custom command-based clients.

```typescript
import { MCPServer, text, object } from 'mcp-use/server'
import { z } from 'zod'

const server = new MCPServer({
  name: 'local-dev-server',
  version: '1.0.0',
})

server.tool(
  {
    name: 'read-project-summary',
    description: 'Return a short local project summary.',
    schema: z.object({
      includeFiles: z.boolean().default(false).describe('Whether to include file names'),
    }),
  },
  async ({ includeFiles }) => {
    if (includeFiles) {
      return object({ summary: 'Local workspace ready', files: ['package.json', 'src/server.ts'] })
    }
    return text('Local workspace ready')
  }
)

await server.listen()
```

### When to choose stdio

| Choose stdio when... | Why |
|---|---|
| The client launches your process directly | No network or reverse proxy needed |
| You are shipping a local package or binary | Simplest install story for desktop users |
| You want fewer moving parts during development | No ports, CORS, or TLS setup |
| The tool should not be remotely reachable | Best default security posture |

### STDIO guardrails

| Rule | Reason |
|---|---|
| Never use `console.log()` | Stdout is reserved for protocol traffic |
| Prefer `console.error()` or `ctx.log()` | Keeps diagnostics off the protocol stream |
| Avoid interactive stdin reads | The MCP transport owns stdin |
| Keep startup deterministic | Desktop clients expect the process to initialize quickly |

❌ **BAD** — Print debugging output to stdout:

```typescript
console.log('starting mcp server')
await server.listen()
```

✅ **GOOD** — Use stderr-safe logging:

```typescript
console.error('starting mcp server')
await server.listen()
```

### STDIO deployment pattern

```json
{
  "mcpServers": {
    "inventory": {
      "command": "node",
      "args": ["/absolute/path/to/dist/server.js"],
      "env": {
        "NODE_ENV": "production"
      }
    }
  }
}
```

### Choosing between stdio and HTTP

| Question | Prefer stdio | Prefer Streamable HTTP |
|---|---|---|
| Is the client on the same machine? | ✅ | ❌ |
| Do you need browser/OAuth redirects? | ❌ | ✅ |
| Do you need horizontal scaling? | ❌ | ✅ |
| Do you want zero exposed ports? | ✅ | ❌ |
| Do you need server-initiated notifications over the network? | ❌ | ✅ |

---

## Serverless Handlers by Platform

Use `getHandler()` when the platform owns the HTTP server lifecycle. In these deployments, prefer request/response handling unless you have a deliberate external session design.

### Shared serverless pattern

```typescript
import { MCPServer, text } from 'mcp-use/server'

const server = new MCPServer({
  name: 'serverless-server',
  version: '1.0.0',
  allowedOrigins: ['https://app.example.com'],
})

server.tool({ name: 'health', description: 'Return health state.' }, async () => text('ok'))

export const handler = await server.getHandler()
```

### Supabase Edge Functions

| Concern | Recommendation |
|---|---|
| Transport | Streamable HTTP over the edge runtime |
| Auth | Use bearer/OAuth verification in the server |
| Persistence | Store business data elsewhere; not in process memory |

```typescript
import { MCPServer, text } from 'mcp-use/server'

const server = new MCPServer({
  name: 'supabase-edge-server',
  version: '1.0.0',
})

server.tool({ name: 'region', description: 'Return current region.' }, async () => text(Deno.env.get('SB_REGION') ?? 'unknown'))

const handler = await server.getHandler({ provider: 'supabase' })
Deno.serve(handler)
```

### Cloudflare Workers

| Concern | Recommendation |
|---|---|
| Session mode | Stateless by default |
| Long-lived streams | Validate worker/platform limits before relying on them |
| Secrets | Store in Worker bindings |
| Origin protection | Use `allowedOrigins` plus Cloudflare rules |

```typescript
import { MCPServer, text } from 'mcp-use/server'

const server = new MCPServer({
  name: 'worker-server',
  version: '1.0.0',
  allowedOrigins: ['https://app.example.com'],
})

server.tool({ name: 'echo-worker', description: 'Echo a worker response.' }, async () => text('hello from workers'))

const handler = await server.getHandler()
export default { fetch: handler }
```

### Deno Deploy

| Concern | Recommendation |
|---|---|
| Session mode | Stateless |
| Runtime APIs | Use `Deno.env` and `fetch`-native primitives |
| URL mode elicitation/auth | Works well for browser-based handoffs |
| Base URL | Set explicitly for public links |

```typescript
import { MCPServer, text } from 'mcp-use/server'

const server = new MCPServer({
  name: 'deno-deploy-server',
  version: '1.0.0',
})

server.tool({ name: 'runtime', description: 'Return runtime name.' }, async () => text('deno-deploy'))

const handler = await server.getHandler()
Deno.serve(handler)
```

### Serverless pitfalls

❌ **BAD** — Keep state in memory and expect it to survive cold starts:

```typescript
const sessions = new Map()
```

✅ **GOOD** — Use request/response handlers or an external store when the platform may restart at any time:

```typescript
```

❌ **BAD** — Assume every platform supports indefinite SSE connections:

```typescript
```

✅ **GOOD** — Treat serverless as request/response-oriented unless you have platform-specific evidence and the right external backing services:

```typescript
```

---

## DNS Rebinding Protection with `allowedOrigins`

`allowedOrigins` protects HTTP transports from requests that arrive with unexpected origins or hosts. This matters most when your server binds to a private interface, runs on a laptop, or sits behind a proxy where browser-based attackers may try DNS rebinding tricks.

### Recommended `allowedOrigins` patterns

| Deployment | Example |
|---|---|
| Reverse-proxied production | `['https://app.example.com']` |
| Multiple trusted fronts | `['https://app.example.com', 'https://admin.example.com']` |
| Internal staging | `['https://staging.example.net']` |

```typescript
const server = new MCPServer({
  name: 'secure-http-server',
  version: '1.0.0',
  allowedOrigins: [
    'https://app.example.com',
    'https://admin.example.com',
  ],
})
```

### What `allowedOrigins` is not

- It is **not** a replacement for authentication.
- It does **not** make wildcard CORS safe.
- It does **not** validate user permissions.
- It should be combined with TLS, auth, and proxy hardening.

### Reverse-proxy checklist

| Check | Why |
|---|---|
| Forward `Host` and `X-Forwarded-*` headers correctly | Avoid false origin mismatches |
| Preserve `/mcp` path | Prevent broken discovery and callbacks |
| Set explicit trusted origins | Avoid accidental exposure |
| Terminate TLS at the edge | Keep browser flows secure |

---

## Transport Selection Playbook

| Scenario | How to start | Session mode | Notes |
|---|---|---|---|
| Claude Desktop / local tool | `server.listen()` (no port) | N/A | No network exposure; client launches the process |
| Public remote server | `server.listen(3000)` | Auto or stateful | `/mcp` endpoint; use `allowedOrigins` |
| Legacy client compatibility | `server.listen(3000)` + `/sse` alias auto-mounted | Stateful | Transitional only; `/sse` is an automatic alias |
| Supabase Edge / Workers / Deno Deploy | `server.getHandler()` | Stateless | Prefer no in-memory state |
| Horizontally scaled app with notifications | `server.listen(3000)` | Stateful + Redis | Pair with `RedisSessionStore` + `RedisStreamManager` |

## Practical defaults

1. Start with **stdio** for local-only tools.
2. Use **Streamable HTTP on `/mcp`** for anything remote.
3. Keep **SSE only for backward compatibility**.
4. Treat **serverless as stateless** unless you have a deliberate distributed session design.
5. Lock down **`allowedOrigins`** before exposing the server to browsers.
