# Platform Overview
Use platform services when Effect code needs runtime I/O without hard-coding Node, Bun, or browser APIs.

## Mental Model

`@effect/platform` defines interfaces and tags. Runtime packages provide layers.

| Need | Platform module | Service tag | Node layer | Bun layer |
|---|---|---|---|---|
| File I/O | `FileSystem` | `FileSystem.FileSystem` | `NodeFileSystem.layer` | `BunFileSystem.layer` |
| Path logic | `Path` | `Path.Path` | `NodePath.layer` | `BunPath.layer` |
| Child processes | `CommandExecutor` via `Command` | `CommandExecutor.CommandExecutor` | `NodeCommandExecutor.layer` | `BunCommandExecutor.layer` |
| Terminal I/O | `Terminal` | `Terminal.Terminal` | `NodeTerminal.layer` | `BunTerminal.layer` |
| Workers | `Worker` | `Worker.WorkerManager` | `NodeWorker.layerManager` | `BunWorker.layerManager` |

The portable package owns the program shape. The runtime package owns the
implementation. That split is the main reason to use platform services instead
of importing `node:fs`, `node:path`, or `node:child_process` directly inside
business code.

## Standard Node Edge

```typescript
import { Effect } from "effect"
import { FileSystem } from "@effect/platform"
import { NodeContext, NodeRuntime } from "@effect/platform-node"

const program = Effect.gen(function* () {
  const fs = yield* FileSystem.FileSystem
  const text = yield* fs.readFileString("README.md")
  yield* Effect.logInfo(`Read ${text.length} characters`)
})

program.pipe(
  Effect.provide(NodeContext.layer),
  NodeRuntime.runMain
)
```

`NodeContext.layer` is the common CLI/server layer because it bundles the Node
implementations for file system, path, command execution, terminal, and worker
manager. Use narrower layers only when you deliberately want a smaller
environment or a test double.

## Runtime Boundary Rule

Keep `@effect/platform-node` and `@effect/platform-bun` near entry points,
composition roots, or tests. Library modules should depend on tags from
`@effect/platform`.

```typescript
import { Effect } from "effect"
import { FileSystem, Path } from "@effect/platform"

export const loadConfig = (directory: string) =>
  Effect.gen(function* () {
    const fs = yield* FileSystem.FileSystem
    const path = yield* Path.Path
    const file = path.join(directory, "config.json")
    return yield* fs.readFileString(file)
  })
```

This function is portable. It runs on Node with `NodeContext.layer`, on Bun with
`BunContext.layer`, and in tests with a custom layer.

## Service Lookup Pattern

Platform services are Effect services. Lookup the tag inside `Effect.gen`, then
call methods on the service value.

```typescript
import { Effect } from "effect"
import { FileSystem, Path, Terminal } from "@effect/platform"

const inspectWorkspace = Effect.gen(function* () {
  const fs = yield* FileSystem.FileSystem
  const path = yield* Path.Path
  const terminal = yield* Terminal.Terminal

  const root = path.resolve(".")
  const entries = yield* fs.readDirectory(root)
  yield* terminal.display(`Workspace has ${entries.length} entries\n`)
})
```

Avoid reaching for the host runtime from the middle of this code. If a platform
operation is missing, model that requirement as a service and provide it at the
edge.

## Layer Selection

Use `NodeContext.layer` for most Node programs. Use individual layers when:

- a library test wants only `NodeFileSystem.layer`;
- a command executor needs the real file system but not terminal input;
- path behavior must be pinned to POSIX or Win32 with `NodePath.layerPosix` or
  `NodePath.layerWin32`;
- a runtime edge is Bun and should use `BunContext.layer`.

```typescript
import { Effect } from "effect"
import { FileSystem } from "@effect/platform"
import { NodeFileSystem, NodeRuntime } from "@effect/platform-node"

const program = Effect.gen(function* () {
  const fs = yield* FileSystem.FileSystem
  const exists = yield* fs.exists("package.json")
  yield* Effect.logInfo(`package.json exists: ${exists}`)
})

program.pipe(
  Effect.provide(NodeFileSystem.layer),
  NodeRuntime.runMain
)
```

## Error Model

Platform I/O failures are typed as platform errors, not thrown exceptions. Keep
them in the Effect error channel and recover at the boundary that can make a
domain decision.

```typescript
import { Effect } from "effect"
import { FileSystem } from "@effect/platform"

const readOptional = (file: string) =>
  Effect.gen(function* () {
    const fs = yield* FileSystem.FileSystem
    const exists = yield* fs.exists(file)
    if (!exists) {
      return "missing"
    }
    return yield* fs.readFileString(file)
  })
```

## Anti-patterns

- Importing host APIs in reusable Effect services.
- Calling runner APIs from library code instead of the entry point.
- Providing a platform layer inside every helper instead of once at the edge.
- Using `Command` where a `FileSystem` method already exists.
- Depending on `NodeContext.layer` in code that should run on Bun.

## Cross-references

See also: [02-filesystem.md](02-filesystem.md), [03-path.md](03-path.md), [05-command.md](05-command.md), [11-node-context.md](11-node-context.md), [12-node-runtime.md](12-node-runtime.md)
