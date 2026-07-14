# Effect Disconnect
Use this only when the caller should stop waiting for interruption cleanup to finish.

## What Disconnect Changes

`Effect.disconnect(effect)` changes interruption back-pressure.

Normally, when a fiber interrupts another fiber, the interrupter waits until the
target fiber finishes its interruption path. That includes finalizers and
`onInterrupt` handlers.

Disconnected work still receives interruption, but the caller can resume before
the interrupted work has fully finished cleanup.

```typescript
import { Effect } from "effect"

const slowCleanup = Effect.sleep("10 seconds").pipe(
  Effect.onInterrupt(() => Effect.logInfo("cleanup in background"))
)

const program = Effect.disconnect(slowCleanup)
```

This is a latency tradeoff. It is not a way to make ownership disappear.

## Race Example

Race losers are interrupted. If the losing branch has slow cleanup, a normal
race can wait for that cleanup before returning.

```typescript
import { Effect } from "effect"

const fast = Effect.succeed("fast")

const slow = Effect.sleep("10 seconds").pipe(
  Effect.onInterrupt(() =>
    Effect.logInfo("slow branch cleanup").pipe(
      Effect.delay("2 seconds")
    )
  )
)

const program = Effect.race(
  fast,
  Effect.disconnect(slow)
)
```

The race can return from the winning branch without waiting for the slow
branch's interruption cleanup to complete.

## When It Is Appropriate

Use `disconnect` when:

- a graceful shutdown coordinator must request several stops quickly
- cleanup is independent and already safe in the background
- a latency-sensitive fallback path should not wait on loser cleanup
- observability records cleanup completion separately

Do not use it because a finalizer is unexpectedly slow. First ask whether the
finalizer is doing too much work or holding a resource too long.

## When It Is Wrong

Avoid `disconnect` when:

- the caller must know the resource is released before continuing
- a semaphore permit must be available before the next step
- tests depend on deterministic cleanup completion
- the cleanup failure mode would be hidden from the owner
- the interrupted work mutates state the caller reads immediately after

Back-pressure is often what makes interruption safe. Removing it should be a
deliberate design choice.

## Structured Concurrency Still Applies

Disconnect is not a general detachment API. It does not say "run forever." It
says "do not make this caller wait for the interruption process."

For fiber lifetime, choose the correct owner with:

- `Effect.fork`
- `Effect.forkScoped`
- `Effect.forkIn`
- `Effect.forkDaemon`

Use disconnect for interruption timing, not for ownership.

## Review Checklist

Before accepting `Effect.disconnect`, require answers to:

- Who owns the disconnected work?
- What happens if cleanup is still running when the caller continues?
- Is resource release required before the next step?
- Is there a test that observes the intended behavior?
- Would `Fiber.interruptFork` be clearer at the fiber-handle level?
- Would fixing slow cleanup be better than hiding the wait?

## Cross-References

See also:

- [02-fork-types.md](02-fork-types.md)
- [04-effect-race.md](04-effect-race.md)
- [11-interruption.md](11-interruption.md)
- [13-effect-timeout.md](13-effect-timeout.md)
