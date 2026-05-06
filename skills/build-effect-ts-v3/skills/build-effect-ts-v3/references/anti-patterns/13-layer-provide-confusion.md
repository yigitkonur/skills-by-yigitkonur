# Layer Provide Confusion
Use this when Layer.provide removes a provider output that the final layer was expected to keep.

## Symptom — Bad Code
```typescript
import { Context, Effect, Layer } from "effect"

class Config extends Context.Tag("Config")<Config, { readonly url: string }>() {}
class Logger extends Context.Tag("Logger")<Logger, { readonly log: (message: string) => Effect.Effect<void> }>() {}
class Database extends Context.Tag("Database")<Database, { readonly query: Effect.Effect<string> }>() {}

const ConfigLive = Layer.succeed(Config, { url: "db://local" })
const LoggerLive = Layer.effect(Logger, Effect.gen(function* () {
  const _config = yield* Config
  return { log: (_message: string) => Effect.void }
}))
const DatabaseLive = Layer.effect(Database, Effect.gen(function* () {
  const _config = yield* Config
  const _logger = yield* Logger
  return { query: Effect.succeed("ok") }
}))

const AppConfigLive = Layer.merge(ConfigLive, LoggerLive)

const MainLive: Layer.Layer<Config | Database, never, never> = DatabaseLive.pipe(
  Layer.provide(AppConfigLive),
  Layer.provide(ConfigLive)
)
```

Exact TypeScript error:

```text
layer-error.ts(26,7): error TS2322: Type 'Layer<Database, never, never>' is not assignable to type 'Layer<Config | Database, never, never>'.
  Type 'Config | Database' is not assignable to type 'Database'.
    Type 'Config' is not assignable to type 'Database'.
      Types of property 'Id' are incompatible.
        Type '"Config"' is not assignable to type '"Database"'.
```

## Why Bad
`Layer.provide` feeds provider output into the target layer and exposes only the target layer output.
The annotation expects both `Config` and `Database`, but the composition exposes only `Database`.
Use `Layer.provideMerge` when the provider must satisfy requirements and remain in the final output.

## Fix — Correct Pattern
```typescript
import { Context, Effect, Layer } from "effect"

class Config extends Context.Tag("Config")<Config, { readonly url: string }>() {}
class Logger extends Context.Tag("Logger")<Logger, { readonly log: (message: string) => Effect.Effect<void> }>() {}
class Database extends Context.Tag("Database")<Database, { readonly query: Effect.Effect<string> }>() {}

const ConfigLive = Layer.succeed(Config, { url: "db://local" })
const LoggerLive = Layer.effect(Logger, Effect.gen(function* () {
  const _config = yield* Config
  return { log: (_message: string) => Effect.void }
}))
const DatabaseLive = Layer.effect(Database, Effect.gen(function* () {
  const _config = yield* Config
  const _logger = yield* Logger
  return { query: Effect.succeed("ok") }
}))

const AppConfigLive = Layer.merge(ConfigLive, LoggerLive)

const MainLive: Layer.Layer<Config | Database, never, never> = DatabaseLive.pipe(
  Layer.provide(AppConfigLive),
  Layer.provideMerge(ConfigLive)
)
```

## Notes
Read [services-layers/12-layer-composition-gotchas.md](../services-layers/12-layer-composition-gotchas.md). Use `Layer.provide` for dependency feeding, `Layer.provideMerge` for dependency feeding plus output retention, and `Layer.merge` for independent outputs.

## Cross-references
See also: [layer composition gotchas](../services-layers/12-layer-composition-gotchas.md), [layer composition](../services-layers/09-layer-merge.md), [context tags](../services-layers/02-context-tag.md).
