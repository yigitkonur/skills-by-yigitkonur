# HTTP Client Overview
Use Effect's platform HTTP client as a typed, composable service instead of calling fetch directly inside application code.

## What it is

`HttpClient` lives in `@effect/platform` and represents an Effect-native client for outbound HTTP. It is a service, so code that needs outbound HTTP expresses that requirement in the `R` channel until a platform layer provides an implementation.

```typescript
import { FetchHttpClient, HttpClient, HttpClientResponse } from "@effect/platform"
import { Effect, Schema } from "effect"

const User = Schema.Struct({
  id: Schema.Number,
  name: Schema.String
})

const getUser = (id: number) =>
  HttpClient.get(`https://api.example.com/users/${id}`).pipe(
    Effect.flatMap(HttpClientResponse.schemaBodyJson(User)),
    Effect.provide(FetchHttpClient.layer)
  )
```

`HttpClient.get` and the other verb helpers are accessors for the `HttpClient.HttpClient` service. The example above requires `HttpClient.HttpClient` until `FetchHttpClient.layer` is provided.

## The moving parts

| Module | Role |
|---|---|
| `HttpClient` | Service tag, verb accessors, filters, retries, transformations, tracing |
| `HttpClientRequest` | Immutable request model and helpers for headers, URLs, and bodies |
| `HttpClientResponse` | Response model and body decoding helpers |
| `FetchHttpClient` | Layer backed by `globalThis.fetch` |
| `HttpApiClient` | Derives a typed client from an `HttpApi` contract |
| `HttpClientError` | Typed request and response failures |

Use the low-level client when the remote API is not described by an `HttpApi`. Use `HttpApiClient.make` when you own, share, or can model the contract. The derived client is the safer default for Effect-to-Effect systems because the same endpoint definition drives server and client types.

## Service access

Use direct accessors for one-off requests:

```typescript
import { FetchHttpClient, HttpClient } from "@effect/platform"
import { Effect } from "effect"

const health = HttpClient.get("https://api.example.com/health").pipe(
  Effect.flatMap((response) => response.text),
  Effect.provide(FetchHttpClient.layer)
)
```

Use the service value when several calls share behavior:

```typescript
import {
  FetchHttpClient,
  HttpClient,
  HttpClientRequest,
  HttpClientResponse
} from "@effect/platform"
import { Effect, Schema } from "effect"

const Account = Schema.Struct({
  id: Schema.String,
  active: Schema.Boolean
})

const program = Effect.gen(function* () {
  const baseClient = yield* HttpClient.HttpClient
  const client = baseClient.pipe(
    HttpClient.filterStatusOk,
    HttpClient.mapRequest(
      HttpClientRequest.prependUrl("https://api.example.com")
    )
  )

  return yield* client.get("/accounts/current").pipe(
    Effect.flatMap(HttpClientResponse.schemaBodyJson(Account))
  )
}).pipe(Effect.provide(FetchHttpClient.layer))
```

The service value is still immutable. Each combinator returns a transformed client; it does not mutate the layer or the global service.

## Request lifecycle

1. Build a `HttpClientRequest` manually or call a client verb helper.
2. Request transformations run through `HttpClient.mapRequest` and `mapRequestEffect`.
3. The platform implementation sends the request.
4. Response transformations, filters, tracing, and retry policies wrap the response effect.
5. The caller decodes the body, inspects status, streams bytes, or returns the raw response.

```typescript
import {
  FetchHttpClient,
  HttpClient,
  HttpClientRequest,
  HttpClientResponse
} from "@effect/platform"
import { Effect, Schema } from "effect"

const SearchResult = Schema.Struct({
  total: Schema.Number
})

const search = (term: string) =>
  HttpClientRequest.get("/search").pipe(
    HttpClientRequest.setUrlParam("q", term),
    HttpClient.execute,
    Effect.flatMap(HttpClientResponse.schemaBodyJson(SearchResult)),
    Effect.provide(FetchHttpClient.layer)
  )
```

For normal code, prefer providing `FetchHttpClient.layer` to the program and using `HttpClient.HttpClient` or accessors. `HttpClient.layerMergedContext` is for the less common case where you build a custom client effect and want it exposed as the `HttpClient` service.

## Status handling

By default, a response with a 404 or 500 is still a successful `HttpClientResponse`. HTTP status becomes a typed failure only when you ask for it.

```typescript
import { HttpClient, HttpClientResponse } from "@effect/platform"
import { Effect, Schema } from "effect"

const Payload = Schema.Struct({
  ok: Schema.Boolean
})

const call = HttpClient.get("https://api.example.com/status").pipe(
  Effect.flatMap(HttpClientResponse.filterStatusOk),
  Effect.flatMap(HttpClientResponse.schemaBodyJson(Payload))
)
```

Use `HttpClient.filterStatusOk` when you want every request through a client to fail on non-2xx responses. Use `HttpClientResponse.filterStatusOk` when the policy belongs to one response.

## Error model

The error channel uses `HttpClientError.HttpClientError` for client failures. It is a union of:

| Error | Common reasons |
|---|---|
| `RequestError` | `Transport`, `Encode`, `InvalidUrl` |
| `ResponseError` | `StatusCode`, `Decode`, `EmptyBody` |

Network and transport failures are request errors. Body parse failures are response errors with reason `Decode`. This distinction matters for recovery: retry transport failures differently from schema failures.

## Use the highest-level client you can

Choose the level based on the contract you have:

| Situation | Use |
|---|---|
| One-off third-party call | `HttpClient.get`, `post`, or `execute` |
| Shared base URL, headers, retries | A transformed `HttpClient` service |
| Schema-checked request body | `HttpClientRequest.schemaBodyJson` |
| Schema-checked response body | `HttpClientResponse.schemaBodyJson` |
| Shared API contract | `HttpApiClient.make(api, { baseUrl })` |

Do not hide raw HTTP calls in Promise helpers. Keep outbound HTTP in Effect so retries, timeouts, tracing, interruption, and typed errors stay visible.

## Cross-references

See also: [02-fetch-http-client.md](02-fetch-http-client.md), [03-request-building.md](03-request-building.md), [04-response-decoding.md](04-response-decoding.md), [05-derived-client.md](05-derived-client.md).
