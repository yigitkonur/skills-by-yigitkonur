# Add Finalizer
Use `Effect.addFinalizer` to register cleanup in the current scope when acquisition is not best expressed as one value.

## Requirement Shape

`Effect.addFinalizer` requires `Scope.Scope` in the environment.

```typescript
import { Effect, Scope } from "effect"

const registerCleanup: Effect.Effect<void, never, Scope.Scope> =
  Effect.addFinalizer(() => Effect.logInfo("cleanup"))
```

That requirement is intentional. The finalizer needs a scope to attach to.

## The Scoped Boundary Pattern

When you use `Effect.addFinalizer`, wrap the whole scoped region with
`Effect.scoped` unless a larger owner already provides a scope.

```typescript
import { Effect } from "effect"

const program = Effect.scoped(
  Effect.gen(function* () {
    yield* Effect.addFinalizer(() => Effect.logInfo("release local resource"))
    yield* Effect.logInfo("resource is in use")
  })
)
```

This pattern is the safe default:

1. enter `Effect.scoped`
2. register finalizers inside it
3. do the work
4. let `Effect.scoped` close the scope

## Finalizer Receives Exit

The finalizer function receives the `Exit` used to close the scope.

```typescript
import { Effect } from "effect"

const program = Effect.scoped(
  Effect.gen(function* () {
    yield* Effect.addFinalizer((exit) =>
      Effect.logInfo(`scope closed with ${exit._tag}`)
    )

    yield* Effect.fail("boom")
  })
)
```

The finalizer runs for success, failure, defects, and interruption. Inspect the
exit only when cleanup behavior genuinely differs by outcome.

## When To Use It

Use `Effect.addFinalizer` for cleanup that belongs to a scope but is not a
simple acquire-release pair.

Good fits:

| Case | Why |
|---|---|
| stop a heartbeat fiber registered during setup | cleanup is tied to a side process |
| unsubscribe from an event bus | registration may be returned by another API |
| restore temporary global runtime state | finalizer reverses a scoped change |
| close several small handles created by one setup | a single finalizer may be clearer |

If you have a clear acquired value and a release action for that value, prefer
`Effect.acquireRelease`.

## Register After Successful Setup

Register the finalizer after the state it cleans up exists.

```typescript
import { Effect } from "effect"

type Subscription = {
  readonly unsubscribe: Effect.Effect<void>
}

declare const subscribe: Effect.Effect<Subscription, "SubscribeError">
declare const consume: (sub: Subscription) => Effect.Effect<void, "ConsumeError">

const program = Effect.scoped(
  Effect.gen(function* () {
    const sub = yield* subscribe
    yield* Effect.addFinalizer(() => sub.unsubscribe)
    yield* consume(sub)
  })
)
```

If `subscribe` fails, no finalizer is registered because there is no
subscription to release.

## Prefer acquireRelease For Single Resource Values

This manual form is correct:

```typescript
import { Effect } from "effect"

type Subscription = {
  readonly unsubscribe: Effect.Effect<void>
}

declare const subscribe: Effect.Effect<Subscription, "SubscribeError">

const program = Effect.scoped(
  Effect.gen(function* () {
    const sub = yield* subscribe
    yield* Effect.addFinalizer(() => sub.unsubscribe)
    return sub
  })
)
```

But this form makes the ownership clearer:

```typescript
import { Effect } from "effect"

const subscription = Effect.acquireRelease(
  subscribe,
  (sub) => sub.unsubscribe
)
```

Prefer the second form when the finalizer is exactly the release action for the
acquired value.

## LIFO Applies

`Effect.addFinalizer` participates in the same finalizer stack as resources
created with `Effect.acquireRelease`.

```typescript
import { Effect } from "effect"

const program = Effect.scoped(
  Effect.gen(function* () {
    yield* Effect.addFinalizer(() => Effect.logInfo("first"))
    yield* Effect.addFinalizer(() => Effect.logInfo("second"))
    yield* Effect.addFinalizer(() => Effect.logInfo("third"))
  })
)
```

On scope close, the default order is `third`, then `second`, then `first`.

## Cross-references

See also: [Scope](02-scope.md), [Acquire Release](03-acquire-release.md), [Effect Scoped](05-effect-scoped.md), [Cleanup Order](08-cleanup-order.md).
