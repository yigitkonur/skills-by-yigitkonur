# Lifecycle: listen, fetch, and Shutdown

*Read this to understand server startup, deployment models, and graceful shutdown (or lack thereof) in v2.*

## Server Lifecycle States

1. **Constructed:** `new MCPServer(config)` creates instance; does NOT bind or listen
2. **Running:** After `server.listen()` or first `server.fetch()` request; accepts connections
3. **Closed:** After `server.close()`; cannot revive

Once closed, create a new instance to serve again.

## listen(): Node.js HTTP Binding

Starts an HTTP listener on the specified host and port.

```typescript
const server = new MCPServer({
  name: "api",
  version: "1.0.0",
  port: 3000,
});

const { port, url } = await server.listen();
// Listening at http://127.0.0.1:3000/mcp

console.log(`Server at ${url}`);
```

**Return value:** `{ port: number, url: string }`
- `port`: Actual bound port (useful when ephemeral port `0` was requested)
- `url`: Full MCP endpoint URL (e.g., `http://localhost:3000/mcp`)

**Blocking:** `listen()` returns after the socket is bound. The process stays running until you call `server.close()` or the process terminates.

## fetch(): Edge Runtime Handler

For edge runtimes (Vercel, Cloudflare, Deno, etc.), export `server.fetch` directly instead of calling `listen()`.

```typescript
// Default export for edge runtimes
export default server.fetch;

// Or named export for frameworks
export const handler = server.fetch;
```

`server.fetch` is a web-standard Fetch API handler:
```typescript
async (request: Request) => Promise<Response>
```

No socket binding occurs; the platform manages HTTP listeners.

## Node.js Binding from fetch

If you need to run `server.fetch` in Node.js without Hono's `listen()`, use the `mcp-use/node` adapter:

```typescript
import { MCPServer } from "mcp-use";
import { toNodeHandler } from "mcp-use/node";
import * as http from "node:http";

const server = new MCPServer({ name: "api", version: "1.0.0" });

// Convert web handler to Node signature
const handler = toNodeHandler(server);

// Bind to Node HTTP server
const httpServer = http.createServer(handler);
await new Promise<void>((resolve) => {
  httpServer.listen(3000, () => {
    console.log("Listening at http://localhost:3000");
    resolve();
  });
});
```

## Graceful Shutdown

`MCPServer.close(): Promise<void>` aborts in-flight MCP exchanges and stops the HTTP listener. A closed server cannot be revived; create a new instance.

```typescript
const { url } = await server.listen(3000);
console.log(`Listening at ${url}`);

process.on("SIGTERM", async () => {
  await server.close();
});

process.on("SIGINT", async () => {
  await server.close();
});
```

**For edge runtimes:**
- Platforms (Vercel, Cloudflare, Deno) manage shutdown automatically
- No cleanup needed in handler code
- Focus on fast request processing; avoid long-lived connections

**For containerized deployments:**
- Set `terminationGracePeriodSeconds: 30` in Kubernetes
- Rely on OS signal handling to exit cleanly
- Platform tears down the container after grace period

## Stateless Request Model

v2 servers are **stateless by default**: each HTTP request builds a fresh MCP handler from the registry. There is no persistent session or connection state.

```typescript
// Every HTTP request → new handler built from registry
// Handler processes request → discards handler
// Next request → new handler built again
```

This means:
- No in-memory session state across requests
- No graceful session draining needed
- Container restarts/rebalancing don't orphan active connections
- Cold start overhead negligible (registry pre-built)

See `../10-sessions/01-overview-stateless-truth.md` for session details.

## Best Practices

### Development (listen)
```typescript
import { MCPServer } from "mcp-use";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
});

// Register tools, resources, prompts...

const { url } = await server.listen();
console.log(`Serving at ${url}`);

// Stop with Ctrl+C
```

### Production (fetch)
```typescript
import { MCPServer } from "mcp-use";

export default new MCPServer({
  name: "my-server",
  version: "1.0.0",
}).fetch;

// Platform manages HTTP server and shutdown
```

### Next.js (integrated)
```typescript
// mcp-server.ts
import { MCPServer } from "mcp-use";

export default new MCPServer({
  name: "my-app",
  version: "1.0.0",
  basePath: "/api/mcp",
});
```

```typescript
// next.config.ts
import { withMcpUse } from "mcp-use/next";
export default withMcpUse(nextConfig, { entry: "./mcp-server.ts" });
```

### Docker + Railway
```dockerfile
FROM node:22-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
ENV NODE_ENV=production
EXPOSE $PORT
CMD ["npm", "start"]
```

```bash
MCP_URL=https://<service>.up.railway.app/mcp npm run build
```

The `npm start` script calls `server.listen()` and runs forever; Railway sends SIGTERM on shutdown.

## Monitoring & Health Checks

For reliable operation, focus on:
1. **Fast startup:** Pre-build registry at server creation, not per-request
2. **Fast requests:** Keep tool/resource callbacks responsive
3. **Health routes:** Add `/health` endpoint for readiness probes

```typescript
server.get("/health", (c) => c.json({ ok: true }));

// Kubernetes probe
livenessProbe:
  httpGet:
    path: /health
    port: 3000
  initialDelaySeconds: 5
  periodSeconds: 10
```

See `06-custom-routes.md` for health endpoint examples.
