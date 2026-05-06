# Add MCP to an Existing App

Run `mcp-use` alongside an existing Express / Fastify / Hono / Next.js app. **Do not** mount it as middleware — `MCPServer` is itself a Hono application that owns its own HTTP listener, sessions, SSE streams, CORS, and Inspector. The supported pattern is a side-car on a separate port.

## Why side-car, not middleware

`MCPServer.listen()` binds its own port. There is no `app.use(mcpServer.middleware())` or `mcpServer.handler()` that returns an Express middleware. Attempting to wire the internal Hono routes into another framework ends up bypassing session management, SSE fan-out, and the Inspector.

If you need REST endpoints alongside MCP, add them **on the `MCPServer` instance** (which is a Hono app — `server.get()`, `server.post()`, `server.use()`) instead of mounting the MCP server inside another framework.

## Layout

```
multi-service-app/
├── src/
│   ├── api.ts          # Existing Express/Fastify/etc. on port 3000
│   └── mcp-server.ts   # MCP on port 3001
├── package.json
└── tsconfig.json
```

Use `src/mcp-server.ts` (not `src/server.ts`) when the app already owns `src/server.ts` or `src/index.ts`. This avoids colliding with the existing host bootstrap and keeps MCP code isolated.

## `src/mcp-server.ts`

```ts
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";

export async function startMCPServer(port = 3001) {
  const server = new MCPServer({
    name: "sidecar-mcp",
    version: "1.0.0",
  });

  // Custom REST endpoints live on the same MCPServer (it IS a Hono app)
  server.get("/api/status", (c) => c.json({ status: "ok" }));

  server.tool(
    { name: "ping", schema: z.object({}) },
    async () => text("pong"),
  );

  await server.listen(port);
  console.log(`MCP on http://localhost:${port}/mcp`);
}
```

## `src/api.ts`

```ts
import express from "express";
import { startMCPServer } from "./mcp-server.js";

const app = express();
const PORT = 3000;

app.get("/", (_, res) => res.send("Hello from Express"));

app.listen(PORT, () => {
  console.log(`Express API on http://localhost:${PORT}`);
});

startMCPServer(3001).catch((e) => {
  console.error("MCP server failed", e);
  process.exit(1);
});
```

## Scripts

```json
{
  "scripts": {
    "dev": "mcp-use dev src/mcp-server.ts",
    "dev:api": "tsx watch src/api.ts",
    "dev:all": "concurrently -n api,mcp \"npm:dev:api\" \"npm:dev\""
  }
}
```

`mcp-use dev` always points at the MCP entry. The host app uses its own runner.

## Connecting clients

| Client | URL |
|---|---|
| Local MCP client | `http://localhost:3001/mcp` |
| Existing app | `http://localhost:3000` |

## Reverse proxy

In production, route both ports through one public domain:

```nginx
location /mcp { proxy_pass http://localhost:3001; }
location /     { proxy_pass http://localhost:3000; }
```

Set `MCP_URL=https://your-domain.com` so widget asset URLs resolve correctly behind the proxy.

## Not supported

| Pattern | Why it fails |
|---|---|
| `app.use("/mcp", mcpServer.handler())` | No such handler is exposed publicly. |
| Reusing one HTTP server with `app.use(mcpHonoApp)` | Bypasses session store, SSE manager, Inspector. |
| Embedding inside Next.js API routes | Use the dedicated handler pattern in `19-nextjs-drop-in/` instead. |

For Next.js drop-in (which is supported via `getHandler()`-style adapters), see `19-nextjs-drop-in/`.
