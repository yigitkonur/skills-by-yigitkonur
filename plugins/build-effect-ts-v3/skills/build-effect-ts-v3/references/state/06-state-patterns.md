# State Patterns
Use these small patterns as starting points for common Effect state designs.

## Counter

Use `Ref.updateAndGet` when callers need the incremented value.

```typescript
import { Effect, Ref } from "effect"

interface Counter {
  readonly next: Effect.Effect<number>
  readonly current: Effect.Effect<number>
}

const makeCounter = Effect.gen(function* () {
  const ref = yield* Ref.make(0)

  return {
    next: Ref.updateAndGet(ref, (n) => n + 1),
    current: Ref.get(ref)
  } satisfies Counter
})
```

## Id Allocator

Use `Ref.modify` when returning a value and advancing state must be atomic.

```typescript
import { Effect, Ref } from "effect"

interface IdState {
  readonly next: number
}

const makeIdAllocator = Effect.gen(function* () {
  const state = yield* Ref.make<IdState>({ next: 1 })

  const allocate = Ref.modify(state, (current) => [
    `task-${current.next}`,
    { next: current.next + 1 }
  ] as const)

  return { allocate }
})
```

## Effectful Cache Refresh

Use `SynchronizedRef` when loading a fresh value is effectful.

```typescript
import { Effect, SynchronizedRef } from "effect"

interface CacheState {
  readonly value: string
  readonly loadedAt: number
}

declare const loadValue: Effect.Effect<string, "LoadFailed">
declare const nowMillis: Effect.Effect<number>

const makeCache = Effect.gen(function* () {
  const state = yield* SynchronizedRef.make<CacheState>({
    value: "empty",
    loadedAt: 0
  })

  const refresh = SynchronizedRef.updateAndGetEffect(state, () =>
    Effect.gen(function* () {
      const value = yield* loadValue
      const loadedAt = yield* nowMillis
      return { value, loadedAt }
    })
  )

  return {
    get: SynchronizedRef.get(state),
    refresh
  }
})
```

## Append-Only History

Use `Ref` with immutable arrays or `Chunk` for an append-only in-memory history.

```typescript
import { Effect, Ref } from "effect"

interface Event {
  readonly type: string
  readonly at: number
}

const makeHistory = Effect.gen(function* () {
  const events = yield* Ref.make<ReadonlyArray<Event>>([])

  const append = (event: Event) =>
    Ref.update(events, (current) => current.concat(event))

  return {
    append,
    all: Ref.get(events)
  }
})
```

## Reactive View State

Use `SubscriptionRef` when consumers need updates as they happen.

```typescript
import { Effect, Stream, SubscriptionRef } from "effect"

interface ViewState {
  readonly route: string
  readonly pending: boolean
}

const makeViewState = Effect.gen(function* () {
  const ref = yield* SubscriptionRef.make<ViewState>({
    route: "/",
    pending: false
  })

  const navigate = (route: string) =>
    SubscriptionRef.update(ref, (state) => ({
      ...state,
      route
    }))

  const pendingRoutes = ref.changes.pipe(
    Stream.filter((state) => state.pending)
  )

  return {
    changes: ref.changes,
    pendingRoutes,
    navigate
  }
})
```

Expose `changes` to observers and command functions to writers. Avoid giving
every component or caller the raw reference.

## Request Context

Use `FiberRef` with `Effect.locally` for request-scoped values.

```typescript
import { Effect, FiberRef } from "effect"

const program = Effect.scoped(
  Effect.gen(function* () {
    const requestId = yield* FiberRef.make("missing")

    const withRequestId = <A, E, R>(
      id: string,
      effect: Effect.Effect<A, E, R>
    ) => Effect.locally(requestId, id)(effect)

    const current = FiberRef.get(requestId)

    return yield* withRequestId("req-9", current)
  })
)
```

## Choosing Pattern By Failure Mode

| Failure mode | Use | Reason |
|---|---|---|
| Lost increments | `Ref.modify` or `Ref.updateAndGet` | One atomic state transition |
| Stale effectful refresh | `SynchronizedRef.updateEffect` | Serializes effectful updater |
| UI does not react to state | `SubscriptionRef` | Publishes `changes` stream |
| Request id leaks between handlers | `FiberRef` | Value is local to the fiber |

## Cross-references

See also: [01-overview.md](01-overview.md), [02-ref.md](02-ref.md), [03-synchronizedref.md](03-synchronizedref.md), [04-subscription-ref.md](04-subscription-ref.md), [05-fiber-ref.md](05-fiber-ref.md).
