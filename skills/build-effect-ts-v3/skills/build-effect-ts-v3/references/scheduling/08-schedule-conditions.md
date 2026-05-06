# Schedule Conditions
Use schedule conditions when recurrence should stop based on inputs, outputs, or elapsed policy constraints.

## Condition map

| Need | Operator |
|---|---|
| Continue while schedule input matches a predicate | `Schedule.whileInput` |
| Continue while schedule output matches a predicate | `Schedule.whileOutput` |
| Stop when schedule output matches a predicate | `Schedule.untilOutput` |
| Continue while an effectful input predicate succeeds | `Schedule.whileInputEffect` |
| Continue while an effectful output predicate succeeds | `Schedule.whileOutputEffect` |
| Stop after elapsed duration | `Schedule.upTo` |

Use conditions to keep stop logic inside the schedule instead of scattering it
around the effect body.

## whileInput

`Schedule.whileInput` keeps recurring only while the input predicate returns
true.

```typescript
import { Data, Effect, Schedule } from "effect"

class HttpFailure extends Data.TaggedError("HttpFailure")<{
  readonly status: number
}> {}

declare const request: Effect.Effect<string, HttpFailure>

const retryOnlyRateLimit = Schedule.spaced("200 millis").pipe(
  Schedule.whileInput((error: HttpFailure) => error.status === 429),
  Schedule.compose(Schedule.recurs(5))
)

const program = request.pipe(
  Effect.retry(retryOnlyRateLimit)
)
```

With retry, input is the error. With repeat, input is the success value.

## whileOutput

`Schedule.whileOutput` keeps recurring while the schedule output satisfies the
predicate.

```typescript
import { Effect, Schedule } from "effect"

const program = Effect.logInfo("limited").pipe(
  Effect.repeat(
    Schedule.recurs(10).pipe(
      Schedule.whileOutput((attempt) => attempt < 3)
    )
  )
)
```

This stops when the schedule output reaches `3`, even though the base schedule
would allow more recurrences.

## untilOutput

`Schedule.untilOutput` stops when the output predicate becomes true.

```typescript
import { Effect, Schedule } from "effect"

const program = Effect.logInfo("until output").pipe(
  Effect.repeat(
    Schedule.recurs(10).pipe(
      Schedule.untilOutput((attempt) => attempt >= 3)
    )
  )
)
```

Use `untilOutput` when the stop condition reads more naturally than a
`whileOutput` inverse.

## Conditions with repeat outputs

For repeat, the schedule input is the successful result of the effect. This is
useful for polling status values.

```typescript
import { Effect, Schedule } from "effect"

declare const readStatus: Effect.Effect<"Pending" | "Ready", "ReadFailed">

const policy = Schedule.spaced("1 second").pipe(
  Schedule.whileInput((status: "Pending" | "Ready") => status === "Pending")
)

const program = readStatus.pipe(
  Effect.repeat(policy)
)
```

The effect repeats only while the previous status was `Pending`.

## Effectful predicates

Use effectful condition variants only when the decision needs services or
effectful checks.

```typescript
import { Effect, Schedule } from "effect"

type RetryGate = {
  readonly allows: (status: number) => Effect.Effect<boolean>
}

declare const gate: RetryGate

const policy = Schedule.identity<number>().pipe(
  Schedule.whileInputEffect((status) => gate.allows(status)),
  Schedule.addDelay(() => "100 millis")
)
```

Keep these predicates fast and side-effect-light. A condition should decide
policy, not perform the operation being scheduled.

## upTo

`Schedule.upTo(duration)` stops a schedule after the elapsed duration is
reached.

```typescript
import { Effect, Schedule } from "effect"

declare const check: Effect.Effect<"Pending" | "Ready", "ReadFailed">

const policy = Schedule.spaced("1 second").pipe(
  Schedule.upTo("30 seconds")
)

const program = check.pipe(
  Effect.repeat(policy)
)
```

Use `upTo` when wall-clock budget is the constraint. Use `recurs` when attempt
count is the constraint.

## Combining conditions

Conditions compose with timing and count schedules.

```typescript
import { Effect, Schedule } from "effect"

declare const readQueueDepth: Effect.Effect<number, "ReadFailed">

const policy = Schedule.spaced("500 millis").pipe(
  Schedule.whileInput((depth: number) => depth > 0),
  Schedule.compose(Schedule.recurs(20))
)

const drain = readQueueDepth.pipe(
  Effect.repeat(policy)
)
```

This repeats while the last observed queue depth is positive, but no more than
twenty scheduled recurrences.

## Review cues

- Put retryable error predicates on retry schedules or retry options.
- Put success-state polling predicates on repeat schedules or repeat options.
- Use `whileInput` when the effect result or error drives recurrence.
- Use `whileOutput` or `untilOutput` when schedule metadata drives recurrence.
- Use `upTo` for elapsed time budgets.
- Prefer pure predicates unless services are genuinely required.

## Cross-references

See also: [01-overview.md](01-overview.md), [03-cron-schedule.md](03-cron-schedule.md), [04-schedule-composition.md](04-schedule-composition.md), [06-effect-retry.md](06-effect-retry.md), [07-effect-repeat.md](07-effect-repeat.md).
