# Jitter and Delay Modification
Use jitter and delay modifiers to alter schedule timing without rewriting recurrence logic.

## Why jitter exists

Backoff alone can still synchronize clients. If many fibers or services fail at
the same time and retry with the same deterministic delay, they can apply load
again at the same time.

Jitter randomizes the delay window so retries spread out.

```typescript
import { Effect, Schedule } from "effect"

declare const request: Effect.Effect<string, "Unavailable">

const policy = Schedule.exponential("100 millis").pipe(
  Schedule.compose(Schedule.recurs(5)),
  Schedule.jittered
)

const program = request.pipe(
  Effect.retry(policy)
)
```

Use jitter for distributed retries, rate-limit recovery, and remote service
contention.

## jittered

In Effect v3 source, `Schedule.jittered` is the default jitter modifier. It
adjusts each interval randomly between `80%` and `120%` of the computed delay.

```typescript
import { Schedule } from "effect"

const policy = Schedule.exponential("100 millis").pipe(
  Schedule.compose(Schedule.recurs(5)),
  Schedule.jittered
)
```

This preserves the schedule output and changes only the timing.

## jitteredWith

Use `Schedule.jitteredWith` when the jitter range matters. The 0-100% jitter
form is explicit in v3 as `min: 0` and `max: 1`.

```typescript
import { Schedule } from "effect"

const fullJitter = Schedule.exponential("100 millis").pipe(
  Schedule.compose(Schedule.recurs(5)),
  Schedule.jitteredWith({ min: 0, max: 1 })
)
```

Prefer `jitteredWith({ min: 0, max: 1 })` when a platform guideline asks for
full jitter.

## addDelay

`Schedule.addDelay` adds extra delay based on the schedule output. It keeps the
schedule's original recurrence behavior and output.

```typescript
import { Effect, Schedule } from "effect"

const snapshot = Effect.logInfo("snapshot")

const policy = Schedule.recurs(3).pipe(
  Schedule.addDelay((attempt) =>
    attempt === 0 ? "100 millis" : "500 millis"
  )
)

const program = snapshot.pipe(
  Effect.repeat(policy)
)
```

Use `addDelay` when the base schedule gives you the right stop behavior and
output, but you need additional waiting.

## modifyDelay

`Schedule.modifyDelay` receives the schedule output and the currently computed
delay, then returns the replacement delay.

```typescript
import { Duration, Schedule } from "effect"

const policy = Schedule.spaced("1 second").pipe(
  Schedule.modifyDelay((attempt, current) =>
    attempt > 10 ? "5 seconds" : Duration.sum(current, "100 millis")
  )
)
```

Use `modifyDelay` when the original delay matters and you want to clamp,
increase, reduce, or otherwise transform it.

## addDelay vs modifyDelay

| Need | Operator |
|---|---|
| Add a surcharge to each interval | `Schedule.addDelay` |
| Replace or transform the computed interval | `Schedule.modifyDelay` |
| Need services while computing extra delay | `Schedule.addDelayEffect` |
| Need services while transforming delay | `Schedule.modifyDelayEffect` |

Prefer the pure versions first. Reach for the effectful variants only when
delay calculation really needs services or effectful state.

## Effectful delay changes

`addDelayEffect` and `modifyDelayEffect` allow service-dependent delay logic.

```typescript
import { Effect, Schedule } from "effect"

type DelayConfig = {
  readonly nextDelay: (attempt: number) => Effect.Effect<string>
}

declare const config: DelayConfig

const policy = Schedule.recurs(5).pipe(
  Schedule.addDelayEffect((attempt) => config.nextDelay(attempt))
)
```

Keep effectful delay policies small. If the delay calculation starts performing
business work, it belongs in the effect being retried or repeated, not in the
schedule modifier.

## Backoff with jitter

The common remote-call policy is bounded exponential backoff plus jitter.

```typescript
import { Effect, Schedule } from "effect"

declare const fetchInvoice: Effect.Effect<string, "Network">

const retryPolicy = Schedule.exponential("100 millis").pipe(
  Schedule.compose(Schedule.recurs(5)),
  Schedule.jitteredWith({ min: 0, max: 1 })
)

const program = fetchInvoice.pipe(
  Effect.retry(retryPolicy)
)
```

This replaces manual retry loops that mix counters, timer calls, and remote
errors in one block.

## Review cues

- Add jitter to remote retries that may fan out from many clients.
- Use `jittered` for the source-backed default range.
- Use `jitteredWith({ min: 0, max: 1 })` for full jitter.
- Use `addDelay` when preserving the original delay and output is enough.
- Use `modifyDelay` when replacing or clamping the computed delay.
- Keep delay policies declarative and side-effect-light.

## Cross-references

See also: [02-built-in-schedules.md](02-built-in-schedules.md), [04-schedule-composition.md](04-schedule-composition.md), [06-effect-retry.md](06-effect-retry.md), [08-schedule-conditions.md](08-schedule-conditions.md).
