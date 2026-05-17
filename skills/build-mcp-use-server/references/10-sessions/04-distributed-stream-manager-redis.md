# Distributed Stream Manager (Redis Pub/Sub)

`RedisStreamManager` routes SSE events across instances using Redis Pub/Sub. Required when a client's notification source (a tool call on instance B) and the client's open SSE stream (on instance A) live on different processes.

## When required

| Situation | `RedisStreamManager`? |
|---|---|
| One instance only | no |
| Multiple instances, no notifications/progress/sampling/subscriptions | no |
| Multiple instances with notifications, progress, sampling, or subscriptions | **yes** |
| Legacy SSE compatibility across nodes | yes |

## How it works

1. Client connects to **Server A** → SSE stream created → A subscribes to that session's Redis channel.
2. Client's next request hits **Server B** → tool runs → B calls `ctx.sendNotification(...)`, `ctx.reportProgress(...)`, or `ctx.log(...)`.
3. B publishes the event to Redis on the session's channel.
4. A receives the published message and writes it to the client's SSE stream.

## Constructor options

```typescript
new RedisStreamManager({
  client,           // required — primary Redis connection
  pubSubClient,     // required — dedicated Pub/Sub connection (separate client)
  prefix,           // optional — channel prefix, default: "mcp:stream:"
  heartbeatInterval // optional — seconds, default: 10; keys expire after 2x this
})
```

| Option | Type | Default | Notes |
|---|---|---|---|
| `client` | Redis client | required | General Redis commands and session-availability checks |
| `pubSubClient` | Redis client | required | **Must be a separate client.** Pub/Sub mode blocks normal commands |
| `prefix` | `string` | `"mcp:stream:"` | Channel prefix for Pub/Sub |
| `heartbeatInterval` | `number` | `10` (sec) | Keep-alive cadence; ownership keys TTL = `heartbeatInterval * 2` |

## Redis names

With the default `prefix: "mcp:stream:"`, runtime names are:

| Purpose | Name pattern |
|---|---|
| Per-session Pub/Sub channel | `mcp:stream:${sessionId}` |
| Delete channel | `delete:mcp:stream:${sessionId}` |
| Active-stream key | `available:mcp:stream:${sessionId}` |
| Active-session SET | `mcp:stream:active` |
| Request route key | `mcp:stream:req-route:${sessionId}:${requestId}` |
| Per-server response channel | `mcp:stream:server:${serverId}` |

## Correct setup

```typescript
import {
  MCPServer,
  RedisSessionStore,
  RedisStreamManager,
} from "mcp-use/server";
import { createClient } from "redis";

const redis = createClient({ url: process.env.REDIS_URL });
const pubSubRedis = redis.duplicate(); // dedicated Pub/Sub connection
await redis.connect();
await pubSubRedis.connect();

const server = new MCPServer({
  name: "distributed-server",
  version: "1.0.0",
  sessionStore: new RedisSessionStore({ client: redis }),
  streamManager: new RedisStreamManager({
    client: redis,
    pubSubClient: pubSubRedis,
  }),
});
```

## Anti-patterns

**BAD** — share one Redis client for commands and Pub/Sub:

```typescript
new RedisStreamManager({ client: redis, pubSubClient: redis })
// Pub/Sub mode blocks regular commands on the same connection
```

**GOOD** — duplicate for Pub/Sub:

```typescript
new RedisStreamManager({ client: redis, pubSubClient: redis.duplicate() })
```

**BAD** — distributed streams with in-memory sessions:

```typescript
new MCPServer({
  streamManager: new RedisStreamManager({ client, pubSubClient }),
  // sessionStore omitted — metadata is not distributed
})
// Reconnecting client finds its stream but loses session state
```

**GOOD** — pair both:

```typescript
new MCPServer({
  sessionStore: new RedisSessionStore({ client }),
  streamManager: new RedisStreamManager({ client, pubSubClient }),
})
```

## Operational notes

- Use a **dedicated prefix per environment** so dev/staging/prod don't collide.
- Confirm Redis eviction policy will not silently drop keys — `noeviction` or a TTL-aware policy is safest.
- Monitor channel subscriber counts to detect orphaned instances.
- The heartbeat keeps active-stream keys fresh; if an instance crashes, those keys stop advertising the dead stream within `heartbeatInterval * 2` seconds.
