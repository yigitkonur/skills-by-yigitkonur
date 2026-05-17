# ScopedCache
Use this when cached values are acquired resources that must be released through `Scope`.

`ScopedCache` is the resource-lifetime version of `Cache`. It caches scoped values and ensures finalizers run when cached resources are no longer used and are invalidated, refreshed, expired, or evicted.

## Constructor

The v3 constructor shape is:

```typescript
import { Duration, Effect, Scope, ScopedCache } from "effect"

type Lookup<Key, Value, Error, Environment> = (
  key: Key
) => Effect.Effect<Value, Error, Environment | Scope.Scope>

declare const make: <Key, Value, Error = never, Environment = never>(
  options: {
    readonly lookup: Lookup<Key, Value, Error, Environment>
    readonly capacity: number
    readonly timeToLive: Duration.DurationInput
  }
) => Effect.Effect<
  ScopedCache.ScopedCache<Key, Value, Error>,
  never,
  Scope.Scope | Environment
>
```

`ScopedCache.make` itself requires a scope because the cache owns resources. `cache.get(key)` also requires a scope because each checkout has a lifetime.

## Basic Pattern

```typescript
import { Effect, ScopedCache } from "effect"

interface Connection {
  readonly tenantId: string
  readonly query: (sql: string) => Effect.Effect<ReadonlyArray<Row>, DbError>
  readonly close: Effect.Effect<void>
}

interface Row {
  readonly id: string
}

class DbError {
  readonly _tag = "DbError"
}

declare const openConnection: (
  tenantId: string
) => Effect.Effect<Connection, DbError>

const acquireConnection = (tenantId: string) =>
  Effect.acquireRelease(
    openConnection(tenantId),
    (connection) => connection.close
  )

const program = Effect.scoped(
  Effect.gen(function* () {
    const cache = yield* ScopedCache.make({
      capacity: 100,
      timeToLive: "10 minutes",
      lookup: acquireConnection
    })

    const connection = yield* cache.get("tenant-1")
    const rows = yield* connection.query("select id from users")

    yield* Effect.logInfo("Rows loaded", rows)
  })
)
```

When the surrounding scope closes, the cache and any resources it still owns can be finalized.

## Operations

`ScopedCache` intentionally mirrors many `Cache` methods:

| Operation | Use |
|---|---|
| `cache.get(key)` | Acquire or reuse scoped value for the caller's scope |
| `cache.getOption(key)` | Read a value if present, without starting a lookup |
| `cache.getOptionComplete(key)` | Read a completed value only |
| `cache.refresh(key)` | Recompute a resource while old users keep their value |
| `cache.invalidate(key)` | Remove one resource and release it when no callers own it |
| `cache.invalidateAll` | Remove all resources |
| `cache.contains(key)` | Approximate membership check |
| `cache.size` | Approximate entry count |
| `cache.cacheStats` | Hits, misses, and size |
| `cache.entryStats(key)` | Loaded timestamp for an entry |

The difference is the environment: value reads are scoped.

## Refresh and Invalidation

`refresh(key)` starts a new lookup. Current users can keep the old resource until their scopes close. Once the new resource is ready, new callers get it.

```typescript
import { Effect, ScopedCache } from "effect"

const rotateTenantConnection = (
  cache: ScopedCache.ScopedCache<string, Connection, DbError>,
  tenantId: string
) =>
  Effect.gen(function* () {
    yield* cache.refresh(tenantId)
    yield* Effect.logInfo("Connection refreshed", { tenantId })
  })

interface Connection {
  readonly tenantId: string
}
class DbError {
  readonly _tag = "DbError"
}
```

Use `invalidate(key)` when the old resource should stop being handed out. Existing users still release through their scopes.

## `makeWith`

Use `ScopedCache.makeWith` for exit-dependent TTLs:

```typescript
import { Effect, Exit, ScopedCache } from "effect"

const makeConnectionCache = ScopedCache.makeWith({
  capacity: 100,
  lookup: acquireConnection,
  timeToLive: Exit.match({
    onFailure: () => "10 seconds",
    onSuccess: () => "10 minutes"
  })
})

declare const acquireConnection: (
  tenantId: string
) => Effect.Effect<Connection, DbError>

interface Connection {
  readonly tenantId: string
}
class DbError {
  readonly _tag = "DbError"
}
```

Shorter failure TTLs prevent repeated immediate hammering while still recovering sooner than successful values.

## When ScopedCache Is Required

Use `ScopedCache` instead of `Cache` when the value is:

- A database connection or transaction handle.
- A file handle.
- A browser page or session.
- A subscription.
- A resource acquired with `Effect.acquireRelease`.
- Anything requiring deterministic cleanup.

If no finalizer is involved, normal `Cache` is usually simpler.

## Cross-references

See also: [01-overview.md](01-overview.md), [02-cache-make.md](02-cache-make.md), [03-cache-operations.md](03-cache-operations.md), [06-keyed-pool.md](06-keyed-pool.md)
