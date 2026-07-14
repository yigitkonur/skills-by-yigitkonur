# Layer ProvideMerge
Use `Layer.provideMerge` when a provider layer should both satisfy dependencies and remain available to consumers.

## Core Semantics

`Layer.provideMerge` feeds one layer into another and keeps both outputs.

```typescript
import { Context, Effect, Layer } from "effect"

class ConfigService extends Context.Tag("app/ConfigService")<
  ConfigService,
  { readonly apiUrl: string }
>() {}

class UsersClient extends Context.Tag("app/UsersClient")<
  UsersClient,
  { readonly findName: (id: string) => Effect.Effect<string> }
>() {}

const ConfigLive = Layer.succeed(ConfigService, {
  apiUrl: "https://example.test"
})

const UsersClientLive = Layer.effect(
  UsersClient,
  Effect.gen(function* () {
    const config = yield* ConfigService
    return {
      findName: (id: string) => Effect.succeed(`${config.apiUrl}/users/${id}`)
    }
  })
)

const TestLive = UsersClientLive.pipe(
  Layer.provideMerge(ConfigLive)
)
```

`TestLive` produces `UsersClient | ConfigService`.

## Type Shape

The simplified transition is:

```typescript
Layer.Layer<UsersClient, never, ConfigService>
Layer.Layer<ConfigService, never, never>
Layer.Layer<UsersClient | ConfigService, never, never>
```

The provider output remains available after it satisfies the dependent layer.

## When It Is The Right Default

Use `provideMerge` when building broad test or application layers where later code may still need provider services.

| Scenario | Why `provideMerge` fits |
|---|---|
| Integration test body yields helper services | Provider outputs remain visible |
| App layer should expose config and clients | Both are part of the app environment |
| Incremental layer graph assembly | Types stay flatter than deeply nested `provide` chains |
| Debugging missing services | Keeping outputs visible helps locate the gap |

## Incremental Composition

Build up a layer without losing intermediate outputs.

```typescript
class LoggerService extends Context.Tag("app/LoggerService")<
  LoggerService,
  { readonly info: (message: string) => Effect.Effect<void> }
>() {}

const LoggerLive = Layer.succeed(LoggerService, {
  info: (message) => Effect.logInfo(message)
})

const AppLive = UsersClientLive.pipe(
  Layer.provideMerge(ConfigLive),
  Layer.provideMerge(LoggerLive)
)
```

`AppLive` produces `UsersClient | ConfigService | LoggerService`, assuming later layers do not override those services.

## Not A Replacement For Merge

Use `Layer.merge` for independent layers. Use `Layer.provideMerge` when the left layer needs the right layer.

```typescript
const Independent = Layer.merge(ConfigLive, LoggerLive)
const Dependent = UsersClientLive.pipe(Layer.provideMerge(ConfigLive))
```

If there is no dependency relationship, `merge` communicates intent better.

## Test Pattern

```typescript
const program = Effect.gen(function* () {
  const users = yield* UsersClient
  const config = yield* ConfigService
  const name = yield* users.findName("u1")
  return `${name} via ${config.apiUrl}`
})

const runnable = program.pipe(
  Effect.provide(TestLive)
)
```

This is exactly the case where `Layer.provide` would leave `ConfigService` missing.

## Chaining Order

In pipe style, each step can use services produced by prior steps.

```typescript
const AppLive2 = UsersClientLive.pipe(
  Layer.provideMerge(ConfigLive),
  Layer.provideMerge(LoggerLive)
)
```

If a later layer also depends on `ConfigService`, it can see the config because the first `provideMerge` kept it in the output.

## Avoid Keeping Too Much At The Boundary

`provideMerge` is not always better. Keeping every low-level dependency visible makes the app environment noisy.

| Keep visible | Hide |
|---|---|
| Services tests yield directly | Implementation-only clients |
| App-level config service | Raw parser internals |
| Public framework services | Private pools and handles |

Use `provideMerge` to preserve intentional surface area, not to avoid thinking about the surface area.

## Flattening Large Graphs

For large app graphs, combine independent roots with `mergeAll`, then use `provideMerge` for dependent increments.

```typescript
const BaseLive = Layer.mergeAll(ConfigLive, LoggerLive)

const AppLive3 = UsersClientLive.pipe(
  Layer.provideMerge(BaseLive)
)
```

This prevents a long sequence of hidden providers from producing a layer that cannot satisfy integration tests.

## Type Reading Example

```typescript
declare const Inner: Layer.Layer<"Inner", never, "Dep">
declare const Dep: Layer.Layer<"Dep", never, never>

const Ready = Inner.pipe(Layer.provideMerge(Dep))
```

`Ready` produces `"Inner" | "Dep"`. That is the only difference from `Layer.provide`, and it is the difference that removes the missing-service error in tests.

## Replacement Caution

If a later layer produces the same tag as an earlier visible provider, be explicit about which one should win. Hidden accidental replacement is harder to debug than a named test override.

## Cross-references

See also: [services-layers/09-layer-merge.md](../services-layers/09-layer-merge.md), [services-layers/10-layer-provide.md](../services-layers/10-layer-provide.md), [services-layers/12-layer-composition-gotchas.md](../services-layers/12-layer-composition-gotchas.md), [services-layers/17-fresh-vs-memoize.md](../services-layers/17-fresh-vs-memoize.md).
