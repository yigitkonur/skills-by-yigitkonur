# Tracing Basics
Use spans to describe operation structure, timing, failures, and trace-local attributes without changing effect types.

## Core APIs

| API | Purpose |
|---|---|
| `Effect.withSpan(name)` | wrap an effect in a child span |
| `Effect.annotateCurrentSpan(key, value)` | add an attribute to the active span |
| `Effect.annotateCurrentSpan(values)` | add several attributes |
| `Effect.spanLinks` | read links registered for the current span stack |
| `Effect.linkSpanCurrent(span, attributes)` | link another span to the current span |
| `Effect.fn("name")` | define a named effectful function that creates spans |

`Effect.withSpan` preserves the success, error, and requirement channels of the
wrapped effect. Instrumentation should not leak into business types.

## Basic Span

```typescript
import { Effect } from "effect"

const loadDashboard = Effect.gen(function* () {
  yield* Effect.annotateCurrentSpan("dashboard.id", "dash-123")
  yield* Effect.logInfo("loading dashboard")
  return { id: "dash-123", panels: 4 }
}).pipe(Effect.withSpan("Dashboards.load"))
```

The span records duration and failure status. The annotation becomes a span
attribute for trace search and inspection.

## Prefer Effect.fn for Named Functions

`Effect.fn("name")` automatically creates spans around each call. See
[Effect Fn](../core/07-effect-fn.md) for the core pattern.

```typescript
import { Effect } from "effect"

const loadUser = Effect.fn("Users.load")(function* (userId: string) {
  yield* Effect.annotateCurrentSpan("user.id", userId)
  yield* Effect.logInfo("loading user")
  return { id: userId, name: "Ada" }
})
```

Do not wrap this same function body in another `Effect.withSpan("Users.load")`.
Add nested spans only for meaningful sub-operations.

## Nested Spans

```typescript
import { Effect } from "effect"

const queryDatabase = Effect.gen(function* () {
  yield* Effect.annotateCurrentSpan("db.system", "postgresql")
  yield* Effect.sleep("20 millis")
  return 3
}).pipe(Effect.withSpan("Database.query"))

const loadPage = Effect.gen(function* () {
  const rows = yield* queryDatabase
  yield* Effect.logInfo("loaded rows", { rows })
  return rows
}).pipe(Effect.withSpan("Pages.load"))
```

Nested spans should mirror meaningful work boundaries, not every local helper.

## Span Options

`Effect.withSpan` accepts `Tracer.SpanOptions`.

```typescript
import { Effect } from "effect"

const publishMessage = Effect.gen(function* () {
  yield* Effect.logInfo("message published")
}).pipe(
  Effect.withSpan("Messages.publish", {
    kind: "producer",
    attributes: {
      "messaging.system": "sqs",
      "messaging.destination": "billing-events"
    }
  })
)
```

Use span kind when the operation crosses process boundaries:

- `server` for inbound request handling
- `client` for outbound requests
- `producer` for enqueue or publish
- `consumer` for dequeue or consume
- `internal` for local work

## Current Span Annotations

```typescript
import { Effect } from "effect"

const authorize = (role: string) =>
  Effect.gen(function* () {
    yield* Effect.annotateCurrentSpan({
      "auth.role": role,
      "auth.decision": "allow"
    })
    return true
  })
```

Annotate only values useful for trace diagnosis. Avoid dumping whole domain
objects into span attributes.

## Failure Status

When an effect fails inside a span, the tracer can mark the span with failure
status and exception events. Keep expected errors typed so spans describe the
failure without forcing defects.

```typescript
import { Effect } from "effect"

class RemoteUnavailable {
  readonly _tag = "RemoteUnavailable"
}

const callRemote = Effect.fail(new RemoteUnavailable()).pipe(
  Effect.withSpan("Remote.call")
)
```

If the caller recovers, the child span still contains the failed operation.

## Span Links

Use links when work is causally related but not parent-child work, such as
batch processing messages created by other traces.

```typescript
import { Effect, Tracer } from "effect"

declare const upstreamSpan: Tracer.ExternalSpan

const processMessage = Effect.gen(function* () {
  yield* Effect.linkSpanCurrent(upstreamSpan, {
    relation: "consumed-message"
  })
  yield* Effect.logInfo("message processed")
}).pipe(Effect.withSpan("Messages.process"))
```

Links preserve relationships without pretending that asynchronous work shares a
single synchronous parent.

## Root Spans

Use `root: true` when a span must start a new trace.

```typescript
import { Effect } from "effect"

const scheduledJob = Effect.logInfo("job ran").pipe(
  Effect.withSpan("Jobs.dailyReconcile", { root: true })
)
```

Root spans are useful for schedulers, CLIs, and workers that start independent
units of work.

## Logs as Trace Events

With OpenTelemetry wiring, logs emitted inside a span can be correlated to the
active span. Keep the log call inside the span region:

```typescript
import { Effect } from "effect"

const program = Effect.gen(function* () {
  yield* Effect.logInfo("inside traced operation")
}).pipe(Effect.withSpan("Operation"))
```

This is why Effect-native logging and tracing should be wired together.

## Anti-patterns

- Creating spans around every small pure transformation.
- Using dynamic ids as span names.
- Adding a second span around an `Effect.fn` body with the same name.
- Annotating spans with large payloads.
- Modeling asynchronous message causality as parent-child when a link is more accurate.

## Review Checklist

- Major service methods use `Effect.fn("Service.method")`.
- Manual spans have stable names.
- Attributes are queryable and bounded where possible.
- `spanLinks` or `linkSpanCurrent` is used for asynchronous causality.
- Root spans are reserved for true trace roots.
- Tracing code does not change business types.

## Cross-references

See also: [span scoped](07-span-scoped.md), [OpenTelemetry setup](11-opentelemetry-setup.md), [OTLP exporters](12-otlp-exporters.md), [Effect Fn](../core/07-effect-fn.md).
