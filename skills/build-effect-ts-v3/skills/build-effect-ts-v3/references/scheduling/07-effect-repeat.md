# Effect Repeat
Use `Effect.repeat` for successful recurrence, and keep failure recovery in retry or error handling.

## Repeat consumes successes

`Effect.repeat(effect, schedule)` re-runs the effect after it succeeds. The
schedule input is the success value.

```typescript
import { Effect, Schedule } from "effect"

const heartbeat = Effect.succeed("ok").pipe(
  Effect.tap((status) => Effect.logInfo("heartbeat", status))
)

const program = heartbeat.pipe(
  Effect.repeat(Schedule.spaced("1 second"))
)
```

If the effect fails, repetition stops and the failure is propagated unless you
use `repeatOrElse`.

## Initial execution is included

Repeats are additional executions after the first run. `Schedule.recurs(2)`
means the effect may run once initially and then two more times.

```typescript
import { Effect, Schedule } from "effect"

const action = Effect.logInfo("run")

const program = action.pipe(
  Effect.repeat(Schedule.recurs(2))
)
```

This can execute `action` up to three total times if all executions succeed.

## repeatN

`Effect.repeatN(effect, n)` repeats immediately up to `n` additional times.

```typescript
import { Effect } from "effect"

const action = Effect.logInfo("flush")

const program = action.pipe(
  Effect.repeatN(2)
)
```

Use `repeatN` for small local repetition. Use schedules when timing,
conditions, or composition matter.

## Repeat with spacing

For polling, `Schedule.spaced` is usually the clearest policy.

```typescript
import { Effect, Schedule } from "effect"

declare const refreshCache: Effect.Effect<void, "RefreshFailed">

const program = refreshCache.pipe(
  Effect.repeat(Schedule.spaced("30 seconds"))
)
```

The next refresh waits until the previous refresh succeeds and the spacing
duration has passed.

## Repeat with fixed cadence

Use `Schedule.fixed` for stable cadence.

```typescript
import { Effect, Schedule } from "effect"

const publishTick = Effect.logInfo("tick")

const program = publishTick.pipe(
  Effect.repeat(Schedule.fixed("1 second"))
)
```

Prefer `fixed` for clock-like behavior. Prefer `spaced` for external calls.

## Repeat until success output changes

The options form supports `until` and `while` predicates over successful
outputs.

```typescript
import { Effect } from "effect"

declare const readStatus: Effect.Effect<"Pending" | "Ready", "ReadFailed">

const waitUntilReady = readStatus.pipe(
  Effect.repeat({
    until: (status) => status === "Ready"
  })
)
```

When a schedule is needed too, put it in the options object.

```typescript
import { Effect, Fiber, Schedule } from "effect"

declare const readStatus: Effect.Effect<"Pending" | "Ready", "ReadFailed">

const waitUntilReady = readStatus.pipe(
  Effect.repeat({
    schedule: Schedule.spaced("1 second"),
    until: (status) => status === "Ready"
  })
)
```

Use `repeat` conditions for success-state polling. Use `retry` conditions for
failure recovery.

## repeatOrElse

`Effect.repeatOrElse` handles a failure that occurs during repetition.

```typescript
import { Effect, Option, Schedule } from "effect"

declare const pullPage: Effect.Effect<number, "PullFailed">

const program = Effect.repeatOrElse(
  pullPage,
  Schedule.recurs(5),
  (error, lastOutput) =>
    Effect.logError("repeat failed", error, Option.isSome(lastOutput)).pipe(
      Effect.as(0)
    )
)
```

The handler receives the failure and an `Option` containing the last schedule
output if one exists.

## schedule skips the initial run

`Effect.schedule` follows a schedule without the extra initial execution that
`repeat` performs.

```typescript
import { Effect, Schedule } from "effect"

const action = Effect.logInfo("scheduled only")

const program = action.pipe(
  Effect.schedule(Schedule.spaced("1 second"))
)
```

Use this when the first execution should happen only after the schedule says so.

## Long-lived repeats

Long-lived repeats usually belong at application edges or in supervised fibers.

```typescript
import { Effect, Schedule } from "effect"

const pulse = Effect.logInfo("pulse").pipe(
  Effect.repeat(Schedule.spaced("5 seconds"))
)

const program = Effect.gen(function* () {
  const fiber = yield* Effect.fork(pulse)
  yield* Effect.sleep("20 seconds")
  yield* Fiber.interrupt(fiber)
})
```

Keep library functions as effect descriptions. Let the application runtime
decide when to fork long-lived repeat loops.

## Review cues

- Use `repeat` for success-driven recurrence.
- Use `retry` for failure-driven recurrence.
- Remember that repeats are additional to the initial execution.
- Use `repeatN` only for immediate local repetition.
- Use `spaced` for polling after successful work.
- Use `repeatOrElse` when a failed repetition needs fallback behavior.
- Keep infinite repeats at runtime edges or supervised fibers.

## Cross-references

See also: [01-overview.md](01-overview.md), [02-built-in-schedules.md](02-built-in-schedules.md), [03-cron-schedule.md](03-cron-schedule.md), [06-effect-retry.md](06-effect-retry.md), [09-effect-delay.md](09-effect-delay.md).
