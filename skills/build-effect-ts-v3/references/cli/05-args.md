# Args
Parse positional command-line inputs with typed `Args` constructors.

## Positional Inputs

Args parse values by position after the command and options. They do not use
flag names at invocation time.

| Constructor | Example input | Parsed type |
|---|---|---|
| `Args.text({ name: "repo" })` | `effect` | `string` |
| `Args.integer({ name: "count" })` | `3` | `number` |
| `Args.float({ name: "ratio" })` | `0.5` | `number` |
| `Args.boolean({ name: "enabled" })` | `true` | `boolean` |
| `Args.date({ name: "when" })` | `2026-05-06` | `Date` |
| `Args.file({ name: "input" })` | `./in.txt` | `string` |
| `Args.directory({ name: "out" })` | `./dist` | `string` |
| `Args.fileText()` | `./readme.md` | `[path, string]` |
| `Args.fileSchema(schema)` | `./settings.json` | schema output |

The `name` in an arg config is for usage, validation, wizard mode, and help.
It is not a named flag.

## Text

```typescript
import { Args, Command } from "@effect/cli"
import { Effect } from "effect"

const repo = Args.text({ name: "repo" })

const command = Command.make("clone", { repo }, ({ repo }) =>
  Effect.logInfo(`clone ${repo}`)
)
```

Example invocation:

```bash
tool clone effect
```

## Integer And Float

Use numeric args for positional numbers:

```typescript
import { Args, Command } from "@effect/cli"
import { Effect } from "effect"

const command = Command.make(
  "scale",
  {
    count: Args.integer({ name: "count" }),
    factor: Args.float({ name: "factor" })
  },
  ({ count, factor }) => Effect.logInfo(`count=${count} factor=${factor}`)
)
```

Use schema combinators for domain-specific constraints.

## Boolean

Boolean args parse textual boolean values, not presence flags:

```typescript
import { Args, Command } from "@effect/cli"
import { Effect } from "effect"

const enabled = Args.boolean({ name: "enabled" })

const command = Command.make("feature", { enabled }, ({ enabled }) =>
  Effect.logInfo(`enabled=${enabled}`)
)
```

For the common `--enabled` shape, use `Options.boolean` instead.

## Date

```typescript
import { Args, Command } from "@effect/cli"
import { Effect } from "effect"

const when = Args.date({ name: "when" })

const command = Command.make("remind", { when }, ({ when }) =>
  Effect.logInfo(when.toISOString())
)
```

Use descriptions to tell users which date format your CLI documents.

## File And Directory

```typescript
import { Args, Command } from "@effect/cli"
import { Effect } from "effect"

const input = Args.file({ name: "input", exists: "yes" })
const output = Args.directory({ name: "output" })

const command = Command.make("copy", { input, output }, ({ input, output }) =>
  Effect.logInfo(`copy ${input} to ${output}`)
)
```

The parser can validate path existence before the handler runs.

## File Text And Content

Use file-reading args when command behavior always needs file contents:

```typescript
import { Args, Command } from "@effect/cli"
import { Effect } from "effect"

const input = Args.fileText({ name: "input" })

const command = Command.make("chars", { input }, ({ input }) => {
  const [path, content] = input
  return Effect.logInfo(`${path} length=${content.length}`)
})
```

For binary input, use `Args.fileContent`.

## File Schema

`Args.fileSchema` reads, parses, and validates a positional file:

```typescript
import { Args, Command } from "@effect/cli"
import { Effect, Schema } from "effect"

const Manifest = Schema.Struct({
  name: Schema.String,
  private: Schema.Boolean
})

const manifest = Args.fileSchema(Manifest, {
  name: "manifest",
  format: "json"
})

const command = Command.make("inspect", { manifest }, ({ manifest }) =>
  Effect.logInfo(`manifest=${manifest.name} private=${manifest.private}`)
)
```

Use `format` for `json`, `yaml`, `ini`, or `toml` content.

## Choice

`Args.choice` maps positional strings to values:

```typescript
import { Args, Command } from "@effect/cli"
import { Effect } from "effect"

const environment = Args.choice([
  ["dev", "development"],
  ["prod", "production"]
] as const, { name: "environment" })

const command = Command.make("deploy", { environment }, ({ environment }) =>
  Effect.logInfo(`environment=${environment}`)
)
```

The parsed value is the second element from the matching tuple.

## Args In Command Config

Args and options can live side by side in the same command config:

```typescript
import { Args, Command, Options } from "@effect/cli"
import { Effect } from "effect"

const command = Command.make(
  "deploy",
  {
    target: Args.text({ name: "target" }),
    dryRun: Options.boolean("dry-run")
  },
  ({ target, dryRun }) => Effect.logInfo(`target=${target} dryRun=${dryRun}`)
)
```

Keep positional args few and obvious. Once order becomes hard to remember, use
named options.

## Cross-references

See also: [03 Options](03-options.md), [06 Args Combinators](06-args-combinators.md), [07 Prompts](07-prompts.md), [08 Subcommands](08-subcommands.md)
