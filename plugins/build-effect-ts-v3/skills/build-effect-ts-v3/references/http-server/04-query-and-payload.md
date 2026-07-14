# Query And Payload
Declare URL search parameters with `setUrlParams` and request bodies with `setPayload`.

## Query Parameters

Use `setUrlParams` for search parameters.

```typescript
import { HttpApiEndpoint } from "@effect/platform"
import { Schema } from "effect"

const listUsers = HttpApiEndpoint.get("listUsers", "/users")
  .setUrlParams(Schema.Struct({
    query: Schema.optional(Schema.String),
    page: Schema.NumberFromString.pipe(
      Schema.optionalWith({ default: () => 1 })
    )
  }))
```

The handler receives a decoded `urlParams` field:

```typescript
handlers.handle("listUsers", ({ urlParams }) =>
  Effect.succeed({
    page: urlParams.page,
    query: urlParams.query
  })
)
```

Search params arrive as strings or repeated strings, so use string-decodable
schemas such as `Schema.NumberFromString`.

## Payloads

Use `setPayload` for request bodies.

```typescript
import { HttpApiEndpoint } from "@effect/platform"
import { Schema } from "effect"

class CreateUser extends Schema.Class<CreateUser>("CreateUser")({
  name: Schema.String,
  email: Schema.String
}) {}

const createUser = HttpApiEndpoint.post("createUser", "/users")
  .setPayload(CreateUser)
```

The handler receives:

```typescript
{
  readonly payload: CreateUser
}
```

## Body Method Choice

Use body-capable methods for JSON payloads:

| Method | JSON body fit |
|---|---|
| `POST` | create or command |
| `PUT` | full replacement |
| `PATCH` | partial update |
| `DELETE` | only when the API intentionally accepts a body |
| `GET` | avoid JSON body; use `setUrlParams` |

Effect validates `GET` payload schemas against URL-parameter encodability. That
is useful for form-style payloads, but application APIs are clearer with
`setUrlParams`.

## Query Plus Payload

An endpoint can use both query parameters and a body.

```typescript
import { HttpApiEndpoint } from "@effect/platform"
import { Schema } from "effect"

class ImportUsers extends Schema.Class<ImportUsers>("ImportUsers")({
  users: Schema.Array(Schema.Struct({
    name: Schema.String,
    email: Schema.String
  }))
}) {}

const importUsers = HttpApiEndpoint.post("importUsers", "/users/import")
  .setUrlParams(Schema.Struct({
    dryRun: Schema.BooleanFromString.pipe(
      Schema.optionalWith({ default: () => false })
    )
  }))
  .setPayload(ImportUsers)
```

Handler:

```typescript
handlers.handle("importUsers", ({ urlParams, payload }) =>
  urlParams.dryRun
    ? Effect.succeed({ imported: 0 })
    : Effect.succeed({ imported: payload.users.length })
)
```

## Repeated Query Values

Search parameters can have repeated values. Model them with arrays that encode
from string arrays.

```typescript
import { HttpApiEndpoint } from "@effect/platform"
import { Schema } from "effect"

const search = HttpApiEndpoint.get("search", "/search")
  .setUrlParams(Schema.Struct({
    tag: Schema.Array(Schema.String),
    page: Schema.NumberFromString
  }))
```

The server normalizes a single supplied value into an array when the schema
expects an array.

## Decode Failures

If query or payload decoding fails, the handler is not called. The server
returns an `HttpApiDecodeError` response with status `400`.

```typescript
import { HttpApiEndpoint } from "@effect/platform"
import { Schema } from "effect"

const page = HttpApiEndpoint.get("page", "/page")
  .setUrlParams(Schema.Struct({
    page: Schema.NumberFromString
  }))
```

`GET /page?page=abc` fails during decode instead of passing `"abc"` to the
handler.

## Payload Encoding

JSON is the default request-body encoding. Override it with
`HttpApiSchema.withEncoding` for URL-encoded forms, text, or binary data.

```typescript
import { HttpApiEndpoint, HttpApiSchema } from "@effect/platform"
import { Schema } from "effect"

const submitForm = HttpApiEndpoint.post("submitForm", "/forms")
  .setPayload(
    Schema.Struct({
      name: Schema.String
    }).pipe(HttpApiSchema.withEncoding({ kind: "UrlParams" }))
  )
```

Use custom encoding when the wire format is part of the public API.

## Handler Boundary

Handlers should treat `urlParams` and `payload` as already-decoded values. If a
handler is still parsing strings from the raw request, move that logic back into
the endpoint schema.

## Cross-references

See also: [02-defining-endpoints.md](02-defining-endpoints.md), [03-path-params.md](03-path-params.md), [12-multipart.md](12-multipart.md), [14-custom-encoding.md](14-custom-encoding.md)
