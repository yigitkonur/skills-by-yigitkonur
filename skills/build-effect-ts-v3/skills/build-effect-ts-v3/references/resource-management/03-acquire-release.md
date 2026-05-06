# Acquire Release
Use `Effect.acquireRelease` to create a scoped resource whose release is guaranteed after successful acquisition.

## What It Does

`Effect.acquireRelease(acquire, release)` combines:

1. an effect that opens or acquires a resource
2. a release function that closes or disposes that resource

The result is a scoped effect. It produces the acquired value and requires
`Scope.Scope` so Effect has a place to register the release finalizer.

```typescript
import { Effect, Scope } from "effect"

type Connection = {
  readonly query: (sql: string) => Effect.Effect<string>
  readonly close: Effect.Effect<void>
}

declare const openConnection: Effect.Effect<Connection, "OpenError">

const connection: Effect.Effect<Connection, "OpenError", Scope.Scope> =
  Effect.acquireRelease(
    openConnection,
    (conn) => conn.close
  )
```

The release action runs when the owning scope closes, not immediately after the
line that acquires the resource.

## Signature Shape

In v3, the release function receives both the acquired value and the `Exit` used
to close the scope.

```typescript
import { Effect, Exit } from "effect"

type Resource = {
  readonly close: Effect.Effect<void>
}

declare const acquire: Effect.Effect<Resource, "OpenError">

const resource = Effect.acquireRelease(
  acquire,
  (value, exit: Exit.Exit<unknown, unknown>) =>
    Effect.logInfo(`closing after ${exit._tag}`).pipe(
      Effect.zipRight(value.close)
    )
)
```

Use the exit when release behavior differs between normal completion and
failure. If the release is the same either way, ignore the second parameter.

## Release Must Not Fail

The release effect's error channel is `never`. If cleanup can report platform
errors, translate them into logs, metrics, or defects according to the owning
boundary. Do not make resource cleanup introduce a new typed failure after the
main program has already exited.

```typescript
import { Effect } from "effect"

type Handle = {
  readonly close: () => Promise<void>
}

declare const openHandle: Effect.Effect<Handle, "OpenError">

const handle = Effect.acquireRelease(
  openHandle,
  (resource) =>
    Effect.promise(() => resource.close()).pipe(
      Effect.tapError((error) => Effect.logError(error)),
      Effect.orDie
    )
)
```

This keeps the finalizer type-compatible while still surfacing unexpected
cleanup defects.

## Acquisition Is Protected

The v3 source documents two protections:

1. the acquire effect is run uninterruptibly
2. the release effect is run uninterruptibly if acquisition succeeded

This prevents the dangerous state where a resource has been acquired but the
runtime never registers its release finalizer.

If you deliberately need interruptible acquisition, v3 also exposes
`Effect.acquireReleaseInterruptible`. Reach for it only when partial acquisition
does not require cleanup or the acquire effect handles its own partial cleanup.

## Using The Scoped Resource

Because `Effect.acquireRelease` returns a scoped effect, most direct use needs
`Effect.scoped`.

```typescript
import { Effect } from "effect"

type Connection = {
  readonly query: (sql: string) => Effect.Effect<string>
  readonly close: Effect.Effect<void>
}

declare const openConnection: Effect.Effect<Connection, "OpenError">

const connection = Effect.acquireRelease(
  openConnection,
  (conn) => conn.close
)

const program = Effect.scoped(
  Effect.gen(function* () {
    const conn = yield* connection
    const result = yield* conn.query("select 1")
    yield* Effect.logInfo(result)
  })
)
```

`Effect.scoped` creates the lifetime boundary. Without it, `Scope.Scope` remains
in the requirement channel.

## Composing Multiple Resources

Acquire resources in dependency order. The scope will release them in reverse.

```typescript
import { Effect } from "effect"

type Database = {
  readonly close: Effect.Effect<void>
}

type Cache = {
  readonly close: Effect.Effect<void>
}

declare const openDatabase: Effect.Effect<Database, "DbOpenError">
declare const openCache: Effect.Effect<Cache, "CacheOpenError">
declare const useBoth: (db: Database, cache: Cache) => Effect.Effect<void>

const database = Effect.acquireRelease(openDatabase, (db) => db.close)
const cache = Effect.acquireRelease(openCache, (cache) => cache.close)

const program = Effect.scoped(
  Effect.gen(function* () {
    const db = yield* database
    const cacheClient = yield* cache
    yield* useBoth(db, cacheClient)
  })
)
```

If cache acquisition fails after the database succeeds, the database release
still runs when the scope closes. If the body is interrupted, both successful
acquisitions are finalized.

## Good Release Functions

Release functions should be:

| Property | Reason |
|---|---|
| idempotent when possible | retries and shutdown paths are easier to reason about |
| untyped-failure only | finalizers must not add typed failures |
| small | cleanup should not become hidden business logic |
| resource-local | the release should close what the acquire opened |
| observable | use Effect logging or metrics for unexpected cleanup problems |

## Common Mistakes

Do not acquire a resource with `Effect.sync` and release it later by hand. That
leaves the lifetime invisible.

Do not put the whole acquire-use-release region inside one `Effect.tryPromise`
callback. That turns structured resource management into one opaque Promise.

Do not call `Effect.scoped` around each individual resource if multiple
dependent resources should share one lifetime. Put one scope around the whole
region.

Do not cast away `Scope.Scope`. The requirement is useful information.

## Cross-references

See also: [Overview](01-overview.md), [Acquire Use Release](04-acquire-use-release.md), [Effect Scoped](05-effect-scoped.md), [Cleanup Order](08-cleanup-order.md).
