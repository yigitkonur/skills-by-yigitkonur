# Health checks and custom routes

*Read this when adding readiness checks, liveness probes, or custom HTTP endpoints in production.*

The MCP endpoint is mounted at `basePath` (default `/mcp`). Health checks and other HTTP routes live elsewhere on `server.app` (the underlying Hono instance). Platforms use these routes for liveness/readiness probes before routing traffic.

## Adding a health route

```typescript
import { MCPServer } from "mcp-use";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
});

// Readiness probe: dependencies initialized
let isReady = false;

(async () => {
  await initializeDatabase();
  await warmUpCache();
  isReady = true;
})();

// Health endpoint
server.get("/health", (c) => {
  if (!isReady) {
    return c.json(
      { status: "not-ready", reason: "dependencies initializing" },
      503
    );
  }
  return c.json({ status: "ok", timestamp: new Date().toISOString() });
});

// Liveness probe (always returns 200)
server.get("/alive", (c) => {
  return c.json({ status: "alive" });
});

await server.listen(3000);
```

Hono's `c.status(code)` returns `void` and is not chainable — pass the status code as `c.json(data, statusCode)` instead of `c.status(code).json(data)`.

## Containerized platforms (Cloud Run, Kubernetes)

Set up probes in your platform configuration:

**Cloud Run (deploy arguments):**
```bash
gcloud run deploy my-server \
  --port 3000 \
  --timeout 30 \
  --health-check-path /health \
  --health-check-interval 10 \
  --health-check-timeout 5 \
  --health-check-unhealthy-threshold 3
```

Deployment docs reference platform-specific probe setup; see `references/25-deploy/` for your platform.

**Kubernetes manifest:**
```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 3000
  initialDelaySeconds: 5
  periodSeconds: 10
livenessProbe:
  httpGet:
    path: /alive
    port: 3000
  initialDelaySeconds: 15
  periodSeconds: 20
```

## Custom routes

Add any Hono middleware or route handler to `server.app`:

```typescript
// Metrics endpoint
server.get("/metrics", (c) => {
  return c.text(`
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total 42
  `);
});

// Config endpoint (public, no auth)
server.get("/config", (c) => {
  return c.json({
    apiVersion: "1.0.0",
    features: ["search", "suggest"],
  });
});

// POST custom webhook
server.post("/webhooks/sync", async (c) => {
  const body = await c.req.json();
  await syncExternalData(body);
  return c.json({ ack: true });
});
```

## Startup and shutdown

v2 has **no graceful-shutdown ceremony** needed for serverless runtimes:

- **Serverless (Vercel, Cloud Run, Lambda):** Function terminates when request completes; no persistent connections to drain. Return HTTP 200 cleanly.
- **Node.js long-running (Railway, Bun, Fly):** Catch `SIGTERM` and close the server, but the MCP protocol is stateless so clients reconnect without state recovery:

```typescript
const { port, url } = await server.listen(3000);
console.log(`Listening at ${url}`);

process.on("SIGTERM", async () => {
  console.log("SIGTERM received, closing server...");
  await server.close();
  process.exit(0);
});
```

No session or stream state exists in v2.0.0-beta.66, so shutdown only needs to close the HTTP listener, not drain in-flight streams or replay queued notifications. Clients simply issue their next independent request; modern-wire clients perform no `initialize` handshake, and any long-lived `subscriptions/listen` stream ends with the listener.

## Latency considerations

- **Cold starts (serverless):** MCP server instantiates fresh per request; no startup time between requests, but platform cold-start adds 100–2000ms latency on first invocation.
- **Lazy initialization:** Defer heavy clients (database pool, external SDK) until first use (see `references/24-production/05-scaling-stateless.md`).
- **Health endpoint latency:** Respond in <100ms; avoid database queries in readiness checks.

## Monitoring

Use HTTP middleware to instrument routes:

```typescript
server.use("*", async (c, next) => {
  const start = Date.now();
  await next();
  const ms = Date.now() - start;
  c.header("x-response-time", `${ms}ms`);
});
```

Attach to MCP events for operation-level insights. The read-only observer context has no built-in timing fields (no `ctx.startTime`/`ctx.endTime`) — track elapsed time manually with `mcp:tools/call` middleware, which wraps the actual handler call:

```typescript
server.use("mcp:tools/call", async (ctx, next) => {
  const start = Date.now();
  const result = await next();
  console.log(`[${ctx.params.name}] ${Date.now() - start}ms`);
  return result;
});
```

See `references/15-logging/03-server-and-request-logging.md` and `references/25-deploy/` for platform-specific observability setup.
