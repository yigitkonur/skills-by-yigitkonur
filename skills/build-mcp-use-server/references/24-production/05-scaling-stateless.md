# Scaling and stateless request model

*Read this when deploying to multiple instances, serverless platforms, or optimizing cold-start latency.*

v2 is stateless: each HTTP request builds a fresh MCP server from the registry, processes one MCP operation, and exits. No session state persists between requests. This enables horizontal scaling without sticky sessions or distributed state stores (which are not shipped in beta.66 anyway).

## Request-per-operation model

Every MCP operation (tool call, resource read, prompt fetch) is a **fresh transaction**:

```
HTTP POST /mcp
  → MCPServer constructed from registry
  → JSON-RPC request parsed
  → Tool callback invoked
  → Result serialized
  → Response sent
  → MCPServer discarded
  ← HTTP 200
```

No state persists between requests. Clients reconnect and re-initialize on every interaction (or poll for updates).

## Stateless advantages

1. **Horizontal scale:** Deploy N identical instances; any instance can handle any request. No session affinity needed.
2. **Serverless-friendly:** Cold starts rebuild the registry once per invocation; no shared state to warm up.
3. **Restart-safe:** Killing an instance does not lose session data; clients reconnect to another instance.
4. **Resource-efficient:** No long-lived connections, memory leaks from dangling sessions, or TTL management.

## Cold starts and lazy initialization

Serverless platforms (Vercel, Cloud Run) incur cold-start latency (100–2000ms) on the first invocation after deploy. The MCP registry builds during server construction; defer expensive initialization:

```typescript
import { MCPServer } from "mcp-use";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
});

// ❌ Slow: initializes on every request
// const db = await connectDatabase();

// ✅ Lazy: initializes once, on first use
let db: Database | null = null;
async function getDb() {
  if (!db) {
    db = await connectDatabase();
  }
  return db;
}

server.tool(
  {
    name: "get-user",
    description: "Fetch a user by ID",
    inputSchema: z.object({ id: z.string() }),
  },
  async ({ id }, ctx) => {
    const database = await getDb();  // Lazy init
    const user = await database.users.get(id);
    return {
      content: [{ type: "text", text: JSON.stringify(user) }],
    };
  }
);

await server.listen(3000);
```

On cold start, the first request pays the connection cost; subsequent requests (on the same container/worker) reuse the connection.

## Horizontal scaling without session state

Deploy the same server to multiple instances (Kubernetes, Railway, multi-container Cloud Run):

```bash
# Kubernetes: 3 replicas, any instance handles any request
kubectl set image deployment/my-server my-server=my-server:v1.2.3
kubectl scale deployment my-server --replicas 3

# No session affinity needed; load balancer routes freely
```

Stateless MCP means:
- No session data to sync across replicas
- No "sticky session" configuration required
- Clients re-initialize on each new request (not visible; happens transparently)

## External state and databases

Business state (users, products, inventory) **lives outside the MCP server**, in a database or external service:

```typescript
server.tool(
  {
    name: "update-user",
    description: "Update user profile",
    inputSchema: z.object({
      id: z.string(),
      name: z.string(),
    }),
  },
  async ({ id, name }, ctx) => {
    // State is in the database; MCP server is stateless
    await db.users.update(id, { name });
    return {
      content: [{ type: "text", text: `Updated user ${id}` }],
    };
  }
);
```

All instances read/write to the same database; MCP server is just a transport layer.

## Input round-trips and request state

When using `input_required` (elicitation), the client echoes back the request in a second call. Use `requestState` codec to carry round-trip state securely:

```typescript
import { createRequestStateCodec, inputRequired } from "mcp-use";

const codec = createRequestStateCodec({
  secret: process.env.REQUEST_STATE_SECRET,
  algorithm: "sha256",
});

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  requestState: codec.verify,
});

server.tool(
  { name: "auth-form", /* ... */ },
  async (params, ctx) => {
    if (!ctx.inputResponses) {
      // First call: no user input yet
      return inputRequired(
        { state: { userId: "user-123" } },  // Encoded in request
        {
          form: [
            {
              type: "text",
              name: "password",
              label: "Enter password",
              required: true,
            },
          ],
        }
      );
    }
    // Second call: state decoded + verified, user input available
    const password = ctx.inputResponses.password;
    const userId = ctx.requestState?.userId;  // Verified by codec
    // ...
  }
);
```

The codec signs `requestState`; tampering is detected and rejected. State survives the round-trip across potentially different instances.

## No graceful shutdown for serverless

**Serverless runtimes (Vercel, Cloud Run, Lambda):** Functions exit after returning the response. No persistent connections to drain or streams to close. Call `server.close()` before exiting if you want, but it's not required; the platform kills the process.

```typescript
// Optional; not required in serverless
process.on("SIGTERM", async () => {
  await server.close();
  process.exit(0);
});
```

**Long-running runtimes (Railway, Fly, Bun):** Node.js processes can listen for `SIGTERM` and close cleanly. Since v2 has no session state, closing just needs to stop the HTTP listener:

```typescript
const { port, url } = await server.listen(3000);
process.on("SIGTERM", async () => {
  console.log("Shutting down...");
  await server.close();
  process.exit(0);
});
```

No need to drain in-flight requests or replay queued notifications (stateless model has neither).

## Monitoring and tracing

Use structured logging and event listeners to monitor multi-instance deployments:

```typescript
server.on("mcp:*", async (ctx) => {
  const traceId = ctx.request?.header("x-trace-id") || generateId();
  await metrics.record({
    traceId,
    method: ctx.request?.method,
    path: ctx.request?.path,
    duration: Date.now() - ctx.startTime,
    instance: process.env.HOSTNAME,  // Identifies which replica
  });
});
```

Logs from all instances flow to a central log aggregator (Datadog, CloudWatch, Stackdriver); correlate by `traceId` or `requestId`.

See `references/15-logging/` and `references/25-deploy/` for platform-specific observability.

## Resource limits

Stateless servers are **CPU and I/O bound**, not memory bound (no session accumulation). Set platform limits accordingly:

| Platform | Memory | CPU | Timeout | Notes |
|----------|--------|-----|---------|-------|
| Vercel Functions | 3GB max | Shared | 30s cold, 900s warm | Cold start pays startup cost |
| Cloud Run | 8GB max | Shared | 900s default | Set `--memory` to match workload |
| Lambda | 10GB max | Proportional | 900s default | ARM64 for cost savings |
| Railway | Unlimited (metered) | Vmetered | Platform-managed | Vertical scaling available |

Keep timeout > max tool duration + buffer (e.g., tool timeout 25s → function timeout 30s).
