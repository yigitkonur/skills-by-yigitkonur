# Retries and Timeouts
Apply retry and timeout policies around `HttpClient` calls while keeping transient failures, decode failures, and status failures distinct.

## Retry at the client level

`HttpClient.retry` transforms a client. Every request executed through the transformed client uses the retry policy.

```typescript
import { HttpClient } from "@effect/platform"
import { Effect, Schedule } from "effect"

const program = Effect.gen(function* () {
  const baseClient = yield* HttpClient.HttpClient
  const retryingClient = baseClient.pipe(
    HttpClient.retry(
      Schedule.exponential("100 millis").pipe(
        Schedule.intersect(Schedule.recurs(3))
      )
    )
  )

  return yield* retryingClient.get("https://api.example.com/flaky")
})
```

Use this when the same policy belongs to every request through that client. For one call, applying `Effect.retry` to the request effect is often simpler.

## Retry options

`HttpClient.retry` also accepts Effect retry options:

```typescript
import { HttpClient } from "@effect/platform"
import { Effect, Schedule } from "effect"

const program = Effect.gen(function* () {
  const baseClient = yield* HttpClient.HttpClient
  const client = baseClient.pipe(
    HttpClient.retry({
      schedule: Schedule.spaced("250 millis"),
      times: 2
    })
  )

  return yield* client.get("https://api.example.com/status")
})
```

Use a `while` predicate when only some error values should be retried.

## Transient retries

`HttpClient.retryTransient` is purpose-built for common transient failures. Source marks transport errors, timeout exceptions, and these response statuses as transient: 408, 429, 500, 502, 503, and 504.

```typescript
import { HttpClient } from "@effect/platform"
import { Effect, Schedule } from "effect"

const program = Effect.gen(function* () {
  const baseClient = yield* HttpClient.HttpClient
  const client = baseClient.pipe(
    HttpClient.retryTransient({
      schedule: Schedule.exponential("100 millis"),
      times: 3
    })
  )

  return yield* client.get("https://api.example.com/report")
})
```

Use `retryTransient` before hand-writing a status predicate. It already covers the common retryable HTTP status codes and transport failures.

## Retry mode

`retryTransient` can retry errors only, responses only, or both.

```typescript
import { HttpClient } from "@effect/platform"
import { Effect } from "effect"

const program = Effect.gen(function* () {
  const baseClient = yield* HttpClient.HttpClient
  const client = baseClient.pipe(
    HttpClient.retryTransient({
      mode: "both",
      times: 2
    })
  )

  return yield* client.get("https://api.example.com/retryable")
})
```

Choose `response-only` when a proxy returns retryable statuses but transport is stable. Choose `errors-only` when the response body or status should be handled exactly once.

## Timeout the request effect

Timeouts are effects, so they can wrap a client call directly:

```typescript
import { HttpClient } from "@effect/platform"
import { Effect } from "effect"

const program = HttpClient.get("https://api.example.com/slow").pipe(
  Effect.timeout("3 seconds")
)
```

`Effect.timeout` changes the success type to an optional value. Use `timeoutFail` when timeout should become a typed failure your caller must handle.

```typescript
import { HttpClient } from "@effect/platform"
import { Data, Effect } from "effect"

class UpstreamTimedOut extends Data.TaggedError("UpstreamTimedOut")<{
  readonly service: string
}> {}

const program = HttpClient.get("https://api.example.com/slow").pipe(
  Effect.timeoutFail({
    duration: "3 seconds",
    onTimeout: () => new UpstreamTimedOut({ service: "reports" })
  })
)
```

Because `HttpClient` requests are interruptible, timeout interruption can abort the underlying request.

## Combine retry and timeout deliberately

Order controls behavior:

```typescript
import { HttpClient } from "@effect/platform"
import { Effect } from "effect"

const perAttemptTimeout = HttpClient.get("https://api.example.com/slow").pipe(
  Effect.timeoutFail({
    duration: "2 seconds",
    onTimeout: () => "attempt timed out" as const
  }),
  Effect.retry({ times: 2 })
)

const wholeOperationTimeout = HttpClient.get("https://api.example.com/slow").pipe(
  Effect.retry({ times: 2 }),
  Effect.timeoutFail({
    duration: "2 seconds",
    onTimeout: () => "operation timed out" as const
  })
)
```

Per-attempt timeout gives each retry its own budget. Whole-operation timeout caps all attempts together.

## Transform response effects

`HttpClient.transformResponse` wraps every response effect for a client. It is useful for cross-cutting timeouts or metrics, but use it sparingly; a local timeout around one call is clearer when only one endpoint needs the policy.

## Scheduling guidance

Start with a bounded schedule. Infinite retry loops around outbound HTTP can hold fibers, saturate upstream services, and hide incidents.

```typescript
import { HttpClient } from "@effect/platform"
import { Schedule } from "effect"

const policy = Schedule.exponential("100 millis").pipe(
  Schedule.intersect(Schedule.recurs(4))
)

const withRetry = HttpClient.retry(policy)
```

For more schedule constructors and composition patterns, see [../scheduling/02-built-in-schedules.md](../scheduling/02-built-in-schedules.md).

## What not to retry

Do not retry schema decode failures by default. A `ResponseError` with reason `Decode` or a `ParseError` usually means the upstream returned a shape you do not understand.

Do not retry `StatusCode` failures blindly. Retry 408, 429, 500, 502, 503, and 504 when they match your upstream contract. Treat 400, 401, 403, and 404 as normal domain outcomes unless the API documents otherwise.

## Cross-references

See also: [01-overview.md](01-overview.md), [05-derived-client.md](05-derived-client.md), [08-error-handling.md](08-error-handling.md), [../scheduling/02-built-in-schedules.md](../scheduling/02-built-in-schedules.md).
