# Shutdown and lifecycle

A long-running server must shut down cleanly: stop accepting new requests, let in-flight work finish within the grace period, close external resources, flush logs, and exit. Otherwise containers get killed mid-request and clients see truncated responses.

## Lifecycle methods

| Method | Effect |
|---|---|
| `server.listen(port?)` | Bind and start accepting HTTP requests |
| `server.getHandler(opts?)` | Return a `fetch`-compatible handler (no listen) |
| `server.close()` | Close the HTTP listener started by `listen()`; no-op when not listening |
| `server.forceClose()` | Force-close active connections when graceful close exceeds your budget |

## Wiring SIGTERM and SIGINT

Production orchestrators (Docker, Kubernetes, systemd, Railway, Fly) send `SIGTERM` then `SIGKILL` after a grace period. Catch `SIGTERM` and `SIGINT`, call `server.close()`, then exit. If active connections hang past your budget, call `server.forceClose()` from a hard timeout.

```typescript
import { MCPServer } from 'mcp-use/server'

const server = new MCPServer({ name: 'my-server', version: '1.0.0' })

await server.listen(3000)

const shutdown = async (signal: string) => {
  console.log(`Received ${signal}, shutting down`)
  const hardStop = setTimeout(() => {
    void server.forceClose().finally(() => process.exit(1))
  }, 15_000)

  try {
    await server.close()
    clearTimeout(hardStop)
    process.exit(0)
  } catch (err) {
    clearTimeout(hardStop)
    console.error('Shutdown error', err)
    process.exit(1)
  }
}

process.on('SIGTERM', () => shutdown('SIGTERM'))
process.on('SIGINT', () => shutdown('SIGINT'))
```

Register listeners **after** `listen()` resolves so a startup failure exits naturally.

## Cleanup hooks

Close external connections (Redis, DB pools) after `server.close()` returns:

```typescript
import { MCPServer, RedisSessionStore } from 'mcp-use/server'
import { createClient } from 'redis'

const redis = createClient({ url: process.env.REDIS_URL })
await redis.connect()

const server = new MCPServer({
  name: 'my-server',
  version: '1.0.0',
  sessionStore: new RedisSessionStore({ client: redis }),
})

await server.listen(3000)

const shutdown = async () => {
  await server.close()
  await redis.quit()
  process.exit(0)
}

process.on('SIGTERM', shutdown)
process.on('SIGINT', shutdown)
```

## Drain timing

Set the orchestrator's grace period longer than your maximum tool call duration. If a tool can run 60 seconds, allow at least 75 seconds before `SIGKILL`.

| Platform | Default grace | How to tune |
|---|---|---|
| Kubernetes | 30 s | `terminationGracePeriodSeconds` |
| Docker | 10 s | `--stop-timeout` or `STOPSIGNAL`/`STOPGRACEPERIOD` |
| Railway / Fly | platform-dependent | Check provider docs |

## Uncaught errors

Don't swallow them. Log and exit — the orchestrator restarts the process:

```typescript
process.on('uncaughtException', (err) => {
  console.error('Uncaught exception', err)
  process.exit(1)
})

process.on('unhandledRejection', (err) => {
  console.error('Unhandled rejection', err)
  process.exit(1)
})
```

## Stateful drain considerations

When using stateful sessions (`10-sessions/`):

- Active SSE or keep-alive connections can keep `server.close()` pending; use `server.forceClose()` when the grace period is nearly exhausted.
- Persisted sessions (Redis, filesystem) survive the restart; in-memory sessions do not.
- Long-running tool calls continue to completion before drain finishes.

For more on production hardening, see `24-production/01-graceful-shutdown.md`.
