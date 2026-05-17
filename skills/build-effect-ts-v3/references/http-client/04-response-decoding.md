# Response Decoding
Decode HTTP responses with `HttpClientResponse` helpers so body, status, and schema failures stay typed.

## Response model

`HttpClientResponse.HttpClientResponse` includes the original request, status, headers, cookies, and body accessors. A non-2xx status is still a successful response until you filter or match it.

```typescript
import { HttpClient, HttpClientResponse } from "@effect/platform"
import { Effect, Schema } from "effect"

const Todo = Schema.Struct({
  id: Schema.Number,
  title: Schema.String,
  completed: Schema.Boolean
})

const getTodo = HttpClient.get("https://api.example.com/todos/1").pipe(
  Effect.flatMap(HttpClientResponse.schemaBodyJson(Todo))
)
```

`schemaBodyJson` first reads `response.json`, then decodes the unknown JSON value with the provided Schema.

## Body accessors

Use raw body accessors when no schema applies:

```typescript
import { HttpClient } from "@effect/platform"
import { Effect } from "effect"

const getText = HttpClient.get("https://api.example.com/readme").pipe(
  Effect.flatMap((response) => response.text)
)

const getJson = HttpClient.get("https://api.example.com/raw-json").pipe(
  Effect.flatMap((response) => response.json)
)

const getBytes = HttpClient.get("https://api.example.com/archive").pipe(
  Effect.flatMap((response) => response.arrayBuffer)
)
```

Raw `json` succeeds with `unknown`. Decode it before passing data into domain logic.

## Schema body JSON

Use schema decoding at the boundary:

```typescript
import { HttpClient, HttpClientResponse } from "@effect/platform"
import { Effect, Schema } from "effect"

const Account = Schema.Struct({
  id: Schema.String,
  balance: Schema.Number
})

const loadAccount = (id: string) =>
  HttpClient.get(`https://api.example.com/accounts/${id}`).pipe(
    Effect.flatMap(HttpClientResponse.filterStatusOk),
    Effect.flatMap(HttpClientResponse.schemaBodyJson(Account))
  )
```

This can fail with a response error from reading the body, a status code error from `filterStatusOk`, or a parse error from Schema decoding.

## Status-aware schema decoding

Use `schemaJson` when the schema includes status, headers, and body in one shape.

```typescript
import { HttpClient, HttpClientResponse } from "@effect/platform"
import { Effect, Schema } from "effect"

const CreatedUserResponse = Schema.Struct({
  status: Schema.Literal(201),
  body: Schema.Struct({
    id: Schema.String,
    name: Schema.String
  })
})

const createUser = HttpClient.post("https://api.example.com/users", {
  acceptJson: true
}).pipe(
  Effect.flatMap(HttpClientResponse.schemaJson(CreatedUserResponse))
)
```

`schemaJson` is useful when the status code is part of the contract. Use `schemaBodyJson` when only the body shape matters.

## Match status

`matchStatus` maps exact status codes, status classes, and an `orElse` branch to effects.

```typescript
import { HttpClient, HttpClientResponse } from "@effect/platform"
import { Effect, Schema } from "effect"

const User = Schema.Struct({
  id: Schema.String,
  name: Schema.String
})

const NotFound = Schema.Struct({
  message: Schema.String
})

const getUser = (id: string) =>
  HttpClient.get(`https://api.example.com/users/${id}`).pipe(
    Effect.flatMap(
      HttpClientResponse.matchStatus({
        "2xx": HttpClientResponse.schemaBodyJson(User),
        404: HttpClientResponse.schemaBodyJson(NotFound),
        orElse: (response) => Effect.succeed({
          message: `unexpected status ${response.status}`
        })
      })
    )
  )
```

This keeps non-2xx branches explicit. If the remote API has well-known error payloads, model them instead of collapsing every status into one generic failure.

## URL params and headers

`HttpClientResponse` re-exports incoming message helpers:

```typescript
import { HttpClient, HttpClientResponse } from "@effect/platform"
import { Effect, Schema } from "effect"

const RateLimitHeaders = Schema.Struct({
  "x-ratelimit-remaining": Schema.String
})

const readLimit = HttpClient.get("https://api.example.com/limited").pipe(
  Effect.flatMap((response) =>
    HttpClientResponse.schemaHeaders(RateLimitHeaders)(response)
  )
)
```

Use `schemaBodyUrlParams` for URL-encoded response bodies. Keep response header schemas small and specific to the headers you actually consume.

## Streaming responses

Use `HttpClientResponse.stream` when bytes should be processed incrementally:

```typescript
import { HttpClient, HttpClientResponse } from "@effect/platform"
import { Stream } from "effect"

const bodyText = HttpClient.get("https://api.example.com/export").pipe(
  HttpClientResponse.stream,
  Stream.decodeText(),
  Stream.runFold("", (all, chunk) => all + chunk)
)
```

The stream can fail with response errors. Do not convert it to a Promise-only stream in the middle of Effect code.

## Decode failures

Body read failures are `HttpClientError.ResponseError` with reason `Decode` or `EmptyBody`. Schema validation failures are `ParseResult.ParseError`.

```typescript
import { HttpClient, HttpClientResponse } from "@effect/platform"
import { Effect, Schema } from "effect"

const Payload = Schema.Struct({
  value: Schema.Number
})

const program = HttpClient.get("https://api.example.com/value").pipe(
  Effect.flatMap(HttpClientResponse.schemaBodyJson(Payload)),
  Effect.catchTag("ResponseError", (error) =>
    error.reason === "Decode"
      ? Effect.logError(error.message)
      : Effect.fail(error)
  )
)
```

Recover only when the fallback is valid for the domain. A decode failure often means the upstream contract drifted.

## Common mistakes

- Do not assume `response.json` returns a domain type; it returns `unknown`.
- Do not forget status filtering when non-2xx responses should fail.
- Do not decode the same body several times unless the accessor caches that body form.
- Do not discard `ParseError` details at API boundaries that need diagnostics.
- Do not treat response decode errors as network errors; they happened after a response was received.

## Cross-references

See also: [03-request-building.md](03-request-building.md), [05-derived-client.md](05-derived-client.md), [08-error-handling.md](08-error-handling.md), [../schema/10-decoding.md](../schema/10-decoding.md).
