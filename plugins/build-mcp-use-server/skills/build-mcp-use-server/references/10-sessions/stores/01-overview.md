# Session Stores Overview

Three canonical stores ship with `mcp-use/server`. All implement the same conceptual contract — save metadata, look up by `Mcp-Session-Id`, refresh `lastAccessedAt`, delete on expiry — but differ in durability, latency, and operational cost.

## Import

```typescript
import {
  InMemorySessionStore,
  FileSystemSessionStore,
  RedisSessionStore,
} from "mcp-use/server";
```

## Comparison

| Store | Survives restart | Multi-instance | Operational cost | Best for |
|---|---|---|---|---|
| `InMemorySessionStore` | no | no | lowest | Local dev, tests, disposable single-instance prod |
| `FileSystemSessionStore` | yes | no | low | Single-server demos, self-hosted single-VM apps, dev with hot reload |
| `RedisSessionStore` | yes | yes | medium | Production HA, horizontal scaling, multi-instance behind a load balancer |

## Decision tree

1. Is the server stateless (edge / serverless)? → no store needed; set `stateless: true`.
2. Single instance, OK to lose sessions on restart? → `InMemorySessionStore`.
3. Single instance, want sessions to survive restart **without** introducing Redis? → `FileSystemSessionStore`.
4. Multiple instances behind a load balancer? → `RedisSessionStore`.
5. Need to push notifications across instances too? → `RedisSessionStore` + `RedisStreamManager` (see `../04-distributed-stream-manager-redis.md`).
6. None of the above fits (Postgres, DynamoDB, Cosmos, etc.)? → implement a custom store. See `05-custom-store.md`.

## Files in this sub-cluster

- `02-memory.md` — `InMemorySessionStore` (production default).
- `03-filesystem.md` — `FileSystemSessionStore` for single-node persistence.
- `04-redis.md` — `RedisSessionStore` for distributed deploys.
- `05-custom-store.md` — implementing the `SessionStore` interface yourself.

## Auto-selection

When `sessionStore` is **not** explicitly set on `MCPServer`:

| Environment | Default |
|---|---|
| `NODE_ENV !== "production"` | `FileSystemSessionStore` (sessions survive hot reload) |
| `NODE_ENV === "production"` | `InMemorySessionStore` |

Override the default any time it doesn't fit your deployment.

**Canonical doc:** https://manufact.com/docs/typescript/server/session-management
