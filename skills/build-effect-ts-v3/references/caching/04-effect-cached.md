# Effect Cached Helpers
Use this for `Effect.cached`, `Effect.cachedWithTTL`, `Effect.cachedInvalidateWithTTL`, and `Effect.cachedFunction` in strict Effect v3.

Effect's cached helpers memoize one effect or one effectful function. They are smaller than `Cache.make` when you do not need an explicit multi-key cache object.

## Real v3 Signatures

These are the v3 source shapes:

```typescript
import { Duration, Effect, Equivalence } from "effect"

declare const cached: <A, E, R>(
  self: Effect.Effect<A, E, R>
) => Effect.Effect<Effect.Effect<A, E, R>>

declare const cachedWithTTL: {
  (timeToLive: Duration.DurationInput): <A, E, R>(
    self: Effect.Effect<A, E, R>
  ) => Effect.Effect<Effect.Effect<A, E>, never, R>

  <A, E, R>(
    self: Effect.Effect<A, E, R>,
    timeToLive: Duration.DurationInput
  ): Effect.Effect<Effect.Effect<A, E>, never, R>
}

declare const cachedInvalidateWithTTL: {
  (timeToLive: Duration.DurationInput): <A, E, R>(
    self: Effect.Effect<A, E, R>
  ) => Effect.Effect<[Effect.Effect<A, E>, Effect.Effect<void>], never, R>

  <A, E, R>(
    self: Effect.Effect<A, E, R>,
    timeToLive: Duration.DurationInput
  ): Effect.Effect<[Effect.Effect<A, E>, Effect.Effect<void>], never, R>
}

declare const cachedFunction: <A, B, E, R>(
  f: (a: A) => Effect.Effect<B, E, R>,
  eq?: Equivalence.Equivalence<A>
) => Effect.Effect<(a: A) => Effect.Effect<B, E, R>>
```

The most important part: `Effect.cachedWithTTL` returns `Effect<Effect<A, E>>`. You yield twice: once to create the cached effect, then once each time you need the cached value.

## `Effect.cachedWithTTL`

This is the double-yield pattern:

```typescript
import { Effect } from "effect"

const fetchRemoteConfig = Effect.succeed({
  version: 1,
  featureEnabled: true
})

const program = Effect.gen(function* () {
  const getConfig = yield* Effect.cachedWithTTL(
    fetchRemoteConfig,
    "5 minutes"
  )

  const first = yield* getConfig
  const second = yield* getConfig

  yield* Effect.logInfo("Both values come from the cached getter", {
    first,
    second
  })
})
```

Do not write this:

```typescript
import { Effect } from "effect"

const wrong = Effect.gen(function* () {
  const config = yield* Effect.cachedWithTTL(fetchRemoteConfig, "5 minutes")
  yield* Effect.logInfo("This is the getter, not the config", config)
})

const fetchRemoteConfig = Effect.succeed({ version: 1 })
```

`config` above is an effect you still need to yield. Name it `getConfig`, `cachedConfig`, or `loadCachedConfig` to avoid confusion.

## `Effect.cachedInvalidateWithTTL`

This returns a tuple: cached getter plus invalidate handle.

```typescript
import { Effect } from "effect"

const fetchRemoteConfig = Effect.succeed({
  version: 1,
  featureEnabled: true
})

const program = Effect.gen(function* () {
  const [getConfig, invalidateConfig] =
    yield* Effect.cachedInvalidateWithTTL(
      fetchRemoteConfig,
      "10 minutes"
    )

  const before = yield* getConfig
  yield* invalidateConfig
  const after = yield* getConfig

  yield* Effect.logInfo("Config refreshed after invalidation", {
    before,
    after
  })
})
```

The invalidate effect does not return the new value. It clears the memoized value so the next `yield* getConfig` recomputes.

## `Effect.cachedFunction`

Use this when the input argument is the cache key:

```typescript
import { Effect } from "effect"

interface User {
  readonly id: string
  readonly name: string
}

class UserError {
  readonly _tag = "UserError"
}

const fetchUser = (id: string): Effect.Effect<User, UserError> =>
  Effect.succeed({ id, name: `User ${id}` })

const program = Effect.gen(function* () {
  const getUser = yield* Effect.cachedFunction(fetchUser)

  const a = yield* getUser("1")
  const b = yield* getUser("1")

  yield* Effect.logInfo("Same argument reuses the memoized result", { a, b })
})
```

The default key comparison uses `Equal.equals` and `Hash.hash`. For object arguments, pass structurally equal values or provide an `Equivalence`.

```typescript
import { Data, Effect, Equivalence } from "effect"

const UserKey = (tenantId: string, userId: string) =>
  Data.struct({ tenantId, userId })

type UserKey = ReturnType<typeof UserKey>

const sameUserKey: Equivalence.Equivalence<UserKey> = (a, b) =>
  a.tenantId === b.tenantId && a.userId === b.userId

const program = Effect.gen(function* () {
  const getUser = yield* Effect.cachedFunction(fetchUser, sameUserKey)
  return yield* getUser(UserKey("tenant-1", "user-1"))
})

declare const fetchUser: (key: UserKey) => Effect.Effect<User, UserError>
interface User {
  readonly id: string
}
class UserError {
  readonly _tag = "UserError"
}
```

If you pass an `Equivalence`, hashing falls back to a broad bucket internally, so equality can become more expensive. Prefer `Data.struct` keys without a custom equivalence when possible.

## Choosing Among Helpers

Use `cached` for one value for the current lifetime.

Use `cachedWithTTL` for one value with time-based refresh.

Use `cachedInvalidateWithTTL` when writes or admin actions need to force refresh.

Use `cachedFunction` when each argument should memoize independently.

Use `Cache.make` when you need capacity, per-key invalidation, stats, or `refresh`.

## Cross-references

See also: [01-overview.md](01-overview.md), [02-cache-make.md](02-cache-make.md), [03-cache-operations.md](03-cache-operations.md), [07-request-resolver.md](07-request-resolver.md)
