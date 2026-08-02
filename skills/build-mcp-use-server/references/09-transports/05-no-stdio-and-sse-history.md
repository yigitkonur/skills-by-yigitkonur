# No stdio and SSE in v2

*Read this when migrating from v1 or understanding what's changed.*

## Stdio removed

v1 supported `server.listen({ stdio: true })` for stdio-based MCP servers (spawned by clients as child processes). v2 **does not export this interface**. All v2 servers are HTTP-only.

**Why:** Stdio is process-coupled; HTTP is decoupled. Stateless HTTP scales to multiple instances without session affinity. Stdio is incompatible with serverless/edge runtimes.

**Workaround:** If a use case requires stdio, implement it outside mcp-use (e.g., wrap `server.fetch` with a stdio-to-HTTP bridge). Most production deployments do not need stdio.

## SSE not a distinct transport

v1 had `{ sse: true }` to enable server-sent events for streaming responses. v2 uses **streamable HTTP**: POST responses can be SSE (if client sends `Accept: text/event-stream`) or JSON, decided per request. There is no `sse` config flag.

In **stateless mode** (v2 default), all responses are JSON; streaming features (progress, notifications, elicitation) are not available within a single request.

## Migration from v1 stdio/SSE

| v1 Pattern | v2 Equivalent | Notes |
|------------|---------------|-------|
| Spawn stdio child process | Deploy HTTP server, use HTTP client | HTTP clients can be local (Inspector, `mcp-use client`) or remote (ChatGPT) |
| `server.listen({ stdio: true })` | Not available | Route stdio manually if needed; use `mcp-use/node` for Node.js HTTP server |
| `{ sse: true }` option | Streamable HTTP (POST/GET default) | v2 auto-negotiates per request; no config needed |
| Server-pushed notifications over long-lived connection | Removed in v2 stateless mode | Use external DB for cross-request state or subscription listeners |

See `../28-migration/07-v1-to-v2-sessions-transports-stdio-sse.md` for detailed migration steps.

## Stateless implications

Without a persistent connection (GET stream), the server **cannot push** to clients between requests. Notifications are delivered only during the originating request's response stream.

For multi-round workflows (e.g., "server initiates ask, client responds"), use `ctx.elicit()` within a single request or store state in an external database + polling.

## What v2 kept from v1

- **HTTP POST:** JSON-RPC request/response (same wire format as v1 streaming mode).
- **JSON responses:** When client does not request streaming, response is JSON (v1 compatibility).
- **Headers:** `mcp-session-id` and negotiation headers work the same (but in v2 stateless mode, sessions are per-request).

See `references/01-concepts/03-transports-overview.md` for architecture context.