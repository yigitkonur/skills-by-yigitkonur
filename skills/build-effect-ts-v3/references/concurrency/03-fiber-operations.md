# Fiber Operations
Use this when you already have a `Fiber` handle and need to join, await, poll, or interrupt it.

## What a Fiber Handle Means

A fiber handle is not the result of the work. It is a handle to work that may
still be running.

```typescript
import { Effect, Fiber } from "effect"

const program = Effect.gen(function* () {
  const fiber = yield* Effect.fork(Effect.succeed(42))
  const value = yield* Fiber.join(fiber)
  return value
})
```

The handle lets the parent decide whether to wait, inspect, cancel, or compose
the child.

## `Fiber.join`

`Fiber.join(fiber)` waits for successful completion and returns the success
value.

If the fiber fails with a typed error, `join` fails with that error. If the
fiber is interrupted, joining observes that interruption through the normal
Effect cause model.

```typescript
import { Effect, Fiber } from "effect"

class WorkerError {
  readonly _tag = "WorkerError"
}

const worker = Effect.fail(new WorkerError())

const program = Effect.gen(function* () {
  const fiber = yield* Effect.fork(worker)
  return yield* Fiber.join(fiber)
})
```

Use `join` when the child result is part of the parent result and errors should
propagate naturally.

## `Fiber.await`

`Fiber.await(fiber)` waits for completion and returns `Exit.Exit<A, E>`.

Use it when you need to inspect every terminal state as data: success, failure,
defect, or interruption.

```typescript
import { Effect, Exit, Fiber } from "effect"

const program = Effect.gen(function* () {
  const fiber = yield* Effect.fork(Effect.succeed("done"))
  const exit = yield* Fiber.await(fiber)

  return Exit.match(exit, {
    onFailure: () => "not ok",
    onSuccess: (value) => value
  })
})
```

`await` is better than `join` for monitoring, logging, dashboards, and final
state aggregation.

## `Fiber.poll`

`Fiber.poll(fiber)` checks whether the fiber is already done.

It returns an `Option` containing an `Exit` when complete, or `Option.none()`
while still running.

```typescript
import { Effect, Fiber, Option } from "effect"

const program = Effect.gen(function* () {
  const fiber = yield* Effect.fork(Effect.sleep("1 second"))
  const status = yield* Fiber.poll(fiber)

  return Option.match(status, {
    onNone: () => "still running",
    onSome: () => "done"
  })
})
```

Polling is for non-blocking observation. Do not build busy loops around it. If
you need to wait for completion, use `join` or `await`.

## `Fiber.interrupt`

`Fiber.interrupt(fiber)` requests interruption and waits until the target fiber
has terminated.

```typescript
import { Effect, Fiber } from "effect"

const longRunning = Effect.sleep("1 minute").pipe(
  Effect.onInterrupt(() => Effect.logInfo("long-running task interrupted"))
)

const program = Effect.gen(function* () {
  const fiber = yield* Effect.fork(longRunning)
  yield* Effect.sleep("100 millis")
  yield* Fiber.interrupt(fiber)
})
```

This waiting behavior is important. It means finalizers have a chance to run
before the interrupter proceeds.

## `Fiber.interruptFork`

`Fiber.interruptFork(fiber)` sends the interrupt in the background and resumes
immediately.

Use it when the caller must not wait for the target's finalizers. That should be
rare in application logic because it weakens back-pressure.

```typescript
import { Effect, Fiber } from "effect"

const stopWithoutWaiting = Effect.gen(function* () {
  const fiber = yield* Effect.fork(Effect.sleep("1 minute"))
  yield* Fiber.interruptFork(fiber)
  yield* Effect.logInfo("interrupt requested")
})
```

Prefer `Fiber.interrupt` when correctness depends on the child actually being
stopped before the parent continues.

## `Fiber.interruptAll`

`Fiber.interruptAll(fibers)` interrupts a collection of fibers and waits for
their termination.

```typescript
import { Effect, Fiber } from "effect"

const program = Effect.gen(function* () {
  const fibers = yield* Effect.forEach(
    [1, 2, 3],
    (n) => Effect.fork(Effect.sleep(`${n} seconds`)),
    { concurrency: 3 }
  )

  yield* Fiber.interruptAll(fibers)
})
```

If you are manually collecting fibers only to interrupt them later, check
whether `Effect.scoped`, `Effect.race`, or `Effect.forEach` with bounded
concurrency can encode ownership more directly.

## `Fiber.joinAll` and `Fiber.awaitAll`

Use `Fiber.joinAll` to await successful completion of several fibers and fail if
any joined fiber fails.

Use `Fiber.awaitAll` when you need all exits, including failures.

```typescript
import { Effect, Fiber } from "effect"

const program = Effect.gen(function* () {
  const fibers = yield* Effect.forEach(
    [1, 2, 3],
    (n) => Effect.fork(Effect.succeed(n)),
    { concurrency: 3 }
  )

  return yield* Fiber.joinAll(fibers)
})
```

## Operation Choice

| Need | Operation |
|---|---|
| Propagate child success or typed failure | `Fiber.join` |
| Inspect the exact terminal state | `Fiber.await` |
| Check without blocking | `Fiber.poll` |
| Stop and wait for cleanup | `Fiber.interrupt` |
| Stop in the background | `Fiber.interruptFork` |
| Stop many and wait | `Fiber.interruptAll` |
| Join many successful results | `Fiber.joinAll` |
| Inspect many exits | `Fiber.awaitAll` |

## Cross-References

See also:

- [02-fork-types.md](02-fork-types.md)
- [04-effect-race.md](04-effect-race.md)
- [09-deferred.md](09-deferred.md)
- [11-interruption.md](11-interruption.md)
