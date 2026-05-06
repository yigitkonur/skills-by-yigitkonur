# Completions
Generate shell completion scripts and use wizard mode from built-in CLI options.

## Built-In Completion Flag

`Command.run` applications include completion generation automatically:

```bash
my-tool --completions bash
my-tool --completions fish
my-tool --completions zsh
```

The v3 source also accepts `sh` as a completion choice. Document Bash, Fish,
and Zsh for normal user-facing instructions.

## Why It Works

Completion scripts are generated from the same command descriptor used for help
and parsing. That means command names, option names, aliases, descriptions, and
subcommands all matter.

```typescript
import { Args, Command, Options } from "@effect/cli"
import { Effect } from "effect"

const command = Command.make("deploy", {
  target: Args.text({ name: "target" }).pipe(
    Args.withDescription("Deployment target")
  ),
  profile: Options.text("profile").pipe(
    Options.withAlias("p"),
    Options.withDescription("Profile name"),
    Options.withDefault("dev")
  )
}, ({ target, profile }) =>
  Effect.logInfo(`deploy ${target} with ${profile}`)
)
```

This command contributes `deploy`, `--profile`, and `-p` to generated metadata.

## Installation Examples

Bash:

```bash
source <(my-tool --completions bash)
```

Fish:

```bash
my-tool --completions fish > ~/.config/fish/completions/my-tool.fish
```

Zsh:

```bash
my-tool --completions zsh > _my-tool
```

Exact shell installation paths are shell-specific; the CLI's job is to print
the script.

## Programmatic Access

The `Command` module exposes completion helpers:

```typescript
import { Command } from "@effect/cli"

declare const command: Command.Command<"tool", never, never, unknown>

const bash = Command.getBashCompletions(command, "tool")
const fish = Command.getFishCompletions(command, "tool")
const zsh = Command.getZshCompletions(command, "tool")
```

These return effects that produce arrays of script lines. Most applications
should rely on the built-in `--completions` flag.

## Wizard Mode

`--wizard` is also built in:

```bash
my-tool --wizard
my-tool deploy --wizard
```

Wizard mode prompts users through the command's args and options. It uses the
same descriptions and primitive metadata as normal parsing.

## Command.wizard

Use `Command.wizard` directly only for custom tooling around command
descriptors:

```typescript
import { Command } from "@effect/cli"

declare const command: Command.Command<"tool", never, never, unknown>
declare const config: import("@effect/cli").CliConfig.CliConfig

const args = Command.wizard(command, ["tool"], config)
```

Application entry points should prefer `Command.run`, which wires built-ins for
users.

## Completion Quality Checklist

Before shipping a CLI, check:

| Item | Why it matters |
|---|---|
| command descriptions | users see useful completion context |
| option aliases | short flags are generated |
| arg names | wizard mode labels positional values |
| choice parsers | completions can suggest fixed choices |
| subcommands | command tree is discoverable |

Completions improve as the command descriptor becomes more precise.

## Cross-references

See also: [02 Command](02-command.md), [03 Options](03-options.md), [05 Args](05-args.md), [07 Prompts](07-prompts.md), [08 Subcommands](08-subcommands.md)
