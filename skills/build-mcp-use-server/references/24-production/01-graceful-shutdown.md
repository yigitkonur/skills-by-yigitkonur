# Graceful shutdown

`SIGTERM` arrives from Docker, Kubernetes, Railway, Fly, and systemd before they `SIGKILL`. Let in-flight tool calls finish within the grace period, flush or close the storage you own, and close every external pool. Anything you skip leaks connections or truncates client responses.

For lifecycle basics (`server.close()`, `server.forceClose()`, grace periods per platform), see `08-server-config/07-shutdown-and-lifecycle.md`. This file is the production-grade shutdown sequence.

## Required ordering

1. Flip an `isShuttingDown` flag (idempotent guard against double-signal).
2. Arm a hard-exit timer (`setTimeout` → `process.exit(1)`) so a stuck handler cannot wedge the pod.
3. `await server.close()` — closes the HTTP listener started by `listen()`.
4. Flush or close session/stream storage you own (`RedisSessionStore.close()`, `RedisStreamManager.close()`, `FileSystemSessionStore.flush()`); in-memory stores have no shutdown hook.
5. Close downstream pools in reverse dependency order: stream-manager Pub/Sub client, command Redis client, DB pool, queue clients.
6. Clear the hard-exit timer, `process.exit(0)`.

Skipping (4) leaks file descriptors and Redis connections per restart. Skipping (2) means a stuck DB query holds the pod hostage past the orchestrator's grace period and gets `SIGKILL`'d mid-write.

## Working pattern

```typescript
import { MCPServer, RedisSessionStore, RedisStreamManager } from "mcp-use/server";
import { createClient } from "redis";
import type { Pool } from "pg";

const redis = createClient({ url: process.env.REDIS_URL });
const pubSubRedis = redis.duplicate();
await Promise.all([redis.connect(), pubSubRedis.connect()]);

const server = new MCPServer({
  name: "prod-server",
  version: "1.0.0",
  sessionStore: new RedisSessionStore({ client: redis }),
  streamManager: new RedisStreamManager({ client: redis, pubSubClient: pubSubRedis }),
});

let dbPool: Pool | null = null; // see 03-lazy-init.md
await server.listen(3000);

let isShuttingDown = false;

async function shutdown(signal: string) {
  if (isShuttingDown) return;
  isShuttingDown = true;
  console.error(`[${signal}] draining...`);

  const forceExit = setTimeout(() => {
    console.error("forced exit after 15s");
    void server.forceClose().finally(() => process.exit(1));
  }, 15_000);

  try {
    await server.close();         // close the HTTP listener
    await dbPool?.end();          // close DB pool
    await pubSubRedis.quit();     // close Pub/Sub client first
    await redis.quit();           // then command client
    clearTimeout(forceExit);
    process.exit(0);
  } catch (err) {
    console.error("shutdown error", err);
    clearTimeout(forceExit);
    process.exit(1);
  }
}

process.on("SIGTERM", () => shutdown("SIGTERM"));
process.on("SIGINT", () => shutdown("SIGINT"));
process.on("uncaughtException", (err) => {
  console.error("uncaught", err);
  process.exit(1);
});
process.on("unhandledRejection", (err) => {
  console.error("unhandledRejection", err);
  process.exit(1);
});
```

## Hard-exit timeout sizing

| Slowest tool call | Hard-exit timer | Orchestrator grace period |
|---|---|---|
| ≤ 5 s | 10 s | 15 s |
| ≤ 30 s | 45 s | 60 s |
| ≤ 60 s | 75 s | 90 s |

Always: `slowest tool < hard-exit timer < orchestrator grace`. If the hard-exit timer is shorter than the slowest tool, you truncate legitimate work. If the orchestrator grace is shorter than the hard-exit timer, you get `SIGKILL`'d mid-shutdown.

For Kubernetes, set `terminationGracePeriodSeconds` accordingly. For Docker, `--stop-timeout`. For Railway/Fly, check provider docs.

## Pub/Sub close order

`RedisStreamManager` uses two separate Redis clients (a Pub/Sub-blocked client and a command client). Quit the Pub/Sub client **first** — quitting the command client first leaves Pub/Sub subscriptions hanging and can hang the parent process for the connection's idle timeout.

## Don't

- Don't `process.exit(0)` synchronously in the signal handler — async resources never close.
- Don't omit the hard-exit timer — a hung handler will keep the pod alive past its grace period.
- Don't close Redis before `server.close()` returns — in-flight work may still depend on it.
