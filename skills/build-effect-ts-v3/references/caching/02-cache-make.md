# Cache.make
Use this for keyed TTL caches with bounded capacity, duplicate in-flight lookup suppression, statistics, and explicit invalidation.

`Cache.make` is the canonical Effect v3 cache constructor:

```typescript
import { Cache, Effect } from "effect"

const makeUserCache = Cache.make({
  capacity: 1_000,
  timeToLive: "5 minutes",
  lookup: (id: string) => fetchUser(id)
})

declare const fetchUser: (id: string) => Effect.Effect<User, UserError>
interface User {
  readonly id: string
}
class UserError {
  readonly _tag = "UserError"
}
```

The source signature in v3 is:

```typescript
import { Cache, Duration, Effect } from "effect"

type Lookup<Key, Value, Error, Environment> = (
  key: Key
) => Effect.Effect<Value, Error, Environment>

declare const make: <Key, Value, Error = never, Environment = never>(
  options: {
    readonly capacity: number
    readonly timeToLive: Duration.DurationInput
    readonly lookup: Lookup<Key, Value, Error, Environment>
  }
) => Effect.Effect<Cache.Cache<Key, Value, Error>, never, Environment>
```

The cache creation effect requires the same environment as the `lookup`. Once created, `cache.get(key)` no longer exposes that environment because the cache captured it.

## Keyed Lookup Semantics

`get(key)` does three things:

1. If a fresh value exists, it returns it.
2. If no fresh value exists, it runs `lookup(key)`.
3. If another fiber is already running the lookup for that same key, it waits for the same result.

This is useful for request bursts:

```typescript
import { Cache, Effect } from "effect"

const program = Effect.gen(function* () {
  const cache = yield* Cache.make({
    capacity: 100,
    timeToLive: "1 minute",
    lookup: (id: string) =>
      Effect.sleep("100 millis").pipe(Effect.as(`user:${id}`))
  })

  const values = yield* Effect.all(
    [
      cache.get("1"),
      cache.get("1"),
      cache.get("1"),
      cache.get("1"),
      cache.get("1"),
      cache.get("1")
    ],
    { concurrency: 6 }
  )

  yield* Effect.logInfo("All lookups share one loaded value", values)
})
```

The six effects ask for the same key. The lookup runs once, and all waiters receive the same computed value.

## Structural Keys

`Cache` stores keys in Effect hash maps. Equality goes through `Equal.equals` and `Hash.hash`. If your key is an object, equip it with structural equality.

```typescript
import { Cache, Data, Effect } from "effect"

const UserProfileKey = (tenantId: string, userId: string) =>
  Data.struct({ tenantId, userId })

type UserProfileKey = ReturnType<typeof UserProfileKey>

interface UserProfile {
  readonly tenantId: string
  readonly userId: string
  readonly displayName: string
}

class ProfileError {
  readonly _tag = "ProfileError"
}

const makeProfileCache = Cache.make({
  capacity: 5_000,
  timeToLive: "15 minutes",
  lookup: (key: UserProfileKey): Effect.Effect<UserProfile, ProfileError> =>
    loadProfile(key.tenantId, key.userId)
})

declare const loadProfile: (
  tenantId: string,
  userId: string
) => Effect.Effect<UserProfile, ProfileError>
```

Every call must construct keys the same way:

```typescript
import { Effect } from "effect"

const program = Effect.gen(function* () {
  const cache = yield* makeProfileCache
  const profile = yield* cache.get(UserProfileKey("tenant-1", "user-1"))
  yield* Effect.logInfo("Loaded profile", profile)
})
```

Do not write `cache.get({ tenantId, userId })` and expect two separate object literals to hit the same entry.

## TTL Selection

Use shorter TTLs for:

- Authorization and entitlement checks.
- Values backed by frequently updated admin screens.
- Failures from unreliable downstream systems.
- Values with external invalidation you cannot reliably observe.

Use longer TTLs for:

- Static lookup tables.
- Public metadata.
- Idempotent expensive computations.
- Configuration values with explicit invalidation.

`Duration.DurationInput` accepts string forms like `"5 minutes"` and constructors such as `Duration.minutes(5)`.

## `Cache.makeWith`

Use `Cache.makeWith` when TTL depends on the lookup exit:

```typescript
import { Cache, Effect, Exit } from "effect"

const cache = Cache.makeWith({
  capacity: 500,
  lookup: (id: string) => fetchFeatureFlags(id),
  timeToLive: Exit.match({
    onFailure: () => "15 seconds",
    onSuccess: () => "10 minutes"
  })
})

declare const fetchFeatureFlags: (
  accountId: string
) => Effect.Effect<ReadonlyArray<string>, FeatureFlagError>

class FeatureFlagError {
  readonly _tag = "FeatureFlagError"
}
```

This is a common pattern when successful data is stable but backend failures should be retried sooner.

## Capacity Selection

Capacity is not a substitute for business limits. It is a memory and churn control. Choose it from expected active keys, not total rows in a database.

Good inputs:

- Number of active tenants per process.
- Number of active users per process window.
- Expected repeated keys within the TTL.
- Value size in memory.

If values are large, prefer a lower capacity and a cheap lookup. If the lookup is expensive but values are small, a larger capacity may be justified.

## When Not To Use `Cache.make`

Do not use `Cache.make` for acquired resources that must be finalized. Use `ScopedCache`.

Do not use `Cache.make` to batch many independent ids into one backend query. Use `RequestResolver.makeBatched`.

Do not use `Cache.make` for a single static effect when `Effect.cached` or `Effect.cachedWithTTL` is clearer.

## Cross-references

See also: [01-overview.md](01-overview.md), [03-cache-operations.md](03-cache-operations.md), [05-scoped-cache.md](05-scoped-cache.md), [07-request-resolver.md](07-request-resolver.md)
