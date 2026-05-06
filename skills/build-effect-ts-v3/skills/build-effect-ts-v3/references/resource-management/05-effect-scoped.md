# Effect Scoped
Use `Effect.scoped` to create the boundary that supplies `Scope.Scope` and closes it when the effect exits.

## What It Removes

Scoped resource effects require `Scope.Scope` in the environment. `Effect.scoped`
creates a scope, provides it to the effect, and removes that requirement from
the resulting type.

```typescript
import { Effect, Scope } from "effect"

type Resource = {
  readonly close: Effect.Effect<void>
}

declare const openResource: Effect.Effect<Resource, "OpenError">

const resource: Effect.Effect<Resource, "OpenError", Scope.Scope> =
  Effect.acquireRelease(openResource, (value) => value.close)

const runnable: Effect.Effect<Resource, "OpenError"> =
  Effect.scoped(resource)
```

The scoped boundary is what makes the resource runnable without a caller
providing `Scope.Scope`.

## Use One Boundary Around The Region

Put `Effect.scoped` around the whole region whose resources should share a
lifetime.

```typescript
import { Effect } from "effect"

type Database = { readonly close: Effect.Effect<void> }
type Subscription = { readonly close: Effect.Effect<void> }

declare const openDatabase: Effect.Effect<Database, "DbError">
declare const openSubscription: (db: Database) => Effect.Effect<Subscription, "SubError">
declare const serve: (sub: Subscription) => Effect.Effect<void, "ServeError">

const database = Effect.acquireRelease(openDatabase, (db) => db.close)

const program = Effect.scoped(
  Effect.gen(function* () {
    const db = yield* database
    const sub = yield* Effect.acquireRelease(
      openSubscription(db),
      (value) => value.close
    )
    yield* serve(sub)
  })
)
```

The database and subscription share the same scope. The subscription is
released first, then the database.

## Do Not Scope Too Early

Scoping too early shortens the resource lifetime and returns values that may
already be closed.

```typescript
import { Effect } from "effect"

type Client = {
  readonly request: Effect.Effect<string>
  readonly close: Effect.Effect<void>
}

declare const openClient: Effect.Effect<Client>

const client = Effect.acquireRelease(openClient, (resource) => resource.close)

const badClient = Effect.scoped(client)
```

`badClient` returns a `Client` after its scope has already closed. That is only
safe if the value is a snapshot, not a live resource. For live clients, keep use
inside the scoped region.

```typescript
import { Effect } from "effect"

const program = Effect.scoped(
  Effect.gen(function* () {
    const resource = yield* client
    return yield* resource.request
  })
)
```

## Scoped Boundary Pattern

When a helper requires `Scope.Scope`, expose either a scoped effect or a runnable
operation, not a cast.

```typescript
import { Effect, Scope } from "effect"

type Lease = {
  readonly release: Effect.Effect<void>
}

declare const acquireLease: Effect.Effect<Lease, "LeaseError">

const lease: Effect.Effect<Lease, "LeaseError", Scope.Scope> =
  Effect.acquireRelease(acquireLease, (value) => value.release)

const withLease = <A, E, R>(
  use: (lease: Lease) => Effect.Effect<A, E, R>
) =>
  Effect.scoped(
    Effect.gen(function* () {
      const value = yield* lease
      return yield* use(value)
    })
  )
```

The helper hides the scope requirement because it owns the whole lifetime.

## Layer Boundaries

Do not wrap a scoped service constructor in `Effect.scoped` before giving it to
`Layer.scoped`. The layer is the lifetime owner.

```typescript
import { Context, Effect, Layer } from "effect"

class Client extends Context.Tag("app/Client")<
  Client,
  { readonly request: Effect.Effect<string> }
>() {}

declare const openClient: Effect.Effect<
  { readonly request: Effect.Effect<string>; readonly close: Effect.Effect<void> }
>

const ClientLive = Layer.scoped(
  Client,
  Effect.acquireRelease(openClient, (client) => client.close)
)
```

The client remains open for the layer lifetime.

## When A Scope Requirement Is Correct

Sometimes the correct public API is a scoped effect. A constructor for a
long-lived client should often return `Effect.Effect<Client, E, Scope.Scope>` so
the caller chooses the lifetime.

Use `Effect.scoped` only at a real owner boundary:

| Owner | Boundary |
|---|---|
| one local operation | `Effect.scoped` |
| service layer | `Layer.scoped` |
| externally managed framework lifetime | `Scope.extend` into that scope |
| direct bracket | `Effect.acquireUseRelease` |

## Cross-references

See also: [Overview](01-overview.md), [Scope](02-scope.md), [Acquire Release](03-acquire-release.md), [Add Finalizer](06-add-finalizer.md).
