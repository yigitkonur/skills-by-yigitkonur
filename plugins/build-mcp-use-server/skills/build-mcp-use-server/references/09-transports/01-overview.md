# Transports in v2

*Read this when understanding how requests flow to the MCP server.*

v2 uses **Streamable HTTP only** — there is no stdio, SSE, or proprietary transport. All runtimes share one portable boundary: the Web-standard Fetch API at `server.fetch(request)`.

## Three transport patterns

1. **Node.js and filesystem runtimes (Railway, Manufact, Bun):** Call `server.listen(port)` to bind HTTP + automatic View file serving.
2. **Edge and serverless (Cloudflare Workers, Deno, Vercel):** Export `server.fetch` or mount via framework (`withMcpUse` for Next.js).
3. **Embedded in frameworks:** Use `mcp-use/next` or `mcp-use/node` adapters to bind the fetch handler.

## Default endpoint

MCP protocol requests route to `{basePath}` (default `/mcp`). POST carries every JSON-RPC exchange. GET/DELETE/HEAD on the MCP path are optional SDK probes that return `204 No Content` in the default stateless mode (they are not errors, and they are not a legacy session-teardown path — v2 has no sessions to tear down). OPTIONS returns `405` unless `config.cors` is set, in which case it returns `204` with CORS headers. Custom routes are mounted separately via `server.get()`, `server.post()`, etc. See `02-streamable-http.md` for the full method table.

## Two wire formats, one endpoint

The same `/mcp` endpoint serves two protocol wire formats, distinguished by the request shape, not the URL:

- **Modern wire (`2026-07-28`):** the native v2 format. No `initialize` handshake — every request carries a `_meta` envelope (`io.modelcontextprotocol/protocolVersion`, `clientInfo`, `clientCapabilities`) plus `mcp-protocol-version`/`mcp-method` headers. Responses are plain JSON, never SSE-framed.
- **Legacy wire (2025-era: `2025-11-25`, `2025-06-18`, `2025-03-26`, `2024-11-05`, `2024-10-07`):** served through a stateless compatibility fallback (`ServerConfig.legacy`, default `"stateless"`) for clients that still speak the traditional `initialize` handshake. Each legacy request is answered by a fresh instance over a session-less transport — no `Mcp-Session-Id` is ever generated or required in this default mode. Legacy responses are SSE-framed and require `Accept: application/json, text/event-stream` (a bare `Accept: application/json` gets `406 Not Acceptable`).

Most MCP clients (including the official SDK's default posture) still speak the legacy 2025 handshake. See `02-streamable-http.md` for exact request/response shapes of both wires.

## Request model

Every request is **stateless** — no session affinity, no server-side state carryover. The MCP SDK maintains per-request context; clients may send `requestState` on an `input_required` retry to allow the server to validate state integrity.

See `03-stateless-and-request-state.md` for state codec usage.

## Cross-cluster references

- Runtime adapters: `04-runtime-adapters-node-next-fetch.md`
- Why stdio/SSE are gone: `05-no-stdio-and-sse-history.md`
- Sessions & scaling without session stores: `../10-sessions/`
