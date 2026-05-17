# Deferred
Use this for one-shot coordination between fibers without polling or mutable flags.

## What Deferred Represents

`Deferred<A, E>` is a value that can be completed exactly once with an Effect
result. Fibers can wait for it with `Deferred.await`.

It is Effect's one-shot signal:

- one fiber creates the deferred
- one or more fibers await it
- another fiber completes it
- all waiters resume with the same result

```typescript
import { Deferred, Effect } from "effect"

const program = Effect.gen(function* () {
  const ready = yield* Deferred.make<void>()

  const worker = Effect.gen(function* () {
    yield* Deferred.await(ready)
    yield* Effect.logInfo("worker started after ready signal")
  })

  yield* Effect.fork(worker)
  yield* Deferred.succeed(ready, undefined)
})
```

Waiting on a deferred suspends the fiber semantically. It does not block an
operating-system thread.

## Use Cases

Use `Deferred` for:

- startup readiness
- handshakes between fibers
- waiting for one background process to publish a value
- test coordination
- turning callback-style completion into an Effect value
- waking several fibers at once

Do not use `Deferred` for streams of values. Use `Queue`, `TQueue`, `PubSub`, or
`Stream` for repeated communication.

## Completing Successfully

`Deferred.succeed(deferred, value)` completes with a success value and returns a
boolean indicating whether this call completed it.

```typescript
import { Deferred, Effect } from "effect"

const publishConfig = Effect.gen(function* () {
  const config = yield* Deferred.make<{ readonly baseUrl: string }>()

  const reader = Effect.gen(function* () {
    const value = yield* Deferred.await(config)
    yield* Effect.logInfo(`configured ${value.baseUrl}`)
  })

  yield* Effect.fork(reader)
  yield* Deferred.succeed(config, { baseUrl: "https://api.example.test" })
})
```

Only the first completion wins. Later completion attempts return `false`.

## Completing With Failure

`Deferred.fail(deferred, error)` completes with a typed failure.

```typescript
import { Deferred, Effect } from "effect"

class StartupError {
  readonly _tag = "StartupError"
}

const program = Effect.gen(function* () {
  const ready = yield* Deferred.make<void, StartupError>()
  yield* Deferred.fail(ready, new StartupError())
  yield* Deferred.await(ready)
})
```

All current and future waiters observe the same failure.

## Completing With Another Effect

`Deferred.complete(deferred, effect)` completes from an effect result.

```typescript
import { Deferred, Effect } from "effect"

declare const loadToken: Effect.Effect<string, "TokenUnavailable">

const program = Effect.gen(function* () {
  const token = yield* Deferred.make<string, "TokenUnavailable">()
  yield* Deferred.complete(token, loadToken)
  return yield* Deferred.await(token)
})
```

Use this when the producer already has an effect whose success or failure should
be shared with waiters.

## Polling Completion

`Deferred.poll(deferred)` checks whether a deferred is complete. It returns an
`Option` of an effect that represents the completed result.

```typescript
import { Deferred, Effect, Option } from "effect"

const check = Effect.gen(function* () {
  const ready = yield* Deferred.make<string>()
  const state = yield* Deferred.poll(ready)

  return Option.match(state, {
    onNone: () => "not ready",
    onSome: () => "ready"
  })
})
```

Use polling for observability. Do not use it to repeatedly check for readiness.
If a fiber must wait, call `Deferred.await`.

## Interruption

`Deferred.interrupt(deferred)` completes the deferred with interruption. Waiters
resume as interrupted.

```typescript
import { Deferred, Effect } from "effect"

const program = Effect.gen(function* () {
  const ready = yield* Deferred.make<void>()

  const waiter = Effect.gen(function* () {
    yield* Deferred.await(ready)
    yield* Effect.logInfo("unreachable if interrupted")
  }).pipe(
    Effect.onInterrupt(() => Effect.logInfo("waiter interrupted"))
  )

  yield* Effect.fork(waiter)
  yield* Deferred.interrupt(ready)
})
```

This is useful when readiness can no longer happen and waiters should stop
rather than receive a domain error.

## Deferred Versus Fiber Join

Use `Fiber.join` when one parent owns one child and wants the child's result.

Use `Deferred` when multiple fibers need a shared one-shot signal or when the
producer and consumers are not in a simple parent-child shape.

```typescript
import { Deferred, Effect } from "effect"

const waitForReady = (ready: Deferred.Deferred<void>) =>
  Deferred.await(ready).pipe(
    Effect.andThen(Effect.logInfo("ready observed"))
  )
```

## Anti-Patterns

- using `Deferred` for repeated events
- completing a deferred in several places without caring who wins
- polling in a loop instead of awaiting
- using mutable boolean flags to coordinate fibers
- using `Deferred` when a scoped resource would express lifetime better

## Cross-References

See also:

- [03-fiber-operations.md](03-fiber-operations.md)
- [10-latch.md](10-latch.md)
- [11-interruption.md](11-interruption.md)
- [12-stm.md](12-stm.md)
