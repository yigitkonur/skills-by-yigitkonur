# SubscriptionRef
Use `SubscriptionRef` when state needs both current-value operations and a `Stream` of changes.

## Model

`SubscriptionRef.SubscriptionRef<A>` extends `SynchronizedRef<A>` and adds a
`readonly changes: Stream.Stream<A>` field. It is the right state primitive
when readers need to react to updates instead of repeatedly polling.

```typescript
import { Effect, Stream, SubscriptionRef } from "effect"

const program = Effect.gen(function* () {
  const ref = yield* SubscriptionRef.make(0)

  const observed = Stream.take(ref.changes, 1).pipe(Stream.runCollect)

  return yield* observed
})
```

Always use `SubscriptionRef.make(initial)`. Avoid the unsafe constructor form:
it is not available in every Effect 3.x minor and it bypasses the ordinary
allocation effect.

## What `changes` Emits

Every run of `ref.changes` emits the value visible when that stream starts, then
emits later updates.

```typescript
import { Effect, Fiber, Stream, SubscriptionRef } from "effect"

const program = Effect.gen(function* () {
  const ref = yield* SubscriptionRef.make(0)

  yield* SubscriptionRef.set(ref, 1)

  const snapshotAndNext = yield* Stream.take(ref.changes, 2).pipe(
    Stream.runCollect,
    Effect.fork
  )

  yield* SubscriptionRef.set(ref, 2)

  return yield* Fiber.join(snapshotAndNext)
})
```

The collected values are `1` and `2`: the current value at subscription time,
then the next update.

## Current Value Operations

Use ordinary reference operations for reads and writes.

```typescript
import { Effect, SubscriptionRef } from "effect"

interface Model {
  readonly selectedUserId: string
  readonly revision: number
}

const selectUser = (
  state: SubscriptionRef.SubscriptionRef<Model>,
  selectedUserId: string
) =>
  SubscriptionRef.update(state, (model) => ({
    selectedUserId,
    revision: model.revision + 1
  }))

const program = Effect.gen(function* () {
  const state = yield* SubscriptionRef.make<Model>({
    selectedUserId: "u1",
    revision: 0
  })

  yield* selectUser(state, "u2")

  return yield* SubscriptionRef.get(state)
})
```

`SubscriptionRef.set`, `update`, and `modify` publish changes to subscribers.

## Effectful Updates

Because `SubscriptionRef` extends `SynchronizedRef`, it supports effectful
updates.

```typescript
import { Effect, SubscriptionRef } from "effect"

interface SearchState {
  readonly query: string
  readonly results: ReadonlyArray<string>
}

declare const search: (
  query: string
) => Effect.Effect<ReadonlyArray<string>, "SearchUnavailable">

const runSearch = (
  state: SubscriptionRef.SubscriptionRef<SearchState>,
  query: string
) =>
  SubscriptionRef.updateEffect(state, () =>
    Effect.map(search(query), (results) => ({
      query,
      results
    }))
  )
```

Subscribers see the committed state after the effectful update succeeds. If the
update fails, no new state is published.

## Forking A Consumer

Run the stream in a fiber when observation is part of a larger program.

```typescript
import { Effect, Fiber, Stream, SubscriptionRef } from "effect"

const program = Effect.gen(function* () {
  const ref = yield* SubscriptionRef.make(0)

  const observer = yield* ref.changes.pipe(
    Stream.take(3),
    Stream.tap((n) => Effect.log(`count=${n}`)),
    Stream.runDrain,
    Effect.fork
  )

  yield* SubscriptionRef.set(ref, 1)
  yield* SubscriptionRef.set(ref, 2)

  yield* Fiber.join(observer)
})
```

Use `Effect.log` for examples and runtime logging. Do not turn stream consumers
into side-effecting callbacks outside Effect.

## React And Effect-Atom Boundary

`SubscriptionRef` is the upstream primitive for Atom's reactive layer: a current
value plus a stream of updates. UI bindings should adapt the stream into React
state at the boundary instead of replacing `SubscriptionRef` with component
local mutation.

See [frontend-atom/05-react-hooks.md](../frontend-atom/05-react-hooks.md) for
the hook-facing layer that consumes this model.

A backend or service module can expose a small state API:

```typescript
import { Effect, Stream, SubscriptionRef } from "effect"

interface UserView {
  readonly name: string
  readonly loading: boolean
}

interface UserViewStore {
  readonly changes: Stream.Stream<UserView>
  readonly get: Effect.Effect<UserView>
  readonly setLoading: (loading: boolean) => Effect.Effect<void>
}

const makeUserViewStore = Effect.gen(function* () {
  const ref = yield* SubscriptionRef.make<UserView>({
    name: "Anonymous",
    loading: false
  })

  return {
    changes: ref.changes,
    get: SubscriptionRef.get(ref),
    setLoading: (loading) =>
      SubscriptionRef.update(ref, (state) => ({
        ...state,
        loading
      }))
  } satisfies UserViewStore
})
```

The React side should consume `changes`; non-UI callers can still use `get` and
commands.

## When Not To Use SubscriptionRef

Do not use `SubscriptionRef` merely because the word "state" appears. If nobody
subscribes to `changes`, use `Ref` or `SynchronizedRef`.

Do not expose the raw reference when callers only need a stream and commands.
Expose the narrow interface.

Do not use `SubscriptionRef` for request-scoped context. Use `FiberRef` with
`Effect.locally` so concurrent requests do not share the value.

## Cross-references

See also: [01-overview.md](01-overview.md), [02-ref.md](02-ref.md), [03-synchronizedref.md](03-synchronizedref.md), [05-fiber-ref.md](05-fiber-ref.md), [frontend-atom/05-react-hooks.md](../frontend-atom/05-react-hooks.md).
