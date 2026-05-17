# Config Overview
Use Effect Config to describe configuration as typed, validated effects instead of reading ambient values in application code.

## Core rule

Do not read `process.env` directly in Effect application, service, or library code.
Use `Config.string("NAME")`, `Config.number("PORT")`, `Config.redacted("API_KEY")`, and composed `Config` values instead.
The default provider already knows how to read the host environment at the runtime edge.
Direct environment access bypasses typed parsing, missing-data errors, validation, test overrides, and redaction.
For the wider anti-pattern, see [process env direct access](../anti-patterns/09-process-env.md).

## What Config is

`Config<A>` is both a description of required configuration and an `Effect<A, ConfigError.ConfigError>`.
You can yield it inside `Effect.gen`.
The value is loaded from the current `ConfigProvider`.
The default provider is installed in Effect's default services.
Tests can replace that provider with `Layer.setConfigProvider`.

```typescript
import { Config, Effect } from "effect"

const ServerConfig = Config.all({
  host: Config.string("HOST"),
  port: Config.integer("PORT")
})

const program = Effect.gen(function*() {
  const server = yield* ServerConfig
  yield* Effect.logInfo(`Starting on ${server.host}:${server.port}`)
})
```

This code has no global read in the body.
The program states what it needs.
The runtime decides where values come from.

## Why it matters

Config moves configuration errors into the Effect error model.
Missing values fail with `ConfigError.MissingData`.
Bad parses fail with `ConfigError.InvalidData`.
Combined configs preserve paths so the error points to the failing key.
Defaults and fallbacks are explicit.
Secrets are redacted by type.

That is the difference between a typed boundary and scattered string lookups.
With scattered lookups, every caller has to remember parsing, defaults, validation, and masking.
With `Config`, the parser is the single source of truth.

## Default provider

Effect installs a default `ConfigProvider.fromEnv()` in its default services.
That is why `yield* Config.string("HOST")` works without passing a provider manually.
The default provider belongs at the runtime boundary.
Do not duplicate it with direct host-environment reads inside business logic.

```typescript
import { Config, Effect } from "effect"

const RequiredHost = Config.string("HOST")

export const program = Effect.gen(function*() {
  const host = yield* RequiredHost
  yield* Effect.logInfo(`Configured host: ${host}`)
})
```

## Loading shape

Primitive constructors parse one value.
Combinators compose primitives into structs, tuples, collections, options, defaults, and validated forms.
Provider combinators adapt naming and source layout.
`Layer.setConfigProvider` changes the source for a scope.

| Need | Use |
|---|---|
| Required text | `Config.string("HOST")` |
| Required number | `Config.number("TIMEOUT")` |
| Required integer | `Config.integer("PORT")` |
| Required boolean | `Config.boolean("FEATURE_ENABLED")` |
| Secret text | `Config.redacted("API_KEY")` |
| Struct | `Config.all({ host, port })` |
| Prefix | `config.pipe(Config.nested("DATABASE"))` |
| Missing value fallback | `config.pipe(Config.withDefault(value))` |
| Test values | `Layer.setConfigProvider(ConfigProvider.fromMap(map))` |

## Boundary pattern

Define configs near the service that needs them.
Read configs while constructing that service.
Pass plain typed values deeper into the implementation.
Only unwrap redacted values at the external boundary that must send them.

```typescript
import { Config, Effect, Redacted } from "effect"

const ApiConfig = Config.all({
  baseUrl: Config.url("API_BASE_URL"),
  apiKey: Config.redacted("API_KEY")
})

const callRemote = (baseUrl: URL, apiKey: string) =>
  Effect.logInfo(`Calling ${baseUrl.origin} with a redacted credential boundary`)

export const program = Effect.gen(function*() {
  const config = yield* ApiConfig
  yield* callRemote(config.baseUrl, Redacted.value(config.apiKey))
})
```

The unwrapped string is not stored on a long-lived domain object.
It exists only for the call that needs the raw credential.

## Naming model

Config paths are path segments.
The default env provider joins segments with `_`.
A nested database config therefore maps to variables such as `DATABASE_HOST` and `DATABASE_PORT`.
`ConfigProvider.fromMap` defaults to `.` for map path segments, but can be configured with `pathDelim: "_"`.

```typescript
import { Config } from "effect"

const DatabaseConfig = Config.all({
  host: Config.string("HOST"),
  port: Config.integer("PORT")
}).pipe(Config.nested("DATABASE"))
```

With the default env provider, the child names are prefixed as `DATABASE_HOST` and `DATABASE_PORT`.
With `ConfigProvider.fromMap(new Map(...))`, use `"DATABASE.HOST"` unless you pass `pathDelim: "_"`.

## Error behavior

Missing data is not the same as invalid data.
`Config.withDefault` and `Config.option` recover from missing data.
They do not hide malformed data.
This is intentional.
A present but invalid port should fail startup rather than silently using a fallback.

```typescript
import { Config } from "effect"

const Port = Config.integer("PORT").pipe(
  Config.validate({
    message: "PORT must be between 1 and 65535",
    validation: (port) => port >= 1 && port <= 65535
  }),
  Config.withDefault(8080)
)
```

If `PORT` is missing, the value is `8080`.
If `PORT` is `"abc"`, loading fails.
If `PORT` is `"70000"`, validation fails.

## Working checklist

- Declare config values with `Config.*` constructors.
- Compose once with `Config.all`.
- Use `Config.nested` for prefixes that belong together.
- Use `Config.redacted` for credentials and tokens.
- Use `Config.validate` for domain constraints.
- Use `Config.withDefault` only for values that are genuinely optional operational defaults.
- Use `Config.option` when absence changes control flow.
- Use `ConfigProvider.fromMap` and `Layer.setConfigProvider` in tests.
- Keep raw environment access at Effect's provider boundary.

## Cross-references

See also: [basic config](02-basic-config.md), [redacted config](03-config-redacted.md), [all and nested](05-config-all-nested.md), [config providers](08-config-providers.md), [test provider layer](09-layer-set-config-provider.md).
