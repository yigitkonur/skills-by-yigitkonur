# Streaming Responses
Return `HttpServerResponse.stream` from handlers when the response should be sent incrementally.

## When To Stream

Use streaming responses for:

- large exports
- server-generated logs
- newline-delimited JSON
- long-running report output
- proxy-like endpoints

Most ordinary JSON endpoints should use `addSuccess` with a schema and return
the typed success value.

## Basic Stream Response

```typescript
import { HttpServerResponse } from "@effect/platform"
import { Chunk, Effect, Stream } from "effect"

const encoder = new TextEncoder()

const response = HttpServerResponse.stream(
  Stream.fromIterable([
    encoder.encode("first\n"),
    encoder.encode("second\n")
  ]),
  {
    headers: {
      "content-type": "text/plain"
    }
  }
)
```

The stream body must emit `Uint8Array` chunks.

## Handler Example

```typescript
import { HttpApiBuilder, HttpServerResponse } from "@effect/platform"
import { Stream } from "effect"

const encoder = new TextEncoder()

const ReportsLive = HttpApiBuilder.group(Api, "reports", (handlers) =>
  handlers.handle("download", () =>
    HttpServerResponse.stream(
      Stream.fromIterable([
        encoder.encode("id,total\n"),
        encoder.encode("1,100\n")
      ]),
      {
        headers: {
          "content-type": "text/csv"
        }
      }
    )
  )
)
```

The endpoint can still declare a success schema for documentation, but returning
`HttpServerResponse` gives the handler control over the wire body.

## NDJSON

Newline-delimited JSON is a common streaming format.

```typescript
import { HttpServerResponse } from "@effect/platform"
import { Stream } from "effect"

const encoder = new TextEncoder()

const ndjson = Stream.fromIterable([
  { type: "started", id: 1 },
  { type: "completed", id: 1 }
]).pipe(
  Stream.map((event) =>
    encoder.encode(`${JSON.stringify(event)}\n`)
  )
)

const response = HttpServerResponse.stream(ndjson, {
  headers: {
    "content-type": "application/x-ndjson"
  }
})
```

Use NDJSON when the client can process each line independently.

## Backpressure And Interruption

Effect streams preserve backpressure. If the client disconnects or the server
scope is interrupted during shutdown, the stream can be interrupted.

Keep stream resource acquisition scoped:

```typescript
import { Effect, Stream } from "effect"

const rows = Stream.acquireRelease(
  Effect.succeed({ close: () => Effect.void }),
  (resource) => resource.close()
).pipe(
  Stream.flatMap(() => Stream.fromIterable(["row-1\n", "row-2\n"]))
)
```

Use scoped streams for files, database cursors, and external subscriptions.

## Documenting Streaming Endpoints

For public APIs, document the media type in the response schema with custom
encoding when possible. If the response is truly manual, add OpenAPI
annotations so Swagger tells consumers what to expect.

```typescript
import { HttpApiEndpoint, HttpApiSchema } from "@effect/platform"
import { Schema } from "effect"

const exportUsers = HttpApiEndpoint.get("exportUsers", "/users/export")
  .addSuccess(
    Schema.String.pipe(
      HttpApiSchema.withEncoding({
        kind: "Text",
        contentType: "text/csv"
      })
    )
  )
```

For very large exports, return `HttpServerResponse.stream` in the handler even
if the documented type is text.

## Cross-references

See also: [07-handlers.md](07-handlers.md), [12-multipart.md](12-multipart.md), [14-custom-encoding.md](14-custom-encoding.md), [17-shutdown-and-signals.md](17-shutdown-and-signals.md)
