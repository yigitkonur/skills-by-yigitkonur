# Scaling and stateless request model

*Read this when deploying to multiple instances, serverless platforms, or optimizing cold-start latency.*

v2 is stateless: ordinary HTTP operations build a request-scoped MCP server from the registry, process one operation, and finish without durable session state. The deliberate exception is a client-initiated `subscriptions/listen` POST whose response remains open to receive matching notifications; it still has no session affinity, backlog, or server-side session store.

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

No state persists between ordinary operations. Modern-wire clients send self-describing operations without `initialize`; legacy compatibility clients may issue stateless initialize requests. Active `subscriptions/listen` connections remain attached to the instance handling that listener until the stream closes.

## Stateless advantages

1. **Horizontal scale:** Deploy N identical instances; any instance can handle any request. No session affinity needed.
2. **Serverless-friendly:** Cold starts rebuild the registry once per invocation; no shared state to warm up.
3. **Restart-safe:** Killing an instance does not lose session data; clients reconnect to another instance.
4. **Bounded streams:** Ordinary operations do not leave dangling sessions. `subscriptions/listen` connections are intentionally long-lived, so account for active-stream memory, platform timeouts, reconnects, and instance-local delivery.

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
- Each HTTP operation is independent: modern `2026-07-28` clients send self-describing requests with no `initialize` handshake at all, while legacy compatibility clients may issue a stateless `initialize` per connection

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
import { acceptedContent, createRequestStateCodec, inputRequired } from "mcp-use";
import { z } from "zod";

const passwordSchema = z.object({
  password: z.string().min(1).describe("Password"),
});

const codec = createRequestStateCodec<{ userId: string }>({
  key: process.env.REQUEST_STATE_SECRET!,  // 32+ bytes
});

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  requestState: { verify: codec.verify },
});

server.tool(
  { name: "auth-form", /* ... */ },
  async (_params, ctx) => {
    const response = acceptedContent(ctx.inputResponses, "password", passwordSchema);
    if (response === undefined) {
      // First call: request typed input and mint trusted workflow state.
      return inputRequired({
        inputRequests: {
          password: inputRequired.elicit({
            message: "Enter your password",
            requestedSchema: passwordSchema,
          }),
        },
        requestState: await codec.mint({ userId: "user-123" }),
      });
    }

    // Re-entry: the framework verified and decoded requestState first.
    const state = ctx.requestState<{ userId: string }>();
    const userId = state?.userId;
    const password = response.password;
    // ...
  }
);
```

The codec signs `requestState`; tampering is detected and rejected. State survives the round-trip across potentially different instances (as long as every instance shares the same `key`).

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

Use structured logging and event listeners to monitor multi-instance deployments. `ctx` on `server.on()` observers has no built-in timing field (no `ctx.startTime`) — measure duration with `server.use()` middleware, which wraps the handler call:

```typescript
server.use("mcp:*", async (ctx, next) => {
  const start = Date.now();
  const traceId = ctx.request?.header("x-trace-id") || generateId();
  await next();
  await metrics.record({
    traceId,
    method: ctx.method,
    duration: Date.now() - start,
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
| Vercel Functions | 2GB default (Hobby max); 4GB max (Pro/Enterprise) | 1 vCPU default; 2 vCPU max (Pro/Enterprise) | 300s default, 800s max GA (Pro/Enterprise); 1800s beta with Fluid Compute | Hobby capped at 300s/2GB regardless |
| Cloud Run | 32GiB max per instance | 8 vCPU max per instance | 300s default, 3600s (60min) max | Set `--memory`/`--cpu`/`--timeout` to match workload |
| Lambda | 10,240MB (10GB) max | Scales with memory, up to 6 vCPU | 900s (15min) max | ARM64 (Graviton2) for ~20% lower cost at similar performance |
| Railway | Metered per GB-minute, plan-capped | Metered per vCPU-minute, plan-capped | Platform-managed (no hard request timeout) | Vertical scaling primary; horizontal via replicas |

These are vendor-controlled limits that change independently of mcp-use — verify current numbers against each platform's docs before sizing production capacity. Keep function timeout > max tool duration + buffer (e.g., tool timeout 25s → function timeout 30s+).
