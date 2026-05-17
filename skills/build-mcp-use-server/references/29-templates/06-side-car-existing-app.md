# Template: Side-Car Alongside an Existing App

Run MCP next to an existing Express (or Fastify, or any HTTP service) on a separate port. Because `MCPServer` is its own self-contained Hono application with its own listener, the idiomatic pattern is to start it on its own port — not to mount it as middleware inside another framework.

## Layout

```
multi-service-app/
└── src/
    ├── api.ts       # Existing Express (or Fastify, etc.) on :3000
    └── mcp.ts       # MCP server on :3001
```

## `src/mcp.ts`

```typescript
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";

export async function startMCPServer(port = 3001) {
  const server = new MCPServer({
    name: "sidecar-mcp",
    version: "1.0.0",
    description: "MCP side-car alongside the main HTTP API",
  });

  // Custom REST routes — MCPServer IS a Hono app.
  server.get("/api/status", (c) => c.json({ status: "ok" }));

  server.tool(
    {
      name: "ping",
      description: "Health check",
      schema: z.object({}),
    },
    async () => text("pong")
  );

  await server.listen(port);
  console.log(`MCP server running on http://localhost:${port}/mcp`);
}
```

## `src/api.ts`

```typescript
import express from "express";
import { startMCPServer } from "./mcp.js";

const app = express();
const PORT = 3000;

// Existing Express routes — untouched.
app.get("/", (_req, res) => res.send("Hello from Express"));
app.get("/api/legacy", (_req, res) => res.json({ source: "express" }));

app.listen(PORT, () => {
  console.log(`Express API on http://localhost:${PORT}`);
});

// Start MCP on its own port. Failures here must not crash the main API.
startMCPServer(3001).catch((err) => {
  console.error("MCP failed to start:", err);
});
```

## `package.json` (excerpt)

```json
{
  "type": "module",
  "scripts": {
    "dev": "tsx src/api.ts",
    "build": "tsc",
    "start": "node dist/api.js"
  },
  "dependencies": {
    "express": "^4.19.0",
    "mcp-use": "^1.21.5",
    "zod": "^4.0.0"
  },
  "devDependencies": {
    "@types/express": "^4.17.0",
    "tsx": "^4.0.0",
    "typescript": "^5.5.0"
  }
}
```

## Run

```bash
npm install
npm run dev
# Express:    http://localhost:3000/
# MCP:        http://localhost:3001/mcp
# MCP status: http://localhost:3001/api/status
```

## Why a separate port

`MCPServer.listen()` boots its own Hono HTTP server. Mounting MCP into Express/Fastify as middleware fights both routers and breaks SSE streaming for Streamable HTTP. The two-port pattern keeps each framework in its lane and lets you scale them independently.

If you genuinely need a single listener, do the inverse: keep `MCPServer` as the host and add Express-style routes on it via `server.get()`, `server.post()`, `server.use()`. See `../17-advanced/` for the Hono passthrough patterns.

## Reverse proxy

In production, put nginx (or your CDN) in front and route by path:

```nginx
location /mcp {
  proxy_pass http://localhost:3001;
  proxy_http_version 1.1;
  proxy_set_header Connection '';
  proxy_buffering off;        # required for SSE
  chunked_transfer_encoding on;
}

location / {
  proxy_pass http://localhost:3000;
}
```

## See also

- Custom routes/middleware on the MCP server itself: `../17-advanced/`
- Production hardening: `../24-production/`
- Multi-server proxy (one MCP fronting many): `../30-workflows/06-multi-server-proxy-gateway.md`
