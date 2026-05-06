# Cache Operations
Use this for the operational methods on `Cache`: `get`, `getOption`, `refresh`, `invalidate`, `contains`, stats, keys, values, and size.

After `Cache.make`, the cache value exposes read, write, refresh, invalidation, and inspection methods. These methods are effects; yield them instead of reading cache state synchronously.

## Method Reference

| Operation | Type | Use |
|---|---|---|
| `cache.get(key)` | `Effect<Value, Error>` | Return fresh value or run lookup |
| `cache.getEither(key)` | `Effect<Either<Value, Value>, Error>` | Distinguish hit from miss-loaded value |
| `cache.getOption(key)` | `Effect<Option<Value>, Error>` | Read only; do not run lookup |
| `cache.getOptionComplete(key)` | `Effect<Option<Value>>` | Read only if lookup is already complete |
| `cache.refresh(key)` | `Effect<void, Error>` | Recompute while old value can still serve |
| `cache.set(key, value)` | `Effect<void>` | Put a known value directly |
| `cache.invalidate(key)` | `Effect<void>` | Remove one key |
| `cache.invalidateWhen(key, predicate)` | `Effect<void>` | Remove one key only if current value matches |
| `cache.invalidateAll` | `Effect<void>` | Remove all keys |
| `cache.contains(key)` | `Effect<boolean>` | Approximate membership check |
| `cache.size` | `Effect<number>` | Approximate entry count |
| `cache.cacheStats` | `Effect<CacheStats>` | Hits, misses, and size snapshot |
| `cache.entryStats(key)` | `Effect<Option<EntryStats>>` | Per-entry loaded timestamp snapshot |
| `cache.keys` | `Effect<Array<Key>>` | Approximate current keys |
| `cache.values` | `Effect<Array<Value>>` | Approximate current values |

## Get

Use `get` for the normal cache path:

```typescript
import { Cache, Effect } from "effect"

const program = Effect.gen(function* () {
  const cache = yield* Cache.make({
    capacity: 100,
    timeToLive: "1 minute",
    lookup: (id: string) => fetchUser(id)
  })

  const user = yield* cache.get("user-1")
  yield* Effect.logInfo("Loaded user", user)
})

declare const fetchUser: (id: string) => Effect.Effect<User, UserError>
interface User {
  readonly id: string
}
class UserError {
  readonly _tag = "UserError"
}
```

`get` may fail with the lookup error. It may also return a cached failure if the previous lookup failed and the TTL has not expired.

## Read Without Loading

Use `getOption` when you do not want a cache miss to trigger the lookup:

```typescript
import { Cache, Effect, Option } from "effect"

const readIfWarm = (cache: Cache.Cache<string, User, UserError>, id: string) =>
  Effect.gen(function* () {
    const warmed = yield* cache.getOption(id)

    return Option.match(warmed, {
      onNone: () => "not-warmed",
      onSome: (user) => `warmed:${user.id}`
    })
  })

interface User {
  readonly id: string
}
class UserError {
  readonly _tag = "UserError"
}
```

`getOptionComplete` is stricter: if a lookup is in progress, it returns `Option.none` instead of waiting for the pending value.

## Refresh

`refresh(key)` always triggers the lookup. It does not first invalidate the current value. Existing callers can continue to receive the old value while the refresh is running.

```typescript
import { Cache, Effect } from "effect"

const refreshAfterWrite = (
  cache: Cache.Cache<string, User, UserError>,
  id: string
) =>
  Effect.gen(function* () {
    yield* updateUser(id)
    yield* cache.refresh(id)
    return yield* cache.get(id)
  })

declare const updateUser: (id: string) => Effect.Effect<void, UserError>
interface User {
  readonly id: string
}
class UserError {
  readonly _tag = "UserError"
}
```

Use `refresh` for background warming. Use `invalidate` when the old value must not be served anymore.

## Invalidation

`invalidate` removes one key:

```typescript
import { Cache, Effect } from "effect"

const removeUser = (
  cache: Cache.Cache<string, User, UserError>,
  id: string
) =>
  Effect.gen(function* () {
    yield* deleteUser(id)
    yield* cache.invalidate(id)
  })

declare const deleteUser: (id: string) => Effect.Effect<void, UserError>
```

`invalidateWhen` removes one key only if the current value matches a predicate. Use `invalidateAll` sparingly, usually after a migration, global configuration switch, or test setup reset.

## Set

`set` inserts a known value without calling the lookup. Use it after a write that returns the updated row:

```typescript
import { Cache, Effect } from "effect"

const saveAndWarm = (
  cache: Cache.Cache<string, User, UserError>,
  input: User
) =>
  Effect.gen(function* () {
    const saved = yield* saveUser(input)
    yield* cache.set(saved.id, saved)
    return saved
  })

declare const saveUser: (input: User) => Effect.Effect<User, UserError>
interface User {
  readonly id: string
}
class UserError {
  readonly _tag = "UserError"
}
```

## Stats

Stats are snapshots, not synchronized business facts. Use `cache.cacheStats`, `cache.entryStats(key)`, `cache.size`, `cache.keys`, and `cache.values` for telemetry and performance tuning. Do not branch critical correctness on exact inspection values under concurrency.

## Cross-references

See also: [01-overview.md](01-overview.md), [02-cache-make.md](02-cache-make.md), [04-effect-cached.md](04-effect-cached.md), [05-scoped-cache.md](05-scoped-cache.md)
