# Fallbacks
Apply CLI, config-file, prompt, and default precedence consistently.

## Precedence

For a parameter that uses every fallback layer, the intended order is:

1. CLI args
2. Config file through `withFallbackConfig`
3. Prompt through `withFallbackPrompt`
4. Static value through `withDefault`

The most explicit source wins. A command-line value should override a config
file, interactive prompt, and static default.

Precedence: CLI args > Config file (`withFallbackConfig`) > Prompt (`withFallbackPrompt`) > `withDefault`.

## Option Fallback Stack

Options support the full stack:

```typescript
import { Command, Options, Prompt } from "@effect/cli"
import { Config, Effect } from "effect"

const name = Options.text("name").pipe(
  Options.withAlias("n"),
  Options.withFallbackConfig(Config.string("NAME")),
  Options.withFallbackPrompt(Prompt.text({ message: "Name:" })),
  Options.withDefault("guest")
)

const command = Command.make("hello", { name }, ({ name }) =>
  Effect.logInfo(`Hello ${name}`)
)
```

`--name Ada` and `-n Ada` both win over every fallback.

## Args Fallback Stack

Args support config fallback and default:

```typescript
import { Args, Command } from "@effect/cli"
import { Config, Effect } from "effect"

const repository = Args.text({ name: "repository" }).pipe(
  Args.withFallbackConfig(Config.string("REPOSITORY")),
  Args.withDefault("effect")
)

const command = Command.make("clone", { repository }, ({ repository }) =>
  Effect.logInfo(`repository=${repository}`)
)
```

Args do not have `withFallbackPrompt` in the v3 source. If a positional value
needs interactive input, model it as an option fallback or use `Command.prompt`.

## Config File Provider

Fallback config reads from the active `ConfigProvider`. Use `ConfigFile.layer`
when that provider should come from disk:

```typescript
import { ConfigFile } from "@effect/cli"
import { NodeContext, NodeRuntime } from "@effect/platform-node"
import { Effect, Layer } from "effect"

declare const cli: (args: ReadonlyArray<string>) => Effect.Effect<void, unknown, unknown>

Effect.suspend(() => cli(process.argv)).pipe(
  Effect.provide(Layer.mergeAll(
    NodeContext.layer,
    ConfigFile.layer("myapp", { formats: ["json", "yaml", "toml"] })
  )),
  NodeRuntime.runMain
)
```

The fallback combinator does not load files by itself; it asks `Config`.

## Prompt Fallback

Use prompt fallback when interactive use is acceptable but automation should
remain possible:

```typescript
import { Command, Options, Prompt } from "@effect/cli"
import { Effect } from "effect"

const token = Options.redacted("token").pipe(
  Options.withFallbackPrompt(Prompt.password({ message: "Token:" }))
)

const command = Command.make("login", { token }, () =>
  Effect.logInfo("login token received")
)
```

For CI or scripts, document the CLI flag or config key so users can avoid
interactive mode.

## Defaults

Use defaults only when a missing value has a real domain meaning:

```typescript
import { Command, Options } from "@effect/cli"
import { Effect } from "effect"

const profile = Options.text("profile").pipe(
  Options.withDefault("dev")
)

const command = Command.make("deploy", { profile }, ({ profile }) =>
  Effect.logInfo(`profile=${profile}`)
)
```

Do not default required deployment targets, credentials, or destructive modes.

## Common Mistakes

| Mistake | Fix |
|---|---|
| default before config fallback | put `withDefault` last |
| prompt for scripted commands | add CLI/config path first |
| duplicated config keys | centralize the `Config.*` descriptor |
| optional plus default accidentally | choose `Option` or a value, not both |

The readable order is also the precedence order: config fallback, prompt
fallback, default.

## Cross-references

See also: [04 Options Combinators](04-options-combinators.md), [06 Args Combinators](06-args-combinators.md), [07 Prompts](07-prompts.md), [10 Config Files](10-config-files.md)
