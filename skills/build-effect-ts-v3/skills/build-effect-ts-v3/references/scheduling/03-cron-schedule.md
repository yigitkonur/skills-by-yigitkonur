# Cron Schedules
Use cron schedules for calendar recurrence, and keep simple duration polling on `spaced` or `fixed`.

## When cron belongs

Use cron when the recurrence is tied to calendar fields:

- every day at 04:00
- the first Monday window of a month
- a specific weekday at midnight
- a day-of-month job such as billing on the 1st

Do not use cron for simple "every N seconds" polling. Use
`Schedule.spaced("N seconds")` or `Schedule.fixed("N seconds")` for that.

## Schedule.cron

`Schedule.cron` accepts either a cron expression or a `Cron.Cron` value. The
schedule output is a tuple of millisecond timestamps representing the active
cron interval window.

```typescript
import { Effect, Schedule } from "effect"

const runDailyReport = Effect.logInfo("daily report")

const dailyAtFourUtc = Schedule.cron("0 4 * * *", "UTC")

const program = runDailyReport.pipe(
  Effect.repeat(dailyAtFourUtc)
)
```

Five-segment expressions are accepted. Effect v3 internally treats them as
minute, hour, day, month, weekday and adds seconds as `0`.

## Six-segment expressions

Use six segments when seconds matter.

```typescript
import { Schedule } from "effect"

const atSecondThirty = Schedule.cron("30 * * * * *", "UTC")
```

The six fields are:

| Field | Range |
|---|---|
| seconds | `0-59` |
| minutes | `0-59` |
| hours | `0-23` |
| day of month | `1-31` |
| month | `1-12` |
| weekday | `0-6` in cron parsing |

Use explicit time zones for production jobs where wall-clock meaning matters.

## Cron.parse

Use `Cron.parse` when cron expressions come from configuration or user input.
It returns `Either.Either<Cron.Cron, Cron.ParseError>`.

```typescript
import { Cron, Effect, Either, Schedule } from "effect"

const parseSchedule = (expression: string) =>
  Either.match(Cron.parse(expression, "UTC"), {
    onLeft: (error) => Effect.fail(error),
    onRight: (cron) => Effect.succeed(Schedule.cron(cron))
  })
```

This keeps invalid cron expressions in the typed error channel instead of
turning them into defects.

## Cron.make

Use `Cron.make` when the allowed fields are already structured.

```typescript
import { Cron, Schedule } from "effect"

const firstBusinessMorning = Cron.make({
  seconds: [0],
  minutes: [0],
  hours: [9],
  days: [1, 2, 3, 4, 5, 6, 7],
  months: [],
  weekdays: [1, 2, 3, 4, 5]
})

const schedule = Schedule.cron(firstBusinessMorning)
```

Empty `months`, `days`, or `weekdays` sets mean unconstrained for that field.

## dayOfMonth

`Schedule.dayOfMonth(day)` triggers at midnight on the specified day of each
month. It produces a count of executions.

```typescript
import { Effect, Schedule } from "effect"

const closeBillingPeriod = Effect.logInfo("closing billing period")

const monthly = closeBillingPeriod.pipe(
  Effect.repeat(Schedule.dayOfMonth(1))
)
```

If the specified day does not exist in a month, that month is skipped. A
schedule for day `31` does not run in a 30-day month.

## dayOfWeek

`Schedule.dayOfWeek(day)` triggers at midnight on the specified weekday. In
this constructor, Monday is `1` and Sunday is `7`.

```typescript
import { Effect, Schedule } from "effect"

const sendWeeklyDigest = Effect.logInfo("weekly digest")

const mondayMidnight = sendWeeklyDigest.pipe(
  Effect.repeat(Schedule.dayOfWeek(1))
)
```

This helper is easier to read than a cron expression when the policy really is
"one weekday at midnight."

## minuteOfHour and hourOfDay

Effect v3 also exports calendar helpers for recurring within an hour or day.

```typescript
import { Effect, Schedule } from "effect"

const runHourly = Effect.logInfo("hourly maintenance").pipe(
  Effect.repeat(Schedule.minuteOfHour(15))
)

const runDaily = Effect.logInfo("daily maintenance").pipe(
  Effect.repeat(Schedule.hourOfDay(3))
)
```

`minuteOfHour(15)` runs at minute 15 of every hour. `hourOfDay(3)` runs at
03:00 each day.

## Inspecting cron values

`Cron.match`, `Cron.next`, and `Cron.sequence` are useful at boundaries and in
tests.

```typescript
import { Cron, Either } from "effect"

const cron = Either.getOrThrow(Cron.parse("0 4 * * *", "UTC"))

const matches = Cron.match(cron, new Date("2026-01-01T04:00:00.000Z"))
const next = Cron.next(cron, new Date("2026-01-01T04:01:00.000Z"))
const upcoming = Cron.sequence(cron, new Date("2026-01-01T00:00:00.000Z"))
```

Keep these helpers out of core retry policies. They are for calendar
inspection; `Schedule.cron` is the bridge into repeatable effects.

## Cron review cues

- Prefer `Schedule.spaced` for interval polling.
- Prefer `Schedule.cron` for wall-clock recurrence.
- Parse external cron strings with `Cron.parse`.
- Avoid unchecked cron parsing in service constructors.
- Name the time zone at production boundaries.
- Use `dayOfMonth` or `dayOfWeek` when that reads clearer than a cron string.

## Cross-references

See also: [01-overview.md](01-overview.md), [02-built-in-schedules.md](02-built-in-schedules.md), [07-effect-repeat.md](07-effect-repeat.md), [08-schedule-conditions.md](08-schedule-conditions.md).
