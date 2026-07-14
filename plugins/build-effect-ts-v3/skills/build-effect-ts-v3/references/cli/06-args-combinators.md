# Args Combinators
Refine positional parsing with optionality, repetition, defaults, schema validation, and config fallback.

## Pipeable Args

Like options, args are pipeable:

```typescript
import { Args } from "@effect/cli"

const target = Args.text({ name: "target" }).pipe(
  Args.withDescription("Deployment target"),
  Args.withDefault("local")
)
```

Use the primitive constructor first, then add combinators.

## Optional

`Args.optional` converts a positional parser to `Option<A>`:

```typescript
import { Args, Command } from "@effect/cli"
import { Effect, Option } from "effect"

const directory = Args.directory({ name: "directory" }).pipe(
  Args.optional
)

const command = Command.make("init", { directory }, ({ directory }) =>
  Option.match(directory, {
    onNone: () => Effect.logInfo("init current directory"),
    onSome: (directory) => Effect.logInfo(`init ${directory}`)
  })
)
```

Use this for truly optional trailing positional values.

## Default

`Args.withDefault` supplies a static value if the arg is missing:

```typescript
import { Args, Command } from "@effect/cli"
import { Effect } from "effect"

const directory = Args.directory({ name: "directory" }).pipe(
  Args.withDefault(".")
)

const command = Command.make("init", { directory }, ({ directory }) =>
  Effect.logInfo(`directory=${directory}`)
)
```

Defaults are easier for handlers than `Option` when there is a natural value.

## Repeated

`Args.repeated` parses zero or more positional values:

```typescript
import { Args, Command } from "@effect/cli"
import { Effect } from "effect"

const files = Args.file({ name: "file", exists: "yes" }).pipe(
  Args.repeated
)

const command = Command.make("format", { files }, ({ files }) =>
  Effect.logInfo(`files=${files.join(",")}`)
)
```

Use repeated args only at the end of a command; otherwise later positional
parsers become ambiguous.

## At Least And Bounds

Use cardinality combinators when repeated values have limits:

```typescript
import { Args, Command } from "@effect/cli"
import { Effect } from "effect"

const files = Args.file({ name: "file", exists: "yes" }).pipe(
  Args.atLeast(1)
)

const command = Command.make("archive", { files }, ({ files }) =>
  Effect.logInfo(`archive ${files.join(",")}`)
)
```

`Args.atLeast(1)` returns a non-empty array type. `Args.atMost(n)` and
`Args.between(min, max)` return arrays checked by the parser.

## Schema Validation

Use `Args.withSchema` when the raw positional parser is too broad:

```typescript
import { Args, Command } from "@effect/cli"
import { Effect, Schema } from "effect"

const count = Args.text({ name: "count" }).pipe(
  Args.withSchema(Schema.NumberFromString)
)

const command = Command.make("take", { count }, ({ count }) =>
  Effect.logInfo(`count=${count}`)
)
```

Prefer schema validation for reusable domain types.

## Config Fallback

`Args.withFallbackConfig` lets an arg come from Effect `Config` if the
positional value is omitted:

```typescript
import { Args, Command } from "@effect/cli"
import { Config, Effect } from "effect"

const repository = Args.text({ name: "repository" }).pipe(
  Args.withFallbackConfig(Config.string("REPOSITORY"))
)

const command = Command.make("clone", { repository }, ({ repository }) =>
  Effect.logInfo(`repository=${repository}`)
)
```

This works with any active `ConfigProvider`, including `ConfigFile.layer`.

## Description

Descriptions are important for positional args because users cannot infer them
from flag names:

```typescript
import { Args } from "@effect/cli"

const target = Args.text({ name: "target" }).pipe(
  Args.withDescription("Deployment target name")
)
```

Keep descriptions short; generated usage already shows the positional shape.

## Repetition With Defaults

For repeated args, prefer an empty array over a default sentinel:

```typescript
import { Args } from "@effect/cli"

const tags = Args.text({ name: "tag" }).pipe(Args.repeated)
```

The absence of values is represented by `[]`. Add `Args.atLeast(1)` when absence
is invalid.

## Cross-references

See also: [05 Args](05-args.md), [03 Options](03-options.md), [10 Config Files](10-config-files.md), [11 Fallbacks](11-fallbacks.md)
