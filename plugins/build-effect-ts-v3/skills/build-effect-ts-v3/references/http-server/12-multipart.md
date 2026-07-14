# Multipart
Use `HttpApiSchema.Multipart` or `HttpApiSchema.MultipartStream` for file uploads.

## Multipart Payloads

Wrap a payload schema with `HttpApiSchema.Multipart`.

```typescript
import { HttpApiEndpoint, HttpApiSchema, Multipart } from "@effect/platform"
import { Schema } from "effect"

const uploadAvatar = HttpApiEndpoint.post("uploadAvatar", "/users/avatar")
  .setPayload(HttpApiSchema.Multipart(Schema.Struct({
    file: Multipart.SingleFileSchema
  })))
  .addSuccess(Schema.Struct({
    contentType: Schema.String,
    size: Schema.Int
  }))
```

The handler receives decoded multipart fields in `payload`.

## Handler Example

```typescript
import { FileSystem, HttpApiBuilder } from "@effect/platform"
import { Effect } from "effect"

const UsersLive = HttpApiBuilder.group(Api, "users", (handlers) =>
  Effect.gen(function*() {
    const fs = yield* FileSystem.FileSystem

    return handlers.handle("uploadAvatar", ({ payload }) =>
      Effect.gen(function*() {
        const stat = yield* fs.stat(payload.file.path).pipe(Effect.orDie)

        return {
          contentType: payload.file.contentType,
          size: Number(stat.size)
        }
      })
    )
  })
)
```

Multipart file parts are stored using the platform file system service.

## Upload Limits

Pass limits to `HttpApiSchema.Multipart`.

```typescript
import { HttpApiSchema, Multipart } from "@effect/platform"
import { Option, Schema } from "effect"

const AvatarPayload = HttpApiSchema.Multipart(
  Schema.Struct({
    file: Multipart.SingleFileSchema
  }),
  {
    maxParts: Option.some(1),
    maxFileSize: Option.some("5 MiB"),
    maxTotalSize: Option.some("6 MiB"),
    fieldMimeTypes: ["image/png", "image/jpeg"]
  }
)
```

Use limits at the schema boundary, not inside the handler.

## Multipart Streams

Use `HttpApiSchema.MultipartStream` when the handler should stream parts
instead of receiving a decoded object.

```typescript
import { HttpApiEndpoint, HttpApiSchema, Multipart } from "@effect/platform"
import { Schema } from "effect"

const uploadStream = HttpApiEndpoint.post("uploadStream", "/uploads/stream")
  .setPayload(HttpApiSchema.MultipartStream(Schema.Struct({
    file: Multipart.SingleFileSchema
  })))
  .addSuccess(Schema.Struct({
    bytes: Schema.Int
  }))
```

The handler receives `payload` as a `Stream.Stream<Multipart.Part, ...>`.

## Streaming Handler

```typescript
import { HttpApiBuilder, Multipart } from "@effect/platform"
import { Chunk, Effect, Stream } from "effect"

const UploadsLive = HttpApiBuilder.group(Api, "uploads", (handlers) =>
  handlers.handle("uploadStream", ({ payload }) =>
    Effect.gen(function*() {
      const firstFile = yield* payload.pipe(
        Stream.filter((part) => part._tag === "File"),
        Stream.mapEffect((file) =>
          file.contentEffect.pipe(
            Effect.map((content) => ({ file, content }))
          )
        ),
        Stream.runCollect,
        Effect.flatMap(Chunk.head),
        Effect.orDie
      )

      return {
        bytes: firstFile.content.length
      }
    })
  )
)
```

Use streaming for large uploads or when you need incremental processing.

## Client Shape

The derived client sends multipart payloads as `FormData`.

```typescript
const data = new FormData()
data.append("file", new Blob(["hello"], { type: "text/plain" }), "hello.txt")

const result = yield* client.users.uploadAvatar({
  payload: data
})
```

The server schema still controls the accepted fields.

## Operational Notes

Multipart handlers usually require `FileSystem.FileSystem` because uploaded
files are represented by platform file metadata. Provide platform layers through
`NodeHttpServer.layer` in real servers and `NodeHttpServer.layerTest` in tests.

## Cross-references

See also: [04-query-and-payload.md](04-query-and-payload.md), [07-handlers.md](07-handlers.md), [13-streaming-responses.md](13-streaming-responses.md), [15-serving.md](15-serving.md)
