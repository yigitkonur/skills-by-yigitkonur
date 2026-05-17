# Transport Debugging

Transport-level bugs (handshake failures, header issues, session ID drift) look like generic "doesn't connect" errors. Diagnose them by isolating the layer: HTTP semantics, MCP protocol semantics, or session state.

---

## The handshake

Streamable HTTP follows this exact dance:

1. Client POSTs `initialize` to `/mcp` with `Accept: application/json, text/event-stream`.
2. Server responds with `serverInfo`, `capabilities`, `protocolVersion`. Response includes `Mcp-Session-Id` header.
3. Client POSTs `notifications/initialized` (no response expected).
4. Every subsequent request carries `Mcp-Session-Id` and `MCP-Protocol-Version` headers.

Break any step → broken connection. Diagnose by replicating the same dance with curl (`../22-validate/02-curl-handshake.md`).

---

## Handshake failure modes

| Symptom | Likely cause | Fix |
|---|---|---|
| 404 on `/mcp` | Server runs but `/mcp` route not mounted | Verify `mcp-use start` and that the route handler is registered |
| 406 Not Acceptable | Missing `Accept: application/json, text/event-stream` | Add header on every request |
| 415 Unsupported Media Type | Missing `Content-Type: application/json` | Add header |
| 400 with "Unsupported protocol version" | Old client sending `2024-11-05` | Bump client; server requires `2025-11-25` |
| 400 with "Missing session ID" | Forgot `Mcp-Session-Id` after init | Capture from initialize response and pass on every request |
| 401 Unauthorized | OAuth required, no bearer token | See OAuth setup in `02-setup/` |
| 403 Forbidden, "Origin not allowed" | DNS rebinding protection, host/origin mismatch | Add origin to `allowedOrigins`; see `dns-rebinding` example |
| Hangs at "Initializing…" | TCP connects but server never responds | Server crashed silently; check logs at `MCP_DEBUG_LEVEL=trace` |
| Connection drops after a few seconds | Reverse proxy buffering SSE | Disable buffering: `proxy_buffering off;` in nginx |

---

## Session ID drift

The `Mcp-Session-Id` header is the canonical identifier for a session. Mismatches cause confusing failures.

| Symptom | Cause |
|---|---|
| 400 "Unknown session" on every call | Server restarted; client still using old ID; client must re-`initialize` |
| Tool call works in Inspector, fails in curl | curl using stale session ID from a previous run |
| Multiple clients sharing one session ID | Don't do this — each client gets its own session via its own `initialize` |
| Session expires unexpectedly | Idle timeout; some servers GC sessions after N minutes; re-initialize |

Verify the session ID is being captured AND passed back:

```bash
# Capture
SESSION=$(curl -s -D - -X POST "$BASE" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"diag","version":"1.0.0"}},"id":1}' \
  | grep -i "mcp-session-id" | awk '{print $2}' | tr -d '\r')

echo "Got: '$SESSION'"
# If empty: server isn't returning the header — check server logs
```

---

## Verbose transport logs

Crank to trace level for HTTP/RPC details:

```bash
MCP_DEBUG_LEVEL=info,transport:trace,rpc:trace mcp-use start
```

You'll see incoming requests, outbound responses, raw headers, and full payloads. Cross-reference with what curl is sending — discrepancies are usually the bug.

For Node's HTTP-level debug:

```bash
NODE_DEBUG=http node dist/server.js
```

---

## SSE-specific issues

Some clients still use the legacy `/sse` GET endpoint with `Accept: text/event-stream`.

| Symptom | Fix |
|---|---|
| Events arrive in batches, not stream | Reverse proxy buffering — disable in nginx/CDN |
| Connection drops every ~30s | No keepalive; server should send periodic `:` heartbeats |
| `Content-Type` mismatch | Must be `text/event-stream`, not `application/event-stream` |
| Mixed content (page over HTTPS, SSE over HTTP) | Browser blocks; serve both over HTTPS |

```bash
# Manually test SSE
curl -N -H "Accept: text/event-stream" http://localhost:3000/sse
```

`-N` disables curl's output buffering.

---

## Behind a tunnel / reverse proxy

When the server is behind ngrok, Cloudflare Tunnel, or your own nginx, transport bugs multiply.

| Symptom | Fix |
|---|---|
| Works on `localhost`, fails through tunnel | Set `MCP_URL=https://tunnel-url.example.com` so widget assets resolve |
| Headers stripped (e.g. no `Mcp-Session-Id`) | Proxy header allowlist; add `Mcp-Session-Id`, `MCP-Protocol-Version` |
| 502 Bad Gateway intermittently | Upstream timeout shorter than tool's longest call; raise to 60s+ |
| Origin mismatch from proxy | Set `Forwarded` / `X-Forwarded-Host` and configure server to trust |

---

## CORS

Browser-based clients hit CORS preflights on every cross-origin call.

```typescript
const server = new MCPServer({
  name: "my-server",
  cors: {
    origin: ["https://app.example.com", "https://inspector.mcp-use.com"],
    credentials: true,
  },
});
```

| Symptom | Cause | Fix |
|---|---|---|
| Browser console: "blocked by CORS" | No `Access-Control-Allow-Origin` header | Configure `cors` |
| Preflight OPTIONS returns 405 | Server doesn't handle OPTIONS | Use the `cors` config; mcp-use handles OPTIONS automatically when configured |
| Cookies not sent | `credentials: true` missing on server, OR `credentials: 'include'` missing on client | Set both |
| Wildcard origin + credentials | Spec disallows `*` with `credentials: true` | Use explicit origin list |

---

## DNS rebinding protection

When `allowedOrigins` is configured, mcp-use rejects requests whose `Host` header doesn't match. Useful in prod, occasionally surprising in dev.

```typescript
new MCPServer({
  name: "my-server",
  allowedOrigins: ["mcp.example.com", "localhost:3000"],
});
```

To verify: send a spoofed `Host` header — should return 403.

```bash
curl -H "Host: evil.example.com" http://localhost:3000/mcp
# Expected: 403
```

There's an example in the mcp-use monorepo: `pnpm run example:server:dns-rebinding`.

---

## Diagnosis flowchart

```
Connection fails
├─ TCP: can curl reach the port? → no → server not listening / port blocked
├─ HTTP: 404? → wrong path; should be /mcp
├─ HTTP: 400 with body? → check error message: headers, protocol version, session ID
├─ HTTP: 401/403? → auth or DNS rebinding
├─ HTTP: 200 but client says "no tools"? → client didn't send notifications/initialized after init
└─ Hangs forever? → server crashed silently; check MCP_DEBUG_LEVEL=trace logs
```

When all else fails, run `mcp-use start` with `MCP_DEBUG_LEVEL=trace`, run the broken client, and read the wire transcript end-to-end.
