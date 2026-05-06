# Schedule Composition
Compose schedules by naming whether you need chaining, both constraints, either constraint, or merged outputs.

## Four composition questions

Before combining schedules, answer one question:

| Need | Operator |
|---|---|
| Feed one schedule's output into another schedule | `Schedule.compose` |
| Continue only while both schedules continue | `Schedule.intersect` |
| Continue while either schedule continues | `Schedule.union` |
| Keep both schedules but compute a custom output | `Schedule.zipWith` |

The operators are not interchangeable. Most retry bugs in generated Effect
code come from treating every combination as "combine schedules."

## compose means chain

`Schedule.compose(a, b)` runs `a`, then feeds each output of `a` as the input to
`b`. The output of the composed schedule is the output of `b`.

```typescript
import { Effect, Schedule } from "effect"

declare const request: Effect.Effect<string, "Temporary">

const policy = Schedule.exponential("100 millis").pipe(
  Schedule.compose(Schedule.recurs(5))
)

const program = request.pipe(
  Effect.retry(policy)
)
```

This is the canonical bounded exponential policy. The first schedule produces
delays; the second schedule counts and stops after five recurrences.

Use `compose` when the second schedule is acting as a limiter or transform over
the first schedule's output.

## intersect means both

`Schedule.intersect(a, b)` continues only while both schedules want to continue.
It combines outputs into a tuple.

```typescript
import { Effect, Schedule } from "effect"

declare const request: Effect.Effect<string, "Temporary">

const policy = Schedule.exponential("100 millis").pipe(
  Schedule.intersect(Schedule.recurs(5))
)

const program = request.pipe(
  Effect.retry(policy)
)
```

This also bounds an exponential retry, but its output is a tuple containing
both outputs. For many retry policies, that output is not observed, so either
`compose` or `intersect` can work. Prefer the canonical `compose` form in this
skill when teaching bounded exponential retries.

Use `intersect` when both schedules are real constraints and both outputs
matter or can be ignored together.

## union means either

`Schedule.union(a, b)` continues while either schedule wants to continue. It
uses the shorter delay by default and combines outputs into a tuple.

```typescript
import { Effect, Schedule } from "effect"

const poll = Effect.logInfo("poll").pipe(
  Effect.repeat(
    Schedule.exponential("100 millis").pipe(
      Schedule.union(Schedule.spaced("1 second"))
    )
  )
)
```

This starts with short exponential delays and then behaves like a one-second
spacing once the exponential delay grows past one second.

Use `union` for "whichever allows the next recurrence sooner" policies, not
for bounding request retries. A union with `Schedule.recurs(5)` does not mean
"stop at five if the other schedule is still continuing."

## Difference table

| Operator | Recurrence rule | Delay rule | Output shape | Typical use |
|---|---|---|---|---|
| `compose` | second schedule controls after receiving first output | from chained decision | second output | bounded exponential teaching form |
| `intersect` | both schedules must continue | longer interval | tuple | combine independent constraints |
| `union` | either schedule may continue | shorter interval | tuple | fastest of two policies |
| `zipWith` | both schedules must continue | intersection timing | custom output | keep both policies and map output |

The important distinction is stop behavior. `intersect` narrows. `union`
widens. `compose` chains.

## zipWith for output control

`Schedule.zipWith` is equivalent to intersecting schedules and mapping their
outputs.

```typescript
import { Schedule } from "effect"

const policy = Schedule.recurs(5).pipe(
  Schedule.zipWith(
    Schedule.spaced("250 millis"),
    (attempt, tick) => ({ attempt, tick })
  )
)
```

Use this when the output becomes part of a fallback or log message.

## retryOrElse with output

The output of a schedule is visible to `Effect.retryOrElse` when retries are
exhausted.

```typescript
import { Data, Effect, Schedule } from "effect"

class Temporary extends Data.TaggedError("Temporary")<{}> {}

const request = Effect.fail(new Temporary({}))

const policy = Schedule.recurs(3).pipe(
  Schedule.zipWith(
    Schedule.spaced("100 millis"),
    (attempt) => attempt
  )
)

const program = Effect.retryOrElse(
  request,
  policy,
  (error, attempts) =>
    Effect.logError("request retries exhausted", error, attempts).pipe(
      Effect.as("fallback")
    )
)
```

If the fallback needs a custom summary, use `zipWith` to shape that output
before passing the schedule to `retryOrElse`.

## andThen is sequencing, not compose

Effect v3 also has `Schedule.andThen`, which runs one schedule to completion
and then switches to another. Do not confuse it with `compose`.

```typescript
import { Effect, Schedule } from "effect"

const program = Effect.logInfo("warm then poll").pipe(
  Effect.repeat(
    Schedule.recurs(3).pipe(
      Schedule.andThen(Schedule.spaced("1 second"))
    )
  )
)
```

This runs the first phase immediately for three recurrences, then continues
with one-second spacing.

Use `andThen` for phases. Use `compose` for output-to-input chaining.

## Composition anti-patterns

Do not use `union` to cap retries.

```typescript
import { Schedule } from "effect"

const keepsGoing = Schedule.exponential("100 millis").pipe(
  Schedule.union(Schedule.recurs(5))
)
```

The exponential schedule is unbounded, so the union can continue after the
recurs side stops. Use the canonical bounded form instead:

```typescript
import { Schedule } from "effect"

const bounded = Schedule.exponential("100 millis").pipe(
  Schedule.compose(Schedule.recurs(5))
)
```

## Composition review cues

- If the phrase is "both constraints," reach for `intersect`.
- If the phrase is "either policy," reach for `union`.
- If the phrase is "use this output as that input," reach for `compose`.
- If a fallback needs structured schedule output, reach for `zipWith`.
- If a policy has phases, consider `andThen`.
- If a retry must stop at a count, do not use `union` for the cap.

## Cross-references

See also: [01-overview.md](01-overview.md), [02-built-in-schedules.md](02-built-in-schedules.md), [05-jitter-and-modify.md](05-jitter-and-modify.md), [06-effect-retry.md](06-effect-retry.md), [08-schedule-conditions.md](08-schedule-conditions.md).
