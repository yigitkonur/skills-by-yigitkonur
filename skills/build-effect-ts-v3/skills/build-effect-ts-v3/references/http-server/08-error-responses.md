# Error Responses
Declare expected HTTP failures with `addError`, predefined `HttpApiError` classes, and status annotations.

## Built-In Errors

`HttpApiError` provides common empty errors.

| Error | Status |
|---|---|
| `HttpApiError.BadRequest` | `400` |
| `HttpApiError.Unauthorized` | `401` |
| `HttpApiError.Forbidden` | `403` |
| `HttpApiError.NotFound` | `404` |
| `HttpApiError.MethodNotAllowed` | `405` |
| `HttpApiError.NotAcceptable` | `406` |
| `HttpApiError.RequestTimeout` | `408` |
| `HttpApiError.Conflict` | `409` |
| `HttpApiError.Gone` | `410` |
| `HttpApiError.InternalServerError` | `500` |
| `HttpApiError.NotImplemented` | `501` |
| `HttpApiError.ServiceUnavailable` | `503` |

```typescript
import { HttpApiEndpoint, HttpApiError } from "@effect/platform"
import { Schema } from "effect"

const getUser = HttpApiEndpoint.get("getUser", "/users/current")
  .addSuccess(Schema.String)
  .addError(HttpApiError.Unauthorized)
  .addError(HttpApiError.NotFound)
```

The built-in errors are useful when no response body is needed.

## Custom Errors

Use `Schema.TaggedError` for custom error bodies.

```typescript
import { HttpApiEndpoint, HttpApiSchema } from "@effect/platform"
import { Schema } from "effect"

class UserNotFound extends Schema.TaggedError<UserNotFound>()(
  "UserNotFound",
  {
    id: Schema.Int
  },
  HttpApiSchema.annotations({ status: 404 })
) {}

const getUser = HttpApiEndpoint.get("getUser", "/users/current")
  .addSuccess(Schema.String)
  .addError(UserNotFound)
```

The annotation puts the HTTP status on the error schema.

## Status Mapping

You can pass status annotations to `addError`.

```typescript
import { HttpApiEndpoint } from "@effect/platform"
import { Schema } from "effect"

class RateLimited extends Schema.TaggedError<RateLimited>()(
  "RateLimited",
  {
    retryAfterSeconds: Schema.Int
  }
) {}

const endpoint = HttpApiEndpoint.get("current", "/current")
  .addSuccess(Schema.String)
  .addError(RateLimited, { status: 429 })
```

If no status is supplied, error responses default to `500`.

## Group And API Errors

Use group-level errors for failures shared by all endpoints in one group.

```typescript
import { HttpApi, HttpApiError, HttpApiGroup } from "@effect/platform"

const users = HttpApiGroup.make("users")
  .add(getUser)
  .addError(HttpApiError.Unauthorized)

class Api extends HttpApi.make("api")
  .add(users)
  .addError(HttpApiError.ServiceUnavailable)
{}
```

Endpoint errors are most specific, group errors apply to the group, and API
errors apply globally.

## Decode Errors

`HttpApi` includes `HttpApiDecodeError` by default. It is produced when path,
query, headers, or payload decoding fails.

```typescript
import { HttpApiEndpoint } from "@effect/platform"
import { Schema } from "effect"

const page = HttpApiEndpoint.get("page", "/page")
  .setUrlParams(Schema.Struct({
    page: Schema.NumberFromString
  }))
  .addSuccess(Schema.String)
```

`/page?page=abc` returns a `400` decode error before the handler runs.

## Handler Failures

Fail with declared errors.

```typescript
import { Effect } from "effect"

const UsersLive = HttpApiBuilder.group(Api, "users", (handlers) =>
  handlers.handle("getUser", ({ path }) =>
    path.id === 0
      ? Effect.fail(new UserNotFound({ id: path.id }))
      : Effect.succeed(new User({ id: path.id, name: "Ada" }))
  )
)
```

Do not throw ordinary exceptions for expected HTTP responses. Throwing defects
are not part of the typed error contract.

## Empty Custom Errors

For custom empty responses, use `HttpApiSchema.EmptyError` or
`HttpApiSchema.asEmpty`.

```typescript
import { HttpApiSchema } from "@effect/platform"

class Archived extends HttpApiSchema.EmptyError<Archived>()({
  tag: "Archived",
  status: 410
}) {}
```

This produces a typed error with an empty HTTP body.

## Text Error Encoding

Errors can use non-JSON encodings.

```typescript
import { HttpApiEndpoint, HttpApiSchema } from "@effect/platform"
import { Schema } from "effect"

class RateLimitError extends Schema.TaggedError<RateLimitError>()(
  "RateLimitError",
  { message: Schema.String }
) {}

const RateLimitText = HttpApiSchema.withEncoding(
  Schema.transform(Schema.String, RateLimitError, {
    decode: (message) => RateLimitError.make({ message }),
    encode: ({ message }) => message,
    strict: true
  }),
  { kind: "Text", contentType: "text/plain" }
).annotations(HttpApiSchema.annotations({ status: 429 }))

const endpoint = HttpApiEndpoint.get("limited", "/limited")
  .addError(RateLimitText)
```

Use this only when the wire contract requires it.

## Cross-references

See also: [02-defining-endpoints.md](02-defining-endpoints.md), [07-handlers.md](07-handlers.md), [09-middleware.md](09-middleware.md), [14-custom-encoding.md](14-custom-encoding.md)
