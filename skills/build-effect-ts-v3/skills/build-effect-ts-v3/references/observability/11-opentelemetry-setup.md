# OpenTelemetry Setup
Wire Effect logs, metrics, and traces to OpenTelemetry at the runtime edge with layers.

## Packages

Effect-native instrumentation uses `effect`. Export wiring uses
`@effect/opentelemetry` plus the OpenTelemetry SDK packages selected by the
runtime.

For Node runtimes, `NodeSdk.layer` accepts:

- `spanProcessor`
- `metricReader`
- `logRecordProcessor`
- `loggerProviderConfig`
- `tracerConfig`
- `resource`
- `shutdownTimeout`

The source target for this skill is Effect 3.21.2 and
`@effect/opentelemetry` source from the same corpus.

## Complete NodeSdk OTLP Layer

This layer wires traces and metrics through OpenTelemetry OTLP HTTP exporters,
sets a service resource, and sets the minimum Effect log level as a layer.

```typescript
import { Config, Effect, Layer, Logger, LogLevel } from "effect"
import { NodeSdk } from "@effect/opentelemetry"
import { OTLPMetricExporter } from "@opentelemetry/exporter-metrics-otlp-http"
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http"
import { PeriodicExportingMetricReader } from "@opentelemetry/sdk-metrics"
import { BatchSpanProcessor } from "@opentelemetry/sdk-trace-base"

export const ObservabilityLive = Layer.unwrapEffect(
  Effect.gen(function* () {
    const endpoint = yield* Config.string(
      "OTEL_EXPORTER_OTLP_ENDPOINT"
    ).pipe(Config.withDefault("http://localhost:4318"))

    const serviceVersion = yield* Config.string(
      "SERVICE_VERSION"
    ).pipe(Config.withDefault("dev"))

    return Layer.mergeAll(
      Logger.minimumLogLevel(LogLevel.Info),
      NodeSdk.layer(() => ({
        resource: {
          serviceName: "orders-api",
          serviceVersion,
          attributes: {
            "deployment.environment": "local"
          }
        },
        spanProcessor: new BatchSpanProcessor(
          new OTLPTraceExporter({
            url: `${endpoint}/v1/traces`
          })
        ),
        metricReader: new PeriodicExportingMetricReader({
          exporter: new OTLPMetricExporter({
            url: `${endpoint}/v1/metrics`
          }),
          exportIntervalMillis: 10_000
        }),
        shutdownTimeout: "5 seconds"
      }))
    )
  })
)
```

`Logger.minimumLogLevel(LogLevel.Info)` is intentionally part of the layer
graph. Do not set it as a side effect outside the runtime.

## Complete Effect Program

```typescript
import { Effect, Layer, Metric } from "effect"

const requests = Metric.counter("http_requests_total", {
  incremental: true
})

export const program = Effect.gen(function* () {
  yield* Metric.increment(requests)
  yield* Effect.annotateCurrentSpan("http.route", "/health")
  yield* Effect.logInfo("health check handled")
}).pipe(
  Effect.withSpan("Http.health"),
  Effect.provide(ObservabilityLive)
)

declare const ObservabilityLive: Layer.Layer<never>
```

Application runners execute `program` at the edge. Libraries return effects and
do not install exporters.

## Logs Through NodeSdk

`NodeSdk.layer` supports `logRecordProcessor` when the runtime has an
OpenTelemetry log processor. Use it when the deployment standardizes on the
official OTel log SDK.

```typescript
import { NodeSdk } from "@effect/opentelemetry"
import { BatchLogRecordProcessor } from "@opentelemetry/sdk-logs"

declare const logProcessor: BatchLogRecordProcessor

const LogsLive = NodeSdk.layer(() => ({
  resource: { serviceName: "orders-api" },
  logRecordProcessor: logProcessor
}))
```

If the project does not already carry an OTel log exporter package, use the
Effect OTLP layer in the next section for a complete all-pillar path.

## All-Pillar OTLP Layer

`Otlp.layerProtobuf` from `@effect/opentelemetry` wires Effect logs, metrics,
and traces to OTLP endpoints derived from one base URL.

```typescript
import { Layer, Logger, LogLevel } from "effect"
import { Otlp } from "@effect/opentelemetry"
import { NodeHttpClient } from "@effect/platform-node"

export const OtlpLive = Layer.mergeAll(
  Logger.minimumLogLevel(LogLevel.Info),
  Otlp.layerProtobuf({
    baseUrl: "http://localhost:4318",
    resource: {
      serviceName: "orders-api",
      serviceVersion: "dev",
      attributes: {
        "deployment.environment": "local"
      }
    },
    loggerExportInterval: "1 second",
    metricsExportInterval: "10 seconds",
    tracerExportInterval: "5 seconds",
    shutdownTimeout: "5 seconds"
  })
).pipe(Layer.provide(NodeHttpClient.layer))
```

Use this path when you want Effect's OTLP exporter implementation instead of
manually constructing OTel SDK processors.

## Resource Attributes

Always set at least:

- `serviceName`
- `serviceVersion`
- deployment environment

Resource attributes are attached to all exported telemetry. They are more
appropriate than repeating service identity as log annotations or metric tags.

## Layer Placement

```typescript
import { Effect, Layer } from "effect"

declare const AppLive: Layer.Layer<never>
declare const ObservabilityLive: Layer.Layer<never>
declare const app: Effect.Effect<void>

export const main = app.pipe(
  Effect.provide(AppLive),
  Effect.provide(ObservabilityLive)
)
```

Keep observability wiring separate from domain layers so tests can replace it
with `NodeSdk.layerEmpty`, no-op loggers, or local exporters.

## Minimum Versions

The official pages scraped for this mission did not publish a numeric minimum
Effect version for logging, metrics, or tracing. The cloned source confirms the
APIs used here exist in Effect 3.21.2. The `NodeSdk` source is in
`@effect/opentelemetry` and exposes `@since 1.0.0`.

## Anti-patterns

- Constructing exporters inside services.
- Installing log level policy outside the layer graph.
- Mixing raw OpenTelemetry spans with Effect spans in domain code.
- Forgetting `NodeHttpClient.layer` when using Effect's OTLP HTTP layer.
- Duplicating service identity as metric tags on every metric.

## Review Checklist

- Runtime wiring uses `Layer`.
- `Logger.minimumLogLevel(LogLevel.Info)` is provided as a layer.
- `NodeSdk.layer` or `Otlp.layerProtobuf` is installed at the edge.
- Resource attributes identify the service.
- Export intervals and shutdown timeout are explicit.
- Domain code only uses Effect-native logs, metrics, and spans.

## Cross-references

See also: [OTLP exporters](12-otlp-exporters.md), [tracing basics](06-tracing-basics.md), [counter and gauge metrics](08-metrics-counter-gauge.md), [log levels](04-log-levels.md).
