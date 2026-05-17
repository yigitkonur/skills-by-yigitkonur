# Config Defaults And Fallbacks
Use Config.withDefault, Config.orElse, and Config.orElseIf to model missing-data defaults and alternate configuration sources explicitly.

## withDefault

`Config.withDefault(defaultValue)` recovers from missing data.
It does not recover from invalid data.
That is the correct behavior for startup configuration.

```typescript
import { Config, Effect } from "effect"

const Port = Config.port("PORT").pipe(
  Config.withDefault(8080)
)

export const program = Effect.gen(function*() {
  const port = yield* Port
  yield* Effect.logInfo(`Using port ${port}`)
})
```

If `PORT` is missing, the value is `8080`.
If `PORT` is malformed, the program fails during config loading.

## Choose defaults deliberately

A default is a production behavior.
Use it when the application can safely run without the source value.
Do not add defaults simply to make tests or local startup easier.
Tests should override the provider.

Good candidates are local bind hosts, feature flags, retry counts, optional allow-lists, and log levels.
Poor candidates are credentials, API keys, payment endpoints, tenant identifiers, and security modes.

## Default after validation

When using a specialized constructor, the default should already satisfy the same domain.
With `Config.port`, the default must be a valid port.

```typescript
import { Config } from "effect"

const HttpConfig = Config.all({
  host: Config.string("HTTP_HOST").pipe(Config.withDefault("127.0.0.1")),
  port: Config.port("HTTP_PORT").pipe(Config.withDefault(3000))
})
```

The default value is typed by TypeScript.
Still choose a value that is operationally safe.

## Defaults for structs

Default a field when the field is optional.
Default the whole struct only when the entire group has a valid fallback.

```typescript
import { Config } from "effect"

const CacheConfig = Config.all({
  enabled: Config.boolean("CACHE_ENABLED").pipe(Config.withDefault(true)),
  ttlMs: Config.integer("CACHE_TTL_MS").pipe(Config.withDefault(60_000))
})
```

This keeps each field's default visible.
It also avoids hiding partial misconfiguration for a whole group.

## orElse

`Config.orElse` tries the first config and falls back to another config if the first fails.
The fallback is lazy.
Use it for migrations between key names or provider layouts.

```typescript
import { Config } from "effect"

const Port = Config.port("HTTP_PORT").pipe(
  Config.orElse(() => Config.port("PORT"))
)
```

This prefers `HTTP_PORT`.
If it cannot be read, it tries `PORT`.
Use this sparingly and remove migration fallbacks after the migration window.

## orElse with defaults

Combine `orElse` and `withDefault` when there is a preferred key, a legacy key, and a safe final default.

```typescript
import { Config } from "effect"

const Host = Config.string("HTTP_HOST").pipe(
  Config.orElse(() => Config.string("HOST")),
  Config.withDefault("127.0.0.1")
)
```

The order is important.
The config tries both source keys before using the default.

## orElseIf

`Config.orElseIf` falls back only when the error satisfies a predicate.
Use it when only specific failure modes should recover.
The predicate receives a `ConfigError.ConfigError`.

```typescript
import { Config, ConfigError } from "effect"

const Host = Config.string("PRIMARY_HOST").pipe(
  Config.orElseIf({
    if: ConfigError.isMissingDataOnly,
    orElse: () => Config.string("SECONDARY_HOST")
  })
)
```

This preserves invalid-data failures from the primary key.
Use it when broad `orElse` would hide bad input.

## Optional versus default

Use `Config.option` when the program has different logic for absence.
Use `Config.withDefault` when absence should become a concrete value immediately.

```typescript
import { Config } from "effect"

const OptionalProxy = Config.option(Config.url("PROXY_URL"))

const TracingEnabled = Config.boolean("TRACING_ENABLED").pipe(
  Config.withDefault(false)
)
```

The proxy URL controls a branch.
The tracing flag has a direct default.

## Checklist

- Use `withDefault` only for missing data.
- Do not expect `withDefault` to recover from invalid data.
- Prefer provider overrides for tests.
- Use `orElse` for intentional key migrations.
- Use `orElseIf` when only selected failures should recover.
- Use `Config.option` when absence is part of business flow.
- Avoid defaults for secrets and required external endpoints.

## Cross-references

See also: [overview](01-overview.md), [validation](06-config-validation.md), [providers](08-config-providers.md), [test provider layer](09-layer-set-config-provider.md).
