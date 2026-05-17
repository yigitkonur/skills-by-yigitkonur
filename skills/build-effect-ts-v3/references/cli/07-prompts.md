# Prompts
Use `Prompt` for interactive CLI input and option fallback.

## Prompt Model

`Prompt<A>` is an Effect that can interact with the terminal and produce `A`.
Prompts are useful in two places:

| Use | API |
|---|---|
| standalone interactive command | `Command.prompt` |
| missing option fallback | `Options.withFallbackPrompt` |

Prompt constructors live in `@effect/cli/Prompt` and are exported from the
package barrel:

```typescript
import { Command, Options, Prompt } from "@effect/cli"
import { Effect } from "effect"
```

## Text

```typescript
import { Command, Prompt } from "@effect/cli"
import { Effect } from "effect"

const name = Prompt.text({
  message: "Name:",
  default: "Ada",
  validate: (value) =>
    value.trim().length === 0
      ? Effect.fail("Name is required")
      : Effect.succeed(value)
})

const command = Command.prompt("hello", name, (name) =>
  Effect.logInfo(`Hello ${name}`)
)
```

Use `validate` for prompt-local checks that can give users immediate feedback.

## Password And Hidden

Use `Prompt.password` or `Prompt.hidden` for secret text. Both return redacted
values.

```typescript
import { Command, Prompt } from "@effect/cli"
import { Effect } from "effect"

const token = Prompt.password({
  message: "Token:"
})

const command = Command.prompt("login", token, () =>
  Effect.logInfo("token captured")
)
```

Do not display the returned value in logs or help text.

## Integer And Float

Number prompts support bounds and step sizes:

```typescript
import { Command, Prompt } from "@effect/cli"
import { Effect } from "effect"

const retries = Prompt.integer({
  message: "Retries:",
  min: 0,
  max: 10,
  incrementBy: 1,
  decrementBy: 1
})

const command = Command.prompt("configure", retries, (retries) =>
  Effect.logInfo(`retries=${retries}`)
)
```

Use `Prompt.float` when precision matters:

```typescript
const ratio = Prompt.float({
  message: "Ratio:",
  min: 0,
  max: 1,
  precision: 2
})
```

## Confirm

`Prompt.confirm` asks yes-or-no questions:

```typescript
import { Command, Prompt } from "@effect/cli"
import { Effect } from "effect"

const proceed = Prompt.confirm({
  message: "Proceed?",
  initial: false
})

const command = Command.prompt("confirm", proceed, (proceed) =>
  Effect.logInfo(`proceed=${proceed}`)
)
```

Use confirm prompts for irreversible or expensive actions, not for normal flags
that users can pass non-interactively.

## Toggle

`Prompt.toggle` is another boolean prompt with active and inactive labels:

```typescript
import { Command, Prompt } from "@effect/cli"
import { Effect } from "effect"

const enabled = Prompt.toggle({
  message: "Feature:",
  initial: true,
  active: "enabled",
  inactive: "disabled"
})

const command = Command.prompt("feature", enabled, (enabled) =>
  Effect.logInfo(`enabled=${enabled}`)
)
```

Use it when labels communicate the current state better than yes or no.

## Select

`Prompt.select` returns the selected choice value:

```typescript
import { Command, Prompt } from "@effect/cli"
import { Effect } from "effect"

const environment = Prompt.select({
  message: "Environment:",
  choices: [
    { title: "Development", value: "dev" },
    { title: "Production", value: "prod" }
  ] as const
})

const command = Command.prompt("deploy", environment, (environment) =>
  Effect.logInfo(`environment=${environment}`)
)
```

Choice values can be strings, numbers, or domain objects.

## Multi Select

`Prompt.multiSelect` returns an array:

```typescript
import { Command, Prompt } from "@effect/cli"
import { Effect } from "effect"

const scopes = Prompt.multiSelect({
  message: "Scopes:",
  min: 1,
  choices: [
    { title: "Read", value: "read", selected: true },
    { title: "Write", value: "write" },
    { title: "Admin", value: "admin", disabled: true }
  ] as const
})

const command = Command.prompt("scopes", scopes, (scopes) =>
  Effect.logInfo(`scopes=${scopes.join(",")}`)
)
```

Use `min` and `max` when the domain needs a bounded selection.

## List

`Prompt.list` parses delimited text into `Array<string>`:

```typescript
import { Command, Prompt } from "@effect/cli"
import { Effect } from "effect"

const tags = Prompt.list({
  message: "Tags:",
  delimiter: ","
})

const command = Command.prompt("tags", tags, (tags) =>
  Effect.logInfo(`tags=${tags.join(",")}`)
)
```

This is useful for interactive input that would otherwise be a repeated option.

## Prompt.all

Combine prompts into a typed record:

```typescript
import { Command, Prompt } from "@effect/cli"
import { Effect } from "effect"

const config = Prompt.all({
  name: Prompt.text({ message: "Name:" }),
  retries: Prompt.integer({ message: "Retries:", min: 0, max: 5 }),
  enabled: Prompt.confirm({ message: "Enabled?" })
})

const command = Command.prompt("setup", config, ({ name, retries, enabled }) =>
  Effect.logInfo(`name=${name} retries=${retries} enabled=${enabled}`)
)
```

Use `Prompt.all` for interactive setup commands.

## Prompt As Fallback

An option can ask only when no CLI value and no config fallback exists:

```typescript
import { Command, Options, Prompt } from "@effect/cli"
import { Config, Effect } from "effect"

const name = Options.text("name").pipe(
  Options.withFallbackConfig(Config.string("NAME")),
  Options.withFallbackPrompt(Prompt.text({ message: "Name:" })),
  Options.withDefault("guest")
)

const command = Command.make("hello", { name }, ({ name }) =>
  Effect.logInfo(`Hello ${name}`)
)
```

Precedence is CLI args, then config file, then prompt, then default.

## Cross-references

See also: [03 Options](03-options.md), [04 Options Combinators](04-options-combinators.md), [08 Subcommands](08-subcommands.md), [11 Fallbacks](11-fallbacks.md)
