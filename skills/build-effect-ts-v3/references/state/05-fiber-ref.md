# FiberRef
Use `FiberRef` for fiber-local state such as request ids, log context, and runtime-local settings.

## Model

`FiberRef.FiberRef<A>` stores a value for the current fiber. Forked fibers
inherit the parent's value, but ordinary updates are local to the fiber that
performs them.

```typescript
import { Effect, FiberRef } from "effect"

const program = Effect.scoped(
  Effect.gen(function* () {
    const ref = yield* FiberRef.make("root")

    yield* FiberRef.set(ref, "current")

    return yield* FiberRef.get(ref)
  })
)
```

`FiberRef.make` is scoped in v3. Wrap construction in `Effect.scoped` unless the
surrounding layer or resource already provides `Scope.Scope`.

## Request-Scoped Context With `Effect.locally`

Use `Effect.locally(ref, value)(effect)` to run an effect with a temporary
fiber-local value. The runtime restores the previous value when the effect
finishes, fails, or is interrupted.

```typescript
import { Effect, FiberRef } from "effect"

type RequestId = string

const program = Effect.scoped(
  Effect.gen(function* () {
    const requestId = yield* FiberRef.make<RequestId>("missing")

    const currentRequestId = FiberRef.get(requestId)

    const handleRequest = (id: RequestId) =>
      Effect.locally(requestId, id)(
        Effect.gen(function* () {
          const idForLogs = yield* currentRequestId
          yield* Effect.log(`handling ${idForLogs}`)
          return idForLogs
        })
      )

    const first = yield* handleRequest("req-1")
    const after = yield* currentRequestId

    return { first, after }
  })
)
```

The returned `after` value is `"missing"`. The request id is scoped to
`handleRequest`, not stored globally.

## Use `getWith` To Read And Continue

`FiberRef.getWith` is useful when the next effect depends on the current
fiber-local value.

```typescript
import { Effect, FiberRef } from "effect"

const program = Effect.scoped(
  Effect.gen(function* () {
    const requestId = yield* FiberRef.make("missing")

    const logWithRequestId = (message: string) =>
      FiberRef.getWith(requestId, (id) =>
        Effect.log(`[${id}] ${message}`)
      )

    return yield* Effect.locally(requestId, "req-2")(
      logWithRequestId("loaded profile")
    )
  })
)
```

Use this instead of passing the value manually through every helper when the
value is true runtime context.

## Fork Inheritance

A child fiber inherits the value visible at fork time.

```typescript
import { Effect, Fiber, FiberRef } from "effect"

const program = Effect.scoped(
  Effect.gen(function* () {
    const ref = yield* FiberRef.make("root")

    const child = yield* Effect.locally(ref, "parent-scope")(
      Effect.gen(function* () {
        const fiber = yield* Effect.fork(FiberRef.get(ref))
        return yield* Fiber.join(fiber)
      })
    )

    const parentAfter = yield* FiberRef.get(ref)

    return { child, parentAfter }
  })
)
```

`child` is `"parent-scope"`, while `parentAfter` is `"root"`.

## Custom Fork And Join

`FiberRef.make` accepts `fork` and `join` options. Use them sparingly and only
when child fibers need customized inheritance or parent-child merge behavior.

```typescript
import { Effect, FiberRef } from "effect"

const program = Effect.scoped(
  Effect.gen(function* () {
    const breadcrumbs = yield* FiberRef.make<ReadonlyArray<string>>([], {
      fork: (items) => items.concat("forked"),
      join: (parent, child) => parent.concat(child)
    })

    yield* FiberRef.update(breadcrumbs, (items) => items.concat("root"))

    return yield* FiberRef.get(breadcrumbs)
  })
)
```

For request ids, the default behavior is usually enough. Custom `join` matters
more for accumulated diagnostic context.

## Built-In FiberRefs

Effect itself uses `FiberRef` for runtime-local settings such as loggers, log
levels, log annotations, request cache state, and current concurrency. That is a
good signal for application usage: use `FiberRef` for contextual runtime state,
not business data shared across all requests.

If business state must be shared and updated by multiple fibers, choose `Ref`,
`SynchronizedRef`, or `SubscriptionRef`.

## Avoid Shared Refs For Request Context

This is the wrong shape:

```typescript
import { Effect, Ref } from "effect"

const wrong = Effect.gen(function* () {
  const requestId = yield* Ref.make("missing")

  const handle = (id: string) =>
    Effect.gen(function* () {
      yield* Ref.set(requestId, id)
      return yield* Ref.get(requestId)
    })

  return yield* Effect.all(
    [handle("req-1"), handle("req-2")],
    { concurrency: 2 }
  )
})
```

Both handlers share one cell. They can overwrite each other. Use a `FiberRef`
and `Effect.locally` so each request gets a scoped value.

## When Not To Use FiberRef

Do not use `FiberRef` for counters, caches, queues, or domain state that should
be shared across fibers. Updates are local by design.

Do not use it to hide required dependencies. If a function truly requires a
service, model that service in `Context` or a layer.

Do not allocate a new `FiberRef` inside a tight loop. Allocate once in the
service or scoped program that owns the contextual value.

## Cross-references

See also: [01-overview.md](01-overview.md), [02-ref.md](02-ref.md), [03-synchronizedref.md](03-synchronizedref.md), [04-subscription-ref.md](04-subscription-ref.md), [services-layers/02-context-tag.md](../services-layers/02-context-tag.md).
