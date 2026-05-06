# FileSystem
Use `FileSystem` for typed file and directory I/O, including scoped temporary files that clean up automatically.

## Service Shape

`FileSystem.FileSystem` is the service tag. The service exposes methods for
access checks, reads, writes, streams, temp paths, file handles, metadata,
watching, and removal.

Common methods:

| Method | Use |
|---|---|
| `readFileString(path, encoding?)` | Read text |
| `writeFileString(path, data, options?)` | Write text |
| `readFile(path)` | Read bytes |
| `writeFile(path, data, options?)` | Write bytes |
| `exists(path)` | Check presence |
| `makeDirectory(path, options?)` | Create a directory |
| `readDirectory(path, options?)` | List children |
| `remove(path, options?)` | Delete file or directory |
| `makeTempFileScoped(options?)` | Create temp file tied to `Scope` |
| `makeTempDirectoryScoped(options?)` | Create temp directory tied to `Scope` |
| `stream(path, options?)` | Read bytes as `Stream` |
| `sink(path, options?)` | Write bytes through `Sink` |

## Basic File Program

```typescript
import { Effect } from "effect"
import { FileSystem, Path } from "@effect/platform"

export const writeReport = (directory: string, body: string) =>
  Effect.gen(function* () {
    const fs = yield* FileSystem.FileSystem
    const path = yield* Path.Path

    yield* fs.makeDirectory(directory, { recursive: true })

    const file = path.join(directory, "report.txt")
    yield* fs.writeFileString(file, body)

    const saved = yield* fs.readFileString(file)
    yield* Effect.logInfo(`Saved ${saved.length} characters`)

    return file
  })
```

This code needs `FileSystem.FileSystem` and `Path.Path`; the caller decides
whether to provide Node, Bun, or test layers.

## Scoped Temp File

Use scoped temp operations for scratch files. The temp file or directory is
removed when the scope closes, including failure and interruption paths.

```typescript
import { Effect } from "effect"
import { FileSystem } from "@effect/platform"
import { NodeContext, NodeRuntime } from "@effect/platform-node"

const program = Effect.scoped(
  Effect.gen(function* () {
    const fs = yield* FileSystem.FileSystem

    const file = yield* fs.makeTempFileScoped({
      prefix: "effect-platform-",
      suffix: ".txt"
    })

    yield* fs.writeFileString(file, "temporary payload")
    const payload = yield* fs.readFileString(file)
    yield* Effect.logInfo(`Temp payload length: ${payload.length}`)

    return file
  })
)

program.pipe(
  Effect.provide(NodeContext.layer),
  NodeRuntime.runMain
)
```

`Effect.scoped` opens a scope for `makeTempFileScoped`. When `program` finishes,
the scope finalizer removes the temp file. Do not manually remove the path in
the happy path unless you need earlier cleanup.

## Scoped Temp Directory

Use scoped directories when a workflow creates multiple files.

```typescript
import { Effect } from "effect"
import { FileSystem, Path } from "@effect/platform"

export const renderInScratch = (name: string, contents: string) =>
  Effect.scoped(
    Effect.gen(function* () {
      const fs = yield* FileSystem.FileSystem
      const path = yield* Path.Path

      const directory = yield* fs.makeTempDirectoryScoped({
        prefix: "render-"
      })

      const output = path.join(directory, name)
      yield* fs.writeFileString(output, contents)

      return yield* fs.readFileString(output)
    })
  )
```

The returned string is safe to use after the scope closes; the scratch path is
not.

## Exists Before Read

`exists` returns an `Effect<boolean, PlatformError>`. It can still fail if the
platform cannot access the path, so keep it in the Effect workflow.

```typescript
import { Effect, Option } from "effect"
import { FileSystem } from "@effect/platform"

export const readIfPresent = (file: string) =>
  Effect.gen(function* () {
    const fs = yield* FileSystem.FileSystem
    const exists = yield* fs.exists(file)

    if (!exists) {
      return Option.none<string>()
    }

    const text = yield* fs.readFileString(file)
    return Option.some(text)
  })
```

Use `Option.match` at the boundary that needs a default or response.

## File Handles

`open` returns a scoped file handle. The handle closes with the scope.

```typescript
import { Effect } from "effect"
import { FileSystem } from "@effect/platform"

export const overwriteBytes = (file: string, bytes: Uint8Array) =>
  Effect.scoped(
    Effect.gen(function* () {
      const fs = yield* FileSystem.FileSystem
      const handle = yield* fs.open(file, { flag: "w+" })
      yield* handle.writeAll(bytes)
      yield* handle.sync
      return yield* handle.stat
    })
  )
```

Use the high-level read and write methods until you need seek, sync, truncation,
or partial reads.

## Streams and Sinks

The service exposes `stream` and `sink` for byte-oriented pipelines.

```typescript
import { Effect, Stream } from "effect"
import { FileSystem } from "@effect/platform"

export const copyBytes = (source: string, destination: string) =>
  Effect.gen(function* () {
    const fs = yield* FileSystem.FileSystem
    yield* fs.stream(source).pipe(Stream.run(fs.sink(destination)))
  })
```

When this shape feels too dense, split lookup from streaming in `Effect.gen` and
return a stream from the generator.

## Watching

`watch(path, options?)` returns a stream of create, update, and remove events.
Node's default backend follows Node runtime behavior; the parcel watcher layer
can provide different recursive semantics.

```typescript
import { Effect, Stream } from "effect"
import { FileSystem } from "@effect/platform"

export const logFirstEvents = (directory: string) =>
  Effect.gen(function* () {
    const fs = yield* FileSystem.FileSystem
    yield* fs.watch(directory, { recursive: true }).pipe(
      Stream.take(10),
      Stream.runForEach((event) => Effect.logInfo(`${event._tag}: ${event.path}`))
    )
  })
```

## Runtime Layers

```typescript
import { Effect } from "effect"
import { FileSystem } from "@effect/platform"
import { NodeFileSystem, NodeRuntime } from "@effect/platform-node"

const program = Effect.gen(function* () {
  const fs = yield* FileSystem.FileSystem
  yield* fs.writeFileString("out.txt", "hello")
})

program.pipe(
  Effect.provide(NodeFileSystem.layer),
  NodeRuntime.runMain
)
```

`NodeContext.layer` also provides `NodeFileSystem.layer`; use it when the same
program needs path, command, terminal, or worker services.

## Anti-patterns

- Creating temp paths without a scope for scratch work.
- Reading text as bytes and decoding manually when `readFileString` is enough.
- Using shell commands for copy, remove, mkdir, or stat.
- Providing the Node layer inside reusable file helpers.
- Returning a scoped temp path and expecting it to survive outside the scope.

## Cross-references

See also: [01-overview.md](01-overview.md), [03-path.md](03-path.md), [10-stream-sink-platform.md](10-stream-sink-platform.md), [11-node-context.md](11-node-context.md), [12-node-runtime.md](12-node-runtime.md)
