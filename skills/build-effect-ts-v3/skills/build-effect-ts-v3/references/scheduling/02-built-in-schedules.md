# Built-in Schedules
Use built-in schedules as small policy values, then compose them instead of writing custom recurrence logic.

## Constructor map

| Constructor | Output | Timing model | Common use |
|---|---|---|---|
| `Schedule.recurs(n)` | `number` | immediate recurrence limit | cap retries or repeats |
| `Schedule.forever` | `number` | immediate unbounded recurrence | polling base before adding delay |
| `Schedule.spaced(duration)` | `number` | gap after each run | polling after work completes |
| `Schedule.fixed(interval)` | `number` | fixed cadence | clocks, periodic heartbeats |
| `Schedule.exponential(base, factor?)` | `Duration` | growing backoff | transient failure retry |
| `Schedule.linear(base)` | `Duration` | steadily growing delay | gentle backoff |

## recurs

`Schedule.recurs(n)` permits `n` recurrences after the initial effect
execution. With retry, that means up to `n` additional attempts after the first
failure. With repeat, that means up to `n` additional successful executions
after the first success.

```typescript
import { Effect, Schedule } from "effect"

declare const request: Effect.Effect<string, "Transient">

const program = request.pipe(
  Effect.retry(Schedule.recurs(3))
)
```

This is equivalent in retry count to:

```typescript
import { Effect } from "effect"

declare const request: Effect.Effect<string, "Transient">

const program = request.pipe(
  Effect.retry({ times: 3 })
)
```

Use the options form for a tiny immediate retry. Use the schedule form when the
same policy will gain delay, jitter, conditions, or composition.

## forever

`Schedule.forever` never stops by itself. It outputs the recurrence count.

```typescript
import { Effect, Schedule } from "effect"

const heartbeat = Effect.logInfo("alive").pipe(
  Effect.repeat(
    Schedule.forever.pipe(
      Schedule.addDelay(() => "30 seconds")
    )
  )
)
```

Prefer adding an explicit delay or condition before using `forever` with
production effects. An immediate forever repeat can monopolize useful runtime
capacity.

## spaced

`Schedule.spaced(duration)` waits for the given duration after the previous run
completes. It is the default choice for polling where the gap should be stable
regardless of how long the work took.

```typescript
import { Effect, Schedule } from "effect"

declare const refreshCache: Effect.Effect<void, "RefreshFailed">

const refreshLoop = refreshCache.pipe(
  Effect.repeat(Schedule.spaced("1 minute"))
)
```

If `refreshCache` takes eight seconds, the next execution starts roughly one
minute after that execution completes.

## fixed

`Schedule.fixed(interval)` tries to maintain a fixed interval between starts.
If the action takes longer than the interval, the next run can happen
immediately to catch up without overlapping executions.

```typescript
import { Effect, Schedule } from "effect"

const tick = Effect.logInfo("tick")

const clock = tick.pipe(
  Effect.repeat(Schedule.fixed("1 second"))
)
```

Use `fixed` when calendar-like cadence matters more than a gap after each
completed run.

## spaced vs fixed

| Question | Prefer |
|---|---|
| Should the next run wait after the last run finishes? | `Schedule.spaced` |
| Should runs align to a regular cadence? | `Schedule.fixed` |
| Could the work sometimes take longer than the interval? | usually `Schedule.spaced` |
| Is this a clock tick or heartbeat cadence? | usually `Schedule.fixed` |

The distinction matters for jobs with variable duration. `spaced` is easier to
reason about for external calls because it naturally slows down when work is
slow.

## exponential

`Schedule.exponential(base, factor?)` produces a delay that grows by the factor
on each recurrence. The default factor is `2`.

```typescript
import { Effect, Schedule } from "effect"

declare const callPartner: Effect.Effect<string, "Unavailable">

const boundedExponential = Schedule.exponential("100 millis").pipe(
  Schedule.compose(Schedule.recurs(5))
)

const program = callPartner.pipe(
  Effect.retry(boundedExponential)
)
```

Use this exact bounded exponential shape as the default retry policy for
transient remote failures:

```typescript
Schedule.exponential("100 millis").pipe(Schedule.compose(Schedule.recurs(5)))
```

The first schedule produces growing delays. `compose` feeds those outputs into
the second schedule and stops when `recurs(5)` stops.

## Custom exponential factor

Pass a factor when doubling is too aggressive.

```typescript
import { Schedule } from "effect"

const slowerGrowth = Schedule.exponential("100 millis", 1.5).pipe(
  Schedule.compose(Schedule.recurs(6))
)
```

Use smaller factors for systems where slow recovery is common and immediate
pressure makes things worse.

## linear

`Schedule.linear(base)` grows steadily instead of multiplying.

```typescript
import { Effect, Schedule } from "effect"

declare const reserveCapacity: Effect.Effect<void, "CapacityBusy">

const program = reserveCapacity.pipe(
  Effect.retry(
    Schedule.linear("250 millis").pipe(
      Schedule.compose(Schedule.recurs(4))
    )
  )
)
```

Linear backoff is useful when an operation often succeeds after a short wait
but still needs increasing breathing room.

## Adding delay to count schedules

Count schedules such as `recurs` and `forever` do not necessarily express an
interesting delay by themselves. Add delay explicitly when the count is the
main output you want to keep.

```typescript
import { Effect, Schedule } from "effect"

const report = Effect.logInfo("snapshot")

const policy = Schedule.recurs(10).pipe(
  Schedule.addDelay(() => "500 millis")
)

const program = report.pipe(
  Effect.repeat(policy)
)
```

`addDelay` keeps the count output and adds timing.

## Bounded unbounded schedules

`spaced`, `fixed`, `exponential`, and `linear` are unbounded unless composed
with a limiter.

```typescript
import { Schedule } from "effect"

const fiveFastPolls = Schedule.spaced("100 millis").pipe(
  Schedule.compose(Schedule.recurs(5))
)

const fiveBackoffRetries = Schedule.exponential("100 millis").pipe(
  Schedule.compose(Schedule.recurs(5))
)
```

Use a bounded version for request retries. Leave schedules unbounded only when
the effect is intentionally long-lived, usually in a supervised fiber or
application entrypoint.

## Cross-references

See also: [01-overview.md](01-overview.md), [04-schedule-composition.md](04-schedule-composition.md), [05-jitter-and-modify.md](05-jitter-and-modify.md), [06-effect-retry.md](06-effect-retry.md), [07-effect-repeat.md](07-effect-repeat.md).
