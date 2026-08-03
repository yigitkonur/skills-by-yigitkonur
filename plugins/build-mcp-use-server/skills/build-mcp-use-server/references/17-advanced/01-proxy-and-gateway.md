# Proxy and Gateway

*Read this when composing multiple upstream MCP servers into a single endpoint, or routing capabilities through a namespace.*

`server.proxy()` connects to upstream HTTP MCP servers and exposes their tools, resources, and prompts through your endpoint. Keys in the config map automatically namespace proxied capabilities.

## Install the optional client

Proxying requires `@mcp-use/client` v2 as an optional peer. If not installed and you call `server.proxy()`, mcp-use throws an install-command error.

```bash
npm install mcp-use@beta @mcp-use/client@beta
```

## Config-map form

Pass an object mapping upstream identifiers to HTTP connection settings:

```typescript
import { MCPServer } from "mcp-use";

const server = new MCPServer({
  name: "gateway",
  version: "1.0.0",
});

await server.proxy({
  weather: {
    url: "https://weather.example.com/mcp",
  },
  internal: {
    url: "https://internal.example.com/mcp",
    authToken: process.env.INTERNAL_MCP_TOKEN,
    headers: { "User-Agent": "gateway/1.0" },
  },
});

server.tool({ name: "gateway_status" }, async () => ({
  content: [{ type: "text", text: "Gateway running" }],
}));

await server.listen();
```

Keys become namespaces: `weather_forecast`, `internal_handbook`.

**Config fields (ProxyHttpConfig):**
- `url` (required): upstream MCP endpoint
- `authToken?`: bearer token sent as `Authorization: Bearer <token>`
- `headers?`: static headers on every upstream request
- `timeout?`: connection timeout (ms)
- `fetch?`: custom fetch implementation
- `protocolNegotiation?`: `"auto" | "legacy"` or pin via `{ pin: string }`

## Connection form

Pass an existing `MCPConnection` when your app manages the client:

```typescript
import { MCPClient } from "@mcp-use/client";
import { MCPServer } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    database: {
      url: "https://database.example.com/mcp",
      authToken: process.env.DB_MCP_TOKEN,
    },
  },
});

const connection = await client.connect("database");

const server = new MCPServer({ name: "gateway", version: "1.0.0" });
await server.proxy(connection);
await server.listen();
```

Ownership differs: server owns config-supplied connections (closes in `server.close()`); you own explicit connections.

## What is forwarded

- Tool metadata, schemas, calls, structured content, errors, cancellation, progress
- Static resource metadata and reads
- Prompt metadata, argument schemas, requests

## What is NOT forwarded

- Resource templates and completion callbacks
- Subscriptions
- Upstream list-change re-sync
- Legacy push-style sampling/elicitation callbacks

For rich gateway behaviors (combining multiple calls, filtering capabilities, transforming schemas), write a custom server with explicit `server.tool()` calls instead.

## Namespacing and static resource URIs

Proxied static resources are re-exposed under `mcp-use-proxy:///<namespace>/<upstream-uri>` (namespace and the original upstream URI are both `encodeURIComponent`-escaped). The gateway resolves reads through the upstream connection captured at mount time, not by re-parsing this URI. Tool names and prompt names are prefixed with `<upstream>_`.

Call `proxy()` before `listen()` or the first `server.fetch()` request. Failures are best-effort: connection error skips upstream; introspection error skips affected capability kind; name collision skips capability.

## Authentication and lifecycle

Proxy config supports bearer tokens and headers only; not automatic OAuth. Obtain/refresh credentials in your application, then pass them. `server.close()` closes only connections server owns.
