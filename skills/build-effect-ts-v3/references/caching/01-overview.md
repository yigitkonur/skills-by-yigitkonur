# Caching Overview
Use this when choosing between Effect's built-in cache, memoization helpers, scoped resource caches, keyed pools, and request batching.

Effect v3 gives you several caching tools. Pick the one that matches the lifetime and shape of the work. Do not start with a hand-rolled `Map` plus timers: that usually misses fiber interruption, duplicate in-flight work, failure caching, request deduplication, scoped cleanup, or least-recently-used eviction.

## Decision Table

| Need | Use | Why |
|---|---|---|
| Cache many keyed lookups | `Cache.make` | Capacity, TTL, concurrent miss deduplication, stats, invalidation |
| Cache one effect result | `Effect.cached` | Lazy memoization of a single effect |
| Cache one effect result for a duration | `Effect.cachedWithTTL` | Same as `cached`, but expires by TTL |
| Cache one effect with manual invalidation | `Effect.cachedInvalidateWithTTL` | Returns both cached getter and invalidation handle |
| Memoize an effectful function | `Effect.cachedFunction` | Caches results per argument using `Equal` / `Hash` or an `Equivalence` |
| Cache acquired resources | `ScopedCache.make` | Keeps finalizers tied to scopes and reference usage |
| Pool resources per key | `KeyedPool.make*` | Pools connections or clients by tenant, shard, region, or DSN |
| Deduplicate and batch data fetches | `RequestResolver.makeBatched` | Dataloader-style N requests into one query |

## Mental Model

`Cache.make` is the general-purpose TTL cache:

```typescript
import { Cache, Effect } from "effect"

const userCache = Cache.make({
  capacity: 1_000,
  timeToLive: "5 minutes",
  lookup: (id: string) => fetchUser(id)
})

declare const fetchUser: (id: string) => Effect.Effect<User, UserError>
interface User {
  readonly id: string
  readonly name: string
}
class UserError {
  readonly _tag = "UserError"
}
```

The cache is itself created by an effect. Yield the cache once, then use its methods:

```typescript
import { Cache, Effect } from "effect"

const program = Effect.gen(function* () {
  const cache = yield* Cache.make({
    capacity: 1_000,
    timeToLive: "5 minutes",
    lookup: (id: string) => fetchUser(id)
  })

  const user = yield* cache.get("user-123")
  yield* Effect.logInfo("Loaded user", user)
})

declare const fetchUser: (id: string) => Effect.Effect<User, UserError>
interface User {
  readonly id: string
  readonly name: string
}
class UserError {
  readonly _tag = "UserError"
}
```

## What Is Cached

`Cache` stores the exit of the lookup for a key. Successful values are cached. Failures are also cached until TTL expiry or invalidation. If a lookup is interrupted, the key is removed so the next call can retry the lookup.

This behavior matters in production:

- Concurrent misses for the same key share one lookup.
- Repeated failures do not hammer the backend until the TTL expires.
- Interrupted lookups do not poison the cache.
- `refresh` can recompute while the old value remains available.

## TTL and Eviction

TTL starts when the value is loaded into the cache. A value older than `timeToLive` is not returned; the next `get` computes a fresh value.

Capacity is an upper bound using least-recently-accessed eviction. When the cache is above capacity, older accessed entries are removed first. The size is approximate under concurrent access, so do not use it for exact business invariants.

Use `Cache.makeWith` when TTL should depend on whether the lookup succeeded or failed:

```typescript
import { Cache, Effect, Exit } from "effect"

const cache = Cache.makeWith({
  capacity: 1_000,
  lookup: (id: string) => fetchUser(id),
  timeToLive: Exit.match({
    onFailure: () => "30 seconds",
    onSuccess: () => "10 minutes"
  })
})

declare const fetchUser: (id: string) => Effect.Effect<User, UserError>
interface User {
  readonly id: string
}
class UserError {
  readonly _tag = "UserError"
}
```

## Key Equality

Effect caches use Effect equality and hashing. Primitive keys behave as expected. Object keys need structural equality, usually by creating them with `Data.struct`, `Data.Class`, or `Data.TaggedClass`.

```typescript
import { Data } from "effect"

const UserKey = (tenantId: string, userId: string) =>
  Data.struct({ tenantId, userId })

const a = UserKey("tenant-a", "user-1")
const b = UserKey("tenant-a", "user-1")
```

Both `a` and `b` identify the same cache key because `Data.struct` equips the object with `Equal` and `Hash`. Plain object literals do not give you that value-based identity.

## Cache vs RequestResolver

Use `Cache.make` when callers directly know the cache key and want a value. Use `RequestResolver` when many independent effects should be combined into fewer backend calls.

`RequestResolver` is not just a cache. It batches requests that are issued in the same request-batching region. It can also use Effect's request cache to deduplicate identical requests in one program. It is the right fit for "load N users by id with one SQL query".

## Cache vs ScopedCache

Use `ScopedCache` for resources with finalizers: connections, file handles, browser pages, model sessions, and other acquired values. A normal `Cache` can remember a value, but it does not manage the resource's acquisition and release lifetime for each checkout.

Use `Effect.scoped` around code that gets from a `ScopedCache` or `KeyedPool`, because the returned resource is valid for that scope.

## Cache vs KeyedPool

Use `KeyedPool` when each key has a pool of reusable resources rather than one cached value. A tenant-aware database client is a typical case: tenant A and tenant B should not share the same pool, but each tenant may need several concurrent connections.

## Anti-patterns

- Do not roll a `Map` plus timers for normal application caching.
- Do not use object literals as keys unless you want reference identity.
- Do not cache nondeterministic effects unless repeated values are intended.
- Do not put `Effect.runPromise` inside services to fill a cache eagerly.
- Do not cache secrets or per-user authorization results without a deliberately short TTL and clear invalidation path.

## Cross-references

See also: [02-cache-make.md](02-cache-make.md), [04-effect-cached.md](04-effect-cached.md), [05-scoped-cache.md](05-scoped-cache.md), [07-request-resolver.md](07-request-resolver.md)
