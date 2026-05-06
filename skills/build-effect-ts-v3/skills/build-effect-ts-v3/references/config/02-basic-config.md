# Basic Config
Use primitive Config constructors to parse strings, numbers, booleans, integers, literals, URLs, durations, dates, ports, and log levels.

## Primitive constructors

Primitive constructors create a `Config<A>` for one value.
The optional `name` is the key read from the current provider.
When the name is omitted, collection constructors or nesting can provide the path.
Every primitive parser returns typed data or a `ConfigError`.

| Constructor | Type | Notes |
|---|---|---|
| `Config.string(name)` | `string` | Required text value |
| `Config.nonEmptyString(name)` | `string` | Fails on empty text |
| `Config.number(name)` | `number` | Floating-point number |
| `Config.integer(name)` | `number` | Integer only |
| `Config.boolean(name)` | `boolean` | Boolean parser |
| `Config.literal(...)(name)` | literal union | Whitelist of allowed values |
| `Config.port(name)` | `number` | Network port in range 1 through 65535 |
| `Config.url(name)` | `URL` | Parsed `URL` instance |
| `Config.date(name)` | `Date` | Parsed date |
| `Config.duration(name)` | `Duration.Duration` | Parsed duration |
| `Config.logLevel(name)` | `LogLevel.LogLevel` | Parsed Effect log level |

## Reading inside Effect

`Config` is an Effect.
Yield it directly inside `Effect.gen`.
Do not pre-read values into constants outside the Effect runtime.

```typescript
import { Config, Effect } from "effect"

const Host = Config.string("HOST")
const Port = Config.integer("PORT")

export const program = Effect.gen(function*() {
  const host = yield* Host
  const port = yield* Port
  yield* Effect.logInfo(`Listening on ${host}:${port}`)
})
```

The host and port are loaded when the program runs.
This keeps tests able to replace the provider.

## Strings

Use `Config.string` for free-form required text.
Use `Config.nonEmptyString` when an empty value is not meaningful.
Validation can add domain-specific constraints after parsing.

```typescript
import { Config } from "effect"

const ServiceName = Config.nonEmptyString("SERVICE_NAME")

const Region = Config.string("AWS_REGION").pipe(
  Config.validate({
    message: "AWS_REGION must start with us-, eu-, or ap-",
    validation: (region) =>
      region.startsWith("us-") ||
      region.startsWith("eu-") ||
      region.startsWith("ap-")
  })
)
```

Use names that match the provider's source layout.
For the default env provider, uppercase underscore names are conventional.
For `fromMap`, the map key must match the provider path rules.

## Numbers and integers

Use `Config.number` for decimal values.
Use `Config.integer` for counts, ports when not using `Config.port`, worker limits, and retry counts.
Parsing is strict enough to fail malformed values instead of returning a default.

```typescript
import { Config } from "effect"

const RuntimeTuning = Config.all({
  requestTimeoutMs: Config.number("REQUEST_TIMEOUT_MS"),
  workerCount: Config.integer("WORKER_COUNT")
})
```

`Config.integer("WORKER_COUNT")` rejects decimal strings.
`Config.number("REQUEST_TIMEOUT_MS")` accepts valid numeric text.
Domain ranges still belong in `Config.validate`.

## Ports

Use `Config.port` when the value is a TCP or HTTP port.
It documents intent and enforces the valid port range.

```typescript
import { Config } from "effect"

const HttpConfig = Config.all({
  host: Config.string("HTTP_HOST"),
  port: Config.port("HTTP_PORT")
})
```

Use `Config.integer` only when the number is not semantically a network port.
That keeps error messages and documentation aligned with the domain.

## Booleans

Use `Config.boolean` for feature flags and operational switches.
Keep the parsed value as a boolean, not a string union.
If the source needs multiple modes, use `Config.literal` instead.

```typescript
import { Config } from "effect"

const Flags = Config.all({
  enableTracing: Config.boolean("ENABLE_TRACING"),
  enableCache: Config.boolean("ENABLE_CACHE")
})
```

A boolean flag answers one yes-or-no question.
Do not overload one flag with multiple meanings.

## Literals

`Config.literal` creates a config that accepts only listed literal values.
It returns a narrow union, so downstream code can switch exhaustively.

```typescript
import { Config } from "effect"

const RuntimeMode = Config.literal("development", "staging", "production")("RUNTIME_MODE")

const Transport = Config.literal("http", "grpc")("TRANSPORT")
```

Use literals for operational modes that are intentionally finite.
Prefer literals over free-form strings plus ad hoc comparisons later.

## URLs, dates, durations, and log levels

Use specialized parsers when the domain has a standard representation.
They document the expected shape at the config boundary.

```typescript
import { Config } from "effect"

const ClientConfig = Config.all({
  baseUrl: Config.url("BASE_URL"),
  expiresAt: Config.date("EXPIRES_AT"),
  requestTimeout: Config.duration("REQUEST_TIMEOUT"),
  minimumLogLevel: Config.logLevel("LOG_LEVEL")
})
```

Keep in mind that `URL`, `Date`, `Duration`, and `LogLevel` are already parsed values.
Do not parse them a second time in service code.

## Combining primitives

Use `Config.all` to load several primitives as one struct.
The resulting type is inferred from each field.
This is the common shape for service configuration.

```typescript
import { Config } from "effect"

export const MailerConfig = Config.all({
  smtpHost: Config.string("SMTP_HOST"),
  smtpPort: Config.port("SMTP_PORT"),
  sender: Config.nonEmptyString("MAIL_SENDER"),
  retries: Config.integer("MAIL_RETRIES")
})
```

The exported value is still a `Config`.
It is not loaded until yielded.

## Naming guidelines

- Name keys for the source, not the TypeScript property.
- Keep TypeScript properties idiomatic camel case.
- Keep env-style keys uppercase with underscores.
- Use `Config.nested` when several keys share a prefix.
- Use provider casing transforms when the source uses a different convention.
- Keep the key string stable; it is an external contract.

## Common mistakes

- Using `Config.string` and parsing numbers later.
- Using `Config.number` for a value that must be an integer.
- Using a free-form string for an enum-like mode.
- Reading primitive configs at module initialization.
- Adding defaults before deciding whether a missing value is actually valid.
- Logging a loaded credential as a normal string.

## Cross-references

See also: [overview](01-overview.md), [validation](06-config-validation.md), [defaults and fallbacks](07-config-withDefault.md), [all and nested](05-config-all-nested.md).
