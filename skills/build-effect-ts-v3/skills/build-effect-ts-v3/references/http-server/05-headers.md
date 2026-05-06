# Headers
Use `setHeaders` for typed request headers and keep every header key lowercase.

## Lowercase Keys Are Mandatory

Header keys in `setHeaders` must be lowercase.

```typescript
import { HttpApiEndpoint } from "@effect/platform"
import { Schema } from "effect"

const endpoint = HttpApiEndpoint.get("withHeaders", "/secure")
  .setHeaders(Schema.Struct({
    "authorization": Schema.String,
    "x-request-id": Schema.String
  }))
```

Do not write `"Authorization"` or `"X-Request-Id"` in the schema. The server
request header map is normalized to lowercase keys, and the schema is decoded
against those keys.

## Basic Header Schema

Headers decode before the handler runs.

```typescript
import { HttpApiEndpoint } from "@effect/platform"
import { Schema } from "effect"

const listUsers = HttpApiEndpoint.get("listUsers", "/users")
  .setHeaders(Schema.Struct({
    "x-page": Schema.NumberFromString.pipe(
      Schema.optionalWith({ default: () => 1 })
    )
  }))
```

The handler receives `headers` with decoded values:

```typescript
handlers.handle("listUsers", ({ headers }) =>
  Effect.succeed({ page: headers["x-page"] })
)
```

## Optional Headers

Optional headers should be explicit in the schema.

```typescript
import { HttpApiEndpoint } from "@effect/platform"
import { Schema } from "effect"

const readReport = HttpApiEndpoint.get("readReport", "/reports/current")
  .setHeaders(Schema.Struct({
    "if-none-match": Schema.optional(Schema.String),
    "x-request-id": Schema.String
  }))
```

The handler can branch on the optional field without reading raw headers.

## Header-Based Authentication

For authentication, prefer `HttpApiSecurity` plus middleware when the header is
a security scheme. Use `setHeaders` for ordinary request metadata.

```typescript
import { HttpApiEndpoint } from "@effect/platform"
import { Schema } from "effect"

const audit = HttpApiEndpoint.post("audit", "/audit")
  .setHeaders(Schema.Struct({
    "x-request-id": Schema.String,
    "x-tenant-id": Schema.String
  }))
```

Security middleware gives better OpenAPI output and reusable server behavior.

## Bad Pattern

```typescript
import { HttpApiEndpoint } from "@effect/platform"
import { Schema } from "effect"

const bad = HttpApiEndpoint.get("bad", "/bad")
  .setHeaders(Schema.Struct({
    "X-Request-Id": Schema.String
  }))
```

That schema is wrong because the key is not lowercase. Use
`"x-request-id"`.

## Raw Request Escape Hatch

The raw request is always present in handlers, but do not use it for headers
already described in the contract.

```typescript
handlers.handle("withHeaders", ({ headers, request }) =>
  Effect.succeed({
    requestId: headers["x-request-id"],
    method: request.method
  })
)
```

This keeps validated data in typed fields and leaves raw access for actual edge
cases.

## Response Headers

`setHeaders` describes request headers. Response headers are set by returning a
typed success value with encoding metadata, or by returning `HttpServerResponse`
when manual control is necessary.

```typescript
import { HttpServerResponse } from "@effect/platform"
import { Effect } from "effect"

handlers.handle("download", () =>
  Effect.succeed(
    HttpServerResponse.text("id,name\n1,Ada\n", {
      headers: {
        "content-type": "text/csv",
        "cache-control": "no-store"
      }
    })
  )
)
```

Use lowercase response header keys too. It keeps examples consistent with the
request side and avoids duplicate-case headers in downstream tooling.

## Cross-references

See also: [02-defining-endpoints.md](02-defining-endpoints.md), [09-middleware.md](09-middleware.md), [10-cors-and-logger.md](10-cors-and-logger.md), [07-handlers.md](07-handlers.md)
