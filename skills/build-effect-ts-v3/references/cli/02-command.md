# Command
Build executable CLI actions with `Command.make`, attach handlers, and run them through `NodeRuntime.runMain`.

## Core Type

`Command.Command<Name, R, E, A>` carries four useful facts:

| Parameter | Meaning |
|---|---|
| `Name` | command name as a string literal |
| `R` | services required by the handler |
| `E` | failures produced by the handler |
| `A` | parsed command config |

`Command` extends `Effect`, so a command value can also be yielded from another
command handler to read the parsed config for that command.

## Constructors

Use `Command.make` for normal commands:

```typescript
import { Command } from "@effect/cli"

const empty = Command.make("status")
```

Add a config record to parse options and args:

```typescript
import { Args, Command, Options } from "@effect/cli"

const command = Command.make("copy", {
  source: Args.file({ name: "source", exists: "yes" }),
  target: Args.text({ name: "target" }),
  force: Options.boolean("force")
})
```

Add the handler as the third argument when the behavior is known at definition
time:

```typescript
import { Args, Command, Options } from "@effect/cli"
import { Effect } from "effect"

const command = Command.make(
  "copy",
  {
    source: Args.file({ name: "source", exists: "yes" }),
    target: Args.text({ name: "target" }),
    force: Options.boolean("force")
  },
  ({ source, target, force }) =>
    Effect.logInfo(`copy ${source} to ${target} force=${force}`)
)
```

## Handler Later

Use `Command.withHandler` when the parser and behavior are easier to define in
separate steps.

```typescript
import { Args, Command } from "@effect/cli"
import { Effect } from "effect"

const parser = Command.make("echo", {
  value: Args.text({ name: "value" })
})

const command = parser.pipe(
  Command.withHandler(({ value }) => Effect.logInfo(value))
)
```

The handler must return `Effect<void, E, R>`. If a command computes a useful
value internally, consume or persist it inside the handler.

## Description

Descriptions feed generated help, wizard prompts, and completion metadata.

```typescript
import { Args, Command, Options } from "@effect/cli"
import { Effect } from "effect"

const command = Command.make(
  "deploy",
  {
    target: Args.text({ name: "target" }).pipe(
      Args.withDescription("Deployment target")
    ),
    dryRun: Options.boolean("dry-run").pipe(
      Options.withDescription("Plan without applying changes")
    )
  },
  ({ target, dryRun }) => Effect.logInfo(`target=${target} dryRun=${dryRun}`)
).pipe(
  Command.withDescription("Deploy a target")
)
```

Descriptions should name domain intent, not restate the parser type.

## Command.run

`Command.run` turns a command into a function from raw argv to an Effect:

```typescript
import { Command } from "@effect/cli"

declare const command: Command.Command<"tool", never, never, {}>

const cli = Command.run(command, {
  name: "Tool",
  version: "1.0.0"
})
```

The resulting `cli` has this shape:

```typescript
const cli: (
  args: ReadonlyArray<string>
) => import("effect").Effect.Effect<void, unknown, unknown>
```

The exact error and requirement types depend on the command handler and on CLI
environment services. In Node, provide `NodeContext.layer` at the edge.

## Built-In Metadata

The `name` and `version` passed to `Command.run` are application metadata, not
the same thing as the command name:

```typescript
const cli = Command.run(command, {
  name: "Acme Release Tool",
  version: "2.4.0"
})
```

Generated help and `--version` use this metadata.

## Empty Root With Subcommands

For command groups, the root can have no handler and no config:

```typescript
import { Args, Command } from "@effect/cli"
import { Effect } from "effect"

const root = Command.make("project")

const init = Command.make("init", {
  name: Args.text({ name: "name" })
}, ({ name }) => Effect.logInfo(`init ${name}`))

const command = root.pipe(Command.withSubcommands([init]))
```

This is useful when the root exists only to route to subcommands.

## Complete Entry Point

This is the full Node entry point pattern to teach and copy:

```typescript
import { Args, Command, Options } from "@effect/cli"
import { NodeContext, NodeRuntime } from "@effect/platform-node"
import { Effect } from "effect"

const command = Command.make(
  "greet",
  {
    name: Options.text("name").pipe(
      Options.withAlias("n"),
      Options.withDescription("Name to greet")
    ),
    punctuation: Args.text({ name: "punctuation" }).pipe(
      Args.withDefault("!")
    )
  },
  ({ name, punctuation }) =>
    Effect.logInfo(`Hello ${name}${punctuation}`)
)

const cli = Command.run(command, {
  name: "Greeter",
  version: "1.0.0"
})

Effect.suspend(() => cli(process.argv)).pipe(
  Effect.provide(NodeContext.layer),
  NodeRuntime.runMain
)
```

`Options.text("name")` parses `--name Ada`; adding
`Options.withAlias("n")` also parses `-n Ada`.

## Cross-references

See also: [01 Overview](01-overview.md), [08 Subcommands](08-subcommands.md), [09 Providing Services](09-providing-services.md), [10 Config Files](10-config-files.md), [12 Completions](12-completions.md)
