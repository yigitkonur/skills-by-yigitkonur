# Latch
Use this for gate-style coordination where fibers wait until a latch opens.

## What a Latch Does

`Effect.makeLatch(open?)` creates a synchronization gate.

A latch can be:

- closed: waiters suspend
- open: waiters proceed

The v3 source marks `Latch` as `@since 3.8.0`. This skill targets
`effect@3.21.2`, where `Effect.makeLatch` is present.

```typescript
import { Effect, Fiber } from "effect"

const program = Effect.gen(function* () {
  const latch = yield* Effect.makeLatch(false)

  const worker = Effect.gen(function* () {
    yield* latch.await
    yield* Effect.logInfo("gate opened")
  })

  yield* Effect.fork(worker)
  yield* latch.open
})
```

## Latch Operations

| Operation | Meaning |
|---|---|
| `latch.await` | wait until open |
| `latch.open` | open permanently until closed |
| `latch.close` | close again |
| `latch.release` | release current waiters without staying open |
| `latch.whenOpen(effect)` | run effect after gate opens |

Use `await` when the waiting point is explicit. Use `whenOpen` when you want to
wrap a whole effect behind the gate.

## `whenOpen`

```typescript
import { Effect, Fiber } from "effect"

const program = Effect.gen(function* () {
  const latch = yield* Effect.makeLatch(false)

  const gated = latch.whenOpen(
    Effect.logInfo("protected work started")
  )

  const fiber = yield* Effect.fork(gated)
  yield* Effect.sleep("100 millis")
  yield* latch.open
  yield* Fiber.await(fiber)
})
```

`whenOpen` is clearer than manually awaiting in every protected workflow when
the whole effect should be gated.

It also keeps the waiting rule close to the effect being protected.

## `release` Versus `open`

`open` changes the latch state. Future waiters pass until the latch is closed.

`release` lets currently waiting fibers proceed without permanently opening the
latch.

```typescript
import { Effect } from "effect"

const releaseOneWave = Effect.gen(function* () {
  const latch = yield* Effect.makeLatch(false)

  yield* Effect.fork(latch.await.pipe(Effect.andThen(Effect.logInfo("wave"))))
  yield* latch.release
})
```

Use `release` for a one-time wave. Use `open` for readiness.

## Deferred Versus Latch

| Need | Use |
|---|---|
| Publish one success or failure value | `Deferred` |
| Gate work until open | `Latch` |
| Re-close the gate | `Latch` |
| Wake current waiters but keep gate closed | `Latch.release` |
| Retry atomically based on shared state | `STM.retry` |

A deferred carries a result. A latch carries a gate state.

## Good Uses

Use a latch for:

- integration tests that release several fibers at once
- startup gates
- pause/resume controls
- coordinated benchmark starts
- preventing workers from starting before warmup completes

Do not use it as a queue. It does not store multiple values.

## Cross-References

See also:

- [09-deferred.md](09-deferred.md)
- [11-interruption.md](11-interruption.md)
- [12-stm.md](12-stm.md)
