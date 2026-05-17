# Effect Delay and Sleep
Use `Effect.delay` and `Effect.sleep` for one-off waiting, and `Schedule` for recurrence policy.

## delay

`Effect.delay(effect, duration)` delays the start of an effect. It does not
change the effect's success, failure, or requirement channels.

```typescript
import { Effect } from "effect"

const program = Effect.logInfo("sent after delay").pipe(
  Effect.delay("500 millis")
)
```

Use `delay` when the work should happen once, later.

## sleep

`Effect.sleep(duration)` is an effect that completes after the duration. It is
useful inside larger workflows.

```typescript
import { Effect } from "effect"

const program = Effect.gen(function* () {
  yield* Effect.logInfo("before")
  yield* Effect.sleep("1 second")
  yield* Effect.logInfo("after")
})
```

Sleep suspends the fiber; it is not a blocking thread sleep.

## Delay vs schedule

| Need | Tool |
|---|---|
| Wait once before an effect starts | `Effect.delay` |
| Pause between two steps in one workflow | `Effect.sleep` |
| Retry after failures | `Effect.retry` with `Schedule` |
| Repeat after successes | `Effect.repeat` with `Schedule` |
| Poll until a condition changes | `Effect.repeat` with conditions |

Do not build retry loops out of `sleep` unless you are implementing a lower
level combinator. Application code should use `Schedule`.

## One-off timeout spacing

Use sleep for intentional sequencing between different actions.

```typescript
import { Effect } from "effect"

declare const reserve: Effect.Effect<void, "ReserveFailed">
declare const confirm: Effect.Effect<void, "ConfirmFailed">

const program = Effect.gen(function* () {
  yield* reserve
  yield* Effect.sleep("250 millis")
  yield* confirm
})
```

The sleep is part of the domain workflow, not a recurrence policy.

## Delay and retry together

Delay can move the first attempt; the schedule controls later attempts.

```typescript
import { Effect, Schedule } from "effect"

declare const request: Effect.Effect<string, "Temporary">

const program = request.pipe(
  Effect.delay("100 millis"),
  Effect.retry(
    Schedule.exponential("100 millis").pipe(
      Schedule.compose(Schedule.recurs(5))
    )
  )
)
```

Use this sparingly. Most retries should start with the first attempt
immediately and delay only the subsequent attempts.

## Duration input style

Both `delay` and `sleep` accept `Duration.DurationInput`. Prefer readable
duration strings at call sites.

```typescript
import { Effect } from "effect"

const shortPause = Effect.sleep("100 millis")
const longPause = Effect.sleep("5 minutes")
```

Avoid bare numeric durations in application code because the unit is easy to
miss during review.

## Interruptibility

Sleeping and delayed effects are runtime-managed. If the fiber is interrupted,
the waiting effect is interrupted too.

```typescript
import { Effect, Fiber } from "effect"

const program = Effect.gen(function* () {
  const fiber = yield* Effect.fork(Effect.sleep("1 hour"))
  yield* Fiber.interrupt(fiber)
})
```

This is one reason to prefer Effect timing primitives over host timer wrappers
inside Effect code.

## Review cues

- Use `Effect.delay` for a one-off delayed start.
- Use `Effect.sleep` between steps in a workflow.
- Use `Schedule` for retry and repeat recurrence.
- Keep duration units visible with strings.
- Avoid host timer wrappers inside Effect services.
- Keep runtime calls at application edges.

## Cross-references

See also: [01-overview.md](01-overview.md), [02-built-in-schedules.md](02-built-in-schedules.md), [06-effect-retry.md](06-effect-retry.md), [07-effect-repeat.md](07-effect-repeat.md).
