# Stream And Sink Platform I/O
Use platform streams and sinks to connect file, command, terminal, and NDJSON workflows without leaving Effect.

## Byte Streams

`FileSystem.stream(path)` returns `Stream<Uint8Array, PlatformError>`.
`FileSystem.sink(path)` returns a `Sink` that accepts `Uint8Array` chunks.
`Command.stream(command)` returns command stdout as bytes.

These APIs let you move data without collecting it into memory.

## Read Text From a File Stream

```typescript
import { Effect, Stream } from "effect"
import { FileSystem } from "@effect/platform"

export const readTextStreamed = (file: string) =>
  Effect.gen(function* () {
    const fs = yield* FileSystem.FileSystem

    return yield* fs.stream(file).pipe(
      Stream.decodeText(),
      Stream.mkString
    )
  })
```

For small files, `readFileString` is clearer. Use streaming when size or
backpressure matters.

## Copy Stream To Sink

```typescript
import { Effect, Stream } from "effect"
import { FileSystem } from "@effect/platform"

export const copyFileStreamed = (source: string, destination: string) =>
  Effect.gen(function* () {
    const fs = yield* FileSystem.FileSystem
    yield* fs.stream(source).pipe(Stream.run(fs.sink(destination)))
  })
```

This stays inside the platform service and avoids shelling out to copy files.

## Command Output To File

```typescript
import { Effect, Stream } from "effect"
import { Command, FileSystem } from "@effect/platform"

export const writeGitStatus = (destination: string) =>
  Effect.gen(function* () {
    const fs = yield* FileSystem.FileSystem

    yield* Command.stream(Command.make("git", "status", "--short")).pipe(
      Stream.run(fs.sink(destination))
    )
  })
```

`Command.stream` needs `CommandExecutor.CommandExecutor`; `fs.sink` needs
`FileSystem.FileSystem`. `NodeContext.layer` provides both.

## Text Lines To Terminal

```typescript
import { Effect, Stream } from "effect"
import { Command, Terminal } from "@effect/platform"

export const printTrackedFiles = Command.streamLines(
  Command.make("git", "ls-files")
).pipe(
  Stream.runForEach((line) =>
    Effect.gen(function* () {
      const terminal = yield* Terminal.Terminal
      yield* terminal.display(`${line}\n`)
    })
  )
)
```

Use `Terminal.display` for intentional CLI output and `Effect.logInfo` for
diagnostics.

## NDJSON File Pipeline

```typescript
import { Effect, Schema, Stream } from "effect"
import { FileSystem, Ndjson } from "@effect/platform"

class Metric extends Schema.Class<Metric>("Metric")({
  name: Schema.String,
  value: Schema.Number
}) {}

export const writeMetrics = (file: string, metrics: ReadonlyArray<Metric>) =>
  Effect.gen(function* () {
    const fs = yield* FileSystem.FileSystem

    yield* Stream.fromIterable(metrics).pipe(
      Stream.pipeThroughChannel(Ndjson.packSchema(Metric)()),
      Stream.run(fs.sink(file))
    )
  })
```

The schema encoder validates outgoing values and writes newline-delimited JSON
bytes to the file sink.

## Backpressure Rule

Prefer stream-to-sink pipelines for:

- command output that can be large;
- file copies and transforms;
- NDJSON imports and exports;
- long-running process logs;
- data that should not be fully resident in memory.

For small bounded values, direct methods are easier to read.

## Anti-patterns

- Collecting large command output with `Command.string`.
- Reading a large file fully before transforming it line by line.
- Leaving the Effect stream model to manually manage host streams.
- Using terminal display as a byte sink.
- Encoding typed NDJSON without schema validation.

## Cross-references

See also: [02-filesystem.md](02-filesystem.md), [05-command.md](05-command.md), [06-terminal.md](06-terminal.md), [08-ndjson.md](08-ndjson.md)
