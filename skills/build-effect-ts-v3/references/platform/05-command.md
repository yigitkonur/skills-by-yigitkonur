# Command
Use `Command` for typed child-process execution, streaming output, and shell-free process composition.

## Two Modules

`Command` is the process description DSL. `CommandExecutor.CommandExecutor` is
the service that runs descriptions.

| Module | Role |
|---|---|
| `Command.make(name, ...args)` | Build a command value |
| `Command.string(command)` | Run and collect stdout as text |
| `Command.lines(command)` | Run and collect stdout lines |
| `Command.stream(command)` | Run and stream stdout bytes |
| `Command.streamLines(command)` | Run and stream stdout lines |
| `Command.exitCode(command)` | Run and return exit code |
| `Command.start(command)` | Start scoped process handle |
| `Command.pipeTo(left, right)` | Connect stdout to stdin |
| `Command.feed(command, input)` | Feed string stdin |
| `Command.workingDirectory(command, cwd)` | Set working directory |
| `Command.env(command, values)` | Set environment for child only |

The executor service is provided by `NodeCommandExecutor.layer`,
`BunCommandExecutor.layer`, or a context bundle.

## Collect Output

```typescript
import { Effect } from "effect"
import { Command } from "@effect/platform"
import { NodeContext, NodeRuntime } from "@effect/platform-node"

const program = Effect.gen(function* () {
  const version = yield* Command.string(Command.make("node", "--version"))
  yield* Effect.logInfo(`Node version: ${version.trim()}`)
})

program.pipe(
  Effect.provide(NodeContext.layer),
  NodeRuntime.runMain
)
```

`Command.string` requires `CommandExecutor.CommandExecutor`. `NodeContext.layer`
provides it.

## Shell-free Arguments

Prefer argument arrays over shell strings. Shell mode is available, but it
changes quoting, escaping, and portability.

```typescript
import { Effect } from "effect"
import { Command } from "@effect/platform"

export const listTrackedFiles = Effect.gen(function* () {
  const lines = yield* Command.lines(
    Command.make("git", "ls-files")
  )

  return lines.filter((line) => line.endsWith(".ts"))
})
```

Use `Command.runInShell(true)` only when the shell itself is part of the
requirement.

## Environment and Working Directory

```typescript
import { pipe } from "effect"
import { Command } from "@effect/platform"

export const runTool = (cwd: string, token: string) =>
  pipe(
    Command.make("tool", "sync"),
    Command.workingDirectory(cwd),
    Command.env({ "API_TOKEN": token }),
    Command.string
  )
```

`Command.env` affects the child command description. Keep configuration loading
outside this helper and pass explicit values in.

## Piping Commands

```typescript
import { pipe } from "effect"
import { Command } from "@effect/platform"

export const sortedNames = pipe(
  Command.make("printf", "zeta\nalpha\nbeta\n"),
  Command.pipeTo(Command.make("sort")),
  Command.lines
)
```

Pipes connect process stdout to process stdin without manually wiring streams.

## Streaming Output

```typescript
import { Effect, Stream } from "effect"
import { Command } from "@effect/platform"

export const streamStatus = Command.streamLines(
  Command.make("git", "status", "--short")
).pipe(
  Stream.runForEach((line) => Effect.logInfo(line))
)
```

Use streaming for long-running commands or large outputs. Use `Command.string`
only when output is naturally bounded.

## Scoped Process Handle

`Command.start` returns a `Process` inside a scope. The process handle exposes
`pid`, `exitCode`, `isRunning`, `kill`, `stdin`, `stdout`, and `stderr`.

```typescript
import { Effect } from "effect"
import { Command } from "@effect/platform"

export const runAndStop = Effect.scoped(
  Effect.gen(function* () {
    const process = yield* Command.start(Command.make("sleep", "30"))
    const running = yield* process.isRunning

    if (running) {
      yield* process.kill("SIGTERM")
    }

    return yield* process.exitCode
  })
)
```

Use this shape when you need lifecycle control rather than simple collection.

## Exit Codes

```typescript
import { Effect } from "effect"
import { Command } from "@effect/platform"

export const isCleanGitTree = Effect.gen(function* () {
  const code = yield* Command.exitCode(
    Command.make("git", "diff", "--quiet")
  )

  return Number(code) === 0
})
```

Some tools communicate expected states through exit codes. Model that explicitly
instead of treating every non-zero status as a defect.

## Runtime Layers

`NodeCommandExecutor.layer` requires `FileSystem.FileSystem`; `NodeContext.layer`
already handles that dependency. If you provide individual layers, merge with
`NodeFileSystem.layer`.

```typescript
import { Effect, Layer } from "effect"
import { Command } from "@effect/platform"
import {
  NodeCommandExecutor,
  NodeFileSystem,
  NodeRuntime
} from "@effect/platform-node"

const Live = NodeCommandExecutor.layer.pipe(
  Layer.provide(NodeFileSystem.layer)
)

const program = Command.string(Command.make("node", "--version"))

program.pipe(
  Effect.provide(Live),
  Effect.flatMap((version) => Effect.logInfo(version.trim())),
  NodeRuntime.runMain
)
```

## Anti-patterns

- Running shell strings when plain arguments work.
- Using child processes for file operations covered by `FileSystem`.
- Collecting unbounded output into a string.
- Starting a process without a scope when lifecycle matters.
- Loading secrets inside command helpers instead of passing explicit values.

## Cross-references

See also: [01-overview.md](01-overview.md), [02-filesystem.md](02-filesystem.md), [10-stream-sink-platform.md](10-stream-sink-platform.md), [11-node-context.md](11-node-context.md), [12-node-runtime.md](12-node-runtime.md)
