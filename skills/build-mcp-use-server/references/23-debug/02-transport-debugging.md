# Transport Debugging

*Read this when HTTP requests are failing, timing out, or returning unexpected status codes.*

## Checking Server Listener

Verify the server is actually listening on the expected port:

```bash
# While npm run dev is running, in another terminal:
curl -I http://localhost:3000/mcp/
# Should return HTTP 200 or 405 (OPTIONS pre-flight), not 404 or connection refused
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

Expected response headers:
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: POST, GET, DELETE, OPTIONS
```

If missing:
- Add `cors: {}` to ServerConfig (enables CORS with defaults)
- Or configure explicitly: `cors: { origin: ["https://inspector.mcp-use.com"] }`

See references/08-server-config/03-cors-and-allowed-origins.md.

## Checking Headers

Verify v2 protocol header is set:

```bash
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Protocol-Version: 2024-11-05" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize",...}' \
  -v
```

Check response headers in `-v` output. If `Mcp-Protocol-Version` header is missing in response, server may not recognize it.

## Checking Timeout

Tool call takes >10s? Set request timeout in Inspector:

Inspector → **Connection Settings** → `Request timeout` (default 10000ms)

To test with curl:

```bash
time curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
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
# All of these are separate, independent calls:
curl -X POST http://localhost:3000/mcp -d '{"jsonrpc":"2.0","id":1,"method":"initialize",...}'
curl -X POST http://localhost:3000/mcp -d '{"jsonrpc":"2.0","id":2,"method":"tools/list",...}'
curl -X POST http://localhost:3000/mcp -d '{"jsonrpc":"2.0","id":3,"method":"tools/call",...}'
```

No session header, no connection-level state. Each handler builds fresh MCP server from registry.

If a tool needs state across calls, use `requestState` codec:

```typescript
const codec = createRequestStateCodec(encodeState, decodeState);
const server = new MCPServer({
  name: "my-server",
  requestState: codec.verify
});
```

See references/10-sessions/03-state-patterns-without-sessions.md.

## Checking Body Parsing

Verify JSON is being parsed:

```bash
# Malformed JSON (missing closing brace)
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1'
# Should return 400 Bad Request

# Valid JSON but missing required field
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0"}'
# Should return JSON-RPC error with code -32700 (parse error) or -32602 (invalid params)
```

## HTTP Methods

v2 supports:
- **POST**: Tool calls, prompts/list, resources/list, initialize
- **GET**: Resource reads, health checks (if custom route added)
- **DELETE**: Cleanup (for custom routes)
- **OPTIONS**: CORS preflight

Trying PUT or PATCH? Server returns **405 Method Not Allowed**.

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

# After deploy:
curl https://my-server.deploy.mcp-use.com/mcp  # Hangs or 500?
```

Check deployment logs:

```bash
mcp-use deployments logs <deployment-id> --follow
```

Common issues:
- Build failed (check build logs)
- Environment variables missing (set via `mcp-use servers env`)
- Port mismatch (deployed server may use different port)

