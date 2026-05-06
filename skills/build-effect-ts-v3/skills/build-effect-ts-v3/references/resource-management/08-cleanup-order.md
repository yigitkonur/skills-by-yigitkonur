# Cleanup Order
Acquire dependent resources in dependency order because Effect finalizers run last-in, first-out by default.

## Default Order

Effect scopes run finalizers sequentially in reverse order of registration by
default. This is last-in, first-out ordering.

If a later resource depends on an earlier resource, this is exactly what you
want:

1. acquire base dependency
2. acquire resource that depends on it
3. acquire top-level worker that depends on both
4. close top-level worker
5. close dependent resource
6. close base dependency

## Three Nested Resources

This example shows three nested resources: database, repository, and
subscription. They are acquired in that order and released in reverse order.

```typescript
import { Effect } from "effect"

type Database = {
  readonly close: Effect.Effect<void>
}

type Repository = {
  readonly close: Effect.Effect<void>
}

type Subscription = {
  readonly close: Effect.Effect<void>
}

declare const openDatabase: Effect.Effect<Database, "DbOpenError">
declare const openRepository: (db: Database) => Effect.Effect<Repository, "RepoOpenError">
declare const openSubscription: (repo: Repository) => Effect.Effect<Subscription, "SubOpenError">
declare const serve: (sub: Subscription) => Effect.Effect<void, "ServeError">

const program = Effect.scoped(
  Effect.gen(function* () {
    const db = yield* Effect.acquireRelease(
      openDatabase,
      (resource) =>
        Effect.logInfo("release database").pipe(
          Effect.zipRight(resource.close)
        )
    )

    const repo = yield* Effect.acquireRelease(
      openRepository(db),
      (resource) =>
        Effect.logInfo("release repository").pipe(
          Effect.zipRight(resource.close)
        )
    )

    const sub = yield* Effect.acquireRelease(
      openSubscription(repo),
      (resource) =>
        Effect.logInfo("release subscription").pipe(
          Effect.zipRight(resource.close)
        )
    )

    yield* serve(sub)
  })
)
```

The release order is:

1. subscription
2. repository
3. database

This order holds whether `serve(sub)` succeeds, fails, or is interrupted.

## addFinalizer Uses The Same Stack

Manual finalizers registered with `Effect.addFinalizer` are part of the same
scope stack.

```typescript
import { Effect } from "effect"

const program = Effect.scoped(
  Effect.gen(function* () {
    yield* Effect.addFinalizer(() => Effect.logInfo("release A"))
    yield* Effect.addFinalizer(() => Effect.logInfo("release B"))
    yield* Effect.addFinalizer(() => Effect.logInfo("release C"))
  })
)
```

The release order is `C`, then `B`, then `A`.

## Acquire Dependencies First

The LIFO rule means acquisition order is a design decision.

| Relationship | Acquire order | Release order |
|---|---|---|
| child depends on parent | parent, then child | child, then parent |
| subscription uses repository | repository, then subscription | subscription, then repository |
| transaction uses connection | connection, then transaction | transaction, then connection |
| temporary annotation wraps work | annotation, then work finalizers | work finalizers, then annotation |

When order matters, do not acquire resources in whatever order is convenient for
local code. Acquire the resource that must outlive the others first.

## When Not To Parallelize Finalizers

Effect exposes finalizer execution-strategy controls such as
`Effect.parallelFinalizers`, but parallel cleanup is only safe for independent
resources.

Keep the default sequential LIFO behavior when:

1. one resource was created from another
2. cleanup operations mutate shared state
3. release logs or metrics need deterministic ordering
4. rollback steps must happen in reverse setup order

Parallel finalizers are a performance choice, not the default safety choice.

## Cross-references

See also: [Overview](01-overview.md), [Scope](02-scope.md), [Acquire Release](03-acquire-release.md), [Add Finalizer](06-add-finalizer.md).
