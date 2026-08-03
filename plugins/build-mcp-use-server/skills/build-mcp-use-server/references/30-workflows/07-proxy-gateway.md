# Workflow: Proxy Gateway

*Read this for an end-to-end workflow: expose upstream MCP tools through one server.*

## Steps

### 1. Scaffold

```bash
npx create-mcp-use-app@2.0.0-beta.14 gateway --template blank --npm --install
cd gateway
```

**Verify:** The blank server starts with `npm run dev`.

### 2. Install the Optional Client Peer

```bash
npm install @mcp-use/client
```

**Verify:** `npm ls @mcp-use/client` prints the installed package.

### 3. Configure Proxy Targets

Use the config-map form documented in `../17-advanced/01-proxy-and-gateway.md`. Supply only URLs and credentials verified for your upstream servers.

```typescript
import { MCPServer } from "mcp-use";

const server = new MCPServer({
  name: "gateway",
  version: "1.0.0",
});

await server.proxy({
  weather: {
    url: process.env.WEATHER_MCP_URL!,
  },
  private: {
    url: process.env.PRIVATE_MCP_URL!,
    headers: {
      Authorization: `Bearer ${process.env.PRIVATE_MCP_TOKEN}`,
    },
  },
});

export default server;
```

Never call `server.listen()` here — the CLI (`mcp-use dev`/`mcp-use start`) owns the listener.

**Verify:** `npm run typecheck` passes after setting all referenced environment variables.

### 4. Start and Inspect

```bash
WEATHER_MCP_URL=https://weather.example.com/mcp \
PRIVATE_MCP_URL=https://private.example.com/mcp \
PRIVATE_MCP_TOKEN=replace-me \
npm run dev
```

Open `http://127.0.0.1:3000/mcp/inspector` and connect to the local endpoint.

**Verify:** `tools/list`, `resources/list`, and `prompts/list` expose upstream entries under their configured namespaces.

### 5. Call Through the Gateway

Select one proxied tool from each namespace and supply valid arguments.

**Verify:** Each call returns the upstream result; the private target receives the configured authorization header.

### 6. Build and Deploy

```bash
npm run build
mcp-use deploy \
  --env WEATHER_MCP_URL=https://weather.example.com/mcp \
  --env PRIVATE_MCP_URL=https://private.example.com/mcp \
  --env PRIVATE_MCP_TOKEN=replace-me
```

**Verify:** Connect Inspector to the deployed MCP URL and repeat both tool calls.

## Boundaries

The proxy surface does not forward every protocol feature. Review unsupported forwarding and connection-form options before relying on notifications, subscriptions, or upstream auth flows. Read `../17-advanced/01-proxy-and-gateway.md` and `../17-advanced/02-proxy-auth-and-namespacing.md`.
