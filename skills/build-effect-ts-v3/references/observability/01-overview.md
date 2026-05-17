# Observability Overview
Use Effect-native observability so logs, metrics, and traces share runtime context instead of becoming side-channel code.

## The Three Pillars

Effect v3 treats observability as part of the runtime.

| Pillar | Effect surface | What it captures |
|---|---|---|
| Logs | `Effect.log*`, `Logger`, `LogLevel` | messages, causes, annotations, log spans, fiber ids |
| Metrics | `Metric`, `MetricBoundaries`, `Effect.withMetric` | counters, gauges, histograms, summaries, frequencies |
| Traces | `Effect.withSpan`, `Effect.fn`, `Tracer` | operation spans, attributes, links, failures, timing |

These APIs are compositional. A service method can open a span, annotate logs,
increment counters, and still keep its original success, error, and requirement
types.

## Default Rule

Start with the Effect API, then export through `@effect/opentelemetry`.

Do not route observability through ad-hoc callbacks. Effect already carries:

- fiber identity
- current span
- log annotations
- metric labels
- runtime services
- scope lifetime
- error causes
- interruption

The runtime has the context that plain callbacks lose.

## Minimal Shape

```typescript
import { Effect, Metric } from "effect"

const requests = Metric.counter("http_requests_total", {
  description: "Total handled HTTP requests",
  incremental: true
})

const handleRequest = Effect.gen(function* () {
  yield* Effect.annotateCurrentSpan("http.route", "/users/:id")
  yield* Metric.increment(requests)
  yield* Effect.logInfo("request handled")
}).pipe(
  Effect.withSpan("Http.handleRequest"),
  Effect.annotateLogs({ route: "/users/:id" })
)
```

The span name gives trace shape. The span attribute gives queryable trace data.
The log annotation makes every log inside the scope searchable. The counter
records throughput without changing the effect's return value.

## Runtime Wiring

Effect-native instrumentation is inert until a runtime has exporters.

Use layers for runtime policy:

```typescript
import { Layer, Logger, LogLevel } from "effect"
import { Otlp } from "@effect/opentelemetry"
import { NodeHttpClient } from "@effect/platform-node"

const ObservabilityLive = Layer.mergeAll(
  Logger.minimumLogLevel(LogLevel.Info),
  Otlp.layerProtobuf({
    baseUrl: "http://localhost:4318",
    resource: {
      serviceName: "billing-api",
      serviceVersion: "1.0.0"
    }
  })
).pipe(Layer.provide(NodeHttpClient.layer))
```

`Logger.minimumLogLevel(LogLevel.Info)` is a `Layer`, so put it in the same
runtime wiring as exporters. Do not configure it by mutating globals.

## Naming Conventions

Prefer stable names over implementation details.

| Signal | Good name | Avoid |
|---|---|---|
| span | `Users.loadProfile` | `db call 2` |
| counter | `users_profile_loads_total` | `count` |
| histogram | `users_profile_latency_ms` | `timing` |
| log annotation | `userId` | `id2` |
| metric tag | `region` | dynamic unbounded request id |

Stable names survive refactors and keep dashboards useful.

## Cardinality Discipline

Tags and annotations are not the same.

Use log annotations for high-cardinality diagnostic values such as request id,
user id, and job id. They are useful in logs but can explode metric storage when
used as metric tags.

Use metric tags for bounded dimensions:

- route template
- region
- deployment stage
- queue name
- outcome
- dependency name

Use span attributes for request-specific trace context when the value helps
debug a single trace.

## Service Pattern

```typescript
import { Effect, Metric } from "effect"

const dbCalls = Metric.counter("db_calls_total", {
  description: "Database calls by repository method",
  incremental: true
})

const loadInvoice = Effect.fn("Invoices.load")(function* (invoiceId: string) {
  yield* Effect.annotateCurrentSpan("invoice.id", invoiceId)
  yield* Metric.increment(dbCalls)
  yield* Effect.logInfo("loading invoice")
  return { id: invoiceId, status: "open" as const }
})
```

`Effect.fn("Invoices.load")` creates a span for each call. Add an explicit
`Effect.withSpan` only when the function is not already wrapped by `Effect.fn`
or when a nested operation needs its own span.

## Edge Pattern

Keep runners and exporter construction at the application edge.

```typescript
import { Effect, Layer } from "effect"

declare const ObservabilityLive: Layer.Layer<never>
declare const program: Effect.Effect<void, never, never>

export const main = program.pipe(
  Effect.withSpan("Main"),
  Effect.provide(ObservabilityLive)
)
```

Library code should return instrumented effects. Application code decides which
logger, tracer, and metric exporter to provide.

## Review Checklist

- Logs use `Effect.logInfo`, `Effect.logWarning`, `Effect.logError`, or `Effect.logDebug`.
- Reusable operations use `Effect.fn("Domain.operation")`.
- Hand-written spans use stable names.
- Span attributes are useful for single-trace diagnosis.
- Metrics use bounded tag values.
- Histograms use explicit `MetricBoundaries`.
- Runtime log level is provided with `Logger.minimumLogLevel`.
- OpenTelemetry wiring is a layer at the edge.

## Cross-references

See also: [logging basics](02-logging-basics.md), [tracing basics](06-tracing-basics.md), [counter and gauge metrics](08-metrics-counter-gauge.md), [OpenTelemetry setup](11-opentelemetry-setup.md).
