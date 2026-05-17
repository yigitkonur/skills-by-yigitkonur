# Resource Management Overview
Use Scope-backed resources when cleanup must be deterministic across success, failure, and interruption.

## The Rule

If an Effect program acquires something that must be released, model that
lifetime with `Effect.acquireRelease`, `Effect.acquireUseRelease`,
`Effect.addFinalizer`, or `Scope` utilities.

Do not hide resource cleanup inside ordinary JavaScript control flow. Effect can
only guarantee cleanup it can see as part of the Effect runtime.

## Why Scope Exists

Effect programs can fail, be retried, race, timeout, fork fibers, or be
interrupted by another fiber. Resource cleanup has to survive all of those
paths.

A `Scope` is the runtime structure that records finalizers. When the scope is
closed, Effect runs the finalizers that were registered in that scope.

The important guarantee is not just "run cleanup after success." The guarantee
is:

| Program outcome | Scope behavior |
|---|---|
| Success | closes the scope and runs finalizers |
| Typed failure | closes the scope and runs finalizers |
| Defect | closes the scope and runs finalizers |
| Interruption | closes the scope and runs finalizers |

That last row is the reason Effect resources should not be implemented with
manual cleanup.

## The Interruption Argument

`try/finally` is a JavaScript construct. It is not an Effect finalizer.

When you place resource cleanup inside a Promise callback, Effect sees one
foreign asynchronous operation. If the fiber running that operation is
interrupted, the runtime can stop waiting for it, but it cannot supervise the
cleanup hidden inside that callback. The interruption can happen between the
protected work and the manual cleanup path, and the finalizer never runs from
Effect's point of view.

That is why a resource-management boundary must not be "open the resource,
run some Promise code, then close it in `finally`." The cleanup is invisible to
scopes, finalizer ordering, interruption, tracing, and structured resource
composition.

| Manual shape | Runtime visibility |
|---|---|
| open inside Promise callback | Effect cannot register a finalizer for the acquired value |
| close in `finally` | Effect cannot order it with scoped finalizers |
| interruption during use | Effect can interrupt the fiber without owning the hidden cleanup |
| `Effect.acquireRelease` | Effect registers release in a `Scope` before use continues |

The Effect form makes acquisition and release visible to the runtime:

```typescript
import { Effect } from "effect"

type Connection = {
  readonly query: (sql: string) => Promise<string>
  readonly close: () => Promise<void>
}

declare const openConnection: () => Promise<Connection>

const connection = Effect.acquireRelease(
  Effect.tryPromise(() => openConnection()),
  (conn) => Effect.promise(() => conn.close())
)

const program = Effect.scoped(
  Effect.gen(function* () {
    const conn = yield* connection
    return yield* Effect.tryPromise(() => conn.query("select 1"))
  })
)
```

`connection` has a `Scope` requirement. `Effect.scoped` creates the scope,
runs the program, then closes the scope on every exit path.

## Resource Shapes

Use the smallest resource primitive that matches the lifetime you need.

| Need | Primitive |
|---|---|
| Acquire a value and release it later | `Effect.acquireRelease` |
| Acquire, use, and release in one expression | `Effect.acquireUseRelease` |
| Add cleanup to the current scope | `Effect.addFinalizer` |
| Bound a scoped program locally | `Effect.scoped` |
| Manually manage a closeable scope | `Scope.make` with `Scope.close` |
| Attach a cleanup effect to one action | `Effect.ensuring` |
| Cleanup based on success, failure, or interruption | `Effect.onExit` |

## Scoped Effects

A scoped resource advertises its lifetime requirement in the `R` channel.

```typescript
import { Effect, Scope } from "effect"

type Socket = {
  readonly send: (message: string) => Effect.Effect<void>
  readonly close: Effect.Effect<void>
}

declare const openSocket: Effect.Effect<Socket, "OpenError">

const socket: Effect.Effect<Socket, "OpenError", Scope.Scope> =
  Effect.acquireRelease(openSocket, (resource) => resource.close)

const runnable: Effect.Effect<void, "OpenError"> = Effect.scoped(
  Effect.gen(function* () {
    const resource = yield* socket
    yield* resource.send("ping")
  })
)
```

If you forget the scope boundary, the type tells you: `Scope.Scope` remains in
the requirements. Do not erase it with casts. Provide a scope with
`Effect.scoped`, `Layer.scoped`, `Scope.extend`, or a wider owning scope.

## Finalizer Timing

Finalizers are not run when `Effect.acquireRelease` is constructed. They are
registered when the resource is acquired, and they run when the owning scope
closes.

This matters for services and layers. A scoped database pool in a layer stays
open for the layer lifetime, not just for the line that constructed it.

## Dependency Ordering

Scopes release finalizers in last-in, first-out order by default. Acquire
dependencies first and dependents second:

1. Open database pool.
2. Open repository using the pool.
3. Open subscription using the repository.

Cleanup happens in reverse:

1. Close subscription.
2. Close repository.
3. Close database pool.

That ordering is why scoped resources compose cleanly without each component
knowing every other component's cleanup function.

## Cross-references

See also: [Scope](02-scope.md), [Acquire Release](03-acquire-release.md), [Effect Scoped](05-effect-scoped.md), [Cleanup Order](08-cleanup-order.md).
