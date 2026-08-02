# Streamable HTTP

*Read this when setting up HTTP endpoints or testing the MCP server.*

v2 uses Web-standard Fetch API (`server.fetch(request)` → `Response`). Endpoints are at `{basePath}` (default `/mcp`).

## HTTP endpoint methods

| Method | Purpose | Payload | Response |
|--------|---------|---------|----------|
| `POST /mcp` | Send MCP JSON-RPC request | JSON body: `{ jsonrpc, method, params }` | JSON `{ result, id }` or error envelope |
| `GET /mcp` | Open SSE stream (reserved; legacy session pattern) | None | `text/event-stream` |
| `DELETE /mcp` | Session teardown (reserved; legacy pattern) | Optional JSON | Success/error |
| `OPTIONS /mcp` | CORS preflight | None | CORS headers + 200 |

In **v2 stateless mode** (default), GET/DELETE return 405 (unsupported); every request is independent.

## v2 curl handshake (stateless)

Initialize the server and list tools:

```bash
# Initialize (server reports capabilities + ready state)
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 0,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": { "name": "cli", "version": "1.0.0" }
    }
  }' | jq .

# List tools
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }' | jq .

# Call a tool
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "my-tool",
      "arguments": { "arg": "value" }
    }
  }' | jq .
```

Protocol version is `2024-11-05` (MCP 2.0); mcp-use v2.0.0-beta.66 implements this version.

## View asset routing

Views compiled to `.mcp-use/build/views/` are mounted at `/mcp/_mcp-use/views/`. The server serves them as MCP resources; clients fetch view HTML from the same origin.

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
