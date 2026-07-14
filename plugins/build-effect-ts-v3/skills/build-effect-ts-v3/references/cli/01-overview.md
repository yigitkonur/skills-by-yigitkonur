# CLI Overview
Understand how `@effect/cli` models typed commands, options, arguments, prompts, fallbacks, services, and shell integration.

## When To Use It

Use `@effect/cli` when a command-line program should keep parsing,
validation, service requirements, help text, wizard mode, and completion
scripts in the same typed Effect program.

It replaces ad-hoc argument parsing with four core concepts:

| Concept | Module | Purpose |
|---|---|---|
| command | `Command` | Names an executable action and attaches a handler |
| options | `Options` | Parses named flags such as `--name foo` |
| args | `Args` | Parses positional values such as `deploy api` |
| prompts | `Prompt` | Asks for interactive input when needed |

The root model is a `Command.Command<Name, R, E, A>`. It is both a command
description and an Effect value for its parsed config. That second point is
what lets a subcommand read its parent's parsed options with `yield* parentCmd`.

## Imports

Prefer the package barrel for examples and application code:

```typescript
import { Args, Command, ConfigFile, Options, Prompt } from "@effect/cli"
import { NodeContext, NodeRuntime } from "@effect/platform-node"
import { Config, Effect, Layer, Option, Schema } from "effect"
```

Deep imports exist in source, but the skill should teach the stable public
surface. Schema lives in `effect` in v3.

## Application Shape

A complete CLI normally follows this shape:

```typescript
import { Args, Command, Options } from "@effect/cli"
import { NodeContext, NodeRuntime } from "@effect/platform-node"
import { Effect } from "effect"

const name = Args.text({ name: "name" })
const loud = Options.boolean("loud").pipe(Options.withAlias("l"))

const greet = Command.make("greet", { name, loud }, ({ name, loud }) =>
  Effect.logInfo(loud ? `HELLO ${name}` : `Hello ${name}`)
)

const cli = Command.run(greet, {
  name: "Greeter",
  version: "1.0.0"
})

Effect.suspend(() => cli(process.argv)).pipe(
  Effect.provide(NodeContext.layer),
  NodeRuntime.runMain
)
```

The handler receives a typed object inferred from the command config. The
runtime edge provides `NodeContext.layer`, because parsing file paths, prompts,
terminal output, and config files can require platform services.

## Built-In Behavior

Every `Command.run` app gets built-in commands and flags:

| Built-in | Behavior |
|---|---|
| `-h`, `--help` | Prints generated usage and descriptions |
| `--version` | Prints the configured application version |
| `--wizard` | Builds the command interactively through prompts |
| `--completions bash` | Prints a Bash completion script |
| `--completions fish` | Prints a Fish completion script |
| `--completions zsh` | Prints a Zsh completion script |
| `--log-level` | Sets Effect runtime log level |

You should not implement these yourself. Add descriptions to commands, options,
and args; the built-ins render them.

## Typed Parsing

Command config is a record whose leaves are `Options`, `Args`, nested records,
or arrays of those values.

```typescript
import { Args, Command, Options } from "@effect/cli"
import { Effect } from "effect"

const command = Command.make(
  "publish",
  {
    target: Args.text({ name: "target" }),
    flags: {
      dryRun: Options.boolean("dry-run"),
      format: Options.choice("format", ["json", "text"] as const)
    }
  },
  ({ target, flags }) =>
    Effect.logInfo(`target=${target} dryRun=${flags.dryRun} format=${flags.format}`)
)
```

The inferred handler config is:

```typescript
type Parsed = {
  readonly target: string
  readonly flags: {
    readonly dryRun: boolean
    readonly format: "json" | "text"
  }
}
```

## Validation Layers

Validation can happen at several levels:

| Layer | API |
|---|---|
| primitive parser | `Options.integer`, `Args.date`, `Prompt.confirm` |
| choice parser | `Options.choice`, `Args.choice`, `Prompt.select` |
| schema validation | `Options.withSchema`, `Args.withSchema`, `Options.fileSchema` |
| fallback config | `Options.withFallbackConfig`, `Args.withFallbackConfig` |
| interactive fallback | `Options.withFallbackPrompt` |

Use `Schema` when the primitive type is not enough:

```typescript
import { Command, Options } from "@effect/cli"
import { Effect, Schema } from "effect"

const port = Options.text("port").pipe(
  Options.withSchema(Schema.NumberFromString)
)

const command = Command.make("serve", { port }, ({ port }) =>
  Effect.logInfo(`Listening on ${port}`)
)
```

## Fallback Precedence

For a single parameter, precedence is:

1. CLI args
2. Config file through `withFallbackConfig`
3. Prompt through `withFallbackPrompt`
4. Static value through `withDefault`

Use this order deliberately. A value explicitly passed on the command line
should win over all fallback mechanisms.

## Cross-references

See also: [02 Command](02-command.md), [03 Options](03-options.md), [05 Args](05-args.md), [08 Subcommands](08-subcommands.md), [11 Fallbacks](11-fallbacks.md)
