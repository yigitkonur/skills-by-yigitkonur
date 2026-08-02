# Railway

*Read this when deploying an MCP server to Railway.*

## When to choose Railway

- Managed Node.js hosting with automatic scaling
- Filesystem persistence for MCP view assets
- Public endpoint with automatic TLS and custom domain support
- Integrated environment variable and secret management
- Simpler alternative to Docker-only platforms

## Handler wiring

Railway is a Node-compatible filesystem runtime. Export `server.fetch` as the default handler:

```ts
import { MCPServer } from "mcp-use";

const server = new MCPServer({ name: "my-server", version: "1.0.0" });
server.tool({ name: "example", description: "...", inputSchema: { type: "object" } }, () => ({
  type: "text",
  text: "ok"
}));

export default server.fetch;
```

Your `server.fetch` handler will serve both MCP endpoints (`/mcp`) and view assets (`/mcp/_mcp-use/*`) from the same origin.

## Build & deploy commands

```bash
# Build assets with Railway public endpoint
MCP_URL=https://<service>.up.railway.app/mcp npm run build

# Deploy via Railway CLI or git push
railway up

# Or configure in railway.json:
# {
#   "build": { "builder": "nixpacks" },
#   "deploy": { "startCommand": "npm start" }
# }
```

## Env & assets

- **MCP_URL (build-time):** Your Railway service public URL + `/mcp` path (e.g., `https://my-app-prod.up.railway.app/mcp`)
- **PORT (runtime):** HTTP listen port (Railway sets via env; use `process.env.PORT || 3000`)
- **HOST (runtime):** Bind to `0.0.0.0` on Railway (not localhost)
- **.mcp-use/build/:** Must be part of deployed repository (or built during Railway build step)

## Gotchas

- **Endpoint discovery:** Use your actual Railway public URL at build time; preview deploys get different URLs (e.g., `https://my-app-pr-123.up.railway.app`)
- **Build during deploy:** Ensure `npm run build` runs in Railway's build phase, not just locally
- **Static binding:** Views are served from the same `server.fetch` handler via `.mcp-use/build/views/`; no separate static asset configuration needed
- **Verify after deploy:** Run `mcp-use@beta screenshot --mcp https://<service>.up.railway.app/mcp --tool <tool-name>` to capture actual rendered view
- **Session state:** Railway containers may restart; maintain persistent state externally (database, Redis, or client-held via `requestState`)
