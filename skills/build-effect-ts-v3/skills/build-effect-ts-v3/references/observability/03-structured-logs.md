# Structured Logs
Use annotations and log spans to attach queryable context to every log produced inside an effect.

## Core APIs

| API | Scope | Use for |
|---|---|---|
| `Effect.annotateLogs(key, value)` | wrapped effect | stable key-value context |
| `Effect.annotateLogs(values)` | wrapped effect | several log attributes |
| `Effect.annotateLogsScoped(values)` | current scope | scoped context inside `Effect.scoped` |
| `Effect.withLogSpan(label)` | wrapped effect | elapsed time in log output |

Structured log context travels with the fiber. You do not pass a logger through
every function just to keep request metadata.

## Annotate a Region

```typescript
import { Effect } from "effect"

const program = Effect.gen(function* () {
  yield* Effect.logInfo("loading account")
  yield* Effect.logInfo("account loaded")
}).pipe(
  Effect.annotateLogs({
    requestId: "req-001",
    accountId: "acc-123"
  })
)
```

Every log produced by `program` receives both annotations.

## Annotate in a Service Method

```typescript
import { Effect } from "effect"

const chargeCard = Effect.fn("Payments.chargeCard")(function* (
  paymentId: string
) {
  yield* Effect.logInfo("charging card")
  yield* Effect.logInfo("card charged")
}).pipe(
  Effect.annotateLogs("component", "payments")
)
```

Use stable component names. Put request-specific values near the request entry
or inside the method that receives them.

## Scoped Annotations

`Effect.annotateLogsScoped` requires a scope and removes annotations when the
scope closes.

```typescript
import { Effect } from "effect"

const scopedProgram = Effect.scoped(
  Effect.gen(function* () {
    yield* Effect.annotateLogsScoped({
      batchId: "batch-2026-05-05",
      source: "nightly-import"
    })
    yield* Effect.logInfo("import started")
    yield* Effect.logInfo("import finished")
  })
)
```

Use scoped annotations when a helper opens contextual logging for a nested
operation but should not affect the caller after that operation returns.

## Log Spans

`Effect.withLogSpan` records elapsed time in log metadata.

```typescript
import { Effect } from "effect"

const rebuildIndex = Effect.gen(function* () {
  yield* Effect.sleep("100 millis")
  yield* Effect.logInfo("index rebuilt")
}).pipe(Effect.withLogSpan("indexRebuild"))
```

Log spans are not distributed tracing spans. Use them when the timing belongs
in logs. Use `Effect.withSpan` or `Effect.fn` when the timing belongs in a trace.

## Combine Annotations and Log Spans

```typescript
import { Effect } from "effect"

const handleWebhook = (webhookId: string) =>
  Effect.gen(function* () {
    yield* Effect.logInfo("webhook accepted")
    yield* Effect.sleep("50 millis")
    yield* Effect.logInfo("webhook processed")
  }).pipe(
    Effect.annotateLogs({ webhookId, component: "webhooks" }),
    Effect.withLogSpan("webhookProcessing")
  )
```

The annotation answers "which webhook?" and the log span answers "how long did
this logged region take?"

## Choosing Context Location

| Context | Put it in | Reason |
|---|---|---|
| request id | log annotation | high cardinality, useful in logs |
| user id | log annotation or span attribute | debug one request |
| route template | metric tag and span attribute | bounded value |
| component | log annotation | stable search field |
| latency | log span, trace span, or histogram | depends on analysis need |

Do not turn every log annotation into a metric tag.

## Nested Annotations

Inner annotations add or override context only for their wrapped region.

```typescript
import { Effect } from "effect"

const program = Effect.logInfo("save completed").pipe(
  Effect.annotateLogs("operation", "save"),
  Effect.annotateLogs("component", "profiles")
)
```

Prefer additive keys. Reusing the same key at many nested levels makes log
searches harder to reason about.

## Structured Message Values

```typescript
import { Effect } from "effect"

const logResult = (orderId: string, cents: number) =>
  Effect.logInfo("order priced", { orderId, cents })
```

Structured message values are useful for the event body. Annotations are useful
for context that should apply to every event in a region.

## Anti-patterns

- Building a custom logger just to add a request id.
- Adding raw ids as metric tags.
- Repeating the same string interpolation in every log call.
- Using a log span where a distributed trace span is needed.
- Opening scoped annotations outside `Effect.scoped`.

## Review Checklist

- Each annotation key has a stable meaning.
- High-cardinality values are limited to logs or trace attributes.
- `annotateLogsScoped` is used only inside a scoped effect.
- Timing in logs uses `withLogSpan`; distributed timing uses tracing spans.
- Service methods do not accept a logger argument just to carry context.

## Cross-references

See also: [logging basics](02-logging-basics.md), [log levels](04-log-levels.md), [tracing basics](06-tracing-basics.md), [metric tags](10-metric-tagged.md).
