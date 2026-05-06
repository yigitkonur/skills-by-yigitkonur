# Redacted Config
Use Config.redacted for secrets and unwrap with Redacted.value only at the external boundary that requires the raw value.

## The rule

Credentials, tokens, passwords, signing keys, and API keys must be loaded with `Config.redacted`.
The loaded value is `Redacted.Redacted`.
Do not convert it to a string for logging, debugging, config snapshots, or domain objects.
Only call `Redacted.value` at the exact boundary where the raw secret must be passed to an external client.

```typescript
import { Config, Effect, Redacted } from "effect"

const ApiKey = Config.redacted("API_KEY")

const sendRequest = (apiKey: string) =>
  Effect.logInfo("Sending request with configured credential")

export const program = Effect.gen(function*() {
  yield* sendRequest(Redacted.value(yield* ApiKey))
})
```

This is the mission-critical pattern.
The unwrap is local to the boundary call.

## Basic redacted value

Passing a name to `Config.redacted` reads a string and wraps it.
The type is `Config.Config<Redacted.Redacted>`.
Effect's redacted value prints safely.
The underlying value is still available through explicit unwrap.

```typescript
import { Config, Effect } from "effect"

const Credentials = Config.all({
  apiKey: Config.redacted("API_KEY"),
  signingSecret: Config.redacted("SIGNING_SECRET")
})

export const program = Effect.gen(function*() {
  const credentials = yield* Credentials
  yield* Effect.logInfo(`Loaded credentials: ${credentials.apiKey}`)
})
```

The log line does not expose the underlying secret value.
Still, prefer logging that credentials were loaded rather than logging the redacted object repeatedly.

## Redacting a validated config

`Config.redacted` also accepts another `Config<A>`.
That form validates or parses first, then wraps the typed value.
Use it when the secret is not just arbitrary text.

```typescript
import { Config, Effect, Redacted } from "effect"

const NumericSecret = Config.redacted(Config.integer("NUMERIC_SECRET"))

const useSecretNumber = (secret: number) =>
  Effect.logInfo(`Using numeric secret length marker: ${String(secret).length}`)

export const program = Effect.gen(function*() {
  const secret = yield* NumericSecret
  yield* useSecretNumber(Redacted.value(secret))
})
```

If the source value cannot parse as an integer, loading fails before redaction succeeds.
That is useful for secrets that are IDs, numeric pins, URLs, or structured values.

## Boundary-only unwrap

The best shape is to keep service configuration redacted and unwrap inside the client constructor or call adapter.
Do not spread raw secrets through the service graph.

```typescript
import { Config, Effect, Redacted } from "effect"

interface HttpClient {
  readonly get: (path: string) => Effect.Effect<string>
}

const makeClient = (options: {
  readonly baseUrl: URL
  readonly apiKey: string
}): HttpClient => ({
  get: (path) =>
    Effect.succeed(`GET ${options.baseUrl.origin}${path} with configured auth`)
})

const ClientConfig = Config.all({
  baseUrl: Config.url("API_BASE_URL"),
  apiKey: Config.redacted("API_KEY")
})

export const makeConfiguredClient = Effect.gen(function*() {
  const config = yield* ClientConfig
  return makeClient({
    baseUrl: config.baseUrl,
    apiKey: Redacted.value(config.apiKey)
  })
})
```

After construction, avoid returning the raw key in public service state.
If the client library stores it internally, keep that storage outside your application domain model.

## Redacted inside structs

Most real services have both normal and sensitive fields.
Use a struct config and keep the secret field redacted.

```typescript
import { Config, Effect, Redacted } from "effect"

const PaymentConfig = Config.all({
  endpoint: Config.url("PAYMENT_ENDPOINT"),
  merchantId: Config.nonEmptyString("PAYMENT_MERCHANT_ID"),
  secret: Config.redacted("PAYMENT_SECRET")
})

const authorize = (endpoint: URL, merchantId: string, secret: string) =>
  Effect.logInfo(`Authorizing merchant ${merchantId} at ${endpoint.origin}`)

export const program = Effect.gen(function*() {
  const config = yield* PaymentConfig
  yield* authorize(
    config.endpoint,
    config.merchantId,
    Redacted.value(config.secret)
  )
})
```

Only the third argument is sensitive.
The rest can remain ordinary typed data.

## Redacted and tests

Tests should provide the source string through `ConfigProvider.fromMap`.
The config still returns `Redacted`.
Assertions should compare redacted values by unwrapping in the test assertion, not by changing production config shape.

```typescript
import { Config, ConfigProvider, Effect, Redacted } from "effect"

const ApiKey = Config.redacted("API_KEY")

const test = Effect.gen(function*() {
  const provider = ConfigProvider.fromMap(new Map([["API_KEY", "test-key"]]))
  const key = yield* provider.load(ApiKey)
  if (Redacted.value(key) !== "test-key") {
    return yield* Effect.fail("unexpected key")
  }
})
```

The production code does not need a special testing accessor.
The boundary is the assertion itself.

## Avoid deprecated secret config

`Config.secret` exists in the source as deprecated.
Do not use it in new v3 guidance.
Use `Config.redacted` and `Redacted.value`.
The redacted API is the current path.

## Checklist

- Use `Config.redacted("KEY")` for string secrets.
- Use `Config.redacted(Config.integer("KEY"))` when the secret needs typed parsing.
- Keep redacted fields redacted in service configuration structs.
- Unwrap with `Redacted.value(config.secret)` when the redacted value is already loaded.
- Prefer `Redacted.value(yield* config)` for one-off boundary calls.
- Never log raw unwrapped values.
- Never convert redacted values into plain strings for diagnostics.
- Never replace redaction with a manual masking convention.

## Cross-references

See also: [overview](01-overview.md), [basic config](02-basic-config.md), [providers](08-config-providers.md), [test provider layer](09-layer-set-config-provider.md).
