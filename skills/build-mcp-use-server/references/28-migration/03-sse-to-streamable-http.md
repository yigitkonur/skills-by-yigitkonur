# SSE → Streamable HTTP Migration

The MCP transport story moved from SSE-based long-poll to Streamable HTTP. SSE still works for legacy clients but has known proxy issues. New deploys should use Streamable HTTP.

---

## 1. Why migrate

| SSE                                              | Streamable HTTP                                    |
|--------------------------------------------------|----------------------------------------------------|
| One persistent connection per client.            | Standard request/response per RPC.                 |
| Server-Sent Events frame format.                 | JSON-RPC over HTTP POST.                           |
| Drops at ~60s through default proxies (nginx, Cloudflare, ALB). | Works through any HTTP proxy.            |
| Notifications: easy (push down the SSE pipe).    | Notifications: via session-id-keyed stream endpoint. |
| Single endpoint serves both directions.          | Two endpoints: `POST /mcp` for requests, `GET /mcp` (with `Accept: text/event-stream`) for the streaming side. |

For new deploys, prefer Streamable HTTP. mcp-use's `MCPServer` defaults to it.

---

## 2. What stays the same

- All tool, resource, prompt registrations.
- Response helpers (`text()`, `error()`, etc.).
- Session id semantics — `Mcp-Session-Id` header.
- Auth flow.
- JSON-RPC payloads.

You're moving the **transport**, not the protocol.

---

## 3. Server-side

If you're on `mcp-use@^1.x` and call `server.listen()`, you're already on Streamable HTTP. SSE was a separate adapter.

If you wired a custom SSE adapter (rare with mcp-use), remove it:

```typescript
// Old, custom SSE wiring — drop this
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
const transport = new SSEServerTransport("/sse", res);
await server.connect(transport);
```

```typescript
// New
import { MCPServer } from "mcp-use/server";
const server = new MCPServer({ name: "...", version: "1.0.0" });
await server.listen(3000);
```

The endpoint is `/mcp`, not `/sse`. Update client configs.

---

## 4. Client-side

Use the SDK's `StreamableHTTPClientTransport`:

```typescript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";

const transport = new StreamableHTTPClientTransport(new URL("https://your-server.com/mcp"));
const client = new Client({ name: "my-client", version: "1.0.0" }, { capabilities: {} });
await client.connect(transport);
```

Or with mcp-use's high-level client:

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    main: {
      url: "https://your-server.com/mcp",
      transport: "http",
    },
  },
});
```

---

## 5. nginx config — if you're proxying

For SSE, you needed `proxy_buffering off` and a long `proxy_read_timeout`. For Streamable HTTP, you still want a long timeout for the GET-streaming side, but buffering can be on for normal POSTs:

```nginx
server {
    listen 443 ssl http2;
    server_name mcp.example.com;

    ssl_certificate     /etc/letsencrypt/live/mcp.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mcp.example.com/privkey.pem;

    location /mcp {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;

        # Required for the streaming GET side
        proxy_set_header Connection '';
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 24h;

        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

The `proxy_read_timeout 24h` matters — without it, the streaming GET drops at the default 60s. The `proxy_buffering off` is still required for the streaming side; disabling it globally on the location is the simplest correct setup.

For Cloudflare, ensure the route is **not** behind "Always Online" or "Cache Everything" page rules. CF's default proxy idle timeout is fine for Streamable HTTP.

For AWS ALB, set the idle timeout to at least 600s (default is 60s — too short for streaming). Apply at the load balancer attribute level.

---

## 6. Sessions — `Mcp-Session-Id`

Streamable HTTP requires session-id correlation. The server returns `Mcp-Session-Id` on the initial `initialize` response. The client must echo it back as a header on every subsequent request.

If your client doesn't, every request creates a new session — manifests as "tools registered but not visible after first call" or "context lost between calls".

The SDK's `StreamableHTTPClientTransport` handles this automatically. Custom HTTP clients must implement it.

```typescript
// In a custom client
const initRes = await fetch("/mcp", { method: "POST", body: JSON.stringify(initRequest) });
const sessionId = initRes.headers.get("Mcp-Session-Id");

// Subsequent calls must include it
const callRes = await fetch("/mcp", {
  method: "POST",
  headers: { "Mcp-Session-Id": sessionId! },
  body: JSON.stringify(callRequest),
});
```

---

## 7. Stale session 404

Streamable HTTP enforces strict session validity. If the server restarts and loses sessions (in-memory store), clients with the old `Mcp-Session-Id` get **404 Not Found**.

The fix is **not** to keep the old session id alive — it's:

1. Use `RedisSessionStore` so sessions survive restarts.
2. Per the MCP spec, clients should send a fresh `InitializeRequest` on any 4xx for a stale session.

See `27-troubleshooting/01-error-catalog.md` row "404 Not Found after server restart".

---

## 8. CORS

Make sure these headers are exposed to the browser:

```typescript
const server = new MCPServer({
  name: "...", version: "1.0.0",
  cors: {
    origin: ["https://your-client.com"],
    allowMethods: ["GET", "POST", "DELETE", "OPTIONS"],
    allowHeaders: ["Content-Type", "Authorization", "mcp-protocol-version", "mcp-session-id"],
    exposeHeaders: ["mcp-session-id"],
  },
});
```

`mcp-session-id` must be in **both** `allowHeaders` and `exposeHeaders`. Without `exposeHeaders`, the browser-side client can't read the session id off the response.

---

## 9. Verifying the migration

1. Start the server. Confirm logs show Streamable HTTP, not SSE.
2. `curl -i -X POST {url}/mcp -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'` — response should include `Mcp-Session-Id` header.
3. Echo the session id on the next call: `curl -i -X POST {url}/mcp -H "Mcp-Session-Id: <id>" -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'` — should list tools.
4. Open the Inspector, confirm full handshake.
5. Test through your real proxy (nginx, Cloudflare, ALB) — long-running tools should not drop at 60s.

If a long-running tool still drops, the proxy timeout is the cause — see §5.
