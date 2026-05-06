# NodeRuntime
Use `NodeRuntime.runMain` as the complete Node entry-point runner for graceful errors and signals.

## Why It Exists

`NodeRuntime.runMain` is the Node runtime implementation of the platform
`RunMain` interface. It launches the main Effect, installs the pretty logger by
default, reports non-interruption failures, sets process exit codes, and handles
`SIGINT` and `SIGTERM`.

The Node source delegates to `@effect/platform-node-shared/NodeRuntime`, which
uses `makeRunMain` from `@effect/platform/Runtime`.

## Complete Entry Point

```typescript
import { Effect, Schedule } from "effect"
import { FileSystem } from "@effect/platform"
import { NodeContext, NodeRuntime } from "@effect/platform-node"

const program = Effect.gen(function* () {
  const fs = yield* FileSystem.FileSystem
  const exists = yield* fs.exists("package.json")

  yield* Effect.logInfo(`package.json exists: ${exists}`)
  yield* Effect.repeat(
    Effect.logInfo("service heartbeat"),
    Schedule.spaced("10 seconds")
  )
})

program.pipe(
  Effect.provide(NodeContext.layer),
  NodeRuntime.runMain
)
```

Run this as the application entry file. `NodeRuntime.runMain` handles `SIGINT`
and `SIGTERM` by interrupting the running fiber. Scoped resources and finalizers
then run through normal Effect interruption.

## Signal Semantics

The Node implementation:

- starts the Effect with `Effect.runFork`;
- registers listeners for `SIGINT` and `SIGTERM`;
- interrupts the runtime fiber on the first signal;
- removes listeners when the fiber exits without a received signal;
- keeps the process alive while the fiber is active;
- uses teardown to choose the exit code.

This is why `NodeRuntime.runMain` is preferred for long-running CLIs, servers,
watchers, and workers.

## Options

```typescript
import { Effect } from "effect"
import { NodeRuntime } from "@effect/platform-node"

const failure = Effect.fail("startup failed")

NodeRuntime.runMain(failure, {
  disablePrettyLogger: true,
  disableErrorReporting: false
})
```

Options:

| Option | Effect |
|---|---|
| `disableErrorReporting` | Do not automatically log failure causes |
| `disablePrettyLogger` | Keep the default logger instead of installing pretty logger |
| `teardown` | Override final exit-code behavior |

Most applications should use defaults.

## Custom Teardown

```typescript
import { Effect, Exit } from "effect"
import { NodeRuntime } from "@effect/platform-node"

const program = Effect.succeed("done")

NodeRuntime.runMain(program, {
  teardown: (exit, onExit) => {
    onExit(Exit.isSuccess(exit) ? 0 : 1)
  }
})
```

Custom teardown is an edge concern. Do not put it inside library code.

## With Layer Launch

Servers often expose a `Layer` that should be launched as the main program.

```typescript
import { Layer } from "effect"
import { NodeRuntime } from "@effect/platform-node"

declare const ServerLive: Layer.Layer<never, never, never>

Layer.launch(ServerLive).pipe(
  NodeRuntime.runMain
)
```

`Layer.launch` acquires the layer, keeps it active, and releases it when
interrupted.

## Worker Runner Entry

```typescript
import { Effect } from "effect"
import { WorkerRunner } from "@effect/platform"
import { NodeRuntime, NodeWorkerRunner } from "@effect/platform-node"

const WorkerLive = WorkerRunner.layer(
  (request: string) => Effect.succeed(request.length)
)

WorkerRunner.launch(WorkerLive).pipe(
  Effect.provide(NodeWorkerRunner.layer),
  NodeRuntime.runMain
)
```

Use the same runner at worker entry points so interruption and teardown stay
consistent with the parent process.

## Anti-patterns

- Using low-level runners as the Node application entry point.
- Starting the main Effect before all runtime layers are provided.
- Swallowing interruption failures at the process boundary.
- Installing custom signal handlers that bypass Effect finalizers.
- Calling the runner from reusable library modules.

## Cross-references

See also: [01-overview.md](01-overview.md), [05-command.md](05-command.md), [09-worker.md](09-worker.md), [11-node-context.md](11-node-context.md)
