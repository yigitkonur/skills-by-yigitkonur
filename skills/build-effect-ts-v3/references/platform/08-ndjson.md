# Ndjson
Use `Ndjson` for newline-delimited JSON channels, especially schema-typed stream boundaries.

## Module Shape

`Ndjson` is a pure channel module, not a service tag. It provides byte and string
variants, plus schema-aware encoders and decoders.

| Function | Direction |
|---|---|
| `pack()` | unknown values to `Uint8Array` lines |
| `packString()` | unknown values to string lines |
| `unpack(options?)` | `Uint8Array` lines to unknown values |
| `unpackString(options?)` | string lines to unknown values |
| `packSchema(schema)` | typed values to bytes |
| `packSchemaString(schema)` | typed values to strings |
| `unpackSchema(schema)` | bytes to typed values |
| `unpackSchemaString(schema)` | strings to typed values |
| `duplex(options?)` | bidirectional bytes |
| `duplexString(options?)` | bidirectional strings |

`ignoreEmptyLines` controls whether blank lines are skipped while decoding.

## Decode Typed Strings

```typescript
import { Chunk, Effect, Schema, Stream } from "effect"
import { Ndjson } from "@effect/platform"

class Event extends Schema.Class<Event>("Event")({
  id: Schema.String,
  value: Schema.Number
}) {}

const source = Stream.make(
  "{\"id\":\"a\",\"value\":1}\n",
  "{\"id\":\"b\",\"value\":2}\n"
)

export const decodeEvents = source.pipe(
  Stream.pipeThroughChannel(Ndjson.unpackSchemaString(Event)()),
  Stream.runCollect,
  Effect.map(Chunk.toReadonlyArray)
)
```

The schema decoder turns malformed lines into parse failures. The output stream
contains `Event` values, not untrusted records.

## Encode Typed Strings

```typescript
import { Schema, Stream } from "effect"
import { Ndjson } from "@effect/platform"

class AuditEvent extends Schema.Class<AuditEvent>("AuditEvent")({
  name: Schema.String,
  at: Schema.String
}) {}

export const encodeAuditEvents = Stream.make(
  new AuditEvent({ name: "created", at: new Date(0).toISOString() })
).pipe(
  Stream.pipeThroughChannel(Ndjson.packSchemaString(AuditEvent)())
)
```

Use the string variants when the surrounding stream already works in text. Use
the byte variants for sockets, files, and HTTP bodies.

## Ignore Empty Lines

```typescript
import { Schema, Stream } from "effect"
import { Ndjson } from "@effect/platform"

const NumberLine = Schema.Number

export const decodeNumbers = Stream.make("1\n\n2\n").pipe(
  Stream.pipeThroughChannel(
    Ndjson.unpackSchemaString(NumberLine)({ ignoreEmptyLines: true })
  )
)
```

Without `ignoreEmptyLines`, a blank line is parsed as JSON and fails.

## File Pipeline

```typescript
import { Effect, Schema, Stream } from "effect"
import { FileSystem, Ndjson } from "@effect/platform"

class RecordLine extends Schema.Class<RecordLine>("RecordLine")({
  key: Schema.String,
  count: Schema.Number
}) {}

export const readRecords = (file: string) =>
  Effect.gen(function* () {
    const fs = yield* FileSystem.FileSystem

    return yield* fs.stream(file).pipe(
      Stream.pipeThroughChannel(Ndjson.unpackSchema(RecordLine)()),
      Stream.runCollect
    )
  })
```

Combine `FileSystem.stream` with `Ndjson.unpackSchema` for typed file ingestion.

## Error Model

Packing failures and unpacking failures use `Ndjson.NdjsonError`. Schema
variants can also fail with `ParseError`. Keep both in the error channel and
recover at the boundary that can reject, quarantine, or report the bad record.

## Anti-patterns

- Splitting NDJSON with string operations in application code.
- Decoding to `unknown` and casting to a domain type.
- Forgetting `ignoreEmptyLines` for producers that emit blank lines.
- Collecting a large NDJSON file before decoding it.
- Using NDJSON for data that is naturally one JSON document.

## Cross-references

See also: [02-filesystem.md](02-filesystem.md), [09-worker.md](09-worker.md), [10-stream-sink-platform.md](10-stream-sink-platform.md)
