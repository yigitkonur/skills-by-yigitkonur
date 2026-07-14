# HTTP Client Error Handling
Handle `HttpClientError` by request-vs-response failure and by reason instead of collapsing every outbound failure into one generic error.

## Error union

`HttpClientError.HttpClientError` is a union of `RequestError` and `ResponseError`.

```typescript
import { HttpClient, HttpClientError } from "@effect/platform"
import { Effect } from "effect"

const program = HttpClient.get("https://api.example.com/users").pipe(
  Effect.catchTag("RequestError", (error: HttpClientError.RequestError) =>
    Effect.logError(error.message)
  )
)
```

Request errors happen before a usable response exists. Response errors happen after the client has a response or while reading that response.

## RequestError reasons

| Reason | Meaning |
|---|---|
| `Transport` | Network or runtime transport failed |
| `Encode` | Request body encoding failed |
| `InvalidUrl` | Request URL plus parameters could not become a valid URL |

```typescript
import { HttpClient, HttpClientError } from "@effect/platform"
import { Effect } from "effect"

const recoverTransport = (error: HttpClientError.RequestError) => {
  switch (error.reason) {
    case "Transport":
      return Effect.logError(`transport failure: ${error.methodAndUrl}`)
    case "Encode":
      return Effect.fail(error)
    case "InvalidUrl":
      return Effect.fail(error)
  }
}

const program = HttpClient.get("https://api.example.com/users").pipe(
  Effect.catchTag("RequestError", recoverTransport)
)
```

Transport errors are the network-like branch. Encode and invalid URL errors are usually local bugs or invalid inputs.

## ResponseError reasons

| Reason | Meaning |
|---|---|
| `StatusCode` | You filtered or matched a status as failure |
| `Decode` | Body, JSON, form, stream, or generated response decoding failed |
| `EmptyBody` | A body accessor required a body but none existed |

```typescript
import { HttpClient, HttpClientResponse } from "@effect/platform"
import { Effect, Schema } from "effect"

const Payload = Schema.Struct({
  id: Schema.String
})

const program = HttpClient.get("https://api.example.com/payload").pipe(
  Effect.flatMap(HttpClientResponse.filterStatusOk),
  Effect.flatMap(HttpClientResponse.schemaBodyJson(Payload)),
  Effect.catchTag("ResponseError", (error) => {
    switch (error.reason) {
      case "StatusCode":
        return Effect.logError(`bad status: ${error.response.status}`)
      case "Decode":
        return Effect.logError(`decode failure: ${error.message}`)
      case "EmptyBody":
        return Effect.logError(`empty body: ${error.methodAndUrl}`)
    }
  })
)
```

This is the core distinction: network or transport failures are request errors; decode failures are response errors.

## Status is opt-in failure

`HttpClient` does not fail a request solely because the server returned 404 or 500. Add filtering when your domain wants non-2xx as failures.

```typescript
import { HttpClient, HttpClientResponse } from "@effect/platform"
import { Effect } from "effect"

const program = HttpClient.get("https://api.example.com/missing").pipe(
  Effect.flatMap(HttpClientResponse.filterStatusOk)
)
```

For APIs where 404 has a response body you need, use `matchStatus` instead of filtering it away.

## Decode errors and parse errors

Body accessor failures become `ResponseError` with reason `Decode`. Schema validation failures from `schemaBodyJson` add `ParseResult.ParseError` to the error channel.

```typescript
import { HttpClient, HttpClientResponse } from "@effect/platform"
import { Effect, Schema } from "effect"

const User = Schema.Struct({
  id: Schema.String,
  name: Schema.String
})

const program = HttpClient.get("https://api.example.com/users/current").pipe(
  Effect.flatMap(HttpClientResponse.schemaBodyJson(User)),
  Effect.catchTags({
    ResponseError: (error) =>
      error.reason === "Decode"
        ? Effect.logError(error.message)
        : Effect.fail(error),
    ParseError: (error) =>
      Effect.logError(`schema mismatch: ${error.message}`)
  })
)
```

Keep these separate when reporting upstream incidents. A malformed JSON body and a JSON body that fails your schema are different failures.

## Client-level recovery

`HttpClient.catchTag`, `catchTags`, and `catchAll` transform the client, not one response effect. Most code should recover at the call site, where the domain context is available. Use client-level recovery for cross-cutting fallback clients, logging, metrics, or retry setup.

## Retry by error type

Retry transport failures and documented transient statuses. Do not retry decode failures by default.

`retryTransient` already treats transport failures, timeout exceptions, and common transient response statuses as retryable.

## Derived client errors

`HttpApiClient.make` generated methods can fail with `HttpClientError`, `ParseError`, and endpoint-defined errors. Endpoint errors are part of the API contract; handle them by tag when schemas define tagged errors.

```typescript
import { HttpApiClient } from "@effect/platform"
import { Effect } from "effect"

declare const Api: typeof import("./api.js").Api

const program = Effect.gen(function* () {
  const client = yield* HttpApiClient.make(Api, {
    baseUrl: "https://api.example.com"
  })

  return yield* client.users.getUser({ path: { id: "user-1" } }).pipe(
    Effect.catchTag("ResponseError", (error) =>
      Effect.logError(error.message)
    )
  )
})
```

If a generated client method returns a typed domain error, prefer recovering from that domain error instead of inspecting raw status codes.

## Common mistakes

- Do not model every outbound failure as one string error.
- Do not treat decode errors as transport failures.
- Do not assume status codes fail without `filterStatus`, `filterStatusOk`, or generated API decoding.
- Do not retry schema mismatches unless the upstream explicitly documents eventual consistency in response shape.
- Do not swallow `InvalidUrl`; fix request construction or validate the input before building the URL.

## Cross-references

See also: [01-overview.md](01-overview.md), [04-response-decoding.md](04-response-decoding.md), [06-retries-and-timeouts.md](06-retries-and-timeouts.md), [../error-handling/04-catch-tag.md](../error-handling/04-catch-tag.md).
