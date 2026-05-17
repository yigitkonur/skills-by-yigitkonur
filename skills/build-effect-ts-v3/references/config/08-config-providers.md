# Config Providers
Use ConfigProvider to control where Config values are loaded from and how config paths map to source keys.

## Provider role

A `ConfigProvider` loads a `Config<A>` into an `Effect<A, ConfigError.ConfigError>`.
Effect's default services install `ConfigProvider.fromEnv()`.
Most application code should define `Config` values and let the current provider load them.
Tests and custom runtimes can replace the provider.

```typescript
import { Config, ConfigProvider, Effect } from "effect"

const Host = Config.string("HOST")

const program = Effect.gen(function*() {
  const provider = ConfigProvider.fromMap(new Map([["HOST", "localhost"]]), {
    pathDelim: "_"
  })
  const host = yield* provider.load(Host)
  yield* Effect.logInfo(`Loaded ${host}`)
})
```

Direct `provider.load` is useful for examples and tests.
Application programs normally yield the config and provide the provider as a layer.

## fromEnv

`ConfigProvider.fromEnv()` creates a provider that loads from the host environment.
Its options are `pathDelim` and `seqDelim`.
The default path delimiter is `_`.
The default sequence delimiter is `,`.

```typescript
import { ConfigProvider } from "effect"

const provider = ConfigProvider.fromEnv({
  pathDelim: "_",
  seqDelim: ","
})
```

Use this at the runtime edge when you need to customize delimiters.
Do not call host environment APIs throughout the codebase.

## fromMap

`ConfigProvider.fromMap` is the standard test provider.
It loads from a flat `Map<string, string>`.
Its options are also `pathDelim` and `seqDelim`.
The default map path delimiter is `.`.

```typescript
import { Config, ConfigProvider, Effect } from "effect"

const Database = Config.all({
  host: Config.string("HOST"),
  port: Config.port("PORT")
}).pipe(Config.nested("DATABASE"))

const program = Effect.gen(function*() {
  const provider = ConfigProvider.fromMap(
    new Map([
      ["DATABASE.HOST", "localhost"],
      ["DATABASE.PORT", "5432"]
    ])
  )
  const database = yield* provider.load(Database)
  yield* Effect.logInfo(`Database ${database.host}:${database.port}`)
})
```

The same config maps to `DATABASE_HOST` with the default env provider.
For `fromMap`, use dotted paths unless you configure `pathDelim: "_"`.

## fromMap with env-style keys

When you want test maps to mirror env key names exactly, configure the delimiter.

```typescript
import { Config, ConfigProvider, Effect } from "effect"

const Database = Config.all({
  host: Config.string("HOST"),
  port: Config.port("PORT")
}).pipe(Config.nested("DATABASE"))

const program = Effect.gen(function*() {
  const provider = ConfigProvider.fromMap(
    new Map([
      ["DATABASE_HOST", "localhost"],
      ["DATABASE_PORT", "5432"]
    ]),
    { pathDelim: "_" }
  )
  const database = yield* provider.load(Database)
  yield* Effect.logInfo(`Database ${database.host}:${database.port}`)
})
```

This is often the clearest test shape when production uses env-style names.

## Sequence delimiter

The `seqDelim` option controls simple delimited collections.
Use it when your source encodes arrays, chunks, or sets as one string.

```typescript
import { Config, ConfigProvider, Effect } from "effect"

const Origins = Config.array(Config.string(), "ALLOWED_ORIGINS")

const program = Effect.gen(function*() {
  const provider = ConfigProvider.fromMap(
    new Map([["ALLOWED_ORIGINS", "https://a.example|https://b.example"]]),
    { seqDelim: "|" }
  )
  const origins = yield* provider.load(Origins)
  yield* Effect.logInfo(`Loaded ${origins.length} origins`)
})
```

Prefer a delimiter that cannot naturally appear unescaped in the values.

## Casing transforms

Provider transforms adapt config path names to source naming conventions.
They return a new provider.

| Transform | Purpose |
|---|---|
| `ConfigProvider.constantCase` | Convert path names to constant case |
| `ConfigProvider.kebabCase` | Convert path names to kebab case |
| `ConfigProvider.lowerCase` | Convert path names to lower case |
| `ConfigProvider.snakeCase` | Convert path names to snake case |
| `ConfigProvider.upperCase` | Convert path names to upper case |
| `ConfigProvider.mapInputPath` | Apply a custom path transform |

```typescript
import { Config, ConfigProvider, Effect } from "effect"

const provider = ConfigProvider.fromMap(new Map([["snake_case", "value"]])).pipe(
  ConfigProvider.snakeCase
)

const program = Effect.gen(function*() {
  const value = yield* provider.load(Config.string("snakeCase"))
  yield* Effect.logInfo(value)
})
```

Use transforms at the provider boundary instead of contorting every config key.

## Provider fallback

`ConfigProvider.orElse` lets one provider fall back to another.
This is useful for runtime composition, migration, or layered local defaults.

```typescript
import { Config, ConfigProvider, Effect } from "effect"

const primary = ConfigProvider.fromMap(new Map([["HOST", "primary"]]), {
  pathDelim: "_"
})

const fallback = ConfigProvider.fromMap(new Map([["PORT", "8080"]]), {
  pathDelim: "_"
})

const provider = primary.pipe(
  ConfigProvider.orElse(() => fallback)
)

const program = Effect.gen(function*() {
  const config = yield* provider.load(Config.all({
    host: Config.string("HOST"),
    port: Config.port("PORT")
  }))
  yield* Effect.logInfo(`${config.host}:${config.port}`)
})
```

If both providers fail, the failure preserves both causes.

## Checklist

- Use `fromEnv` at the runtime edge.
- Use `fromMap` for tests.
- Remember `fromMap` defaults to dot path segments.
- Pass `{ pathDelim: "_" }` when a test map uses env-style keys.
- Use casing transforms at the provider boundary.
- Use provider fallback only when source order is intentional.
- Prefer `Layer.setConfigProvider` to install providers for whole programs.

## Cross-references

See also: [overview](01-overview.md), [all and nested](05-config-all-nested.md), [collections](04-config-collections.md), [test provider layer](09-layer-set-config-provider.md).
