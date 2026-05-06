# Span Scoped
Use scoped spans when span lifetime must follow a scope rather than the lexical duration of one effect.

## APIs

| API | Lifetime | Use when |
|---|---|---|
| `Effect.makeSpanScoped(name)` | current scope | you need the span value |
| `Effect.withSpanScoped(name)` | current scope | a wrapped effect opens a scoped span |
| `Effect.useSpan(name, evaluate)` | callback effect | you need a span value for one effect |

`makeSpanScoped` and `withSpanScoped` require `Scope.Scope` and end the span
when the scope finalizes.

## Why Scoped Spans Exist

Most spans should use `Effect.withSpan`. It starts and ends the span around one
effect.

Scoped spans are for work whose lifetime is tied to a resource:

- a server request scope
- a stream subscription
- a workflow lease
- a long-lived connection
- a supervised worker region

## Make a Scoped Span

```typescript
import { Effect } from "effect"

const program = Effect.scoped(
  Effect.gen(function* () {
    const span = yield* Effect.makeSpanScoped("Import.session")
    span.attribute("import.source", "nightly")
    yield* Effect.logInfo("import session opened")
  })
)
```

The span closes when the outer scope closes.

## Use a Span Value

Use `Effect.useSpan` when the span value is needed only inside one callback.

```typescript
import { Effect } from "effect"

const program = Effect.useSpan("Reports.render", (span) =>
  Effect.gen(function* () {
    span.attribute("report.kind", "monthly")
    yield* Effect.logInfo("rendered report")
  })
)
```

This avoids exposing a span beyond the region that owns it.

## Scoped Wrapper

```typescript
import { Effect } from "effect"

const subscription = Effect.gen(function* () {
  yield* Effect.logInfo("subscription active")
  yield* Effect.sleep("1 second")
}).pipe(Effect.withSpanScoped("Notifications.subscription"))

const program = Effect.scoped(subscription)
```

Use `withSpanScoped` when the span should stay open for the surrounding scope,
not only the immediate effect body.

## Parent Behavior

The source notes for `makeSpanScoped` say the span is not added to the current
span stack. That means child spans are not automatically created under it unless
you explicitly make it the parent for a region.

For ordinary nested traces, use `Effect.withSpan`.

## Resource Pattern

`acquireConnection` returns a scoped effect — the span lives as long as the surrounding scope, not as long as the gen body. Apply `Effect.scoped` at the boundary that owns the resource lifetime, not around the acquisition itself.

```typescript
import { Effect } from "effect"

const acquireConnection = Effect.gen(function* () {
  const span = yield* Effect.makeSpanScoped("Database.connection")
  span.attribute("db.system", "postgresql")
  yield* Effect.logInfo("connection acquired")
  return { close: Effect.logInfo("connection closed") }
})

const useConnection = Effect.scoped(
  Effect.gen(function* () {
    const conn = yield* acquireConnection
    yield* Effect.logInfo("running query under the open span")
    yield* conn.close
  })
)
```

The span represents the resource lifetime. The finalizer closes the scope, and
the scope ends the span.

## Choosing the API

| Need | Use |
|---|---|
| trace one effect | `Effect.withSpan` |
| trace a named function | `Effect.fn("name")` |
| access the span object briefly | `Effect.useSpan` |
| span follows resource scope | `Effect.makeSpanScoped` |
| wrapper span follows resource scope | `Effect.withSpanScoped` |

Do not reach for scoped spans by default. Scope lifetime is more complex than a
normal child span.

## Anti-patterns

- Using scoped spans for simple request handlers that finish in one effect.
- Forgetting `Effect.scoped` around `makeSpanScoped`.
- Expecting `makeSpanScoped` to automatically parent child spans.
- Passing span objects deep into domain services.
- Leaving long-lived spans unnamed or dynamically named.

## Review Checklist

- Scoped span examples are wrapped in `Effect.scoped`.
- Normal child spans still use `Effect.withSpan`.
- Span names describe resource lifetime.
- Span attributes are added near acquisition.
- Span values are not used as a replacement for Effect context.

## Cross-references

See also: [tracing basics](06-tracing-basics.md), [OpenTelemetry setup](11-opentelemetry-setup.md), [supervisor](13-supervisor.md), [structured logs](03-structured-logs.md).
