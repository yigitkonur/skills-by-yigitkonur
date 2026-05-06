# Ref
Use `Ref` for atomic shared state when every update can be computed synchronously from the current value.

## Model

`Ref.Ref<A>` is a mutable reference whose operations are effects. It stores one
immutable value of type `A` and exposes atomic read, write, and modify
operations.

```typescript
import { Effect, Ref } from "effect"

const program = Effect.gen(function* () {
  const ref = yield* Ref.make(0)
  const value = yield* Ref.get(ref)

  return value
})
```

The constructor is effectful because allocation is part of the Effect runtime
model. Create the `Ref` inside a layer, service constructor, scoped resource, or
program edge; do not hide it in a module-level mutable variable.

## Core Operations

Use these operations most often:

| Operation | Result | Use when |
|---|---|---|
| `Ref.make(initial)` | `Effect<Ref<A>>` | Allocate the cell |
| `Ref.get(ref)` | `Effect<A>` | Read the current value |
| `Ref.set(ref, value)` | `Effect<void>` | Replace the value |
| `Ref.update(ref, f)` | `Effect<void>` | Transform the value and ignore the new value |
| `Ref.updateAndGet(ref, f)` | `Effect<A>` | Transform and return the new value |
| `Ref.getAndUpdate(ref, f)` | `Effect<A>` | Transform and return the old value |
| `Ref.modify(ref, f)` | `Effect<B>` | Return a derived result and install a new value atomically |

`Ref` update functions are pure. If the update needs an effect, use
`SynchronizedRef`.

## Pure Updates

Keep values immutable and replace the whole state.

```typescript
import { Effect, Ref } from "effect"

interface Cart {
  readonly items: ReadonlyArray<string>
}

const addItem = (cart: Ref.Ref<Cart>, item: string) =>
  Ref.update(cart, (state) => ({
    items: state.items.concat(item)
  }))

const program = Effect.gen(function* () {
  const cart = yield* Ref.make<Cart>({ items: [] })

  yield* addItem(cart, "book")
  yield* addItem(cart, "pen")

  return yield* Ref.get(cart)
})
```

Do not mutate arrays or objects inside the reference. Treat the old value as a
snapshot and return a new value.

## `modify` For Read-And-Write Decisions

Use `Ref.modify` when the result must be derived from the exact state that is
being replaced.

```typescript
import { Effect, Ref } from "effect"

interface Sequence {
  readonly next: number
}

const allocateId = (sequence: Ref.Ref<Sequence>) =>
  Ref.modify(sequence, (state) => [
    `job-${state.next}`,
    { next: state.next + 1 }
  ] as const)

const program = Effect.gen(function* () {
  const sequence = yield* Ref.make<Sequence>({ next: 1 })

  const first = yield* allocateId(sequence)
  const second = yield* allocateId(sequence)

  return [first, second] as const
})
```

This avoids the stale-read shape:

```typescript
import { Effect, Ref } from "effect"

interface Sequence {
  readonly next: number
}

const allocateIdWrong = (sequence: Ref.Ref<Sequence>) =>
  Effect.gen(function* () {
    const state = yield* Ref.get(sequence)
    yield* Ref.set(sequence, { next: state.next + 1 })
    return `job-${state.next}`
  })
```

The two-step version can race if another fiber updates between `get` and `set`.
When the result and next value depend on the same snapshot, use `modify`.

## Optional Updates

Use `updateSome` when an update should only happen for some states.

```typescript
import { Effect, Option, Ref } from "effect"

type Gate =
  | { readonly _tag: "Open"; readonly count: number }
  | { readonly _tag: "Closed" }

const passThrough = (gate: Ref.Ref<Gate>) =>
  Ref.updateSome(gate, (state) =>
    state._tag === "Open"
      ? Option.some({ _tag: "Open", count: state.count + 1 } as const)
      : Option.none()
  )

const program = Effect.gen(function* () {
  const gate = yield* Ref.make<Gate>({ _tag: "Open", count: 0 })

  yield* passThrough(gate)

  return yield* Ref.get(gate)
})
```

Use `modifySome` when the skipped branch should return a fallback result.

## Shared State In Services

A `Ref` often belongs inside a service implementation.

```typescript
import { Effect, Ref } from "effect"

interface Counter {
  readonly increment: Effect.Effect<number>
  readonly current: Effect.Effect<number>
}

const makeCounter = Effect.gen(function* () {
  const ref = yield* Ref.make(0)

  return {
    increment: Ref.updateAndGet(ref, (n) => n + 1),
    current: Ref.get(ref)
  } satisfies Counter
})
```

The service exposes effects, not the raw `Ref`, unless consumers genuinely need
to coordinate atomic operations themselves.

## Concurrent Updates

`Ref.update` is safe for concurrent fibers.

```typescript
import { Effect, Ref } from "effect"

const program = Effect.gen(function* () {
  const counter = yield* Ref.make(0)

  yield* Effect.all(
    [
      Ref.update(counter, (n) => n + 1),
      Ref.update(counter, (n) => n + 1),
      Ref.update(counter, (n) => n + 1)
    ],
    { concurrency: 3, discard: true }
  )

  return yield* Ref.get(counter)
})
```

The result is `3`. Each update is atomic even though the fibers run
concurrently.

## When Not To Use Ref

Do not use `Ref` when the update function needs to call a database, wait on a
queue, run validation effects, or use services from the environment. Use
`SynchronizedRef`.

Do not use `Ref` to notify observers. Use `SubscriptionRef` when consumers need
a stream of changes.

Do not use `Ref` for request context or tracing data that should differ per
fiber. Use `FiberRef`.

Do not store mutable objects in a `Ref` and mutate them in place. The atomicity
only protects replacing the reference value; it does not make nested mutation
safe.

## Cross-references

See also: [01-overview.md](01-overview.md), [03-synchronizedref.md](03-synchronizedref.md), [04-subscription-ref.md](04-subscription-ref.md), [06-state-patterns.md](06-state-patterns.md).
