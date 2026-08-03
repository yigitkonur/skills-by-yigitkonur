# Streamable HTTP

*Read this when setting up HTTP endpoints or testing the MCP server.*

v2 uses Web-standard Fetch API (`server.fetch(request)` → `Response`). Endpoints are at `{basePath}` (default `/mcp`).

## HTTP endpoint methods

| Method | Purpose | Payload | Response (stateless default) |
|--------|---------|---------|----------|
| `POST /mcp` | Send MCP JSON-RPC request (modern or legacy wire) | JSON body | JSON `{ result, id }` / error envelope (modern), or SSE-framed JSON-RPC (legacy) |
| `GET /mcp` | Browser navigation or SDK probe | None | HTML navigation (`Accept: text/html`) returns the landing page/auth response; other probes return `204 No Content` |
| `DELETE /mcp` | Optional SDK probe | None | `204 No Content` |
| `HEAD /mcp` | Browser navigation or SDK probe | None | HTML navigation follows the landing-page branch; other probes return `204 No Content` |
| `OPTIONS /mcp` | CORS preflight | None | `405` if `config.cors` is unset; `204` + CORS headers if `config.cors` is set |

DELETE and non-HTML GET/HEAD probes are **not** a legacy SSE-stream-open or session-teardown mechanism — the stateless mount answers them with `204`. HTML-accepting GET/HEAD navigation is handled first at the same `basePath` and returns the landing page (or its OAuth response). A bare `OPTIONS` without CORS configured is a real `405`, since there is no preflight to answer.

## Modern wire (2026-07-28): the native v2 protocol

The modern wire has **no `initialize` handshake**. Every request carries its own protocol version and client identity in a `_meta` envelope, mirrored into headers for routing. Responses are plain `application/json`, never SSE-framed, and work with any `Accept` header (including none).

```bash
# tools/list on the modern wire — no prior initialize call
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "mcp-protocol-version: 2026-07-28" \
  -H "mcp-method: tools/list" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {
      "_meta": {
        "io.modelcontextprotocol/protocolVersion": "2026-07-28",
        "io.modelcontextprotocol/clientInfo": { "name": "cli", "version": "1.0.0" },
        "io.modelcontextprotocol/clientCapabilities": {}
      }
    }
  }' | jq .

# tools/call — add mcp-name mirroring params.name for name-addressed methods
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "mcp-protocol-version: 2026-07-28" \
  -H "mcp-method: tools/call" \
  -H "mcp-name: my-tool" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "my-tool",
      "arguments": { "arg": "value" },
      "_meta": {
        "io.modelcontextprotocol/protocolVersion": "2026-07-28",
        "io.modelcontextprotocol/clientInfo": { "name": "cli", "version": "1.0.0" },
        "io.modelcontextprotocol/clientCapabilities": {}
      }
    }
  }' | jq .
```

Calling `initialize` on the modern wire is a protocol error (method not found) — there is nothing to initialize.

## Legacy wire (2025-era): compatibility fallback

Most existing MCP clients — including the official SDK's default posture — still speak the traditional `initialize` handshake with protocol versions `2025-11-25` (latest legacy), `2025-06-18`, `2025-03-26`, `2024-11-05`, or `2024-10-07`. mcp-use v2 serves these through `ServerConfig.legacy: "stateless"` (the default): each legacy request gets a fresh, session-less handler instance. `Mcp-Session-Id` is never generated or required in this mode.

Legacy requests **must** send `Accept: application/json, text/event-stream` (both media types) — a bare `Accept: application/json` gets `406 Not Acceptable`. Legacy responses are SSE-framed (`Content-Type: text/event-stream`, body shaped as `event: message\ndata: {...}\n\n`) even for a single non-streaming JSON-RPC result.

```bash
# Legacy initialize handshake — dual Accept header is required
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 0,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": { "name": "cli", "version": "1.0.0" }
    }
  }'
# Response is SSE-framed: "event: message\ndata: {...}\n\n" — pipe through
# `grep '^data:' | sed 's/^data: //' | jq .` to extract the JSON-RPC body.
```

Set `legacy: "reject"` on `ServerConfig` to refuse legacy-classified requests outright (unsupported-protocol-version error) and force clients onto the modern wire only.

## View asset routing

Production build output `.mcp-use/build/views/<name>/<path>` maps to `GET {basePath}/_mcp-use/views/<name>/<path>` (default `/mcp/_mcp-use/views/<name>/<path>`); project-public files map to `GET {basePath}/_mcp-use/public/<path>`. Hosts obtain the View's HTML document only through `resources/read` — there is no separate HTTP document route.

## Security defaults

- Localhost-class binds (`127.0.0.1`, `::1`, `localhost`) require Host header validation by default.
- CORS is off unless `config.cors` is set.
- Origin validation is off unless `allowedOrigins` is set.

See `../08-server-config/03-cors-and-allowed-origins.md` and `../08-server-config/04-dns-rebinding-and-host-validation.md`.

## Local dev pattern

Bind to `127.0.0.1` (default) and test with curl or an MCP client (Inspector, `mcp-use client`). Use `mcp-use dev` during development for live reload.

For remote sharing: see `../21-tunneling/`.

## v2-specific: No session state in HTTP handler

v2 stateless means each POST is independent; no session affinity. The SDK handles request lifetime; your callback runs once per request. Use `requestState` codec to verify round-trip state (e.g., for `input_required` retry validation).

See `03-stateless-and-request-state.md` and `../10-sessions/03-state-patterns-without-sessions.md`.
