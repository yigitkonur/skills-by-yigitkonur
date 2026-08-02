# Custom Routes

*Read this to add HTTP routes (health checks, webhooks, metrics, etc.) outside the MCP endpoint.*

## Adding Custom Routes

Use `server.get()`, `server.post()`, `server.put()`, `server.patch()`, `server.delete()`, `server.all()` to add routes. These are standard Hono route handlers.

```typescript
import { MCPServer } from "mcp-use";

const server = new MCPServer({
  name: "api",
  version: "1.0.0",
});

// GET /health
server.get("/health", (c) => c.json({ ok: true }));

// POST /webhook
server.post("/webhook", async (c) => {
  const payload = await c.req.json();
  console.log("Webhook received:", payload);
  return c.json({ received: true }, 201);
});

// Catch-all
server.all("*", (c) => c.text("Not found", 404));
```

## Route Handler Context

Each handler receives a Hono context object `c` with:
- `c.req.path`, `c.req.method`, `c.req.headers`
- `c.req.json()`, `c.req.text()`, `c.req.param(name)`, `c.req.query(name)`
- `c.json(data, status?)`, `c.text(text, status?)`, `c.html(html, status?)`
- `c.header(name, value)`, `c.status(code)`

Standard Hono patterns apply.

## Health Check Endpoint

v2 ships no built-in health endpoint. Add one for container orchestration (Kubernetes, Docker Compose, etc.):

```typescript
server.get("/health", (c) => {
  // Minimal check: return 200 if server is running
  return c.json({
    status: "healthy",
    timestamp: new Date().toISOString(),
  });
});

// For probes that verify tool execution:
server.get("/health/ready", async (c) => {
  try {
    // Test tool availability (example)
    if (!server.app) throw new Error("MCP server not initialized");
    return c.json({ ready: true });
  } catch (err) {
    return c.json({ ready: false, error: String(err) }, 503);
  }
});
```

**Kubernetes example:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: mcp-server
spec:
  containers:
  - name: api
    image: mcp-server:1.0.0
    livenessProbe:
      httpGet:
        path: /health
        port: 3000
      initialDelaySeconds: 10
    readinessProbe:
      httpGet:
        path: /health/ready
        port: 3000
```

## Metrics & Logging Endpoint

```typescript
// GET /metrics (Prometheus format)
server.get("/metrics", (c) => {
  const metrics = `
# HELP mcp_requests_total Total requests
# TYPE mcp_requests_total counter
mcp_requests_total{method="POST"} 42
  `.trim();
  return c.text(metrics);
});

// GET /logs (recent log entries)
server.get("/logs", (c) => {
  return c.json({
    entries: logBuffer.slice(-100),  // last 100 logs
  });
});
```

## Webhook Receiver

```typescript
interface WebhookPayload {
  event: string;
  timestamp: number;
  data: Record<string, unknown>;
}

server.post("/webhook", async (c) => {
  try {
    const payload = await c.req.json() as WebhookPayload;
    
    // Validate signature
    const signature = c.req.header("x-webhook-signature");
    if (!signature || !verifySignature(signature, payload)) {
      return c.json({ error: "Invalid signature" }, 403);
    }
    
    // Process event
    if (payload.event === "tool_enabled") {
      console.log("Tool enabled:", payload.data);
      await server.notifyToolsChanged();
    }
    
    return c.json({ processed: true }, 202);
  } catch (err) {
    return c.json({ error: String(err) }, 400);
  }
});

function verifySignature(signature: string, payload: WebhookPayload): boolean {
  // Implement HMAC verification with your secret
  return true;  // placeholder
}
```

## Mounting Custom Routes Before/After MCP

Routes are Hono routes; they coexist with the MCP endpoint at `basePath`.

```typescript
const server = new MCPServer({
  name: "api",
  version: "1.0.0",
  basePath: "/mcp",
});

// Custom routes (outside /mcp)
server.get("/health", (c) => c.json({ ok: true }));
server.post("/webhook", async (c) => { /* ... */ });

// MCP endpoint at /mcp
// GET /mcp → landing page
// POST /mcp → MCP protocol

// Now:
// GET /health → 200 ok
// POST /mcp → MCP tools/call
// GET /mcp → landing page
```

## Accessing MCP Context from Routes

Custom routes don't have automatic access to MCP context (auth, requestState, etc.). Use middleware if you need to share state:

```typescript
// Middleware sets a variable for all routes
server.use(async (c, next) => {
  c.set("user_id", extractUserFromAuth(c.req.header("authorization")));
  await next();
});

// Custom route reads the variable
server.get("/user-profile", (c) => {
  const userId = c.get("user_id");
  return c.json({ user_id: userId });
});
```

For authenticated MCP operations, use `ctx.auth` (available in tool/resource/prompt callbacks).

## Route Groups & Prefixes (Hono Router)

```typescript
// Hono Router for organization
const admin = new Hono();
admin.get("/users", (c) => c.json([]));
admin.post("/users", (c) => c.json({ created: true }, 201));

// Mount at prefix
server.app.route("/api/admin", admin);

// Now:
// GET /api/admin/users
// POST /api/admin/users
```

See Hono docs for more routing patterns.
