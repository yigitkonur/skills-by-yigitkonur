# KeyedPool
Use this when each key needs its own pool of reusable scoped resources.

`KeyedPool<K, A, E>` is a pool of pools. Each key has a pool of resources of type `A`. Getting a resource is scoped; invalidating a resource tells the pool to eventually replace it.

## Constructors

Effect v3 exposes four constructors:

```typescript
import { Duration, Effect, KeyedPool, Scope } from "effect"

declare const make: <K, A, E, R>(
  options: {
    readonly acquire: (key: K) => Effect.Effect<A, E, R>
    readonly size: number
  }
) => Effect.Effect<KeyedPool.KeyedPool<K, A, E>, never, Scope.Scope | R>

declare const makeWith: <K, A, E, R>(
  options: {
    readonly acquire: (key: K) => Effect.Effect<A, E, R>
    readonly size: (key: K) => number
  }
) => Effect.Effect<KeyedPool.KeyedPool<K, A, E>, never, Scope.Scope | R>

declare const makeWithTTL: <K, A, E, R>(
  options: {
    readonly acquire: (key: K) => Effect.Effect<A, E, R>
    readonly min: (key: K) => number
    readonly max: (key: K) => number
    readonly timeToLive: Duration.DurationInput
  }
) => Effect.Effect<KeyedPool.KeyedPool<K, A, E>, never, Scope.Scope | R>

declare const makeWithTTLBy: <K, A, E, R>(
  options: {
    readonly acquire: (key: K) => Effect.Effect<A, E, R>
    readonly min: (key: K) => number
    readonly max: (key: K) => number
    readonly timeToLive: (key: K) => Duration.DurationInput
  }
) => Effect.Effect<KeyedPool.KeyedPool<K, A, E>, never, Scope.Scope | R>
```

The pool itself is scoped. Checked-out resources are also scoped.
## Fixed Size Per Key

Use `KeyedPool.make` when every key should have the same pool size:

```typescript
import { Effect, KeyedPool } from "effect"

interface Client {
  readonly tenantId: string
  readonly request: (path: string) => Effect.Effect<string, ClientError>
}

class ClientError {
  readonly _tag = "ClientError"
}

declare const makeClient: (
  tenantId: string
) => Effect.Effect<Client, ClientError>

const program = Effect.scoped(
  Effect.gen(function* () {
    const pool = yield* KeyedPool.make({
      acquire: makeClient,
      size: 4
    })

    const client = yield* KeyedPool.get(pool, "tenant-1")
    const body = yield* client.request("/users")

    yield* Effect.logInfo("Response body", body)
  })
)
```

Use `Effect.scoped` at the usage boundary. That releases the checkout when the scoped block exits.

## Size Per Key

Use `makeWith` when high-volume keys need larger pools:

```typescript
import { Effect, KeyedPool } from "effect"

const pool = KeyedPool.makeWith({
  acquire: makeClient,
  size: (tenantId: string) => tenantId === "enterprise" ? 16 : 4
})

declare const makeClient: (tenantId: string) => Effect.Effect<Client, ClientError>
interface Client {
  readonly tenantId: string
}
class ClientError {
  readonly _tag = "ClientError"
}
```

This keeps tenant sizing logic near the resource pool instead of scattering semaphores through call sites.

## TTL Shrinking

Use `makeWithTTL` when each key has a minimum and maximum size, and excess idle resources should shrink after one shared TTL:

```typescript
import { Effect, KeyedPool } from "effect"

const pool = KeyedPool.makeWithTTL({
  acquire: makeClient,
  min: () => 1,
  max: (tenantId: string) => tenantId === "enterprise" ? 16 : 4,
  timeToLive: "2 minutes"
})

declare const makeClient: (tenantId: string) => Effect.Effect<Client, ClientError>
interface Client {
  readonly tenantId: string
}
class ClientError {
  readonly _tag = "ClientError"
}
```

Use `makeWithTTLBy` when idle shrink time should differ by key.

## Invalidate Bad Resources

If a checked-out resource is known bad, invalidate it:

```typescript
import { Effect, KeyedPool } from "effect"

const useClient = (
  pool: KeyedPool.KeyedPool<string, Client, ClientError>,
  tenantId: string
) =>
  Effect.scoped(
    Effect.gen(function* () {
      const client = yield* pool.get(tenantId)
      const response = yield* client.request("/health")

      if (response === "stale") {
        yield* pool.invalidate(client)
      }

      return response
    })
  )

interface Client {
  readonly tenantId: string
  readonly request: (path: string) => Effect.Effect<string, ClientError>
}
class ClientError {
  readonly _tag = "ClientError"
}
```

Invalidation marks the item so the pool can reallocate it, potentially lazily.

## KeyedPool vs Cache
Use `Cache` when one key maps to one value. Use `ScopedCache` when one key maps to one acquired resource. Use `KeyedPool` when one key maps to several reusable acquired resources with concurrent checkout.

## Cross-references

See also: [01-overview.md](01-overview.md), [05-scoped-cache.md](05-scoped-cache.md), [02-cache-make.md](02-cache-make.md), [07-request-resolver.md](07-request-resolver.md)
