# Options
Parse named command-line inputs with typed `Options` constructors.

## Named Inputs

Options parse named flags and values. The option name maps directly to the long
flag:

| Constructor | CLI syntax | Parsed type |
|---|---|---|
| `Options.boolean("verbose")` | `--verbose` | `boolean` |
| `Options.text("name")` | `--name Ada` | `string` |
| `Options.integer("count")` | `--count 3` | `number` |
| `Options.float("ratio")` | `--ratio 0.5` | `number` |
| `Options.date("when")` | `--when 2026-05-06` | `Date` |
| `Options.redacted("token")` | `--token secret` | `Redacted` |
| `Options.choice("format", values)` | `--format json` | union of choices |
| `Options.file("config")` | `--config ./app.json` | `string` |
| `Options.directory("out")` | `--out ./dist` | `string` |

`Options.text("name")` is not positional. It becomes `--name foo`. Add
`Options.withAlias("n")` to also accept `-n foo`.

## Boolean

Boolean options are flags. Presence controls the parsed value:

```typescript
import { Command, Options } from "@effect/cli"
import { Effect } from "effect"

const verbose = Options.boolean("verbose")

const command = Command.make("scan", { verbose }, ({ verbose }) =>
  Effect.logInfo(`verbose=${verbose}`)
)
```

Use boolean options for mode switches, not for values that have more than two
states. For a small fixed set, use `Options.choice`.

## Text

Text options require a value after the flag:

```typescript
import { Command, Options } from "@effect/cli"
import { Effect } from "effect"

const name = Options.text("name").pipe(
  Options.withDescription("Display name")
)

const command = Command.make("hello", { name }, ({ name }) =>
  Effect.logInfo(`Hello ${name}`)
)
```

Valid invocations include:

```bash
tool hello --name Ada
tool hello --name=Ada
```

With an alias:

```typescript
const name = Options.text("name").pipe(Options.withAlias("n"))
```

Valid invocations include:

```bash
tool hello -n Ada
tool hello --name Ada
```

## Integer And Float

Use numeric parsers before schema validation. They produce `number` and fail
with CLI validation errors when input is not numeric.

```typescript
import { Command, Options } from "@effect/cli"
import { Effect } from "effect"

const command = Command.make(
  "resize",
  {
    width: Options.integer("width"),
    scale: Options.float("scale").pipe(Options.withDefault(1))
  },
  ({ width, scale }) => Effect.logInfo(`width=${width} scale=${scale}`)
)
```

Use `Options.withSchema` when the numeric parser needs a domain constraint.

## Date

`Options.date` parses a `Date` from a named value:

```typescript
import { Command, Options } from "@effect/cli"
import { Effect } from "effect"

const when = Options.date("when")

const command = Command.make("schedule", { when }, ({ when }) =>
  Effect.logInfo(`scheduled=${when.toISOString()}`)
)
```

Keep accepted date formats user-facing in descriptions or examples. The parser
handles conversion, while business rules should remain in the handler or schema
layer.

## Redacted

Use `Options.redacted` for sensitive strings:

```typescript
import { Command, Options } from "@effect/cli"
import { Effect } from "effect"

const token = Options.redacted("token")

const command = Command.make("login", { token }, () =>
  Effect.logInfo("token received")
)
```

Do not convert redacted values to plain strings for logging. Pass them only to
services that require the secret material.

## Choice

Use `Options.choice` when the command accepts a fixed string set:

```typescript
import { Command, Options } from "@effect/cli"
import { Effect } from "effect"

const format = Options.choice("format", ["json", "text"] as const)

const command = Command.make("render", { format }, ({ format }) =>
  Effect.logInfo(`format=${format}`)
)
```

For non-string values, use `Options.choiceWithValue`:

```typescript
import { Command, Options } from "@effect/cli"
import { Effect } from "effect"

const retries = Options.choiceWithValue("retries", [
  ["none", 0],
  ["normal", 3],
  ["aggressive", 10]
] as const)

const command = Command.make("sync", { retries }, ({ retries }) =>
  Effect.logInfo(`retries=${retries}`)
)
```

## Files And Directories

File options parse paths and can require existence:

```typescript
import { Command, Options } from "@effect/cli"
import { Effect } from "effect"

const input = Options.file("input", { exists: "yes" })
const output = Options.directory("output")

const command = Command.make("convert", { input, output }, ({ input, output }) =>
  Effect.logInfo(`input=${input} output=${output}`)
)
```

The `exists` setting is part of `Primitive.PathExists`; use the values accepted
by the source package, including `"yes"` for must-exist paths.

## File Contents

Use file content options when parsing should read the file before the handler:

```typescript
import { Command, Options } from "@effect/cli"
import { Effect } from "effect"

const input = Options.fileText("input")

const command = Command.make("count", { input }, ({ input }) => {
  const [path, content] = input
  return Effect.logInfo(`${path} has ${content.length} characters`)
})
```

For binary content, use `Options.fileContent`.

## File Schema

Use `Options.fileSchema` to read, parse, and validate file content:

```typescript
import { Command, Options } from "@effect/cli"
import { Effect, Schema } from "effect"

const Settings = Schema.Struct({
  name: Schema.String,
  port: Schema.Number
})

const settings = Options.fileSchema("settings", Settings, "json")

const command = Command.make("serve", { settings }, ({ settings }) =>
  Effect.logInfo(`serve ${settings.name} on ${settings.port}`)
)
```

Supported parse formats include `json`, `yaml`, `ini`, and `toml`.

## Cross-references

See also: [04 Options Combinators](04-options-combinators.md), [05 Args](05-args.md), [07 Prompts](07-prompts.md), [10 Config Files](10-config-files.md), [11 Fallbacks](11-fallbacks.md)
