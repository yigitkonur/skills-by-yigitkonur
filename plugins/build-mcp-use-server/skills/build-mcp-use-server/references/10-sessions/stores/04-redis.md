# RedisSessionStore

Stores session metadata in Redis. The production option for horizontally scaled or multi-instance deployments — sessions live outside the process and are shared across nodes.

## Install

```bash
npm install redis
# or
npm install ioredis
```

## Constructor

```typescript
new RedisSessionStore({ client, prefix, defaultTTL, serialize })
```

| Option | Type | Default | Notes |
|---|---|---|---|
| `client` | Redis client | required | Connected `redis` or `ioredis` client |
| `prefix` | `string` | `"mcp:session:"` | Key prefix — namespace per environment/app |
| `defaultTTL` | `number` (sec) | `3600` (1h) | TTL applied to each session key |
| `serialize` | `boolean` | typed default `true` | Present in `RedisSessionStoreConfig`; runtime `1.26.0` always JSON-serializes |

## Usage

```typescript
import { MCPServer, RedisSessionStore } from "mcp-use/server";
import { createClient } from "redis";

const redis = createClient({
  url: process.env.REDIS_URL,
  password: process.env.REDIS_PASSWORD,
});
await redis.connect();

const server = new MCPServer({
  name: "redis-backed-server",
  version: "1.0.0",
  sessionStore: new RedisSessionStore({
    client: redis,
    prefix: "prod:mcp:",
    defaultTTL: 86_400, // 24h
  }),
});
```

## Tradeoffs

| Pro | Con |
|---|---|
| Sessions persist across restarts | Requires running Redis |
| Shared across instances — works behind any load balancer | Network latency on every session read/write |
| Clients resume sessions after deploys without re-init | Operational cost (connection pool, eviction policy, monitoring) |

## When required

- Production behind a load balancer with more than one replica.
- Blue/green or rolling deploys where clients should not have to re-initialize.
- Pairing with `RedisStreamManager` for cross-instance notifications.

## Connection setup

Use a single connected client — `RedisSessionStore` does not connect it for you. Reuse the same client elsewhere if you want; pass a separate `client.duplicate()` to `RedisStreamManager` for Pub/Sub (see `../04-distributed-stream-manager-redis.md`).

```typescript
const redis = createClient({ url: process.env.REDIS_URL });
await redis.connect();
// reused across the app
new RedisSessionStore({ client: redis });
```

`ioredis` works equivalently:

```typescript
import Redis from "ioredis";
const redis = new Redis(process.env.REDIS_URL);
new RedisSessionStore({ client: redis });
```

## Operational notes

- **Prefix per environment:** `dev:mcp:`, `staging:mcp:`, `prod:mcp:`. Avoid cross-environment collisions during local Redis sharing.
- **Eviction policy:** ensure Redis is configured so session keys are not silently evicted under memory pressure. `noeviction` is safest; otherwise use a policy compatible with TTL-based expiry.
- **Match `defaultTTL` with `sessionIdleTimeoutMs`** (see `../05-retention-and-cleanup.md`). When they diverge, you waste memory or 404 prematurely.
- **Monitor key counts:** abandoned clients accumulate as zombies until TTL expires.
- **Cleanup:** Redis handles TTL-driven expiry. Explicit `DELETE /mcp` removes the key immediately. There is no in-process sweeper.

## Anti-patterns

**BAD** — pass `0` expecting sessions to live forever:

```typescript
new RedisSessionStore({ client: redis, defaultTTL: 0 })
// Runtime still calls Redis SET with EX/setEx semantics; use a positive TTL.
```

**BAD** — share one client between session store and Pub/Sub stream manager:

```typescript
new RedisStreamManager({ client: redis, pubSubClient: redis })
// Pub/Sub mode blocks regular commands. Use `redis.duplicate()`.
```

**GOOD** — duplicate for Pub/Sub:

```typescript
new RedisStreamManager({ client: redis, pubSubClient: redis.duplicate() })
```

## Pairing with `RedisStreamManager`

If your tools emit notifications, progress events, sampling requests, or resource subscription updates, also use `RedisStreamManager` so events reach clients connected to other replicas. Full setup in `../04-distributed-stream-manager-redis.md`.
