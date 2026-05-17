# State Overview
Choose the smallest Effect state primitive that matches the sharing and observation boundary.

## Decision Tree

Use this tree before writing stateful code:

```text
Need atomic local writes?
  -> Ref

Need an update function that performs effects?
  -> SynchronizedRef

Need a change Stream for observers?
  -> SubscriptionRef

Need per-fiber state inherited by child fibers?
  -> FiberRef
```

If none of those cases fits, reconsider whether the value is state at all. Many
programs only need ordinary values passed through `Effect.gen`, services in
`Context`, or stream elements flowing through `Stream`.

## Ref Family At A Glance

| Primitive | Sharing model | Update function | Observation | Typical use |
|---|---|---|---|---|
| `Ref.Ref<A>` | Shared by all fibers that hold it | Pure `(A) => A` | Pull with `Ref.get` | Counters, flags, immutable snapshots |
| `SynchronizedRef.SynchronizedRef<A>` | Shared by all fibers that hold it | Effectful `(A) => Effect<A, E, R>` | Pull with `SynchronizedRef.get` | Cache refreshes, guarded loads, serialized writes |
| `SubscriptionRef.SubscriptionRef<A>` | Shared by all fibers that hold it | Pure or effectful | Pull and subscribe with `ref.changes` | Reactive model state, live dashboards, UI backing stores |
| `FiberRef.FiberRef<A>` | Local to the current fiber, inherited by forked fibers | Pure local mutation | Read in current fiber | Request id, log annotation state, runtime-local settings |

The common mistake is reaching for a mutable closure because it feels smaller.
In Effect code, a closure with `let current = ...` is invisible to the runtime:
it has no typed construction effect, no interruption behavior, no stream of
changes, and no per-fiber semantics. Use the Ref family instead.

## `Ref` Is The Default

Pick `Ref` when updates are pure and the current value is enough.

```typescript
import { Effect, Ref } from "effect"

const program = Effect.gen(function* () {
  const count = yield* Ref.make(0)

  yield* Ref.update(count, (n) => n + 1)
  yield* Ref.update(count, (n) => n + 1)

  return yield* Ref.get(count)
})
```

`Ref.update` is atomic. If multiple fibers run updates concurrently, each update
sees a coherent current value and installs a coherent next value.

## Upgrade To `SynchronizedRef` For Effectful Updates

Use `SynchronizedRef` when the new state depends on an effect performed inside
the update.

```typescript
import { Effect, SynchronizedRef } from "effect"

declare const loadFreshToken: Effect.Effect<string, "TokenUnavailable">

const program = Effect.gen(function* () {
  const token = yield* SynchronizedRef.make("initial")

  yield* SynchronizedRef.updateEffect(token, () => loadFreshToken)

  return yield* SynchronizedRef.get(token)
})
```

This is not just `Ref` plus `flatMap`. The effectful update is serialized by the
reference, so concurrent updaters do not race through stale reads.

## Upgrade To `SubscriptionRef` For Streams

Use `SubscriptionRef` when readers need a live stream of state changes.

```typescript
import { Effect, Fiber, Stream, SubscriptionRef } from "effect"

const program = Effect.gen(function* () {
  const ref = yield* SubscriptionRef.make(0)

  const firstThree = yield* Stream.take(ref.changes, 3).pipe(
    Stream.runCollect,
    Effect.fork
  )

  yield* SubscriptionRef.set(ref, 1)
  yield* SubscriptionRef.set(ref, 2)

  return yield* Fiber.join(firstThree)
})
```

`ref.changes` emits the value visible at subscription time and subsequent
changes. Use `SubscriptionRef.make`; do not build this with an ad hoc `PubSub`
unless the model is genuinely not "current value plus updates".

## Use `FiberRef` For Fiber-Local Context

Use `FiberRef` when state must be scoped to the fiber running an effect.

```typescript
import { Effect, FiberRef } from "effect"

const program = Effect.scoped(
  Effect.gen(function* () {
    const requestId = yield* FiberRef.make("missing")

    const read = FiberRef.get(requestId)
    const handled = Effect.locally(requestId, "req-123")(read)

    return yield* handled
  })
)
```

`FiberRef` is the right primitive for request-scoped context. It is not a
replacement for shared mutable state: another fiber can inherit the value, but
ordinary updates stay local to the fiber.

## Anti-patterns

Avoid `let` variables outside an effect to coordinate fibers. They bypass
Effect's concurrency model and make tests order-dependent.

Avoid `SubscriptionRef` when nobody subscribes to `changes`. The stream support
has a purpose; if there are no observers, `Ref` or `SynchronizedRef` is simpler.

## Cross-references

See also: [02-ref.md](02-ref.md), [03-synchronizedref.md](03-synchronizedref.md), [04-subscription-ref.md](04-subscription-ref.md), [05-fiber-ref.md](05-fiber-ref.md), [06-state-patterns.md](06-state-patterns.md).
