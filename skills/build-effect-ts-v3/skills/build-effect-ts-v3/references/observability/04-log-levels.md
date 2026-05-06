# Log Levels
Use `LogLevel` and logger layers to make runtime log visibility explicit and composable.

## Levels

Effect v3 exposes log levels through `LogLevel`.

| Level | Typical use |
|---|---|
| `LogLevel.Trace` | highly detailed diagnostics |
| `LogLevel.Debug` | development diagnostics |
| `LogLevel.Info` | normal operational events |
| `LogLevel.Warning` | unusual but recovered conditions |
| `LogLevel.Error` | failures needing attention |
| `LogLevel.Fatal` | unrecoverable conditions |
| `LogLevel.None` | suppress logging |

Info, warning, error, and fatal are visible by default. Debug and trace require
lowering the minimum level.

## Local Minimum Level

Use `Logger.withMinimumLogLevel` around a small region.

```typescript
import { Effect, Logger, LogLevel } from "effect"

const debugRegion = Effect.gen(function* () {
  yield* Effect.logDebug("loading cache entry")
  yield* Effect.logInfo("cache entry loaded")
}).pipe(Logger.withMinimumLogLevel(LogLevel.Debug))
```

This changes the minimum level for that effect only.

## Application Minimum Level

`Logger.minimumLogLevel` is a layer.

```typescript
import { Effect, Logger, LogLevel } from "effect"

const LogLevelLive = Logger.minimumLogLevel(LogLevel.Info)

declare const program: Effect.Effect<void>

const main = program.pipe(Effect.provide(LogLevelLive))
```

Put this layer beside the rest of your runtime wiring.

## Configured Minimum Level

Use `Config.logLevel` when the deployment controls log verbosity.

```typescript
import { Config, Effect, Layer, Logger, LogLevel } from "effect"

const LogLevelLive = Layer.unwrapEffect(
  Config.logLevel("LOG_LEVEL").pipe(
    Config.withDefault(LogLevel.Info),
    Effect.map((level) => Logger.minimumLogLevel(level))
  )
)
```

This keeps configuration in Effect's `Config` system and still produces a
normal `Layer`.

## Temporary Debugging

```typescript
import { Effect, Logger, LogLevel } from "effect"

const inspectImport = Effect.gen(function* () {
  yield* Effect.logDebug("read import header")
  yield* Effect.logTrace("decoded import row")
}).pipe(Logger.withMinimumLogLevel(LogLevel.Trace))
```

Keep trace-level regions narrow. Trace logs can become expensive and noisy.

## Level Selection

Use levels based on operator action:

| Operator question | Level |
|---|---|
| Is the service healthy? | info |
| Did a recoverable issue occur? | warning |
| Did a request or job fail? | error |
| Is a shutdown unavoidable? | fatal |
| What data path did this take? | debug |
| What branch was executed? | trace |

Do not use error level for ordinary business rejections that do not require
operator action.

## Layer Composition

```typescript
import { Layer, Logger, LogLevel } from "effect"
import { Otlp } from "@effect/opentelemetry"
import { NodeHttpClient } from "@effect/platform-node"

const ObservabilityLive = Layer.mergeAll(
  Logger.minimumLogLevel(LogLevel.Info),
  Otlp.layerProtobuf({
    baseUrl: "http://localhost:4318",
    resource: { serviceName: "orders-api" }
  })
).pipe(Layer.provide(NodeHttpClient.layer))
```

The minimum-level layer composes like any other layer. It does not need a custom
bootstrap hook.

## Anti-patterns

- Changing log levels by mutating global logger state.
- Enabling trace level across an entire production service by default.
- Using warning for expected successful branches.
- Hiding failures at debug level.
- Configuring log level separately from the Effect runtime layer graph.

## Review Checklist

- Application-wide level is provided by `Logger.minimumLogLevel`.
- Narrow debugging uses `Logger.withMinimumLogLevel`.
- Deployment-driven level uses `Config.logLevel`.
- Debug and trace logs have a clear owner and purpose.
- Error logs correspond to failures or operator action.

## Cross-references

See also: [logging basics](02-logging-basics.md), [structured logs](03-structured-logs.md), [custom logger](05-custom-logger.md), [OpenTelemetry setup](11-opentelemetry-setup.md).
