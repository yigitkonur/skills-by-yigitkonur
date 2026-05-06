# Metrics Counter Gauge
Use counters for cumulative events and gauges for current values, then update them through Effect operations.

## Core APIs

| API | Metric type | Use for |
|---|---|---|
| `Metric.counter(name, options)` | counter | cumulative counts |
| `Metric.gauge(name, options)` | gauge | current value |
| `Metric.increment(metric)` | counter or gauge | add one |
| `Metric.incrementBy(metric, amount)` | counter or gauge | add amount |
| `Metric.set(metric, value)` | gauge | set current value |
| `Metric.update(metric, input)` | any metric | send raw update input |
| `Effect.withMetric(metric)` | effect aspect | record success value |

Counter and gauge metrics can use `number` or `bigint` input.

## Counter

```typescript
import { Effect, Metric } from "effect"

const jobsStarted = Metric.counter("jobs_started_total", {
  description: "Total jobs started",
  incremental: true
})

const startJob = Effect.gen(function* () {
  yield* Metric.increment(jobsStarted)
  yield* Effect.logInfo("job started")
})
```

Use `incremental: true` for monotonic event counters.

## Counter by Amount

```typescript
import { Effect, Metric } from "effect"

const bytesUploaded = Metric.counter("bytes_uploaded_total", {
  description: "Total bytes uploaded",
  incremental: true
})

const recordUpload = (bytes: number) =>
  Effect.gen(function* () {
    yield* Metric.incrementBy(bytesUploaded, bytes)
    yield* Effect.logInfo("upload recorded", { bytes })
  })
```

Counters should not be decremented. If the value can go down, use a gauge.

## Gauge

```typescript
import { Effect, Metric } from "effect"

const queueDepth = Metric.gauge("queue_depth", {
  description: "Current pending job count"
})

const recordDepth = (depth: number) =>
  Effect.gen(function* () {
    yield* Metric.set(queueDepth, depth)
    yield* Effect.logInfo("queue depth sampled", { depth })
  })
```

Gauges represent the latest sampled value.

## Incrementing Gauges

```typescript
import { Effect, Metric } from "effect"

const activeWorkers = Metric.gauge("active_workers", {
  description: "Current active worker count"
})

const workerStarted = Metric.increment(activeWorkers)
const workerStopped = Metric.incrementBy(activeWorkers, -1)

const workerLifecycle = Effect.gen(function* () {
  yield* workerStarted
  yield* Effect.addFinalizer(() => workerStopped)
  yield* Effect.logInfo("worker running")
})
```

Use finalizers for lifecycle gauges so decrement logic stays tied to runtime
scope.

## BigInt Metrics

```typescript
import { Metric } from "effect"

const rowsProcessed = Metric.counter("rows_processed_total", {
  bigint: true,
  incremental: true
})
```

Use bigint only when values can exceed safe integer limits and your exporter
and backend handle integer values as expected.

## Track Success Value

`Effect.withMetric` records the effect's success value into a metric whose input
type accepts that value.

```typescript
import { Effect, Metric } from "effect"

const payloadBytes = Metric.counter("payload_bytes_total", {
  description: "Total payload bytes",
  incremental: true
})

const loadPayloadSize = Effect.succeed(512).pipe(
  Effect.withMetric(payloadBytes)
)
```

Use explicit `Metric.incrementBy` when the metric update is more readable than
making the success value double as instrumentation input.

## Track Outcome Counts

```typescript
import { Effect, Metric } from "effect"

const failures = Metric.counter("job_failures_total", {
  incremental: true
})

declare const runJob: Effect.Effect<void, "JobFailed">

const instrumented = runJob.pipe(
  Effect.tapError(() => Metric.increment(failures))
)
```

Typed errors make outcome metrics precise without parsing messages.

## Placement

Define metrics once at module scope:

```typescript
import { Metric } from "effect"

export const httpRequests = Metric.counter("http_requests_total", {
  description: "Total HTTP requests",
  incremental: true
})
```

Update them inside effects. Avoid constructing metrics dynamically with request
ids or other high-cardinality names.

## Counter vs Gauge

| Question | Metric |
|---|---|
| How many requests have completed? | counter |
| How many jobs are currently queued? | gauge |
| How many bytes have been uploaded? | counter |
| How much memory is currently used? | gauge |
| How many workers are active right now? | gauge |

Choose based on whether the value is cumulative or current.

## Anti-patterns

- Creating a new metric name per user, request, or tenant.
- Using a counter for values that can decrease.
- Forgetting to decrement lifecycle gauges in a finalizer.
- Recording values outside Effect when the update belongs to an effectful operation.
- Hiding metric updates in unrelated utility functions.

## Review Checklist

- Metric names are stable and low-cardinality.
- Counters that represent events use `incremental: true`.
- Gauges are set or adjusted with lifecycle-safe effects.
- Failure metrics use typed error recovery.
- Metric updates are inside effects and are yielded or returned.

## Cross-references

See also: [histogram and summary metrics](09-metrics-histogram-summary.md), [metric tags](10-metric-tagged.md), [OpenTelemetry setup](11-opentelemetry-setup.md), [supervisor](13-supervisor.md).
