# Logging Basics
Use `Effect.log*` APIs for runtime-aware messages that preserve fiber, cause, annotation, and span context.

## Core APIs

| API | Level | Default visibility |
|---|---|---|
| `Effect.log` | info | shown |
| `Effect.logInfo` | info | shown |
| `Effect.logWarning` | warning | shown |
| `Effect.logError` | error | shown |
| `Effect.logFatal` | fatal | shown |
| `Effect.logDebug` | debug | hidden by default |
| `Effect.logTrace` | trace | hidden by default |

All of these return `Effect<void>`. They compose inside `Effect.gen`, `pipe`,
services, finalizers, retries, and schedules.

## Basic Use

```typescript
import { Effect } from "effect"

const program = Effect.gen(function* () {
  yield* Effect.logInfo("starting worker")
  yield* Effect.logDebug("loaded worker configuration")
  yield* Effect.logWarning("queue depth is high")
  yield* Effect.logError("job failed")
})
```

Use levels for operational meaning:

- info: normal business milestone
- warning: unusual but recovered condition
- error: expected failure worth investigating
- fatal: unrecoverable application condition
- debug: development or temporary diagnosis
- trace: very detailed execution diagnosis

## Multiple Message Values

Log functions accept multiple values.

```typescript
import { Effect } from "effect"

const logJob = (jobId: string, attempt: number) =>
  Effect.logInfo("job attempt", { jobId, attempt })
```

Prefer small structured values over string interpolation when the logger can
preserve structured bodies.

## Keep Logs Inside the Effect

```typescript
import { Effect } from "effect"

const parseMessage = (raw: string) =>
  Effect.gen(function* () {
    yield* Effect.logDebug("parsing message")
    return JSON.parse(raw) as { readonly type: string }
  })
```

The log is part of the effect description. It will be repeated by retries,
interrupted with the fiber, and annotated by surrounding scopes.

## Log Around Expected Failures

Use typed error recovery to log failures.

```typescript
import { Effect } from "effect"

class MissingUser {
  readonly _tag = "MissingUser"
  constructor(readonly userId: string) {}
}

declare const loadUser: (
  userId: string
) => Effect.Effect<string, MissingUser>

const program = loadUser("u-123").pipe(
  Effect.tapError((error) =>
    Effect.logWarning("user lookup failed", {
      reason: error._tag,
      userId: error.userId
    })
  )
)
```

Do not throw just to make a logger see an error. Expected failures belong in
the error channel.

## Log Causes at Boundaries

`Effect.logError` is useful with `catchAllCause` at an application edge.

```typescript
import { Cause, Effect } from "effect"

declare const program: Effect.Effect<void, string>

const main = program.pipe(
  Effect.catchAllCause((cause) =>
    Effect.gen(function* () {
      yield* Effect.logError("application failed", Cause.pretty(cause))
      return yield* Effect.failCause(cause)
    })
  )
)
```

Inside services, prefer domain-specific recovery. At the edge, cause logging
can preserve defects, interruptions, and expected errors.

## Debug Visibility

Debug and trace logs are not shown by the default minimum level.

```typescript
import { Effect, Logger, LogLevel } from "effect"

const program = Effect.logDebug("debug details").pipe(
  Logger.withMinimumLogLevel(LogLevel.Debug)
)
```

Use `Logger.withMinimumLogLevel` for a small region. Use
`Logger.minimumLogLevel(LogLevel.Info)` as a `Layer` for application-wide policy.

## Effectful Logging in Pipelines

`Effect.tap` is the usual way to log a successful value without changing it.

```typescript
import { Effect } from "effect"

const loadCount = Effect.succeed(42).pipe(
  Effect.tap((count) => Effect.logInfo("loaded count", { count }))
)
```

Use `Effect.tapError` for failures and `Effect.tapBoth` when both sides need
separate observability.

## Logging in Finalizers

Finalizers are effects too, so they can log.

```typescript
import { Effect } from "effect"

const scopedResource = Effect.acquireRelease(
  Effect.logInfo("acquired resource"),
  () => Effect.logInfo("released resource")
)
```

Keep finalizer logs short. Finalizers often run while a fiber is failing or
being interrupted.

## Message Style

Use event-style messages:

- `order accepted`
- `worker started`
- `cache refresh failed`
- `retry scheduled`

Avoid embedding all context in the message string. Use log annotations or
structured message values for context that should be queried.

## Review Checklist

- Log calls are `yield*`ed or returned, not built and ignored.
- Debug logs are behind an intentional minimum level.
- Expected failures are logged with typed recovery combinators.
- High-cardinality context uses annotations, not metric tags.
- Logs at service boundaries explain business events, not every local step.
- Edge cause logging uses `catchAllCause` when defects or interruptions matter.

## Cross-references

See also: [structured logs](03-structured-logs.md), [log levels](04-log-levels.md), [custom logger](05-custom-logger.md), [tracing basics](06-tracing-basics.md).
