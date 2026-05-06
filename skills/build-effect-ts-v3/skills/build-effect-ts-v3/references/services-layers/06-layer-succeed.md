# Layer Succeed
Use `Layer.succeed` when a service implementation is already available synchronously.

## Signature Shape

In v3 source, `Layer.succeed` constructs a layer from a tag and a value.

```typescript
import { Context, Effect, Layer } from "effect"

class FeatureFlags extends Context.Tag("app/FeatureFlags")<
  FeatureFlags,
  {
    readonly isEnabled: (name: string) => Effect.Effect<boolean>
  }
>() {}

const FeatureFlagsLive = Layer.succeed(FeatureFlags, {
  isEnabled: (_name) => Effect.succeed(false)
})
```

The type is `Layer.Layer<FeatureFlags, never, never>`.

## Use It For Pure Values

Good candidates:

| Service | Reason |
|---|---|
| Static feature flags | Already known |
| In-memory test repository | No acquisition |
| Pure formatter | No effects during construction |
| Fixed clock | Deterministic tests |

If construction needs config, I/O, or another service, use `Layer.effect`.

## Test Doubles

`Layer.succeed` is the simplest test layer.

```typescript
import { Context, Effect, Layer } from "effect"

class Mailer extends Context.Tag("app/Mailer")<
  Mailer,
  {
    readonly send: (address: string, body: string) => Effect.Effect<void>
  }
>() {}

const MailerTest = Layer.succeed(Mailer, {
  send: (_address, _body) => Effect.void
})
```

Keep test doubles small. If the fake needs state, put that state in a scoped layer or a `Ref` created by `Layer.effect`.

## Do Not Allocate Hidden Resources

Avoid putting hidden resource allocation inside the object literal.

```typescript
import { Context, Effect, Layer, Ref } from "effect"

class Counter extends Context.Tag("app/Counter")<
  Counter,
  { readonly next: Effect.Effect<number> }
>() {}

const CounterLive = Layer.effect(
  Counter,
  Ref.make(0).pipe(
    Effect.map((ref) => ({
      next: Ref.updateAndGet(ref, (n) => n + 1)
    }))
  )
)
```

`Layer.effect` makes allocation explicit and keeps failures or dependencies in the layer type.

## Inline Value Vs Shared Value

For pure values, inline service objects are fine. For values that should be shared by identity, create them first and pass the same object.

```typescript
const flags = {
  isEnabled: (_name: string) => Effect.succeed(false)
}

const FeatureFlagsTest = Layer.succeed(FeatureFlags, flags)
```

This makes it obvious whether tests are using the same fake implementation.

## Boundary Validation

Validate external input before putting it into a service value.

```typescript
const makePortLayer = (port: number) =>
  Layer.succeed(PortService, {
    port: Number.isInteger(port) && port > 0 ? port : 3000
  })
```

Do not push invalid values into a layer and expect downstream services to rediscover the problem repeatedly.

## Replacement Pattern

`Layer.succeed` is also a clean way to override one service in a larger graph.

```typescript
const AppForTests = AppLive.pipe(
  Layer.provideMerge(FeatureFlagsTest)
)
```

If the larger graph already produces the same tag, prefer composing a clearly named test graph rather than relying on accidental override order.

## Cross-references

See also: [services-layers/02-context-tag.md](../services-layers/02-context-tag.md), [services-layers/05-context-reference.md](../services-layers/05-context-reference.md), [services-layers/07-layer-effect.md](../services-layers/07-layer-effect.md), [services-layers/15-effect-provide.md](../services-layers/15-effect-provide.md).
