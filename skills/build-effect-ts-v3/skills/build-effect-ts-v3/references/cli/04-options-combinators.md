# Options Combinators
Refine option parsing with aliases, descriptions, defaults, repetition, schema validation, and fallbacks.

## Pipeable Options

Every `Options<A>` is pipeable. Define the primitive parser first, then add
combinators in the order a reader would expect:

```typescript
import { Options } from "@effect/cli"

const name = Options.text("name").pipe(
  Options.withAlias("n"),
  Options.withDescription("Display name"),
  Options.withDefault("world")
)
```

`Options.text("name")` parses `--name Ada`; `Options.withAlias("n")` adds
`-n Ada`.

## Alias

Use `withAlias` for short flags:

```typescript
import { Command, Options } from "@effect/cli"
import { Effect } from "effect"

const verbose = Options.boolean("verbose").pipe(
  Options.withAlias("v")
)

const output = Options.text("output").pipe(
  Options.withAlias("o")
)

const command = Command.make("build", { verbose, output }, ({ verbose, output }) =>
  Effect.logInfo(`verbose=${verbose} output=${output}`)
)
```

Aliases are single names without the dash. The parser supplies `-v` and `-o`
from the alias values.

## Optional

`Options.optional` converts `Options<A>` into `Options<Option<A>>`.

```typescript
import { Command, Options } from "@effect/cli"
import { Effect, Option } from "effect"

const tag = Options.text("tag").pipe(Options.optional)

const command = Command.make("release", { tag }, ({ tag }) =>
  Option.match(tag, {
    onNone: () => Effect.logInfo("release without tag"),
    onSome: (tag) => Effect.logInfo(`release ${tag}`)
  })
)
```

Use `Option.match` to handle both branches explicitly.

## Defaults

`Options.withDefault` supplies a value when the CLI input and all fallbacks are
missing:

```typescript
import { Command, Options } from "@effect/cli"
import { Effect } from "effect"

const retries = Options.integer("retries").pipe(
  Options.withDefault(3)
)

const command = Command.make("sync", { retries }, ({ retries }) =>
  Effect.logInfo(`retries=${retries}`)
)
```

Do not combine `optional` and `withDefault` unless you intentionally want a
union around `Option`.

## Repeated

`Options.repeated` accepts zero or more occurrences and returns `Array<A>`:

```typescript
import { Command, Options } from "@effect/cli"
import { Effect } from "effect"

const tags = Options.text("tag").pipe(Options.repeated)

const command = Command.make("label", { tags }, ({ tags }) =>
  Effect.logInfo(`tags=${tags.join(",")}`)
)
```

Example invocation:

```bash
tool label --tag api --tag stable
```

## At Least, At Most, Between

Use cardinality combinators when repetition has limits:

```typescript
import { Command, Options } from "@effect/cli"
import { Effect } from "effect"

const reviewers = Options.text("reviewer").pipe(
  Options.atLeast(1)
)

const command = Command.make("request-review", { reviewers }, ({ reviewers }) =>
  Effect.logInfo(`reviewers=${reviewers.join(",")}`)
)
```

`Options.atLeast(1)` returns a non-empty array type. `Options.atMost(n)` and
`Options.between(min, max)` return arrays constrained by the parser.

## Schema Validation

Use `Options.withSchema` to decode or refine after primitive parsing:

```typescript
import { Command, Options } from "@effect/cli"
import { Effect, Schema } from "effect"

const port = Options.text("port").pipe(
  Options.withSchema(Schema.NumberFromString)
)

const command = Command.make("serve", { port }, ({ port }) =>
  Effect.logInfo(`port=${port}`)
)
```

This is useful when CLI input starts as text but the domain needs a richer type.

## Map And MapEffect

Use `Options.map` for pure conversion and `Options.mapEffect` when validation
needs platform services:

```typescript
import { Command, Options } from "@effect/cli"
import { Effect } from "effect"

const normalized = Options.text("name").pipe(
  Options.map((name) => name.trim().toLowerCase())
)

const command = Command.make("user", { normalized }, ({ normalized }) =>
  Effect.logInfo(`user=${normalized}`)
)
```

Prefer `withSchema` for reusable domain validation and `map` for local shaping.

## Fallback Config

`Options.withFallbackConfig` reads from the active Effect `ConfigProvider` when
the option is missing.

```typescript
import { Command, Options } from "@effect/cli"
import { Config, Effect } from "effect"

const port = Options.integer("port").pipe(
  Options.withFallbackConfig(Config.integer("PORT")),
  Options.withDefault(3000)
)

const command = Command.make("serve", { port }, ({ port }) =>
  Effect.logInfo(`port=${port}`)
)
```

If `ConfigFile.layer` is provided at runtime, this can read config-file values.

## Fallback Prompt

`Options.withFallbackPrompt` asks interactively if the CLI value and config
fallback are missing:

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

See also: [03 Options](03-options.md), [07 Prompts](07-prompts.md), [10 Config Files](10-config-files.md), [11 Fallbacks](11-fallbacks.md)
