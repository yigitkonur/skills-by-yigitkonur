# No stdio and SSE in v2

*Read this when migrating from v1 or understanding what's changed.*

## Stdio removed

v1 supported `server.listen({ stdio: true })` for stdio-based MCP servers (spawned by clients as child processes). v2 **does not export this interface**. All v2 servers are HTTP-only.

**Why:** Stdio is process-coupled; HTTP is decoupled. Stateless HTTP scales to multiple instances without session affinity. Stdio is incompatible with serverless/edge runtimes.

**Workaround:** If a use case requires stdio, implement it outside mcp-use (e.g., wrap `server.fetch` with a stdio-to-HTTP bridge). Most production deployments do not need stdio.

## SSE not a distinct transport

v1 had `{ sse: true }` to enable server-sent events for streaming responses. v2 has no `sse` config flag; whether a POST response is SSE-framed or plain JSON is decided by which protocol wire the request uses, not by an explicit client opt-in flag:

- **Modern wire (`2026-07-28`)**: always answers with a single plain `application/json` body — never SSE-framed, regardless of `Accept`.
- **Legacy wire (2025-era protocol versions)**: always answers SSE-framed (`Content-Type: text/event-stream`, `event: message\ndata: {...}\n\n`) — even for a single non-streaming JSON-RPC result — and requires the client to send `Accept: application/json, text/event-stream` (a bare `Accept: application/json` gets `406 Not Acceptable`).

So "streaming vs JSON" in v2 is a consequence of which wire the client speaks, not a per-request negotiation within one wire.

## Migration from v1 stdio/SSE

| v1 Pattern | v2 Equivalent | Notes |
|------------|---------------|-------|
| Spawn stdio child process | Deploy HTTP server, use HTTP client | HTTP clients can be local (Inspector, `mcp-use client`) or remote (ChatGPT) |
| `server.listen({ stdio: true })` | Not available | Route stdio manually if needed; use `mcp-use/node` for Node.js HTTP server |
| `{ sse: true }` option | No config flag; framing follows the protocol wire | Modern wire (2026-07-28) is always JSON; legacy wire is always SSE-framed |
| Server notifications | `subscriptions/listen` long-lived POST stream | Client initiates the listener; there is no server-opened GET stream, session affinity, backlog, or durable queue |

See `../28-migration/07-v1-to-v2-sessions-transports-stdio-sse.md` for detailed migration steps.

## Stateless implications

The old session-resume GET stream is gone, but v2 has one deliberate long-lived exception: a client may open `subscriptions/listen` as a POST response stream. Server `notify*` methods publish to matching active listeners; if no listener is open, the event is lost. This stream has no session store, affinity, backlog, or server-initiated reconnect.

Request-scoped `ctx.sendNotification()`/progress/log messages still end with their originating operation. For multi-round input, use `inputRequired.elicit()` and request state; for durable cross-request application state, use an external store.

## What v2 kept from v1

- **HTTP POST:** JSON-RPC request/response (same wire format as v1 streaming mode).
- **JSON responses:** The modern (2026-07-28) wire always answers plain JSON.
- **Legacy protocol-version compatibility:** the `legacy: "stateless"` fallback still accepts 2025-era `initialize` handshakes and their negotiation headers.

**Headers changed, not "the same":** v2's default stateless mode never generates or requires an `Mcp-Session-Id` header. The transport is constructed with `sessionIdGenerator: undefined`, which makes the SDK's session-validation check a no-op — there is no session to identify, so the header is neither sent by the server nor checked on incoming requests, even on the legacy wire.

See `../01-concepts/03-transports-overview.md` for architecture context.