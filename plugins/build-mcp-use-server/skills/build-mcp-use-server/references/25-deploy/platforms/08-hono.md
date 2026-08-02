# Hono

*Read this when deploying an MCP server mounted in a Hono application.*

## When to choose Hono

- Framework-first deployment on any Hono-supported runtime (Node, Bun, Cloudflare Workers, Deno, AWS Lambda, etc.)
- MCP server as a mounted subtree within a larger Hono application
- Shared middleware and routing with non-MCP handlers
- Single codebase targeting multiple runtimes

## Handler wiring

Mount `server.fetch` at the MCP route and all nested paths. Hono's context provides the raw fetch request:

```ts
import { Hono } from "hono";
import { MCPServer } from "mcp-use";

const app = new Hono();
const server = new MCPServer({ name: "my-server", version: "1.0.0" });

server.tool({ name: "example", description: "...", inputSchema: { type: "object" } }, () => ({
  type: "text",
  text: "ok"
}));

// Mount MCP server at /mcp and all nested paths (/mcp/*)
app.all("/mcp", (c) => server.fetch(c.req.raw));
app.all("/mcp/*", (c) => server.fetch(c.req.raw));

// Add other Hono routes as needed
app.get("/health", (c) => c.json({ status: "ok" }));

export default app;
```

## Build & deploy commands

```bash
# Build assets with public MCP endpoint
MCP_URL=https://api.example.com/mcp npm run build

# Deploy Hono app for your target runtime (platform varies)
# For Node: npm start
# For Cloudflare: wrangler deploy
# For Deno: deployctl deploy
# For Vercel: automatically detected
```

## Env & assets

- **MCP_URL (build-time):** Public endpoint where MCP server is mounted (e.g., `https://api.example.com/mcp`)
- **MCP_ASSETS_URL (build-time, optional):** If using external CDN, specify asset origin
- **.mcp-use/build/views/:** Served by same `server.fetch` handler (no separate asset routing needed)
- **Runtime env:** PORT, HOST, NODE_ENV as per your selected Hono runtime

## Gotchas

- **Preserve nested paths:** Both `/mcp` and `/mcp/*` must route to `server.fetch` so the `_mcp-use` asset subtree is accessible
- **Request unwrapping:** Use `c.req.raw` to pass the underlying Web-standard Request to `server.fetch`
- **Runtime-specific routing:** Different Hono adapters (Workers, Lambda, Deno) have different deployment models; consult Hono docs for your target
- **Verify after deploy:** Run `mcp-use@beta screenshot --mcp https://api.example.com/mcp --tool <tool-name>` against live endpoint
- **Middleware order:** MCP routes should execute before unrelated middleware that might reject or transform the request
