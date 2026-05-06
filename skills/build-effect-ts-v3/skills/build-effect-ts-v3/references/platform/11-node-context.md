# NodeContext
Use `NodeContext.layer` as the standard Node platform layer bundle for CLIs and servers.

## What It Provides

`NodeContext.layer` provides this union:

| Service | Provider inside bundle |
|---|---|
| `CommandExecutor.CommandExecutor` | `NodeCommandExecutor.layer` |
| `FileSystem.FileSystem` | `NodeFileSystem.layer` |
| `Path.Path` | `NodePath.layer` |
| `Terminal.Terminal` | `NodeTerminal.layer` |
| `Worker.WorkerManager` | `NodeWorker.layerManager` |

The source builds the bundle with `Layer.mergeAll(...)` and then
`Layer.provideMerge(NodeFileSystem.layer)`, because the Node command executor
depends on file-system support.

## Standard Entry Composition

```typescript
import { Effect } from "effect"
import { Command, FileSystem, Path, Terminal } from "@effect/platform"
import { NodeContext, NodeRuntime } from "@effect/platform-node"

const program = Effect.gen(function* () {
  const fs = yield* FileSystem.FileSystem
  const path = yield* Path.Path
  const terminal = yield* Terminal.Terminal

  const file = path.join(".", "package.json")
  const exists = yield* fs.exists(file)
  const version = yield* Command.string(Command.make("node", "--version"))

  yield* terminal.display(`package present: ${exists}\n`)
  yield* Effect.logInfo(`runtime: ${version.trim()}`)
})

program.pipe(
  Effect.provide(NodeContext.layer),
  NodeRuntime.runMain
)
```

This is the preferred shape for most Node CLI entry points.

## Library Boundary

Do not require `NodeContext.NodeContext` from reusable modules unless the module
is explicitly Node-only. Prefer precise service requirements.

```typescript
import { Effect } from "effect"
import { FileSystem } from "@effect/platform"

export const readPackage = Effect.gen(function* () {
  const fs = yield* FileSystem.FileSystem
  const path = yield* Path.Path

  return yield* fs.readFileString(path.join(".", "package.json"))
})
```

The entry point can still provide `NodeContext.layer`; the helper does not need
to know that.

## Narrow Layers

Use individual layers when a program truly needs only one service.

```typescript
import { Effect } from "effect"
import { FileSystem } from "@effect/platform"
import { NodeFileSystem, NodeRuntime } from "@effect/platform-node"

const program = Effect.gen(function* () {
  const fs = yield* FileSystem.FileSystem
  return yield* fs.readDirectory(".")
})

program.pipe(
  Effect.provide(NodeFileSystem.layer),
  Effect.flatMap((files) => Effect.logInfo(`files: ${files.length}`)),
  NodeRuntime.runMain
)
```

Narrow layers are useful in tests and scripts where the dependency set matters.

## Command Executor Alone

`NodeCommandExecutor.layer` depends on `FileSystem.FileSystem`, so either use
`NodeContext.layer` or provide the file-system layer.

```typescript
import { Effect, Layer } from "effect"
import { Command } from "@effect/platform"
import {
  NodeCommandExecutor,
  NodeFileSystem,
  NodeRuntime
} from "@effect/platform-node"

const CommandLive = NodeCommandExecutor.layer.pipe(
  Layer.provide(NodeFileSystem.layer)
)

Command.string(Command.make("node", "--version")).pipe(
  Effect.provide(CommandLive),
  Effect.flatMap((version) => Effect.logInfo(version.trim())),
  NodeRuntime.runMain
)
```

If the program also needs path, terminal, or workers, `NodeContext.layer` is
clearer.

## Replacing One Service

Compose a custom layer when tests need real Node services plus one override.

```typescript
import { Effect, Layer } from "effect"
import { FileSystem, Path } from "@effect/platform"
import { NodePath } from "@effect/platform-node"

const TestFileSystem = FileSystem.layerNoop({
  exists: (path) => Effect.succeed(path === "config.json"),
  readFileString: (path) =>
    Effect.succeed(path === "config.json" ? "{\"ok\":true}" : "")
})

export const TestLive = Layer.merge(
  TestFileSystem,
  NodePath.layerPosix
)
```

In real tests, implement only the methods the subject calls and keep the fake
small. For broad integration tests, prefer the real Node layer.

## Node-only Code

It is valid for entry points, adapters, and runtime integrations to import from
`@effect/platform-node`. Keep that dependency out of domain services unless
there is no portable abstraction for the capability.

## Anti-patterns

- Importing Node platform packages from shared domain modules.
- Providing `NodeContext.layer` repeatedly inside helper functions.
- Using `NodeCommandExecutor.layer` without satisfying its file-system need.
- Treating `NodeContext.layer` as a substitute for application service layers.
- Replacing every service in tests when one small fake is enough.

## Cross-references

See also: [01-overview.md](01-overview.md), [02-filesystem.md](02-filesystem.md), [05-command.md](05-command.md), [12-node-runtime.md](12-node-runtime.md), [13-bun-platform.md](13-bun-platform.md)
