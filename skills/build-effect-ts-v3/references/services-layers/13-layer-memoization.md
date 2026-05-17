# Layer Memoization
Layers are memoized by reference identity when provided globally, so store reusable layers in constants.

## The Rule

The official v3 docs state that layers are memoized using reference equality. Reusing the same layer value reuses construction in the dependency graph.

```typescript
import { Context, Effect, Layer } from "effect"

class ConfigService extends Context.Tag("app/ConfigService")<
  ConfigService,
  { readonly value: string }
>() {}

const ConfigLive = Layer.effect(
  ConfigService,
  Effect.logInfo("config initialized").pipe(
    Effect.as({ value: "live" })
  )
)
```

If `ConfigLive` is provided to two dependent branches as the same reference, Effect can share it.

## Store Parameterized Layers

Do this:

```typescript
const makeConfigLive = (value: string) =>
  Layer.effect(
    ConfigService,
    Effect.logInfo("config initialized").pipe(
      Effect.as({ value })
    )
  )

const ConfigForTests = makeConfigLive("test")
```

Then reuse `ConfigForTests`.

## Avoid Inline Constructors

This creates different layer references:

```typescript
const BranchA = ServiceALive.pipe(
  Layer.provide(makeConfigLive("test"))
)

const BranchB = ServiceBLive.pipe(
  Layer.provide(makeConfigLive("test"))
)
```

Even though the arguments match, the layer values are different. Store the layer in a const when sharing matters.

## Global Vs Local Providing

Memoization is strongest when the layer graph is provided once at the application edge.

```typescript
const AppLive = Layer.merge(
  ServiceALive.pipe(Layer.provide(ConfigForTests)),
  ServiceBLive.pipe(Layer.provide(ConfigForTests))
)

const runnable = program.pipe(Effect.provide(AppLive))
```

Providing separate local layers in separate effects can allocate separately because each provision has its own lifecycle.

## When Duplicate Construction Is Correct

Sometimes you want fresh instances:

| Need | Tool |
|---|---|
| Separate stateful test dependencies | `Layer.fresh` |
| Per-tenant layer value | Parameterized layer stored per tenant |
| Explicit scoped instance per branch | `Layer.fresh` around that layer |

Do not rely on inline constructor calls as an implicit freshness policy. Use `Layer.fresh` so the intent is visible.

## Memoization And Tests

Tests often create duplicate layers accidentally:

```typescript
const makeStoreLive = (name: string) =>
  Layer.effect(
    ConfigService,
    Effect.logInfo("store initialized", { name }).pipe(
      Effect.as({ value: name })
    )
  )
```

If every test gets a fresh graph, this may be fine. If one test graph has multiple branches and those branches should share the same store, store the layer first.

```typescript
const StoreLive = makeStoreLive("test")

const TestLive = Layer.merge(
  ServiceALive.pipe(Layer.provide(StoreLive)),
  ServiceBLive.pipe(Layer.provide(StoreLive))
)
```

## Memoization Is Not Caching Method Results

Layer memoization shares service construction. It does not cache calls to service methods.

```typescript
class ExpensiveService extends Context.Tag("app/ExpensiveService")<
  ExpensiveService,
  { readonly compute: Effect.Effect<number> }
>() {}
```

If `compute` should cache values, model that inside the service implementation with a `Ref`, cache, or another appropriate Effect data type. Do not expect the layer to memoize method calls.

## Inspecting Duplicate Initialization

Add `Layer.tap` or construction-time `Effect.logInfo` to the layer. If it logs twice in one provided graph, check for inline layer factory calls or `Layer.fresh`.

## Constant Naming

Name stored layer values after their sharing policy.

| Name | Signal |
|---|---|
| `ConfigLive` | Normal shared live layer |
| `ConfigTest` | Test graph layer |
| `FreshConfigLive` | Freshness is intentional |
| `TenantALive` | Parameterized value is already fixed |

## Cross-references

See also: [services-layers/08-layer-scoped.md](../services-layers/08-layer-scoped.md), [services-layers/09-layer-merge.md](../services-layers/09-layer-merge.md), [services-layers/14-managed-runtime.md](../services-layers/14-managed-runtime.md), [services-layers/17-fresh-vs-memoize.md](../services-layers/17-fresh-vs-memoize.md).
