# Scheduling Overview
Use `Schedule` as a declarative retry and repeat policy, not as an ad-hoc timer loop.

## Mental model

`Schedule.Schedule<Out, In, R>` is a stateful, immutable description of
recurrence.

Read the type left to right:

| Channel | Meaning | Retry example | Repeat example |
|---|---|---|---|
| `Out` | value produced by the schedule | retry count, delay, tuple | repeat count, delay, tuple |
| `In` | value consumed at each decision | failure value | success value |
| `R` | services the schedule needs | random, clock, custom services | random, clock, custom services |

When a schedule is used with `Effect.retry`, the schedule consumes failures.
When it is used with `Effect.repeat`, the schedule consumes successes.

The schedule decides:

- whether another recurrence is allowed
- when that recurrence may happen
- what output describes the current recurrence

## Effects stay lazy

Constructing a retry policy does not start a timer, fork a fiber, or call the
effect. The schedule is only interpreted when the surrounding effect runs.

```typescript
import { Effect, Schedule } from "effect"

const pullOnce = Effect.logInfo("pulling remote state").pipe(
  Effect.as({ version: 1 })
)

const poll = pullOnce.pipe(
  Effect.repeat(Schedule.spaced("5 seconds"))
)
```

`pullOnce` is still a lazy effect. `poll` is another lazy effect that will run
`pullOnce`, wait according to the schedule, and run it again while the schedule
continues.

## Retry and repeat differ by input

Use `retry` when the next decision depends on failures. Use `repeat` when the
next decision depends on successes.

```typescript
import { Data, Effect, Schedule } from "effect"

class TemporaryFailure extends Data.TaggedError("TemporaryFailure")<{}> {}

const request = Effect.fail(new TemporaryFailure({}))

const retried = request.pipe(
  Effect.retry(Schedule.recurs(3))
)

const heartbeat = Effect.succeed("ok").pipe(
  Effect.repeat(Schedule.spaced("1 second"))
)
```

In `retried`, the schedule input is `TemporaryFailure`. In `heartbeat`, the
schedule input is `"ok"`.

## Schedules are values

Create policies once, name them, and pass them around like ordinary values.

```typescript
import { Effect, Schedule } from "effect"

const shortBackoff = Schedule.exponential("100 millis").pipe(
  Schedule.compose(Schedule.recurs(5))
)

declare const callPartner: Effect.Effect<string, "Unavailable">

const program = callPartner.pipe(
  Effect.retry(shortBackoff)
)
```

This is the canonical bounded exponential policy for this skill: start at
`"100 millis"` and stop after five recurrences.

## What a schedule replaces

A manual loop usually hides policy inside control flow:

- attempt counters spread across mutable variables
- timer calls embedded inside branches
- error predicates duplicated around sleeps
- no typed connection between the failure and retry policy
- interruption and supervision handled manually or not at all

An Effect schedule moves those decisions into a composable value:

```typescript
import { Effect, Schedule } from "effect"

declare const refreshToken: Effect.Effect<string, "Network" | "Denied">

const policy = Schedule.exponential("200 millis").pipe(
  Schedule.compose(Schedule.recurs(4))
)

const refreshed = refreshToken.pipe(
  Effect.retry(policy)
)
```

The retry behavior now lives in `policy`, which can be tested, shared, and
combined with other schedule constraints.

## Output matters

The output type is not incidental. `Schedule.recurs(3)` outputs the recurrence
count. `Schedule.exponential("100 millis")` outputs a `Duration`. Composition
operators decide which output survives or how outputs combine.

```typescript
import { Schedule } from "effect"

const counts: Schedule.Schedule<number> = Schedule.recurs(3)
const delays = Schedule.exponential("100 millis")

const boundedDelays = delays.pipe(
  Schedule.compose(counts)
)
```

`boundedDelays` keeps the count output from the second schedule because
`compose` feeds the first schedule's output into the second schedule.

## Choosing the first tool

| Need | Use |
|---|---|
| Retry a failing effect immediately a fixed number of times | `Effect.retry(effect, { times: n })` |
| Retry with backoff or jitter | `Effect.retry(effect, schedule)` |
| Repeat a successful effect | `Effect.repeat(effect, schedule)` |
| Run once after a delay | `Effect.delay(effect, duration)` |
| Sleep inside a larger workflow | `Effect.sleep(duration)` |
| Calendar-like recurrence | `Schedule.cron`, `Schedule.dayOfMonth`, `Schedule.dayOfWeek` |

Prefer the schedule form when policy needs to be named, composed, bounded,
jittered, or shared.

## Cross-references

See also: [02-built-in-schedules.md](02-built-in-schedules.md), [04-schedule-composition.md](04-schedule-composition.md), [06-effect-retry.md](06-effect-retry.md), [07-effect-repeat.md](07-effect-repeat.md), [09-effect-delay.md](09-effect-delay.md).
