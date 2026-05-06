# OTLP Exporters
Use `@effect/opentelemetry` OTLP layers when one base endpoint should export Effect logs, metrics, and traces.

## Exporter Choices

| Layer | Serialization | Requires |
|---|---|---|
| `Otlp.layerJson` | JSON | `HttpClient` |
| `Otlp.layerProtobuf` | protobuf | `HttpClient` |
| `Otlp.layer` | caller-provided serialization | `HttpClient` and `OtlpSerialization` |
| `OtlpTracer.layer` | traces only | `HttpClient` and `OtlpSerialization` |
| `OtlpMetrics.layer` | metrics only | `HttpClient` and `OtlpSerialization` |
| `OtlpLogger.layer` | logs only | `HttpClient` and `OtlpSerialization` |

Use the combined `Otlp.layerProtobuf` for most Node services.

## Combined OTLP Layer

```typescript
import { Layer, Logger, LogLevel } from "effect"
import { Otlp } from "@effect/opentelemetry"
import { NodeHttpClient } from "@effect/platform-node"

const TelemetryLive = Layer.mergeAll(
  Logger.minimumLogLevel(LogLevel.Info),
  Otlp.layerProtobuf({
    baseUrl: "http://localhost:4318",
    resource: {
      serviceName: "billing-api",
      serviceVersion: "1.4.0"
    },
    loggerExportInterval: "1 second",
    metricsExportInterval: "10 seconds",
    tracerExportInterval: "5 seconds"
  })
).pipe(Layer.provide(NodeHttpClient.layer))
```

The combined layer sends:

- logs to `/v1/logs`
- metrics to `/v1/metrics`
- traces to `/v1/traces`

The source builds these paths from the provided `baseUrl`.

## Headers and Resource

```typescript
import { Otlp } from "@effect/opentelemetry"

const OtlpLive = Otlp.layerJson({
  baseUrl: "https://otel-collector.internal",
  headers: {
    Authorization: "Bearer local-token"
  },
  resource: {
    serviceName: "report-worker",
    serviceVersion: "2026.05.05",
    attributes: {
      "deployment.environment": "staging"
    }
  }
})
```

In production, source secrets through `Config.redacted` and build the layer from
an effectful configuration value.

## Effectful Configuration

```typescript
import { Config, Effect, Layer, Logger, LogLevel } from "effect"
import { Otlp } from "@effect/opentelemetry"
import { NodeHttpClient } from "@effect/platform-node"

const OtlpLive = Layer.unwrapEffect(
  Effect.gen(function* () {
    const baseUrl = yield* Config.string("OTEL_EXPORTER_OTLP_ENDPOINT")
    const serviceName = yield* Config.string("OTEL_SERVICE_NAME")

    return Layer.mergeAll(
      Logger.minimumLogLevel(LogLevel.Info),
      Otlp.layerProtobuf({
        baseUrl,
        resource: { serviceName }
      })
    ).pipe(Layer.provide(NodeHttpClient.layer))
  })
)
```

This keeps deployment configuration inside Effect and still returns a layer.

## Traces Only

```typescript
import { Layer } from "effect"
import { OtlpSerialization, OtlpTracer } from "@effect/opentelemetry"
import { NodeHttpClient } from "@effect/platform-node"

const TracesLive = OtlpTracer.layer({
  url: "http://localhost:4318/v1/traces",
  resource: { serviceName: "trace-only-worker" },
  exportInterval: "5 seconds",
  maxBatchSize: 1000
}).pipe(
  Layer.provide(OtlpSerialization.layerProtobuf),
  Layer.provide(NodeHttpClient.layer)
)
```

Use component layers for tests or unusual deployments. Combined OTLP wiring is
less error-prone for normal services.

## Metrics Only

```typescript
import { Layer } from "effect"
import { OtlpMetrics, OtlpSerialization } from "@effect/opentelemetry"
import { NodeHttpClient } from "@effect/platform-node"

const MetricsLive = OtlpMetrics.layer({
  url: "http://localhost:4318/v1/metrics",
  resource: { serviceName: "metrics-worker" },
  exportInterval: "10 seconds"
}).pipe(
  Layer.provide(OtlpSerialization.layerProtobuf),
  Layer.provide(NodeHttpClient.layer)
)
```

The metrics exporter snapshots Effect metrics on the export interval.

## Logs Only

```typescript
import { Layer, Logger } from "effect"
import { OtlpLogger, OtlpSerialization } from "@effect/opentelemetry"
import { NodeHttpClient } from "@effect/platform-node"

const LogsLive = OtlpLogger.layer({
  url: "http://localhost:4318/v1/logs",
  resource: { serviceName: "logs-worker" },
  replaceLogger: Logger.defaultLogger,
  exportInterval: "1 second"
}).pipe(
  Layer.provide(OtlpSerialization.layerProtobuf),
  Layer.provide(NodeHttpClient.layer)
)
```

`replaceLogger` replaces the provided logger. Without it, the OTLP logger is
added alongside existing logger behavior.

## Export Intervals

Default source intervals are:

| Signal | Default |
|---|---|
| logs | `1 second` |
| traces | `5 seconds` |
| metrics | `10 seconds` |
| shutdown | `3 seconds` |

Set intervals explicitly in production so runtime behavior is reviewable.

## Anti-patterns

- Providing trace exporter layers but forgetting metrics and logs.
- Using separate service names for logs, metrics, and traces from the same runtime.
- Hard-coding authorization values in shared source files.
- Forgetting the HTTP client layer.
- Rebuilding exporters per request.

## Review Checklist

- Combined OTLP layer is used unless a component-only exporter is required.
- `baseUrl` points at the collector root, not a signal-specific path.
- Resource service name is stable.
- Export intervals are explicit.
- HTTP client and serialization requirements are provided.

## Cross-references

See also: [OpenTelemetry setup](11-opentelemetry-setup.md), [custom logger](05-custom-logger.md), [histogram and summary metrics](09-metrics-histogram-summary.md), [tracing basics](06-tracing-basics.md).
