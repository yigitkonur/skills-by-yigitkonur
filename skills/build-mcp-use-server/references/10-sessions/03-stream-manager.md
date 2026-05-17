# Stream Manager (Default, In-Memory)

The **stream manager** routes server-initiated events — notifications, progress updates, log messages, sampling responses, resource subscription updates — to the SSE stream attached to a given session.

The default `InMemoryStreamManager` keeps stream ownership in process memory. It is the right choice for single-instance servers.

## What it does

When a tool calls `ctx.sendNotification(...)`, `ctx.reportProgress(...)`, or `ctx.log(...)`:

1. The manager looks up the SSE stream registered for `ctx.session.sessionId`.
2. If the stream lives in this process, it writes the event directly.
3. If the session has no active SSE stream (HTTP-only client), the event is dropped — there is no buffer.

## Default behavior

You don't need to construct it explicitly. `MCPServer` installs `InMemoryStreamManager` by default.

```typescript
import { MCPServer } from "mcp-use/server";

const server = new MCPServer({ name: "my-server", version: "1.0.0" });
// InMemoryStreamManager is installed automatically
```

Explicit form (rarely needed):

```typescript
import { MCPServer, InMemoryStreamManager } from "mcp-use/server";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  streamManager: new InMemoryStreamManager(),
});
```

## When in-memory is sufficient

| Deployment | In-memory OK? |
|---|---|
| Single Node.js process | yes |
| Single container behind a single replica | yes |
| Multiple replicas, no notifications/progress/sampling/subscriptions | usually yes |
| Multiple replicas with notifications/progress/sampling/subscriptions | **no — use Redis** |
| Edge / serverless (stateless) | n/a |

## Why it breaks across instances

A client opens an SSE stream against **Server A**. The stream is registered in A's local map. The client's next HTTP request is load-balanced to **Server B**. B receives a tool call that wants to notify the client — but B's local map has no entry for that session. The notification disappears.

`RedisStreamManager` solves this by publishing events through Redis Pub/Sub so the owning instance picks them up. See `04-distributed-stream-manager-redis.md`.

## Pairing rules

- `InMemoryStreamManager` works with any session store.
- It does **not** make sense to pair `InMemoryStreamManager` with multiple replicas if your tools emit notifications — events would only reach clients connected to the originating instance.
- Pair `RedisStreamManager` only with `RedisSessionStore`. Pairing it with in-memory sessions is broken (see `04-distributed-stream-manager-redis.md`).

> Tool-level notification APIs live under `../14-notifications/` and `../15-logging/`. This file covers only the manager that routes those events.
