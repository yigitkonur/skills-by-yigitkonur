# SynchronizedRef
Use `SynchronizedRef` when shared state must be updated by an effectful, serialized updater.

## Model

`SynchronizedRef.SynchronizedRef<A>` extends `Ref.Ref<A>`. It supports the same
basic reads and pure writes, plus effectful update operations such as
`updateEffect`, `updateAndGetEffect`, and `modifyEffect`.

```typescript
import { Effect, SynchronizedRef } from "effect"

const program = Effect.gen(function* () {
  const ref = yield* SynchronizedRef.make(0)

  yield* SynchronizedRef.updateEffect(ref, (n) =>
    Effect.succeed(n + 1)
  )

  return yield* SynchronizedRef.get(ref)
})
```

The important property is serialization: the update effect runs while the
reference is coordinating updates. Another effectful updater cannot read the
same old value and commit a conflicting result.

## When To Upgrade From Ref

Use `SynchronizedRef` when the update itself needs to call another effect, read
from services in `R`, fail through the typed error channel, wait, retry, or
return a result derived from the same guarded state transition. If the function
is pure, stay with `Ref`.

## Effectful Refresh

A common case is a token or cached value refreshed by an effect.

```typescript
import { Effect, SynchronizedRef } from "effect"

interface TokenState {
  readonly value: string
  readonly version: number
}

declare const fetchToken: Effect.Effect<string, "TokenUnavailable">

const refreshToken = (state: SynchronizedRef.SynchronizedRef<TokenState>) =>
  SynchronizedRef.updateAndGetEffect(state, (current) =>
    Effect.map(fetchToken, (value) => ({
      value,
      version: current.version + 1
    }))
  )

const program = Effect.gen(function* () {
  const state = yield* SynchronizedRef.make<TokenState>({
    value: "initial",
    version: 0
  })

  return yield* refreshToken(state)
})
```

The error channel of `fetchToken` remains visible. A failed update does not
install a new value.

## `modifyEffect` For Atomic Decisions

Use `modifyEffect` when the caller needs a result and the state transition must
be one serialized unit.

```typescript
import { Effect, SynchronizedRef } from "effect"

interface ReservationState {
  readonly remaining: number
}

declare const persistReservation: (
  amount: number
) => Effect.Effect<string, "PersistenceFailed">

const reserve = (
  state: SynchronizedRef.SynchronizedRef<ReservationState>,
  amount: number
) =>
  SynchronizedRef.modifyEffect(state, (current) => {
    if (current.remaining < amount) {
      return Effect.succeed([
        { _tag: "Rejected", available: current.remaining } as const,
        current
      ] as const)
    }

    return Effect.map(persistReservation(amount), (reservationId) => [
      { _tag: "Accepted", reservationId } as const,
      { remaining: current.remaining - amount }
    ] as const)
  })
```

Both the result and the next state are based on the same guarded snapshot.

## Conditional Effectful Updates

Use `updateSomeEffect` when only some states require a change.

```typescript
import { Effect, Option, SynchronizedRef } from "effect"

type Session =
  | { readonly _tag: "Anonymous" }
  | { readonly _tag: "Authenticated"; readonly userId: string }

declare const reloadUser: (
  userId: string
) => Effect.Effect<string, "UserUnavailable">

const refreshAuthenticated = (session: SynchronizedRef.SynchronizedRef<Session>) =>
  SynchronizedRef.updateSomeEffect(session, (state) =>
    state._tag === "Authenticated"
      ? Option.some(
          Effect.map(reloadUser(state.userId), (userId) => ({
            _tag: "Authenticated",
            userId
          } as const))
        )
      : Option.none()
  )
```

Skipped states keep the current value and do not run the effect.

## Avoid Get-Then-Effect-Then-Set

This shape is not equivalent:

```typescript
import { Effect, Ref } from "effect"

interface TokenState {
  readonly value: string
  readonly version: number
}

declare const fetchToken: Effect.Effect<string, "TokenUnavailable">

const refreshWrong = (state: Ref.Ref<TokenState>) =>
  Effect.gen(function* () {
    const current = yield* Ref.get(state)
    const value = yield* fetchToken
    yield* Ref.set(state, { value, version: current.version + 1 })
  })
```

If two fibers run this concurrently, both can read the same version, both can
fetch, and the later write can erase the earlier transition. Use
`SynchronizedRef.updateEffect` or `modifyEffect`.

## Relationship To SubscriptionRef

`SubscriptionRef` is the reactive upgrade path from `SynchronizedRef`: it keeps
the current value, supports effectful updates, and exposes a `changes` stream.
If no consumer needs the stream, `SynchronizedRef` is the narrower primitive.

## Cross-references

See also: [01-overview.md](01-overview.md), [02-ref.md](02-ref.md), [04-subscription-ref.md](04-subscription-ref.md), [06-state-patterns.md](06-state-patterns.md).
