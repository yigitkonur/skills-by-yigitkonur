# Request Building
Build immutable `HttpClientRequest` values with typed body, URL, header, and authentication helpers.

## Request constructors

`HttpClientRequest` has constructors for common HTTP methods. `get` and `head` reject body options at the type level; methods with request bodies accept `Options.NoUrl`.

```typescript
import { HttpClientRequest } from "@effect/platform"

const listUsers = HttpClientRequest.get("https://api.example.com/users")
const createUser = HttpClientRequest.post("https://api.example.com/users")
const replaceUser = HttpClientRequest.put("https://api.example.com/users/123")
const updateUser = HttpClientRequest.patch("https://api.example.com/users/123")
const deleteUser = HttpClientRequest.del("https://api.example.com/users/123")
```

Requests are immutable values. Every helper returns a new request.

## URL helpers

Use URL helpers rather than string concatenation when composing requests.

```typescript
import { HttpClientRequest } from "@effect/platform"

const request = HttpClientRequest.get("https://api.example.com/v1").pipe(
  HttpClientRequest.appendUrl("users/123"),
  HttpClientRequest.setUrlParam("include", "teams"),
  HttpClientRequest.setHash("profile")
)
```

`appendUrl` joins path segments safely around leading and trailing slashes. `prependUrl` is usually used on a client transformation to attach a base URL to relative requests.

```typescript
import { HttpClient, HttpClientRequest } from "@effect/platform"
import { Effect } from "effect"

const program = Effect.gen(function* () {
  const baseClient = yield* HttpClient.HttpClient
  const apiClient = baseClient.pipe(
    HttpClient.mapRequest(
      HttpClientRequest.prependUrl("https://api.example.com/v1")
    )
  )

  return yield* apiClient.get("/users")
})
```

## Query parameters

Use `setUrlParam` for one value, `setUrlParams` for replacing multiple values, and `appendUrlParams` when you need to add to existing parameters.

```typescript
import { HttpClientRequest } from "@effect/platform"

const request = HttpClientRequest.get("/search").pipe(
  HttpClientRequest.setUrlParam("q", "effect"),
  HttpClientRequest.appendUrlParams({
    tag: ["typescript", "runtime"],
    page: "1"
  })
)
```

For GET and HEAD endpoints modeled with `HttpApiEndpoint.setPayload`, the generated client encodes the payload as URL search parameters when the method has no body.

## Headers and auth

Headers are set on the request:

```typescript
import { HttpClientRequest } from "@effect/platform"
import { Redacted } from "effect"

const request = HttpClientRequest.get("/accounts/current").pipe(
  HttpClientRequest.acceptJson,
  HttpClientRequest.setHeader("x-client", "billing-worker"),
  HttpClientRequest.bearerToken(Redacted.make("token-value"))
)
```

Use `basicAuth` or `bearerToken` for common authorization headers. Passing redacted values protects inspection and logging paths that respect Effect redaction.

## JSON bodies

Use `schemaBodyJson` when you have a Schema. It encodes the domain value before attaching the request body and can fail with `HttpBodyError`.

```typescript
import { HttpClient, HttpClientRequest, HttpClientResponse } from "@effect/platform"
import { Effect, Schema } from "effect"

const CreateUser = Schema.Struct({
  name: Schema.String,
  email: Schema.String
})

const User = Schema.Struct({
  id: Schema.String,
  name: Schema.String,
  email: Schema.String
})

const createUser = (input: typeof CreateUser.Type) =>
  HttpClientRequest.post("/users").pipe(
    HttpClientRequest.schemaBodyJson(CreateUser)(input),
    Effect.flatMap(HttpClient.execute),
    Effect.flatMap(HttpClientResponse.schemaBodyJson(User))
  )
```

Use `bodyJson` only when the value is already the encoded JSON shape and no schema validation is needed.

```typescript
import { HttpClientRequest } from "@effect/platform"

const request = HttpClientRequest.post("/events").pipe(
  HttpClientRequest.bodyUnsafeJson({
    type: "started",
    source: "worker"
  })
)
```

`bodyUnsafeJson` is synchronous and assumes JSON encoding succeeds. Prefer `bodyJson` or `schemaBodyJson` for values that may fail to encode.

## Text, bytes, form data, and streams

Request body helpers cover common body types:

| Helper | Use for |
|---|---|
| `bodyText` | Text payloads and custom text content types |
| `bodyUint8Array` | Binary payloads |
| `bodyUrlParams` | Form URL encoded bodies |
| `bodyFormData` | Browser `FormData` |
| `bodyFormDataRecord` | Record-shaped form data |
| `bodyStream` | Streaming `Uint8Array` chunks |
| `bodyFile` | File system backed body with `FileSystem` requirement |
| `bodyFileWeb` | Web `File`-like values |

```typescript
import { HttpClientRequest } from "@effect/platform"
import { Stream } from "effect"

const uploadStream = Stream.fromIterable(["first", "second"]).pipe(
  Stream.encodeText
)

const request = HttpClientRequest.post("/upload").pipe(
  HttpClientRequest.bodyStream(uploadStream, {
    contentType: "text/plain"
  })
)
```

Streaming bodies keep the body in the Effect runtime, so logging, interruption, and scope behavior can still be coordinated by the program.

## Execute manually

Build a request manually when request construction has its own pipeline:

```typescript
import { HttpClient, HttpClientRequest, HttpClientResponse } from "@effect/platform"
import { Effect, Schema } from "effect"

const Report = Schema.Struct({
  id: Schema.String,
  status: Schema.String
})

const request = HttpClientRequest.get("/reports/latest").pipe(
  HttpClientRequest.acceptJson,
  HttpClientRequest.setHeader("x-requested-by", "scheduler")
)

const program = request.pipe(
  HttpClient.execute,
  Effect.flatMap(HttpClientResponse.schemaBodyJson(Report))
)
```

For a simple call, the verb helpers on `HttpClient` are shorter. For a reusable or schema-encoded body, explicit request construction is clearer.

## Common mistakes

- Do not manually concatenate base URLs onto every path; transform the client with `prependUrl`.
- Do not attach request bodies to GET or HEAD by bypassing typed helpers.
- Do not use unsafe JSON helpers when schema encoding can fail.
- Do not put secrets in plain strings when `Redacted` values are available.
- Do not decode response bodies while building the request. Keep request and response phases separate.

## Cross-references

See also: [01-overview.md](01-overview.md), [02-fetch-http-client.md](02-fetch-http-client.md), [04-response-decoding.md](04-response-decoding.md), [08-error-handling.md](08-error-handling.md).
