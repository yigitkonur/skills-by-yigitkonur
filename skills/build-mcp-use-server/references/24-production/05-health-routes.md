# Health routes

Two distinct endpoints, two distinct purposes. Conflating them breaks load balancers and rolling deploys.

| Route | Purpose | Reads | Behavior on degraded state |
|---|---|---|---|
| `GET /health` | "Is the process alive?" | Process metrics only | Return 200 unless the process is unrecoverable |
| `GET /ready` | "Should I receive traffic?" | Process + downstream readiness | Return 503 when downstreams are not yet usable |

Kubernetes uses these as `livenessProbe` and `readinessProbe`. A failing `/ready` removes the pod from the service backend without restarting it; a failing `/health` restarts the pod. Backwards = restart loops.

Use `server.get(...)` to register both. See `08-server-config/05-middleware-and-custom-routes.md` for the middleware/route surface — register **before** `listen()`.

## `/health` — liveness

Cheap, no I/O. If this returns 200, the event loop is alive and the process can serve.

```typescript
import { MCPServer } from "mcp-use/server";

const startedAt = Date.now();
const server = new MCPServer({ name: "my-server", version: "1.0.0" });

server.get("/health", (c) =>
  c.json({
    status: "ok",
    uptimeSeconds: Math.floor((Date.now() - startedAt) / 1000),
    version: config.version,
  })
);
```

Don't query Redis or the DB here. A flaky DB connection should not cause the orchestrator to kill the pod and replay the same flake on the new one.

## `/ready` — readiness

Verifies the server can actually do work. Check every dependency the *typical* tool call needs. Return 503 + which check failed if any check fails.

```typescript
let isShuttingDown = false; // set in shutdown handler — see 01-graceful-shutdown.md

server.get("/ready", async (c) => {
  if (isShuttingDown) {
    return c.json({ status: "shutting-down" }, 503);
  }

  const checks: Record<string, "ok" | string> = {};
  let allOk = true;

  // DB
  try {
    const db = await getDB();
    await db.query("SELECT 1");
    checks.db = "ok";
  } catch (err) {
    checks.db = (err as Error).message;
    allOk = false;
  }

  // Redis (only if you use it)
  try {
    await redis.ping();
    checks.redis = "ok";
  } catch (err) {
    checks.redis = (err as Error).message;
    allOk = false;
  }

  return c.json({ status: allOk ? "ready" : "not-ready", checks }, allOk ? 200 : 503);
});
```

The shutdown flag is critical. During graceful shutdown, `/ready` should return 503 immediately so the load balancer drains traffic before `server.close()` finishes.

## What to check vs not check

| Dependency | Check in `/ready`? |
|---|---|
| DB pool | Yes — every tool likely needs it |
| Redis (session store, stream manager) | Yes — sessions break without it |
| External SaaS API | No — wraps too many failure modes; use circuit-breaker pattern in the tool |
| LLM provider | No — same reason |
| Filesystem | Only if a tool requires it |

`/ready` should fail fast (≤ 500 ms total) and check only what your server *requires* to function. A degraded external API is a per-tool concern, not a readiness concern.

## Timeouts on the checks

A hung Redis call should not hang `/ready`. Wrap with a timeout:

```typescript
async function withTimeout<T>(p: Promise<T>, ms: number, label: string): Promise<T> {
  return Promise.race([
    p,
    new Promise<T>((_, reject) =>
      setTimeout(() => reject(new Error(`${label} timeout`)), ms)
    ),
  ]);
}

checks.db = await withTimeout(db.query("SELECT 1"), 1000, "db").then(() => "ok").catch((e) => e.message);
```

## Optional: MCP resource for health

If MCP clients want richer telemetry, expose it as a resource — not via the HTTP route. See `06-resources/`. Memory stats, queue depth, version build SHA all belong there.

## Probe configuration (Kubernetes example)

```yaml
livenessProbe:
  httpGet: { path: /health, port: 3000 }
  initialDelaySeconds: 5
  periodSeconds: 10
  timeoutSeconds: 2
readinessProbe:
  httpGet: { path: /ready, port: 3000 }
  initialDelaySeconds: 1
  periodSeconds: 5
  timeoutSeconds: 2
```

`initialDelaySeconds` on liveness must be longer than your slowest cold-start (lazy DB pool init, etc. — see `03-lazy-init.md`). Otherwise the pod restarts before it ever finishes booting.

## Don't

- Don't expose business metrics on `/health` — keep it cheap and dependency-free.
- Don't reuse `/health` as both liveness and readiness — Kubernetes treats them differently and you lose the ability to drain.
- Don't return 200 on `/ready` while shutting down — set the flag the instant `SIGTERM` arrives.
- Don't put `/health` behind auth — the LB needs to hit it without credentials.
