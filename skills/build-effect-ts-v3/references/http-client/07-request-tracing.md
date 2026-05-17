# Request Tracing
Use `HttpClient` tracing helpers to create client spans, customize names, and propagate W3C trace context headers.

## Default client spans

`HttpClient.make` wraps requests in client spans when tracing is enabled for the fiber. The span records HTTP method, URL fields, request headers after redaction, response status, and response headers after redaction.

```typescript
import { FetchHttpClient, HttpClient } from "@effect/platform"
import { Effect } from "effect"

const program = HttpClient.get("https://api.example.com/health").pipe(
  Effect.flatMap((response) => response.text),
  Effect.provide(FetchHttpClient.layer)
)
```

You usually do not need to create a span manually around every request. The client implementation does it.

## Trace propagation

`HttpClient.withTracerPropagation(true)` enables injection of W3C trace context headers into outbound requests. The source uses the current span and writes trace context headers onto the `HttpClientRequest` before the platform transport sends it.

```typescript
import { HttpClient } from "@effect/platform"
import { Effect } from "effect"

const program = Effect.gen(function* () {
  const baseClient = yield* HttpClient.HttpClient
  const client = baseClient.pipe(
    HttpClient.withTracerPropagation(true)
  )

  return yield* client.get("https://api.example.com/health")
})
```

Use this when downstream services participate in distributed tracing. Disable it when calling systems that reject unknown headers or when a privacy boundary forbids trace propagation.

## Propagation is automatic after enabling

Do not manually add trace headers when `withTracerPropagation(true)` is active. The client injects the W3C trace context headers from the active span.

```typescript
import { HttpClient, HttpClientRequest } from "@effect/platform"
import { Effect } from "effect"

const program = Effect.gen(function* () {
  const baseClient = yield* HttpClient.HttpClient
  const client = baseClient.pipe(
    HttpClient.withTracerPropagation(true),
    HttpClient.mapRequest(
      HttpClientRequest.setHeader("x-client", "billing")
    )
  )

  return yield* client.get("https://api.example.com/invoices")
})
```

Business headers and trace propagation can coexist. Let the client own trace context.

## Disable tracing for selected requests

Use `withTracerDisabledWhen` when some requests should skip client spans.

```typescript
import { HttpClient } from "@effect/platform"
import { Effect } from "effect"

const program = Effect.gen(function* () {
  const baseClient = yield* HttpClient.HttpClient
  const client = baseClient.pipe(
    HttpClient.withTracerDisabledWhen((request) =>
      request.url.includes("/health")
    )
  )

  return yield* client.get("https://api.example.com/health")
})
```

This is useful for noisy health checks or endpoints where tracing would add volume without diagnostic value.

## Customize span names

`withSpanNameGenerator` sets the naming function for request spans.

```typescript
import { HttpClient } from "@effect/platform"
import { Effect } from "effect"

const program = Effect.gen(function* () {
  const baseClient = yield* HttpClient.HttpClient
  const client = baseClient.pipe(
    HttpClient.withSpanNameGenerator((request) =>
      `http ${request.method} ${request.url}`
    )
  )

  return yield* client.get("https://api.example.com/users")
})
```

Keep names low-cardinality when possible. Full URLs with IDs can make tracing backends harder to aggregate. If cardinality matters, map known route templates before naming spans.

## Redaction

The implementation redacts request and response headers before recording them as span attributes. Use the platform header redaction facilities for secrets instead of stripping all headers from spans.

```typescript
import { HttpClient, HttpClientRequest } from "@effect/platform"
import { Effect, Redacted } from "effect"

const program = Effect.gen(function* () {
  const baseClient = yield* HttpClient.HttpClient
  const client = baseClient.pipe(
    HttpClient.mapRequest(
      HttpClientRequest.bearerToken(Redacted.make("token-value"))
    )
  )

  return yield* client.get("https://api.example.com/me")
})
```

Prefer request helpers that understand redacted values. That keeps inspection, logs, and tracing safer.

## Derived clients

`HttpApiClient.make` uses the provided `HttpClient`, so tracing policies apply through `transformClient`.

```typescript
import { HttpApiClient, HttpClient } from "@effect/platform"
import { Effect } from "effect"

declare const Api: typeof import("./api.js").Api

const program = Effect.gen(function* () {
  const client = yield* HttpApiClient.make(Api, {
    baseUrl: "https://api.example.com",
    transformClient: (httpClient) =>
      httpClient.pipe(
        HttpClient.withTracerPropagation(true),
        HttpClient.withSpanNameGenerator((request) =>
          `api ${request.method} ${request.url}`
        )
      )
  })

  return yield* client.users.getUser({ path: { id: "user-1" } })
})
```

This is the right place to apply propagation to a generated API client. The endpoint-specific typing stays intact.

## Common mistakes

- Do not manually inject trace context headers when `withTracerPropagation(true)` is enabled.
- Do not disable tracing globally to quiet one noisy endpoint; use `withTracerDisabledWhen`.
- Do not put secrets in custom span names.
- Do not generate high-cardinality span names unless your tracing backend can handle them.
- Do not assume propagation works without an active tracing setup; the helper controls HTTP header propagation, not exporter configuration.

## Cross-references

See also: [01-overview.md](01-overview.md), [02-fetch-http-client.md](02-fetch-http-client.md), [05-derived-client.md](05-derived-client.md), [../observability/01-overview.md](../observability/01-overview.md).
