# Greenfield CLI
Build a small file-processing CLI with Effect v3, `@effect/cli`, Node platform services, layers, and test overrides.

Use this when the user asks for a new command-line program. The official examples repo ships a CLI template with `src/Cli.ts` and `src/bin.ts`; this version keeps that structure while using the repo-required barrel imports.

## Primitive index

| Primitive | Read first |
|---|---|
| `Effect.gen`, `Effect.all`, `Effect.fn` | [core](../core/05-generators.md), [core](../core/08-effect-all.md), [core](../core/07-effect-fn.md) |
| `Command`, `Options`, command runner | [cli](../cli/02-command.md), [cli](../cli/03-options.md), [cli](../cli/09-providing-services.md) |
| `FileSystem`, `Path`, `NodeRuntime.runMain` | [platform](../platform/02-filesystem.md), [platform](../platform/03-path.md), [platform](../platform/12-node-runtime.md) |
| `Effect.Service`, `Layer.succeed`, `Layer.merge` | [services-layers](../services-layers/03-effect-service.md), [services-layers](../services-layers/06-layer-succeed.md), [services-layers](../services-layers/09-layer-merge.md) |
| typed errors, logging, tests | [error-handling](../error-handling/02-data-tagged-error.md), [observability](../observability/02-logging-basics.md), [testing](../testing/08-test-layers.md) |

## 1. Package setup

Create a minimal Node ESM project. `tsx` is enough for development; use `tsup` only when you want a single-file binary.

```typescript
{
  "type": "module",
  "scripts": {
    "dev": "tsx src/bin.ts --input ./samples --ext .txt",
    "build": "tsc -p tsconfig.json",
    "test": "vitest"
  },
  "dependencies": {
    "@effect/cli": "^0.70.0",
    "@effect/platform": "^0.95.0",
    "@effect/platform-node": "^0.90.0",
    "effect": "^3.21.2"
  },
  "devDependencies": {
    "@effect/vitest": "^0.28.0",
    "tsx": "^4.20.0",
    "typescript": "^5.9.0",
    "vitest": "^4.0.0"
  }
}
```

## 2. Entry point

`src/bin.ts` is the only place that reads process arguments or exits the process. Everything else stays as plain Effects.

```typescript
import { NodeContext, NodeRuntime } from "@effect/platform-node"
import { Effect } from "effect"
import { run } from "./cli.js"
import { FileProcessor } from "./services.js"

run(process.argv).pipe(
  Effect.provide(FileProcessor.Default),
  Effect.provide(NodeContext.layer),
  NodeRuntime.runMain({ disableErrorReporting: true })
)
```

If you do not need `@effect/cli`, the same orchestration can be exposed as `main.pipe(Effect.provide(...), NodeRuntime.runMain)`. Keep `Effect.runPromise` out of service code; see [runpromise mid-code](../anti-patterns/04-runpromise-mid-code.md).

## 3. Main orchestration

`src/cli.ts` parses options and delegates all work to a service. The command action is an `Effect.gen` program, not a callback that performs work directly.

```typescript
import { Command, Options } from "@effect/cli"
import { Effect } from "effect"
import { FileProcessor } from "./services.js"

const input = Options.text("input").pipe(
  Options.withAlias("i"),
  Options.withDescription("Directory to scan")
)

const ext = Options.text("ext").pipe(
  Options.withDefault(".txt"),
  Options.withDescription("File extension to include")
)

const command = Command.make("scan", { input, ext }, ({ input, ext }) =>
  Effect.gen(function*() {
    const processor = yield* FileProcessor
    const summary = yield* processor.scan(input, ext)
    yield* Effect.logInfo("scan complete", summary)
  })
)

export const run = Command.run(command, {
  name: "file-scan",
  version: "0.1.0"
})
```

## 4. Per-feature service definitions

`src/services.ts` owns the feature. Use `Effect.Service` when the live implementation needs dependencies or setup.

```typescript
import { FileSystem, Path } from "@effect/platform"
import { Effect, ReadonlyArray, Schema } from "effect"

export class ScanError extends Schema.TaggedError<ScanError>()("ScanError", {
  path: Schema.String,
  reason: Schema.String
}) {}

export interface ScanSummary {
  readonly directory: string
  readonly matched: number
}

export class FileProcessor extends Effect.Service<FileProcessor>()(
  "app/FileProcessor",
  {
    effect: Effect.gen(function*() {
      const fs = yield* FileSystem.FileSystem
      const path = yield* Path.Path

      const scan = Effect.fn("FileProcessor.scan")(function*(directory: string, ext: string) {
        const entries = yield* fs.readDirectory(directory).pipe(
          Effect.mapError((error) => new ScanError({ path: directory, reason: String(error) }))
        )
        const matched = entries.pipe(
          ReadonlyArray.filter((entry) => path.extname(entry) === ext)
        )
        return { directory, matched: matched.length } satisfies ScanSummary
      })

      return { scan } as const
    })
  }
) {}
```

