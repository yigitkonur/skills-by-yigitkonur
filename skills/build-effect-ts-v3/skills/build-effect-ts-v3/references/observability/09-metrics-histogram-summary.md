# Metrics Histogram Summary
Use histograms for bucketed distributions, summaries for quantiles, and frequencies for categorical occurrence counts.

## Core APIs

| API | Use for |
|---|---|
| `Metric.histogram(name, boundaries, description)` | bucketed numeric observations |
| `MetricBoundaries.linear({ start, width, count })` | evenly-spaced buckets |
| `MetricBoundaries.exponential({ start, factor, count })` | exponentially-spaced buckets |
| `Metric.summary(options)` | rolling quantiles |
| `Metric.summaryTimestamp(options)` | timestamped summary observations |
| `Metric.frequency(name, options)` | counts by observed string |
| `Metric.timer(name)` | duration histogram in milliseconds |
| `Metric.timerWithBoundaries(name, boundaries)` | duration histogram with custom boundaries |
| `Metric.trackDuration(metric)` | record effect duration |
| `Metric.trackDurationWith(metric, f)` | convert duration before recording |

Histograms need explicit boundaries. Use `MetricBoundaries.linear` or
`MetricBoundaries.exponential` unless a hand-picked boundary array is truly
clearer.

## Linear Histogram

```typescript
import { Duration, Effect, Metric, MetricBoundaries } from "effect"

const responseSize = Metric.histogram(
  "http_response_size_bytes",
  MetricBoundaries.linear({ start: 0, width: 1024, count: 20 }),
  "HTTP response size in bytes"
)

const recordResponseSize = (bytes: number) =>
  Effect.gen(function* () {
    yield* Metric.update(responseSize, bytes)
    yield* Effect.logInfo("response size recorded", { bytes })
  })
```

Use linear buckets when the expected range is narrow and evenly distributed.

## Exponential Histogram

```typescript
import { Duration, Effect, Metric, MetricBoundaries } from "effect"

const requestLatency = Metric.histogram(
  "http_request_latency_ms",
  MetricBoundaries.exponential({ start: 1, factor: 2, count: 16 }),
  "HTTP request latency in milliseconds"
)

const handleRequest = Effect.sleep("25 millis").pipe(
  Metric.trackDurationWith(requestLatency, (duration) =>
    Duration.toMillis(duration)
  )
)
```

Use exponential buckets for latency because useful boundaries often grow
quickly from single milliseconds to seconds.

## Timer Metric

```typescript
import { Effect, Metric } from "effect"

const requestTimer = Metric.timerWithBoundaries(
  "http_request_duration",
  [5, 10, 25, 50, 100, 250, 500, 1000],
  "HTTP request duration"
)

const timed = Effect.sleep("30 millis").pipe(
  Metric.trackDuration(requestTimer)
)
```

Timer metrics record `Duration` input and add a time-unit tag.

## Summary

```typescript
import { Effect, Metric } from "effect"

const renderSummary = Metric.summary({
  name: "report_render_latency_ms",
  maxAge: "5 minutes",
  maxSize: 1000,
  error: 0.01,
  quantiles: [0.5, 0.9, 0.99],
  description: "Report render latency"
})

const recordRender = (millis: number) =>
  Effect.gen(function* () {
    yield* Metric.update(renderSummary, millis)
    yield* Effect.logInfo("render latency recorded", { millis })
  })
```

Use summaries when local rolling quantiles are useful. Use histograms when the
backend should aggregate bucketed distributions across workers.

## Frequency

```typescript
import { Effect, Metric } from "effect"

const errorKinds = Metric.frequency("job_error_kinds", {
  description: "Job errors by kind",
  preregisteredWords: ["Validation", "Timeout", "Remote"]
})

const recordErrorKind = (kind: "Validation" | "Timeout" | "Remote") =>
  Metric.update(errorKinds, kind)
```

Frequency metrics are for string categories. Keep categories bounded.

## Track Duration with Conversion

```typescript
import { Duration, Effect, Metric, MetricBoundaries } from "effect"

const latencyMillis = Metric.histogram(
  "dependency_latency_ms",
  MetricBoundaries.exponential({ start: 1, factor: 2, count: 12 })
)

declare const callDependency: Effect.Effect<string>

const instrumented = callDependency.pipe(
  Metric.trackDurationWith(latencyMillis, Duration.toMillis)
)
```

Use `Metric.trackDurationWith` when your metric accepts `number`. Use
`Metric.trackDuration` when the metric accepts `Duration.Duration`.

## Boundary Selection

| Distribution | Boundary helper |
|---|---|
| payload sizes in a narrow range | `MetricBoundaries.linear` |
| network latency | `MetricBoundaries.exponential` |
| known SLO buckets | `MetricBoundaries.fromIterable` |
| simple duration timing | `Metric.timerWithBoundaries` |

Do not rely on implicit buckets for histograms. The constructor requires
boundaries because bucket design is a product decision.

## Histogram vs Summary

Use histograms when:

- backend aggregation matters
- dashboards compare services or instances
- SLO buckets are known
- bucket counts are more useful than local quantiles

Use summaries when:

- local quantile approximation is enough
- the process owns the rolling window
- you need fixed memory with `maxSize`
- cross-instance aggregation is not the goal

## Anti-patterns

- Creating histograms without deliberate bucket boundaries.
- Using summaries for globally aggregated service SLOs.
- Recording request ids as frequency values.
- Tracking duration by manually reading wall-clock time around effects.
- Mixing seconds and milliseconds in one metric name.

## Review Checklist

- Histogram boundaries use `MetricBoundaries.linear`, `MetricBoundaries.exponential`, or an explicit SLO list.
- Metric names include units when the backend will not infer them.
- Frequency values are bounded categories.
- Duration tracking uses `Metric.trackDuration` or `Metric.trackDurationWith`.
- Summaries define `maxAge`, `maxSize`, `error`, and `quantiles`.

## Cross-references

See also: [counter and gauge metrics](08-metrics-counter-gauge.md), [metric tags](10-metric-tagged.md), [OpenTelemetry setup](11-opentelemetry-setup.md), [tracing basics](06-tracing-basics.md).
