# Bun

*Read this when deploying an MCP server using Bun as the runtime.*

## When to choose Bun

- Node.js-compatible runtime with native binary performance
- Filesystem persistence — deploy `.mcp-use/build` with server on same system
- Single binary deployment model
- Local development and production on same filesystem

## Handler wiring

Bun is Node-compatible. Export `server.fetch` directly or wrap it in a Bun HTTP handler:

```ts
import { MCPServer } from "mcp-use";

const server = new MCPServer({ name: "my-server", version: "1.0.0" });
server.tool({ name: "example", description: "...", inputSchema: { type: "object" } }, () => ({
  type: "text",
  text: "ok"
}));

export default server.fetch;
```

Or with explicit Bun server binding:

```ts
const port = process.env.PORT || 3000;
Bun.serve({
  port,
  fetch(request) {
    return server.fetch(request);
  }
});
```

## Build & deploy commands

```bash
# Build assets with public endpoint
MCP_URL=https://api.example.com/mcp npm run build

# Run server (Bun auto-discovers server.ts or bun-server.ts)
bun run src/server.ts

# Or deploy via containerization / platform
bun build --target=bun src/server.ts --outdir=dist
bun start  # invokes dist/server.js
```

## Env & assets

- **MCP_URL (build-time):** Public endpoint for view embedding
- **PORT (runtime):** HTTP listen port (default 3000)
- **HOST (runtime):** Bind address (default 127.0.0.1; use 0.0.0.0 for deployed)
- **.mcp-use/build/:** Must be co-deployed with server on same filesystem

## Gotchas

- **Filesystem requirement:** Server reads `.mcp-use/build/views/` from disk; ensure build output is part of deployment
- **Verify after build:** Call `mcp-use@beta screenshot` against deployed endpoint; HTTP 200 alone does not validate streamable MCP or rendered views
- **Session state:** Bun follows Node stateless pattern (fresh instance per request); maintain external state if multi-instance
- **Binary size:** Bun is a single binary; no separate runtime installation needed
