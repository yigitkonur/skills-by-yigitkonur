# Debugging Remote Clients Over a Tunnel

When ChatGPT, Claude, or another remote MCP client hits your tunneled server and something breaks, you have three places to look: the **client**, the **tunnel relay**, and the **local server**. Work outward from the closest signal.

---

## 1. Enable Server-Side Trace Logging

Set the debug level before `mcp-use start` / `mcp-use dev`:

```bash
MCP_DEBUG_LEVEL=trace mcp-use start --port 3000 --tunnel
```

`trace` in `mcp-use` request logging includes:

- The compact request line for each non-noisy request.
- Request headers and parsed request body.
- Response headers and response body when the response can be cloned and read.

Lower levels:

| Level | What you see |
|---|---|
| `info` | Compact lines; tool arguments are hidden. |
| `debug` | Compact lines; tool arguments are included. |
| `trace` | Compact lines plus request/response headers and bodies. |

For remote-client debugging, `trace` is almost always the right level — round-trip visibility matters more than log volume.

---

## 2. Map a Remote Call to a Server Log Line

The compact log line prints the MCP method, and `tools/call` includes the tool name. In `debug` and `trace`, tool arguments are also included:

```
[12:00:00.000] sess=abc123 POST /mcp [tools/call: get-weather] args={"city":"Paris"} OK (42ms)
```

When ChatGPT reports "the tool failed" but you can't tell which call:

1. Note the timestamp ChatGPT shows.
2. Grep server logs for that minute.
3. Find the matching method/tool name.
4. At `trace`, read the request body and response body block after the compact line.

---

## 3. Confirm the Tunnel Is Actually Forwarding

Hit the tunnel URL with `curl` from a different machine (or `curl` over IPv6 / from a phone hotspot to bypass local routing):

```bash
curl -i "https://happy-blue-cat.local.mcp-use.run/mcp" \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"curl","version":"0"}}}'
```

You should see:

- HTTP 200 for a successful initialize response.
- An `Mcp-Session-Id` header on a stateful server's first response.
- A JSON body or an SSE event stream.

If `curl` fails:

| Symptom | Likely cause |
|---|---|
| 404 | Wrong path — tunnel forwards `/mcp`, not `/`. |
| 502 / connection refused | Local server isn't listening on the port the tunnel was started against. |
| Timeout | Tunnel expired (24h limit), idle tunnel cleanup ran, or local server crashed. |
| 401 | Your auth middleware blocks the request — see "tunnel auth" below. |

---

## 4. Gate Reverse-Channel Features

Sampling (`ctx.sample()`) and elicitation (`ctx.elicit()`) are reverse-channel calls — server to client. Before calling them from a tunneled server, gate on the client's advertised capabilities.

If a sampling call hangs, the client either:

- Did not declare `sampling` in its capabilities (check with `ctx.client.can("sampling")` before calling).
- Dropped the streaming channel.
- Is waiting on client-side user approval.

Use the same pattern for elicitation: only call `ctx.elicit()` when `ctx.client.can("elicitation")` is true.

---

## 5. Inspect What the Client Sent

`MCP_DEBUG_LEVEL=trace` prints the parsed request body. For `tools/call`, inspect the `params.arguments` and `_meta` fields the client actually sent:

```json
{
  "name": "search",
  "arguments": { "query": "foo", "limit": 10 },
  "_meta": {
    "user": { "subject": "user_xyz", "locale": "en-US", "location": { ... } }
  }
}
```

If `_meta.user` is missing, that is client behavior. Treat `ctx.client.user()` as optional request metadata, not identity proof.

Add a one-line tool to surface what the server actually sees:

```typescript
server.tool(
  { name: "_debug_caller", schema: z.object({}) },
  async (_p, ctx) => object({
    clientInfo: ctx.client.info(),
    capabilities: ctx.client.capabilities(),
    user: ctx.client.user(),
    auth: ctx.auth ? { userId: ctx.auth.user.userId } : null,
    session: ctx.session.sessionId,
  })
);
```

Call it from the remote client to confirm client metadata and authenticated identity are reaching the server.

---

## 6. Streaming-Specific Failures

For streaming responses, distinguish a tunnel problem from a client capability or local-server problem:

| Symptom | Cause | Fix |
|---|---|---|
| Client disconnects after inactivity | Tunnel idle cleanup or client-side timeout | Recreate the tunnel and retry with a shorter tool response. |
| Notifications never arrive | Client does not support or subscribe to the needed capability | Check `ctx.client.can(...)` before sending server-initiated work. |
| Long tool responses truncate | Intermediary buffering or local server crash | Test from another network and inspect `MCP_DEBUG_LEVEL=trace` output. |

---

## 7. Common Failure Patterns

| Symptom | Where to look | Likely fix |
|---|---|---|
| ChatGPT "tool not found" | Server tool registration | Confirm `await server.proxy(...)` finished before `listen()`; check trace for `tools/list` response. |
| 401 from tunnel URL | Auth middleware | Bypass auth for the tunnel during dev, or pass the right header. |
| Tool runs, response empty | Response shape | Use `text()` / `object()` / `error()` helpers — don't return raw strings. |
| Tunnel URL works in `curl`, fails in ChatGPT | Capabilities mismatch | Check `_debug_caller` output; ensure the protocol version matches. |
| Sampling never returns | Client capabilities | Gate with `ctx.client.can("sampling")` before calling. |
| Random 502s | Local server crashed | Trace log shows the unhandled exception; fix and restart. |

---

## 8. Quick Diagnostic Script

```bash
# Run before suspecting the tunnel itself

# 1. Reachability
curl -sI "https://happy-blue-cat.local.mcp-use.run/mcp" | head -1

# 2. Initialize handshake
curl -s -X POST "https://happy-blue-cat.local.mcp-use.run/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"diag","version":"0"}}}' \
  | head -50

# 3. List tools (after capturing the Mcp-Session-Id from above)
curl -s -X POST "https://happy-blue-cat.local.mcp-use.run/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: paste-from-initialize-response" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'
```

If steps 1–3 succeed from `curl` but the remote client fails, the problem is on the client side (capabilities, auth, headers), not the tunnel.

---

## 9. See Also

- **Trace-level logging configuration** → `../15-logging/01-overview.md`
- **Inspector for protocol-level debugging** → `../20-inspector/01-overview.md`
- **`ctx.client.*` capabilities** → `../16-client-introspection/01-overview.md`
- **Transport debugging tactics** → `../23-debug/04-transport-debugging.md`
