# Metric Tagged
Use metric tags for bounded dimensions and log or trace context for high-cardinality values.

## Core APIs

| API | Scope | Use for |
|---|---|---|
| `Metric.tagged(metric, key, value)` | one metric | static tag on a metric |
| `Metric.tagged(key, value)(metric)` | one metric | pipeable static tag |
| `Metric.taggedWithLabels(metric, labels)` | one metric | static labels from `MetricLabel` |
| `Metric.taggedWithLabelsInput(metric, f)` | one metric | derive labels from update input |
| `Effect.tagMetrics(key, value)` | wrapped effect | tag all metrics in an effect |
| `Effect.tagMetrics(values)` | wrapped effect | add several tags |
| `Effect.tagMetricsScoped(key, value)` | current scope | scoped tag inside `Effect.scoped` |

Tags are part of the metric identity. Treat every tag value as a storage
dimension.

## Static Metric Tag

```typescript
import { Effect, Metric } from "effect"

const requests = Metric.counter("http_requests_total", {
  incremental: true
}).pipe(
  Metric.tagged("route", "/users/:id"),
  Metric.tagged("method", "GET")
)

const recordRequest = Metric.increment(requests)
```

Use route templates, not raw request paths.

## Tag a Region

```typescript
import { Effect, Metric } from "effect"

const jobs = Metric.counter("jobs_total", {
  incremental: true
})

const runJob = Effect.gen(function* () {
  yield* Metric.increment(jobs)
  yield* Effect.logInfo("job completed")
}).pipe(
  Effect.tagMetrics({
    queue: "priority",
    worker: "email"
  })
)
```

All metric updates inside the wrapped effect receive the tags.

## Scoped Metric Tags

```typescript
import { Effect, Metric } from "effect"

const processed = Metric.counter("messages_processed_total", {
  incremental: true
})

const program = Effect.scoped(
  Effect.gen(function* () {
    yield* Effect.tagMetricsScoped("consumer", "billing")
    yield* Metric.increment(processed)
    yield* Effect.logInfo("message processed")
  })
)
```

Use scoped tags when a framework or adapter opens the metric context for nested
work and wants automatic cleanup.

## Dynamic Labels from Input

`Metric.taggedWithLabelsInput` derives labels from each update input. Use it
only when the input domain is bounded.

```typescript
import { Metric, MetricLabel } from "effect"

type Outcome = "success" | "failure"

const outcomes = Metric.frequency("payment_outcomes").pipe(
  Metric.taggedWithLabelsInput((outcome: Outcome) => [
    MetricLabel.make("outcome", outcome)
  ])
)
```

If the input can contain user ids, request ids, or arbitrary strings, do not use
it as metric labels.

## Tags vs Annotations

| Value | Use | Reason |
|---|---|---|
| route template | metric tag | bounded and useful for aggregation |
| deployment stage | metric tag | small fixed set |
| request id | log annotation | high cardinality |
| user id | log annotation or span attribute | high cardinality |
| error kind | metric tag or frequency value | bounded if typed |
| raw error message | log body | unbounded |

Metric tags are for aggregation. Logs and spans are for diagnosis.

## Outcome Metric

```typescript
import { Effect, Metric } from "effect"

const requests = Metric.counter("http_requests_total", {
  incremental: true
})

const recordOutcome = (outcome: "success" | "failure") =>
  Metric.increment(requests.pipe(Metric.tagged("outcome", outcome)))

declare const handle: Effect.Effect<void, "RequestFailed">

const instrumented = handle.pipe(
  Effect.tap(() => recordOutcome("success")),
  Effect.tapError(() => recordOutcome("failure"))
)
```

The outcome set is fixed, so it is safe as a tag.

## Service-Level Tags

```typescript
import { Effect, Metric } from "effect"

const dbCalls = Metric.counter("db_calls_total", {
  incremental: true
})

const queryUsers = Effect.gen(function* () {
  yield* Metric.increment(dbCalls)
  yield* Effect.logInfo("queried users")
}).pipe(
  Effect.tagMetrics("dependency", "postgresql")
)
```

Service-level tags are useful when several services update shared metric names.

## Anti-patterns

- Tagging metrics with raw request paths.
- Tagging metrics with user, tenant, session, or request ids.
- Generating tag keys dynamically.
- Using unbounded exception messages as frequency values.
- Using tags to carry context that belongs in logs.

## Review Checklist

- Every tag value has a bounded value set.
- Route tags use templates.
- Outcome tags come from typed outcomes.
- Scoped metric tags are used inside `Effect.scoped`.
- High-cardinality context is routed to logs or spans.

## Cross-references

See also: [counter and gauge metrics](08-metrics-counter-gauge.md), [histogram and summary metrics](09-metrics-histogram-summary.md), [structured logs](03-structured-logs.md), [tracing basics](06-tracing-basics.md).
