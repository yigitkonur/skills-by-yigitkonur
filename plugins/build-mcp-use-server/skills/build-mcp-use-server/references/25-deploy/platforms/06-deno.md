# Deno Deploy

*Read this when deploying an MCP server to Deno Deploy (edge runtime).*

## When to choose Deno Deploy

- Edge-first deployment model with automatic global distribution
- No persistent filesystem; stateless handler-per-request pattern
- External asset storage required (CDN or object bucket)
- Permissions model: read-only for fixture data, no telemetry write access

## Handler wiring

Deno Deploy is an edge runtime. Export `server.fetch` as the default handler in a `deno.json` or `deployctl`-configured entrypoint:

```ts
import { MCPServer } from "mcp-use";

const server = new MCPServer({ name: "my-server", version: "1.0.0" });
server.tool({ name: "example", description: "...", inputSchema: { type: "object" } }, () => ({
  type: "text",
  text: "ok"
}));

export default server.fetch;
```

## Build & deploy commands

```bash
# Build with public MCP endpoint and external asset CDN
MCP_URL=https://<project>.deno.dev/mcp \
MCP_ASSETS_URL=https://<cdn-origin> \
npm run build

# Deploy code to Deno Deploy; assets to CDN
deployctl deploy --project=<project> server.ts

# Publish .mcp-use/build/views/ to CDN at destination printed by build
```

The build output prints the exact destination path for assets, e.g.:
```
https://<cdn-origin>/mcp/_mcp-use/views/<view-name>/
```

Publish `.mcp-use/build/views/` to your CDN at that prefix.

## Env & assets

- **MCP_URL (build-time):** Public Deno Deploy endpoint (required for view embedding)
- **MCP_ASSETS_URL (build-time):** External CDN origin for `.mcp-use/build/views/`
- **Permissions:** Grant only `--allow-env`, `--allow-net`, `--allow-read` (no write for telemetry)
- **Asset host:** Must allow iframe CORS and CSP requirements for view rendering

## Gotchas

- **No filesystem:** Server cannot read `.mcp-use/build/views/` from disk — assets must be external
- **Asset host CORS:** View iframes require origin + CSP domain whitelisting on CDN
- **Verify after deploy:** Always run `mcp-use@beta screenshot` against live deployment before advertising
- **Session state:** Deno Deploy is stateless (fresh instance per request); maintain state externally (DB, KV store, or client-held via `requestState`)
