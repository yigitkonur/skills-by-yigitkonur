# Effect Retry
Use `Effect.retry` for typed failure recovery, with schedules describing when and how often to try again.

## Retry consumes failures

`Effect.retry(effect, schedule)` re-runs the effect when it fails. The schedule
input is the failure value.

```typescript
import { Data, Effect, Schedule } from "effect"

class NetworkFailure extends Data.TaggedError("NetworkFailure")<{}> {}

const request = Effect.fail(new NetworkFailure({}))

const program = request.pipe(
  Effect.retry(Schedule.recurs(3))
)
```

If the effect eventually succeeds, the success value is returned. If the
schedule stops while the effect is still failing, the last failure is
propagated.

## Immediate retry sugar

`Effect.retry(eff, { times: 3 })` is sugar for immediate retry with
`Schedule.recurs(3)`.

```typescript
import { Effect, Schedule } from "effect"

declare const request: Effect.Effect<string, "Temporary">

const withOptions = request.pipe(
  Effect.retry({ times: 3 })
)

const withSchedule = request.pipe(
  Effect.retry(Schedule.recurs(3))
)
```

Use the options form when immediate retry is enough. Use an explicit schedule
when adding delay, jitter, composition, or reusable policy names.

## There is no retryN export

Effect v3 exports `Effect.retry`, not `Effect.retryN`. For fixed retry counts,
use:

```typescript
import { Effect } from "effect"

declare const request: Effect.Effect<string, "Temporary">

const program = request.pipe(
  Effect.retry({ times: 3 })
)
```

If generated code reaches for `Effect.retryN`, replace it with the options form
or `Schedule.recurs(n)`.

## Bounded exponential retry

Use the canonical bounded exponential schedule for transient remote failures.

```typescript
import { Effect, Schedule } from "effect"

declare const callPartner: Effect.Effect<string, "Unavailable">

const retryPolicy = Schedule.exponential("100 millis").pipe(
  Schedule.compose(Schedule.recurs(5))
)

const program = callPartner.pipe(
  Effect.retry(retryPolicy)
)
```

Add jitter for distributed systems:

```typescript
import { Effect, Schedule } from "effect"

declare const callPartner: Effect.Effect<string, "Unavailable">

const retryPolicy = Schedule.exponential("100 millis").pipe(
  Schedule.compose(Schedule.recurs(5)),
  Schedule.jitteredWith({ min: 0, max: 1 })
)

const program = callPartner.pipe(
  Effect.retry(retryPolicy)
)
```

This keeps retry policy declarative and interruption-aware.

## Retry while a predicate holds

The options form supports `while` and `until` predicates over the failure.

```typescript
import { Data, Effect } from "effect"

class HttpFailure extends Data.TaggedError("HttpFailure")<{
  readonly status: number
}> {}

declare const request: Effect.Effect<string, HttpFailure>

const program = request.pipe(
  Effect.retry({
    times: 3,
    while: (error) => error.status === 429
  })
)
```

This retries only while the failure remains retryable. It stops and propagates
the failure when the predicate is false or the retry count is exhausted.

For broader error-channel shaping before retry, see
[../error-handling/06-catch-all.md](../error-handling/06-catch-all.md). Prefer
narrow typed predicates or tagged recovery before using broad handlers for
retry-only-on-specific-error policies.

## Retry with schedule input

When you use a schedule directly, the schedule can inspect the failure as
input.

```typescript
import { Data, Effect, Schedule } from "effect"

class RateLimited extends Data.TaggedError("RateLimited")<{
  readonly retryAfter: string
}> {}

declare const request: Effect.Effect<string, RateLimited>

const policy = Schedule.identity<RateLimited>().pipe(
  Schedule.addDelay((error) => error.retryAfter),
  Schedule.compose(Schedule.recurs(5))
)

const program = request.pipe(
  Effect.retry(policy)
)
```

Use this shape when the failure itself carries retry policy information, such
as a `Retry-After` header that has already been decoded into a duration string.

## retryOrElse

`Effect.retryOrElse` runs a fallback effect when the retry schedule is
exhausted.

```typescript
import { Data, Effect, Schedule } from "effect"

class NetworkFailure extends Data.TaggedError("NetworkFailure")<{}> {}

const request = Effect.fail(new NetworkFailure({}))

const program = Effect.retryOrElse(
  request,
  Schedule.recurs(3),
  (error, attempts) =>
    Effect.logError("request failed after retries", error, attempts).pipe(
      Effect.as("cached-value")
    )
)
```

The fallback receives the last error and the schedule output at exhaustion.
Shape the schedule output with `zipWith` if the fallback needs structured
metadata.

## Retry boundaries

Retry only expected typed failures. Defects, interruption, and programmer
errors should not become ordinary retry cases.

Good retry candidates:

- transient network failures
- HTTP 429 or 503 after decoding into typed errors
- lock contention
- temporary queue or database unavailability

Poor retry candidates:

- validation failures
- permission denial
- invariant defects
- schema bugs
- missing required configuration

## Review cues

- Replace manual retry loops with `Effect.retry`.
- Use `{ times: n }` for immediate fixed retries.
- Use `Schedule.exponential("100 millis").pipe(Schedule.compose(Schedule.recurs(5)))` for bounded exponential retry.
- Add jitter for distributed retries.
- Use `while` for retryable error predicates.
- Do not invent `Effect.retryN`.
- Do not retry broad error unions without a typed policy.

## Cross-references

See also: [01-overview.md](01-overview.md), [02-built-in-schedules.md](02-built-in-schedules.md), [04-schedule-composition.md](04-schedule-composition.md), [05-jitter-and-modify.md](05-jitter-and-modify.md), [../error-handling/06-catch-all.md](../error-handling/06-catch-all.md).
