# Subcommands
Compose command trees with `Command.withSubcommands` and read parent config with `yield* parentCmd`.

## Command Trees

Use subcommands when the first positional word selects a behavior:

```bash
tool project init my-app
tool project clean --dry-run
```

The parent command owns shared options. Children own action-specific args and
options.

## Basic Subcommands

```typescript
import { Args, Command, Options } from "@effect/cli"
import { Effect } from "effect"

const project = Command.make("project", {
  verbose: Options.boolean("verbose").pipe(Options.withAlias("v"))
})

const init = Command.make("init", {
  name: Args.text({ name: "name" })
}, ({ name }) =>
  Effect.logInfo(`init ${name}`)
)

const clean = Command.make("clean", {
  dryRun: Options.boolean("dry-run")
}, ({ dryRun }) =>
  Effect.logInfo(`clean dryRun=${dryRun}`)
)

const command = project.pipe(
  Command.withSubcommands([init, clean])
)
```

The root can have its own handler, but command-group roots often only route.

## Parent Context Access

`Command` extends `Effect`, so a subcommand handler can yield the parent command
to access the parent's parsed config.

```typescript
import { Args, Command, Options } from "@effect/cli"
import { Effect } from "effect"

const parentCmd = Command.make("workspace", {
  profile: Options.text("profile").pipe(
    Options.withAlias("p"),
    Options.withDefault("dev")
  )
})

const buildCmd = Command.make("build", {
  target: Args.text({ name: "target" })
}, ({ target }) =>
  Effect.gen(function*() {
    const parent = yield* parentCmd
    yield* Effect.logInfo(`profile=${parent.profile} target=${target}`)
  })
)

const command = parentCmd.pipe(
  Command.withSubcommands([buildCmd])
)
```

This is the canonical pattern for shared flags. Do not duplicate parent options
on every child command.

## Nested Subcommands

Subcommands can have subcommands:

```typescript
import { Args, Command } from "@effect/cli"
import { Effect } from "effect"

const root = Command.make("db")
const user = Command.make("user")

const create = Command.make("create", {
  email: Args.text({ name: "email" })
}, ({ email }) =>
  Effect.logInfo(`create user ${email}`)
)

const command = root.pipe(
  Command.withSubcommands([
    user.pipe(Command.withSubcommands([create]))
  ])
)
```

Keep nesting shallow unless the domain already has a clear hierarchy.

## Shared Parent Options

Parent options are best for values that affect all children:

| Shared option | Good parent fit |
|---|---|
| `--profile` | selects runtime configuration |
| `--verbose` | controls logging |
| `--config` | selects config file location |
| `--cwd` | sets working directory |

Child options are better for action-specific details:

| Child option | Better child fit |
|---|---|
| `deploy --strategy` | only deploy uses it |
| `test --watch` | only test uses it |
| `clean --dry-run` | only clean uses it |

## Handling Optional Child Selection

`withSubcommands` adds parsed subcommand information internally. For most
applications, attach handlers to child commands and let the CLI dispatch.

If the parent has behavior too, keep it simple:

```typescript
import { Command } from "@effect/cli"
import { Effect } from "effect"

const root = Command.make("tool", {}, () =>
  Effect.logInfo("choose a subcommand")
)
```

Generated help will still list the children.

## Descriptions

Add descriptions to parent and children:

```typescript
const command = parentCmd.pipe(
  Command.withDescription("Workspace commands"),
  Command.withSubcommands([
    buildCmd.pipe(Command.withDescription("Build a target"))
  ])
)
```

Descriptions feed help, wizard mode, and completion metadata.

## Runtime Wiring

Subcommand trees run the same way as single commands:

```typescript
import { Command } from "@effect/cli"
import { NodeContext, NodeRuntime } from "@effect/platform-node"
import { Effect } from "effect"

declare const command: Command.Command<string, never, never, unknown>

const cli = Command.run(command, {
  name: "Workspace",
  version: "1.0.0"
})

Effect.suspend(() => cli(process.argv)).pipe(
  Effect.provide(NodeContext.layer),
  NodeRuntime.runMain
)
```

The parent-context requirement created by `yield* parentCmd` is resolved by
`Command.withSubcommands`.

## Cross-references

See also: [02 Command](02-command.md), [03 Options](03-options.md), [05 Args](05-args.md), [09 Providing Services](09-providing-services.md), [12 Completions](12-completions.md)
