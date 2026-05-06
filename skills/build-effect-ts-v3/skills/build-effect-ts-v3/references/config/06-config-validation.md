# Config Validation
Use Config.validate and Config.option to model domain constraints and intentional missing values at the configuration boundary.

## Validation belongs at the boundary

Parsing proves that a value has the right primitive type.
Validation proves that the typed value is acceptable for your domain.
Put both in the `Config` definition so invalid startup state fails before services run.

```typescript
import { Config } from "effect"

const WorkerCount = Config.integer("WORKER_COUNT").pipe(
  Config.validate({
    message: "WORKER_COUNT must be between 1 and 64",
    validation: (count) => count >= 1 && count <= 64
  })
)
```

Downstream code can now treat the value as already checked.
It does not need to repeat range guards.

## Predicate validation

The common form accepts a message and a predicate.
When the predicate returns `false`, loading fails with invalid data at the original path.

```typescript
import { Config } from "effect"

const PoolSize = Config.integer("DB_POOL_SIZE").pipe(
  Config.validate({
    message: "DB_POOL_SIZE must be positive",
    validation: (size) => size > 0
  })
)
```

Use messages that tell the operator how to fix the value.
Avoid vague messages such as `invalid config`.

## Validate after parse

Validation receives the parsed value, not the raw source text.
Use typed operations in the predicate.

```typescript
import { Config } from "effect"

const TimeoutMs = Config.number("TIMEOUT_MS").pipe(
  Config.validate({
    message: "TIMEOUT_MS must be a finite positive number",
    validation: (timeout) => Number.isFinite(timeout) && timeout > 0
  })
)
```

Do not parse the string manually in the validation function.
Choose the right primitive parser first.

## Whole-struct validation

Validate a composed config when the rule involves more than one field.
This keeps cross-field constraints in one place.

```typescript
import { Config } from "effect"

const CacheConfig = Config.all({
  minimumTtlMs: Config.integer("CACHE_MIN_TTL_MS"),
  maximumTtlMs: Config.integer("CACHE_MAX_TTL_MS")
}).pipe(
  Config.validate({
    message: "CACHE_MAX_TTL_MS must be greater than or equal to CACHE_MIN_TTL_MS",
    validation: (config) => config.maximumTtlMs >= config.minimumTtlMs
  })
)
```

The rule belongs to the struct because neither field can validate it alone.

## Config.option

`Config.option(config)` converts missing data into `Option.none()`.
If the value is present but invalid, loading still fails.
That distinction is important.

```typescript
import { Config, Effect, Option } from "effect"

const ProxyUrl = Config.option(Config.url("PROXY_URL"))

export const program = Effect.gen(function*() {
  const proxyUrl = yield* ProxyUrl
  const label = Option.match(proxyUrl, {
    onNone: () => "no proxy configured",
    onSome: (url) => `proxy configured at ${url.origin}`
  })
  yield* Effect.logInfo(label)
})
```

Use `Option.match`.
Do not force optional config with unsafe extraction.

## Optional structs

Wrap the whole struct with `Config.option` when the group is optional as a unit.
Wrap individual fields when each field is independently optional.

```typescript
import { Config } from "effect"

const AwsCredentials = Config.option(
  Config.all({
    accessKeyId: Config.redacted("AWS_ACCESS_KEY_ID"),
    secretAccessKey: Config.redacted("AWS_SECRET_ACCESS_KEY")
  })
)
```

This says credentials are absent unless the required group can be read.
If one field is present but malformed, loading fails.

## Optional with nested config

Optional groups compose naturally with nesting.
Apply `Config.nested` inside the optional wrapper when the group lives under a prefix.

```typescript
import { Config } from "effect"

const OptionalDatabase = Config.option(
  Config.all({
    host: Config.string("HOST"),
    port: Config.port("PORT")
  }).pipe(Config.nested("DATABASE"))
)
```

With the default env provider, the keys are `DATABASE_HOST` and `DATABASE_PORT`.
Missing data becomes `Option.none()`.
Invalid data remains a failure.

## Validation versus defaults

`Config.withDefault` handles missing data.
`Config.validate` handles unacceptable data.
Use both when needed, but keep their jobs separate.

```typescript
import { Config } from "effect"

const Port = Config.port("PORT").pipe(
  Config.withDefault(8080),
  Config.validate({
    message: "PORT must not be 0",
    validation: (port) => port !== 0
  })
)
```

For `Config.port`, the range already excludes zero.
The example shows composition; avoid redundant validation in real code.

## Checklist

- Parse with the most specific primitive constructor first.
- Validate domain constraints after parsing or composition.
- Use whole-struct validation for cross-field rules.
- Use `Config.option` only for meaningful absence.
- Treat invalid present values as failures.
- Use `Option.match` to consume optional config.
- Write actionable validation messages.

## Cross-references

See also: [basic config](02-basic-config.md), [defaults and fallbacks](07-config-withDefault.md), [collections](04-config-collections.md), [all and nested](05-config-all-nested.md).
