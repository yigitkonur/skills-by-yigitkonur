# Layer Set Config Provider
Use Layer.setConfigProvider to install deterministic ConfigProvider overrides for tests and scoped runtime programs.

## Why a layer override

Most application code should yield `Config` values directly.
That code reads from the current `ConfigProvider`.
`Layer.setConfigProvider(provider)` replaces the current provider for the provided scope.
This is the clean test seam for configuration.

```typescript
import { Config, ConfigProvider, Effect, Layer } from "effect"

const ServerConfig = Config.all({
  host: Config.string("HOST"),
  port: Config.port("PORT")
})

const program = Effect.gen(function*() {
  const server = yield* ServerConfig
  yield* Effect.logInfo(`${server.host}:${server.port}`)
})

const TestConfigLayer = Layer.setConfigProvider(
  ConfigProvider.fromMap(
    new Map([
      ["HOST", "127.0.0.1"],
      ["PORT", "3000"]
    ]),
    { pathDelim: "_" }
  )
)

export const testProgram = program.pipe(
  Effect.provide(TestConfigLayer)
)
```

The production program is unchanged.
The test installs a deterministic provider.

## Complete test-layer pattern

Use this complete pattern in tests.
Define the config once.
Define the program against that config.
Build a `ConfigProvider.fromMap`.
Install it with `Layer.setConfigProvider`.
Run the program with the layer.

```typescript
import { describe, it, expect } from "@effect/vitest"
import { Config, ConfigProvider, Effect, Layer, Redacted } from "effect"

const AppConfig = Config.all({
  database: Config.all({
    host: Config.string("HOST"),
    port: Config.port("PORT")
  }).pipe(Config.nested("DATABASE")),
  apiKey: Config.redacted("API_KEY")
})

const makeConnectionLabel = Effect.gen(function*() {
  const config = yield* AppConfig
  const rawKey = Redacted.value(config.apiKey)
  return `${config.database.host}:${config.database.port}:${rawKey.length}`
})

const TestConfigLayer = Layer.setConfigProvider(
  ConfigProvider.fromMap(
    new Map([
      ["DATABASE_HOST", "localhost"],
      ["DATABASE_PORT", "5432"],
      ["API_KEY", "test-secret"]
    ]),
    { pathDelim: "_" }
  )
)

describe("makeConnectionLabel", () => {
  it.effect("uses test config provider", () =>
    Effect.gen(function*() {
      const label = yield* makeConnectionLabel.pipe(
        Effect.provide(TestConfigLayer)
      )

      expect(label).toBe("localhost:5432:11")
    }))
})
```

This example intentionally uses env-style test keys.
`Config.nested("DATABASE")` prefixes child names as `DATABASE_HOST` and `DATABASE_PORT` under the underscore delimiter.
The redacted value is unwrapped only at the boundary that needs the raw key length.

## Scoped override

`Layer.setConfigProvider` is scoped through normal layer provision.
The override applies to the effect it provides.
Other tests or programs can use different providers.

```typescript
import { Config, ConfigProvider, Effect, Layer } from "effect"

const Name = Config.string("NAME")

const readName = Effect.gen(function*() {
  return yield* Name
})

const AliceLayer = Layer.setConfigProvider(
  ConfigProvider.fromMap(new Map([["NAME", "alice"]]), { pathDelim: "_" })
)

const BobLayer = Layer.setConfigProvider(
  ConfigProvider.fromMap(new Map([["NAME", "bob"]]), { pathDelim: "_" })
)

export const both = Effect.all([
  readName.pipe(Effect.provide(AliceLayer)),
  readName.pipe(Effect.provide(BobLayer))
], { concurrency: 2 })
```

Each effect receives the provider from its own provided layer.
No global mutation is required.

## Checklist

- Build test values with `ConfigProvider.fromMap`.
- Use `{ pathDelim: "_" }` when map keys mirror env-style names.
- Install the provider with `Layer.setConfigProvider`.
- Provide the layer to the effect or service layer that reads config.
- Keep production config definitions unchanged for tests.
- Keep redacted values redacted until the test assertion or external boundary.
- Avoid global mutation for config tests.

## Cross-references

See also: [overview](01-overview.md), [redacted config](03-config-redacted.md), [all and nested](05-config-all-nested.md), [providers](08-config-providers.md).
