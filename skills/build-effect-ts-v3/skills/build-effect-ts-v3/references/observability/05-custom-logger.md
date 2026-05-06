# Custom Logger
Use custom loggers as runtime layers when the default formatting or destination is not enough.

## Logger Model

`Logger.Logger<Message, Output>` consumes log options and returns an output.
Most application code never sees the logger directly. It writes with
`Effect.log*`, and the runtime provides logger behavior.

Important constructors and combinators:

| API | Purpose |
|---|---|
| `Logger.make` | build a logger from `Logger.Options` |
| `Logger.replace` | replace one logger with another using a layer |
| `Logger.replaceEffect` | replace with an effectfully-created logger |
| `Logger.replaceScoped` | replace with a scoped effectful logger |
| `Logger.add` | add a logger alongside existing loggers |
| `Logger.addScoped` | add a scoped effectful logger |
| `Logger.batched` | batch logger output over a duration window |
| `Logger.zip` | combine two logger values |

## Make a Logger

```typescript
import { Effect, Layer, Logger } from "effect"

const auditLogger = Logger.make((options) => {
  const message = Array.isArray(options.message)
    ? options.message.join(" ")
    : String(options.message)

  return {
    level: options.logLevel.label,
    message,
    annotations: Object.fromEntries(options.annotations)
  }
})

const AuditLoggerLive = Logger.replace(Logger.defaultLogger, auditLogger)

declare const program: Effect.Effect<void>

const main = program.pipe(Effect.provide(AuditLoggerLive))
```

`Logger.make` should be small. If output requires a network client, use an
effectful or scoped logger so acquisition and cleanup stay in Effect.

## Preserve Runtime Metadata

`Logger.Options` carries more than the message.

Useful fields include:

- `logLevel`
- `message`
- `cause`
- `context`
- `spans`
- `annotations`
- `fiberId`
- `date`

Use these fields instead of re-creating context by hand.

## Add Instead of Replace

Use `Logger.add` when you want the default logger and one extra destination.

```typescript
import { Logger } from "effect"

const structuredLogger = Logger.make((options) => ({
  level: options.logLevel.label,
  annotations: Object.fromEntries(options.annotations),
  spanCount: options.spans.length
}))

const StructuredLoggerLive = Logger.add(structuredLogger)
```

Use `Logger.replace` when the default logger would duplicate output or expose
the wrong format.

## Batched Logger

`Logger.batched` groups output and returns an effectful logger in a scope.

```typescript
import { Effect, Logger } from "effect"

const batchedLogger = Logger.stringLogger.pipe(
  Logger.batched("1 second", (messages) =>
    Effect.logInfo("flushed log batch", { count: messages.length })
  )
)

const BatchedLoggerLive = Logger.replaceScoped(
  Logger.defaultLogger,
  batchedLogger
)
```

The flush function is an Effect. Keep batching scoped so pending messages flush
or release when the runtime scope ends.

## Combine Loggers

```typescript
import { Logger } from "effect"

const metadataLogger = Logger.make((options) => ({
  level: options.logLevel.label,
  fiber: String(options.fiberId),
  annotations: Object.fromEntries(options.annotations)
}))

const combined = Logger.zip(Logger.defaultLogger, metadataLogger)

const CombinedLoggerLive = Logger.replace(Logger.defaultLogger, combined)
```

`Logger.zip` is useful for fan-out, but prefer `Logger.add` for simple
"existing logger plus this logger" behavior.

## When to Use OpenTelemetry Logger

Use `@effect/opentelemetry` when logs should be exported as OTLP records with
trace and span ids. The package supplies logger layers so application code can
keep using `Effect.log*`.

Do not build a custom OTLP encoder unless the package layer cannot support the
deployment target.

## Custom Logger Boundaries

Custom loggers belong at the runtime edge:

- application bootstrap
- test runtime
- CLI runner
- worker runtime
- platform adapter

They do not belong in domain services. Domain services should emit log events,
not decide where those events are written.

## Anti-patterns

- Passing logger objects through every service method.
- Dropping `annotations`, `spans`, or `cause` from a structured logger.
- Replacing the default logger when adding a side logger would be enough.
- Building network clients inside `Logger.make`.
- Creating a batch logger without scoped lifetime.

## Review Checklist

- `Logger.make` uses `Logger.Options` instead of reconstructing metadata.
- Runtime wiring uses `Logger.replace`, `Logger.add`, or scoped variants.
- Batched loggers are installed with scoped layer APIs.
- Domain code still writes through `Effect.log*`.
- OpenTelemetry export is delegated to `@effect/opentelemetry` when possible.

## Cross-references

See also: [logging basics](02-logging-basics.md), [structured logs](03-structured-logs.md), [log levels](04-log-levels.md), [OTLP exporters](12-otlp-exporters.md).