## 5. Layer wiring

The CLI's layer graph is intentionally small. `NodeContext.layer` supplies platform services; the feature service can stay defaulted.

```typescript
import { NodeContext } from "@effect/platform-node"
import { Layer } from "effect"
import { FileProcessor } from "./services.js"

export const AppLayer = Layer.merge(FileProcessor.Default, NodeContext.layer)
```

For a larger CLI, split services by feature and merge only at the edge. Do not construct layers inline in command handlers; see [inline layer construction](../anti-patterns/14-inline-layer-construction.md).

## 6. Test layer override

Override the feature service, not the whole CLI parser. This keeps parser behavior and business behavior independently testable.

```typescript
import { it } from "@effect/vitest"
import { Effect, Layer } from "effect"
import { FileProcessor } from "../src/services.js"

const FileProcessorTest = Layer.succeed(FileProcessor, {
  scan: () => Effect.succeed({ directory: "fixture", matched: 2 })
})

it.effect("uses the file processor service", () =>
  Effect.gen(function*() {
    const processor = yield* FileProcessor
    const summary = yield* processor.scan("fixture", ".txt")
    expect(summary.matched).toBe(2)
  }).pipe(Effect.provide(FileProcessorTest))
)
```

For platform-facing tests, prefer a service wrapper over temporary files unless the test is explicitly verifying `FileSystem` behavior. Use [stateful test layers](../testing/09-stateful-test-layers.md) when the test needs mutable in-memory fixtures.

## Workflow checklist

1. Create `src/bin.ts` first and keep it as the only process entry.
2. Create `src/cli.ts` with one command and one action Effect.
3. Move real work into `src/services.ts` before adding subcommands.
4. Provide `NodeContext.layer` only at the entry point.
5. Use `Options.withDefault` for safe CLI defaults.
6. Use `Options.withDescription` so generated help stays useful.
7. Add typed failures for user-facing validation and file failures.
8. Log summaries with `Effect.logInfo`, not ad hoc side effects.
9. Keep filesystem access behind the feature service.
10. Add a test layer before adding the second command.
11. Add subcommands only after the first command has a stable service.
12. Add shell completions after the public command names stabilize.
13. Use `Effect.all(..., { concurrency })` for batch file work.
14. Keep command parsing tests separate from service behavior tests.
15. Treat the compiled binary as the deployment artifact.
16. Put package `bin` metadata under source control with the command name.
17. Document required config through `Config`, not ambient reads.
18. Re-run the CLI against a fixture directory before release.
19. Verify failure output with an invalid path.
20. Verify success output with at least one matching file.
21. Keep examples short enough for users to paste into a new repo.
22. Link every primitive back to this skill's reference pages.
23. Prefer one command per feature service.
24. Split shared utilities only after a fourth repeated use.
25. Keep the runtime edge boring.
26. Keep service code reusable from tests, scripts, and future HTTP wrappers.
27. Add [prompts](../cli/07-prompts.md) only for genuinely interactive flows.
28. Add [subcommands](../cli/08-subcommands.md) when command options stop scaling.
29. Add [config files](../cli/10-config-files.md) when flags become repetitive.
30. Use [fallbacks](../cli/11-fallbacks.md) for environment-specific defaults.
31. Use [completions](../cli/12-completions.md) for installed developer tools.
32. Keep service failures typed before mapping them to process exits.
33. Keep help text focused on user inputs, not implementation details.
34. Verify the compiled entry imports `.js` paths for ESM output.
35. Prefer `NodeContext.layer` over hand-rolled Node wrappers.
36. Keep this workflow as the starting point for small local automation.
37. Add [terminal](../platform/06-terminal.md) only when interactive output needs terminal capabilities.
38. Add [command execution](../platform/05-command.md) only when shelling out is the feature itself.

## 7. Deployment

Build the CLI with `tsc` for local tools or `tsup` for a single distributable file. Keep `#!/usr/bin/env node` only in the entry file, then set `bin` in `package.json` to the compiled path. For container deployment, run the compiled CLI as the container command and inject runtime configuration through Effect `Config`, not through direct environment reads.

## Cross-references

See also: [greenfield HTTP API](02-greenfield-http-api.md), [adding Effect to existing code](05-adding-effect-existing.md), [background worker](07-background-worker.md), [anti-patterns overview](../anti-patterns/01-overview.md).
