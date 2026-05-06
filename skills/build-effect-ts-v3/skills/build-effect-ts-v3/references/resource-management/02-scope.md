# Scope
Use `Scope` when you need an explicit lifetime boundary or need to pass a scoped resource into a wider owner.

## What Scope Represents

`Scope.Scope` is the environment service that records finalizers. A scoped
effect requires it in the `R` channel because the effect needs a place to
register cleanup.

`Scope.Closeable` is a scope you can close yourself. Closing it runs the
registered finalizers.

From the v3 source:

| API | Shape |
|---|---|
| `Effect.scope` | gets the current `Scope.Scope` |
| `Scope.make` | creates a `Scope.Closeable` |
| `Scope.addFinalizer` | adds cleanup that does not inspect `Exit` |
| `Scope.addFinalizerExit` | adds cleanup that receives the closing `Exit` |
| `Scope.close` | closes a closeable scope |
| `Scope.extend` | provides a scope without closing it |

## Let Effect Own Most Scopes

Most application code should not call `Scope.make`. Use `Effect.scoped` around
the scoped region:

```typescript
import { Effect } from "effect"

const program = Effect.scoped(
  Effect.gen(function* () {
    yield* Effect.addFinalizer(() => Effect.logInfo("cleanup"))
    yield* Effect.logInfo("work")
  })
)
```

This creates a scope, runs the body, and closes the scope with the body's exit.

Use explicit `Scope` operations when you are writing framework integration,
resource pools, tests that inspect cleanup, or low-level lifecycle utilities.

## Creating A Closeable Scope

`Scope.make` creates a closeable scope. The optional execution strategy controls
how finalizers run when the scope closes.

```typescript
import { Effect, ExecutionStrategy, Exit, Scope } from "effect"

const program = Effect.gen(function* () {
  const scope = yield* Scope.make(ExecutionStrategy.sequential)

  yield* Scope.addFinalizer(
    scope,
    Effect.logInfo("closing explicit resource")
  )

  yield* Scope.close(scope, Exit.succeed("done"))
})
```

Use this directly only when you really need manual ownership. A closeable scope
is easy to leak if you create it without a guaranteed close path.

## Closing With Exit

`Scope.close(scope, exit)` passes the closing `Exit` to finalizers registered
with `Scope.addFinalizerExit` or `Effect.addFinalizer`.

```typescript
import { Effect, Exit, Scope } from "effect"

const program = Effect.gen(function* () {
  const scope = yield* Scope.make()

  yield* Scope.addFinalizerExit(scope, (exit) =>
    Effect.logInfo(`scope closed with ${exit._tag}`)
  )

  yield* Scope.close(scope, Exit.fail("shutdown"))
})
```

Choose an exit that reflects why the owner is closing the scope. For tests,
`Exit.succeed("done")` is often enough. Runtime-owned scopes receive the real
exit of the scoped effect.

## Adding Finalizers Directly

`Scope.addFinalizer(scope, effect)` registers a cleanup effect on a specific
scope. The cleanup action is run when that scope closes.

```typescript
import { Effect, Exit, Scope } from "effect"

const program = Effect.gen(function* () {
  const scope = yield* Scope.make()

  yield* Scope.addFinalizer(scope, Effect.logInfo("first cleanup"))
  yield* Scope.addFinalizer(scope, Effect.logInfo("second cleanup"))

  yield* Scope.close(scope, Exit.succeed("done"))
})
```

By default, finalizers run sequentially in reverse registration order. In this
example, `second cleanup` runs before `first cleanup`.

## Effect.addFinalizer Versus Scope.addFinalizer

Use `Effect.addFinalizer` when you are already inside a scoped effect and want
to add cleanup to the current scope.

```typescript
import { Effect } from "effect"

const scopedProgram = Effect.gen(function* () {
  yield* Effect.addFinalizer(() => Effect.logInfo("current scope cleanup"))
  yield* Effect.logInfo("work")
})

const runnable = Effect.scoped(scopedProgram)
```

Use `Scope.addFinalizer` when you have an explicit `Scope.Scope` value and want
to register cleanup on that exact scope.

```typescript
import { Effect, Scope } from "effect"

const registerOn = (scope: Scope.Scope) =>
  Scope.addFinalizer(scope, Effect.logInfo("cleanup on provided scope"))
```

Both forms register finalizers. The difference is where the scope comes from.

## Extending A Scoped Resource

`Scope.extend(effect, scope)` provides a scope to an effect that requires
`Scope.Scope`, but it does not close that scope when the effect completes.

Use it when the resource must outlive the local acquisition site.

```typescript
import { Effect, Scope } from "effect"

type Client = {
  readonly request: Effect.Effect<string>
  readonly close: Effect.Effect<void>
}

declare const openClient: Effect.Effect<Client>

const client = Effect.acquireRelease(openClient, (resource) => resource.close)

const allocateIn = (scope: Scope.Scope) =>
  Scope.extend(client, scope)
```

`allocateIn(scope)` returns the client while registering its release in the
provided scope. The caller that owns `scope` decides when cleanup happens.

## Do Not Close A Scope You Do Not Own

If an effect receives `Scope.Scope` from the environment, it should add
finalizers or extend resources into it. It should not close it. Closing a
borrowed scope can release resources still needed by the actual owner.

Ownership rule:

| Scope source | Who closes it |
|---|---|
| Created by `Effect.scoped` | `Effect.scoped` |
| Created by `Layer.scoped` | layer runtime |
| Created by `Scope.make` in your code | your code |
| Received from `Effect.scope` | the surrounding owner |

## Prefer Higher-Level Brackets

If all you want is acquire, use, and release in one region, prefer
`Effect.acquireUseRelease`. It handles scope creation and close timing for that
single bracket.

If you need a resource value to be composed with other scoped values, use
`Effect.acquireRelease` and let `Effect.scoped` or a layer own the boundary.

## Cross-references

See also: [Overview](01-overview.md), [Effect Scoped](05-effect-scoped.md), [Add Finalizer](06-add-finalizer.md), [Cleanup Order](08-cleanup-order.md).
