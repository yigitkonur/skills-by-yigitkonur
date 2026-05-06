# Bun Platform
Use Bun platform layers when the application edge runs on Bun instead of Node.

## Runtime Package

`@effect/platform-bun` mirrors the same portable service model as the Node
package.

| Need | Bun module |
|---|---|
| Context bundle | `BunContext.layer` |
| Runtime entry | `BunRuntime.runMain` |
| File system | `BunFileSystem.layer` |
| Path | `BunPath.layer` |
| Command executor | `BunCommandExecutor.layer` |
| Terminal | `BunTerminal.layer` |
| Workers | `BunWorker.layerManager` |
| HTTP server | `BunHttpServer.layer` |

`BunContext.layer` bundles command executor, file system, path, terminal, and
worker manager.

## Basic Bun Entry

```typescript
import { Effect } from "effect"
import { FileSystem, Path } from "@effect/platform"
import { BunContext, BunRuntime } from "@effect/platform-bun"

const program = Effect.gen(function* () {
  const fs = yield* FileSystem.FileSystem
  const path = yield* Path.Path

  const file = path.join(".", "package.json")
  const exists = yield* fs.exists(file)

  yield* Effect.logInfo(`package present: ${exists}`)
})

program.pipe(
  Effect.provide(BunContext.layer),
  BunRuntime.runMain
)
```

The application code still imports portable services from `@effect/platform`.
Only the edge imports Bun layers.

## Bun Context

The Bun context type is the same service union as the Node context:

- `CommandExecutor.CommandExecutor`;
- `FileSystem.FileSystem`;
- `Path.Path`;
- `Terminal.Terminal`;
- `Worker.WorkerManager`.

That parity is what lets portable modules move between Node and Bun by changing
the provided layer.

## Bun HTTP Server

`BunHttpServer.layer(options)` provides an HTTP server plus the Bun context and
HTTP platform dependencies.

```typescript
import { Layer } from "effect"
import { HttpRouter, HttpServerResponse } from "@effect/platform"
import { BunHttpServer, BunRuntime } from "@effect/platform-bun"

const RouterLive = HttpRouter.empty.pipe(
  HttpRouter.get("/health", HttpServerResponse.text("ok"))
)

const ServerLive = RouterLive.pipe(
  Layer.provide(BunHttpServer.layer({ port: 3000 }))
)

Layer.launch(ServerLive).pipe(
  BunRuntime.runMain
)
```

Use `BunHttpServer.layerConfig` when options should come from `Config`.

## File-system KeyValueStore

```typescript
import { Effect } from "effect"
import { KeyValueStore } from "@effect/platform"
import { BunKeyValueStore, BunRuntime } from "@effect/platform-bun"

const program = Effect.gen(function* () {
  const store = yield* KeyValueStore.KeyValueStore
  yield* store.set("runtime", "bun")
})

program.pipe(
  Effect.provide(BunKeyValueStore.layerFileSystem(".data")),
  BunRuntime.runMain
)
```

The Bun key-value file-system layer follows the same API as the Node helper.

## When To Choose Bun Layers

Use Bun layers when the process is executed by Bun or when Bun-specific HTTP
server behavior is required. Keep platform-independent services portable so the
runtime decision remains isolated to the entry point.

## Anti-patterns

- Importing Bun platform modules from shared business logic.
- Providing Node and Bun context layers to the same service graph.
- Assuming Bun HTTP server options apply to Node HTTP server layers.
- Using runtime-specific layers in package code that should be testable with
  memory or no-op layers.

## Cross-references

See also: [01-overview.md](01-overview.md), [07-keyvaluestore.md](07-keyvaluestore.md), [09-worker.md](09-worker.md), [11-node-context.md](11-node-context.md)
