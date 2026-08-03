# Transport Debugging

*Read this when HTTP requests are failing, timing out, or returning unexpected status codes.*

## Checking Server Listener

Verify the server is actually listening on the expected port:

```bash
# While npm run dev is running, in another terminal:
curl -I http://localhost:3000/mcp
# curl -I sends HEAD; the default stateless /mcp endpoint returns 204 No Content for HEAD.
# 404 or connection refused means the server isn't listening at that path/port.
```

If connection refused:
- `npm run dev` is running? Check terminal
- Port correct? Check `package.json` scripts (default 3000) or `--port` flag
- Firewall blocking? On Linux, check `sudo netstat -tulnp | grep 3000`

## Checking CORS (for Remote Clients)

When connecting from a different origin (tunneled, deployed, or different domain):

```bash
# From Inspector at inspector.mcp-use.com, calling your local server
# Browser sends CORS preflight:
curl -X OPTIONS http://localhost:3000/mcp \
  -H "Origin: https://inspector.mcp-use.com" \
  -H "Access-Control-Request-Method: POST" \
  -v
```

Expected response headers (CORS is off by default — this preflight only returns these once `cors: {}` or an explicit `cors` config is set):
```
Access-Control-Allow-Origin: https://inspector.mcp-use.com
Access-Control-Allow-Methods: GET, HEAD, POST, OPTIONS
```

Defaults reflect the request's `Origin` header back rather than sending a literal `*`; `Access-Control-Allow-Methods` defaults to `GET, HEAD, POST, OPTIONS` (no `DELETE`).

If missing:
- Add `cors: {}` to ServerConfig (enables CORS; reflects request `Origin`)
- Or configure explicitly: `cors: { origin: ["https://inspector.mcp-use.com"] }`

See references/08-server-config/03-cors-and-allowed-origins.md.

## Checking Headers

Verify the required `Accept` header is set — every POST needs `application/json` and `text/event-stream` both present, or the server returns `406 Not Acceptable` before it even looks at the body:

```bash
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Protocol-Version: 2024-11-05" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize",...}' \
  -v
```

Check response headers in `-v` output. `Mcp-Protocol-Version` is optional on the request — only sent back / validated when the client sends it. If you get `406`, drop straight to the Accept header before suspecting protocol version.

## Checking Timeout

Tool call takes >10s? Set request timeout in Inspector:

Inspector → **Connection Settings** → `Request timeout` (default 10000ms)

To test with curl:

```bash
time curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call",...}' \
  --max-time 30  # 30 second limit
```

Long-running tools should report progress:

```typescript
async (args, ctx) => {
  for (let i = 0; i < 10; i++) {
    await ctx.reportProgress?.(i, 10, `Processing ${i}...`);
    await sleep(1000);
  }
  return { content: [...] };
}
```

## Debugging POST Stateless Requests

v2 streamable HTTP is stateless. Each POST is independent:

```bash
# All of these are separate, independent calls (each still needs the Accept header above):
curl -X POST http://localhost:3000/mcp -H "Accept: application/json, text/event-stream" -d '{"jsonrpc":"2.0","id":1,"method":"initialize",...}'
curl -X POST http://localhost:3000/mcp -H "Accept: application/json, text/event-stream" -d '{"jsonrpc":"2.0","id":2,"method":"tools/list",...}'
curl -X POST http://localhost:3000/mcp -H "Accept: application/json, text/event-stream" -d '{"jsonrpc":"2.0","id":3,"method":"tools/call",...}'
```

No session header, no connection-level state, and no `notifications/initialized` call required between them. Each handler builds a fresh MCP server from the registry.

If a tool needs state across calls, use `requestState` codec:

```typescript
import { createRequestStateCodec, MCPServer } from "mcp-use";

const stateCodec = createRequestStateCodec<MyStateShape>({
  key: process.env.REQUEST_STATE_SECRET!,  // 32+ bytes
  ttlSeconds: 600,                          // default 600
});

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  requestState: { verify: stateCodec.verify },
});
```

`stateCodec.mint(data)` produces the opaque state string to hand back to the client; `requestState.verify` (wired from `stateCodec.verify`) checks it before handler re-entry. See references/10-sessions/03-state-patterns-without-sessions.md.

## Checking Body Parsing

Verify JSON is being parsed:

```bash
# Malformed JSON (missing closing brace) — Accept header still required, or you'll get 406 instead
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1'
# Should return 400 Bad Request

# Valid JSON but missing required field
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0"}'
# Should return JSON-RPC error with code -32700 (parse error) or -32602 (invalid params)
```

## HTTP Methods

At the default `/mcp` endpoint in v2's stateless mode:
- **POST**: MCP operations (modern or legacy wire)
- **HTML-navigation GET/HEAD** (`Accept: text/html`): landing page or OAuth response at `basePath`
- **Other GET/HEAD and DELETE**: `204 No Content` compatibility probes
- **OPTIONS**: CORS preflight only when `cors` is configured

Custom routes added with `server.get/post/put/patch/delete/all`, `server.app.route(...)` for a Hono sub-app, or `server.use(...)` for middleware can implement their own GET/DELETE handlers (for example, a health check). There is no `server.route()` method. These are separate routes, not the `/mcp` endpoint's own behavior.

Trying PUT or PATCH at `/mcp`? Server returns **405 Method Not Allowed**.

## Network Inspection

Use browser DevTools or Postman to inspect requests/responses:

1. Open browser DevTools → **Network** tab
2. Trigger tool call from Inspector
3. Click the request to `/mcp`
4. See exact headers, request body, response body
5. Check **Timing** tab for server latency

Or use Postman:
- Import curl command (Postman → Import → Raw text, paste curl)
- Edit and re-run
- Full UI inspection of each field

## Checking Deployment vs Local

Deployed server not responding? Verify deployed URL:

```bash
# Before:
curl http://localhost:3000/mcp  # Works

# After deploy: use the exact MCP endpoint from the platform/dashboard.
export MCP_URL="PASTE_THE_EXACT_DEPLOYED_MCP_URL"
curl "${MCP_URL}"  # GET should be 204 on the stateless MCP route; use POST probes for protocol behavior.
```

Check deployment logs:

```bash
mcp-use deployments logs <deployment-id> --follow
```

Common issues:
- Build failed (check build logs)
- Environment variables missing (set via `mcp-use servers env`)
- Port mismatch (deployed server may use different port)

