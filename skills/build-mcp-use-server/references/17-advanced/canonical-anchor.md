# Canonical Example: Proxy Gateway with Multi-Tenant Auth

*The canonical example for the 17-advanced cluster, referenced by other clusters. End-to-end proxy gateway with bearer token passthrough and resource URIs.*

## Complete server

```typescript
import { MCPServer } from "mcp-use";

const server = new MCPServer({
  name: "multi-api-gateway",
  version: "1.0.0",
  basePath: "/mcp",
});

// Proxy two upstream servers with independent auth
await server.proxy({
  users: {
    url: process.env.USERS_API_URL || "https://users.example.com/mcp",
    authToken: process.env.USERS_API_TOKEN,
    timeout: 5000,
  },
  billing: {
    url: process.env.BILLING_API_URL || "https://billing.example.com/mcp",
    authToken: process.env.BILLING_API_TOKEN,
    timeout: 5000,
  },
});

// Local health tool
server.tool(
  { name: "gateway_health" },
  async () => ({
    content: [
      {
        type: "text",
        text: JSON.stringify({ status: "ok", upstreams: 2 }),
      },
    ],
  })
);

await server.listen();
```

## Environment

```bash
# .env
USERS_API_URL=https://users.example.com/mcp
USERS_API_TOKEN=sk-users-xxx

BILLING_API_URL=https://billing.example.com/mcp
BILLING_API_TOKEN=sk-billing-yyy

PORT=3000
MCP_URL=http://localhost:3000
```

## Calling the gateway

Clients connect to `http://localhost:3000/mcp` and see:

- `users_listUsers`, `users_getUserById` (from upstream `users` server)
- `billing_getInvoices`, `billing_createInvoice` (from upstream `billing` server)
- `gateway_health` (local tool)

Each upstream tool is namespaced with its config key. Static resources use `mcp-use-proxy://users/...` URIs.

## Features demonstrated

1. **Multi-upstream proxy** — two independent upstreams (lines 12–25)
2. **Bearer auth passthrough** — tokens read from env (lines 15, 20)
3. **Timeout config** — 5-second connection timeout (lines 16, 21)
4. **Local tools** — gateway-specific tools alongside proxied (lines 28–37)
5. **Port + base URL** — environment-driven config (lines 39)

## Testing with inspector

```bash
npm run dev
# Inspector: http://localhost:3000/mcp/inspector
# Tools tab shows: users_*, billing_*, gateway_health
```

## Testing with curl

```bash
# Call a proxied tool via gateway
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": { "name": "users_listUsers", "arguments": {} }
  }'
```

## Key constraints

- **Call proxy() before listen()** — introspection happens at startup
- **No OAuth bridge** — tokens are static; refresh in your app if needed
- **Namespace collision prevention** — use distinct upstream keys to avoid tool name conflicts
- **No resource template forwarding** — static resources only (subscriptions not supported)
