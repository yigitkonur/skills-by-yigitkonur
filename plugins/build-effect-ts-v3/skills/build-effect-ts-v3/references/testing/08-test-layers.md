# Test Layers
Use test layers to replace service implementations; do not replace Effect service modules with `vi.mock`.

## The Rule

If production code depends on a service tag, tests should provide another
implementation of that tag.

```typescript
import { expect, it } from "@effect/vitest"
import { Context, Effect, Layer } from "effect"

class PaymentGateway extends Context.Tag("test/PaymentGateway")<
  PaymentGateway,
  { readonly charge: (cents: number) => Effect.Effect<string> }
>() {}

const mockImpl = {
  charge: (cents: number) => Effect.succeed(`test-charge-${cents}`)
}

const PaymentGatewayTest = Layer.succeed(PaymentGateway, mockImpl)

const checkout = (cents: number) =>
  Effect.gen(function* () {
    const gateway = yield* PaymentGateway
    return yield* gateway.charge(cents)
  })

it.effect("uses a test layer", () =>
  Effect.gen(function* () {
    const receipt = yield* checkout(500).pipe(Effect.provide(PaymentGatewayTest))

    expect(receipt).toBe("test-charge-500")
  })
)
```

`Layer.succeed(Service, mockImpl)` gives the program a service value through the
same environment channel production uses.

## Why Not vi.mock

`vi.mock` replaces imported modules. Effect service dependencies are not import
dependencies at the call site; they are runtime requirements in the `R` channel.

| Approach | What it changes | Effect fit |
|---|---|---|
| `Layer.succeed(PaymentGateway, mockImpl)` | Runtime service implementation | Correct |
| `vi.mock("./payment-gateway")` | Module loader behavior | Wrong boundary |

Use module stubbing only for legacy code that is not yet expressed as Effect
services. For Effect services, provide layers.

## Layer.succeed For Pure Doubles

Use `Layer.succeed` when construction has no effectful setup.

```typescript
import { Context, Effect, Layer } from "effect"

class FeatureFlags extends Context.Tag("test/FeatureFlags")<
  FeatureFlags,
  { readonly enabled: (name: string) => Effect.Effect<boolean> }
>() {}

const FeatureFlagsTest = Layer.succeed(FeatureFlags, {
  enabled: (name) => Effect.succeed(name === "new-checkout")
})
```

Pure doubles are easiest to read and should be the default.

## Layer.effect For Constructed Doubles

Use `Layer.effect` when the test implementation needs a `Ref`, generated data,
or another service during construction.

```typescript
import { Context, Effect, Layer, Ref } from "effect"

class Attempts extends Context.Tag("test/Attempts")<
  Attempts,
  { readonly next: Effect.Effect<number> }
>() {}

const AttemptsTest = Layer.effect(
  Attempts,
  Ref.make(0).pipe(
    Effect.map((ref) => ({
      next: Ref.updateAndGet(ref, (n) => n + 1)
    }))
  )
)
```

Do not hide mutable state in a closure outside the layer. Put it in Effect data
structures so construction and sharing are explicit.

## Compose Test Graphs

Test layers compose like production layers.

```typescript
import { Context, Effect, Layer } from "effect"

class Config extends Context.Tag("test/Config")<
  Config,
  { readonly baseUrl: string }
>() {}

class Client extends Context.Tag("test/Client")<
  Client,
  { readonly get: (path: string) => Effect.Effect<string> }
>() {}

const ConfigTest = Layer.succeed(Config, { baseUrl: "https://example.test" })

const ClientTest = Layer.effect(
  Client,
  Effect.gen(function* () {
    const config = yield* Config
    return {
      get: (path: string) => Effect.succeed(`${config.baseUrl}${path}`)
    }
  })
)

const TestLayer = ClientTest.pipe(Layer.provide(ConfigTest))
```

Use `Layer.provide` when satisfying dependencies of a layer. Use
`Layer.provideMerge` when you need to keep both the provider and provided layer
outputs available.

## Provide Close To The Program

For one test, provide the layer directly to the program under test.

```typescript
import { expect, it } from "@effect/vitest"
import { Context, Effect, Layer } from "effect"

class AuditLog extends Context.Tag("test/AuditLog")<
  AuditLog,
  { readonly append: (message: string) => Effect.Effect<void> }
>() {}

const AuditLogTest = Layer.succeed(AuditLog, {
  append: (_message) => Effect.void
})

const submitOrder = Effect.gen(function* () {
  const audit = yield* AuditLog
  yield* audit.append("order submitted")
  return "submitted"
})

it.effect("provides the test graph", () =>
  Effect.gen(function* () {
    const value = yield* submitOrder.pipe(Effect.provide(AuditLogTest))
    expect(value).toBe("submitted")
  })
)
```

The `Effect.provide(AuditLogTest)` call is visible at the program boundary. If
several tests use the same graph, lift that graph into `it.layer` instead of
copying the provision call everywhere.

## Name Layers By Behavior

Name test layers after the behavior they provide, not just `Mock`.

| Weak name | Better name |
|---|---|
| `UserRepoMock` | `UserRepoAlwaysFindsAlice` |
| `MailerMock` | `MailerNoop` |
| `GatewayMock` | `GatewayAlwaysApproves` |
| `FlagsMock` | `FlagsNewCheckoutEnabled` |

Behavioral names make failures easier to read and discourage configurable
mega-fakes.

## Keep Doubles Honest

A good test layer:

- Implements the same service interface as production.
- Uses typed failures, not thrown exceptions.
- Stores mutable state in `Ref`, `Queue`, or another Effect data type.
- Exposes observation methods when the test must assert calls.
- Is named by behavior, such as `UsersAlwaysMissing` or `MailerSpy`.

Avoid broad, configurable fakes that simulate an entire external system. Prefer
small layers per behavior being tested.

## Source Anchors

`Layer.succeed` and `Layer.effect` are v3 layer constructors. `@effect/vitest`
`it.layer` builds a runtime from a layer, while normal `it.effect` bodies can
use `Effect.provide` to supply a test layer per test.

## Cross-references

See also: [02-it-effect.md](02-it-effect.md), [05-it-layer.md](05-it-layer.md), [09-stateful-test-layers.md](09-stateful-test-layers.md), [10-spy-layers.md](10-spy-layers.md), [services-layers/06-layer-succeed.md](../services-layers/06-layer-succeed.md).
