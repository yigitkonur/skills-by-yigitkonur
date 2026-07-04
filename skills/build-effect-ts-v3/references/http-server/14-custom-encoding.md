# Custom Encoding
Use `HttpApiSchema.withEncoding` to describe non-JSON request and response bodies.

## Encoding Kinds

`HttpApiSchema.withEncoding` supports these wire kinds:

| Kind | Encoded shape |
|---|---|
| `"Json"` | JSON body |
| `"UrlParams"` | URL-encoded form record |
| `"Text"` | string body |
| `"Uint8Array"` | binary body |

JSON is the default. Add custom encoding only when the wire contract requires
another format.

## URL-Encoded Forms

```typescript
import { HttpApiEndpoint, HttpApiSchema } from "@effect/platform"
import { Schema } from "effect"

const submitForm = HttpApiEndpoint.post("submitForm", "/form")
  .setPayload(
    Schema.Struct({
      name: Schema.String,
      email: Schema.String
    }).pipe(HttpApiSchema.withEncoding({
      kind: "UrlParams"
    }))
  )
  .addSuccess(Schema.String)
```

The encoded schema must be compatible with string records.

## Text Responses

```typescript
import { HttpApiEndpoint, HttpApiSchema } from "@effect/platform"
import { Schema } from "effect"

const exportCsv = HttpApiEndpoint.get("exportCsv", "/users.csv")
  .addSuccess(
    Schema.String.pipe(
      HttpApiSchema.withEncoding({
        kind: "Text",
        contentType: "text/csv"
      })
    )
  )
```

The handler returns a string:

```typescript
handlers.handle("exportCsv", () =>
  Effect.succeed("id,name\n1,Ada\n")
)
```

The server encodes the response using the schema encoding metadata.

## Binary Responses

```typescript
import { HttpApiEndpoint, HttpApiSchema } from "@effect/platform"
import { Schema } from "effect"

const download = HttpApiEndpoint.get("download", "/download")
  .addSuccess(
    Schema.Uint8ArrayFromSelf.pipe(
      HttpApiSchema.withEncoding({
        kind: "Uint8Array",
        contentType: "application/octet-stream"
      })
    )
  )
```

Use binary encoding for small binary payloads. For large files, return
`HttpServerResponse.stream` or `HttpServerResponse.file`.

## Text Error Responses

Custom encoding also works for errors.

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
  {
    kind: "Text",
    contentType: "text/plain"
  }
).annotations(HttpApiSchema.annotations({ status: 429 }))

const limited = HttpApiEndpoint.get("limited", "/limited")
  .addError(RateLimitText)
```

This is useful when an upstream protocol requires plain text errors.

## Empty Responses

Use `HttpApiSchema.NoContent`, `Created`, `Accepted`, or `Empty(status)` for
empty bodies.

```typescript
import { HttpApiEndpoint, HttpApiSchema } from "@effect/platform"

const accepted = HttpApiEndpoint.post("startJob", "/jobs")
  .addSuccess(HttpApiSchema.Accepted)
```

Empty response schemas avoid fake JSON payloads like `{ ok: true }` when the
wire contract is actually status-only.

## Prefer Schema Encoding First

Reach for `HttpApiSchema.withEncoding` before returning a manual
`HttpServerResponse`. Schema encoding keeps Swagger and derived clients aligned.
Use manual responses when streaming, setting cookies, or integrating with a
protocol that cannot be described cleanly as a schema.

## Cross-references

See also: [04-query-and-payload.md](04-query-and-payload.md), [08-error-responses.md](08-error-responses.md), [13-streaming-responses.md](13-streaming-responses.md), [02-defining-endpoints.md](02-defining-endpoints.md)
