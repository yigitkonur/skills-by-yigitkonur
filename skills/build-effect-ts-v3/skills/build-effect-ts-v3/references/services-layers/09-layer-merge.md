# Layer Merge
Use `Layer.merge` and `Layer.mergeAll` to combine independent layer outputs.

## Merge Semantics

`Layer.merge(left, right)` combines outputs and requirements. It does not satisfy one layer's dependencies with the other layer's outputs.

```typescript
import { Context, Effect, Layer } from "effect"

class ConfigService extends Context.Tag("app/ConfigService")<
  ConfigService,
  { readonly apiUrl: string }
>() {}

class LoggerService extends Context.Tag("app/LoggerService")<
  LoggerService,
  { readonly info: (message: string) => Effect.Effect<void> }
>() {}

const ConfigLive = Layer.succeed(ConfigService, {
  apiUrl: "https://example.test"
})

const LoggerLive = Layer.succeed(LoggerService, {
  info: (message) => Effect.logInfo(message)
})

const AppBaseLive = Layer.merge(ConfigLive, LoggerLive)
```

The result produces `ConfigService | LoggerService`.

## MergeAll

Use `Layer.mergeAll` for more than two independent layers.

```typescript
const AppLive = Layer.mergeAll(
  ConfigLive,
  LoggerLive
)
```

Avoid duplicate service outputs unless you intentionally want replacement behavior. Distinct service outputs are clearer.

## Merge Is Not Dependency Wiring

If `UsersClientLive` requires `ConfigService`, this is incomplete:

```typescript
const Incomplete = Layer.merge(UsersClientLive, ConfigLive)
```

The merged layer produces both services, but `UsersClientLive` still has its construction requirement. Use `Layer.provide` or `Layer.provideMerge` to feed `ConfigLive` into `UsersClientLive`.

## Decision Table

| Goal | Combinator |
|---|---|
| Put independent services side by side | `Layer.merge` |
| Put many independent services side by side | `Layer.mergeAll` |
| Feed one layer into another and hide provider outputs | `Layer.provide` |
| Feed one layer into another and keep provider outputs | `Layer.provideMerge` |

## Parallel Construction

The v3 source describes merge as concurrent composition. Do not rely on construction order between independent layers. If one layer needs another, model that with `Layer.provide` or `Layer.provideMerge`.

## Merge Does Not Order Startup

Merged layers are independent. Do not rely on `ConfigLive` initializing before `LoggerLive` unless `LoggerLive` explicitly depends on `ConfigService`.

```typescript
const LoggerNeedsConfig = Layer.effect(
  LoggerService,
  Effect.gen(function* () {
    const config = yield* ConfigService
    return {
      info: (message: string) =>
        Effect.logInfo(`${config.apiUrl}: ${message}`)
    }
  })
)

const LoggerReady = LoggerNeedsConfig.pipe(
  Layer.provide(ConfigLive)
)
```

The dependency relationship is now in the type.

## Merge Before Provide

When a dependent layer needs several independent services, merge those dependencies first.

```typescript
const BaseLive = Layer.merge(ConfigLive, LoggerLive)
const UsersReady = UsersClientLive.pipe(
  Layer.provide(BaseLive)
)
```

This reads as: build the base environment, then feed it into the users client.

## Duplicate Output Rule

If two layers produce the same tag, name the decision.

```typescript
const LoggerTest = Layer.succeed(LoggerService, {
  info: (_message) => Effect.void
})
```

Prefer constructing a test app layer with `LoggerTest` directly over merging two logger implementations and relying on the last one you notice.

## Reading Merge Types

If either side has requirements, the merged layer keeps them.

```typescript
declare const A: Layer.Layer<"A", never, "Config">
declare const B: Layer.Layer<"B", never, "Clock">

const Both = Layer.merge(A, B)
```

`Both` produces `"A" | "B"` and requires `"Config" | "Clock"`. Merge widens; it does not subtract requirements.

## Cross-references

See also: [services-layers/10-layer-provide.md](../services-layers/10-layer-provide.md), [services-layers/11-layer-providemerge.md](../services-layers/11-layer-providemerge.md), [services-layers/12-layer-composition-gotchas.md](../services-layers/12-layer-composition-gotchas.md), [services-layers/13-layer-memoization.md](../services-layers/13-layer-memoization.md).
