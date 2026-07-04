# Fresh Vs Memoize
Use `Layer.fresh` and `Layer.memoize` when the default reference-identity memoization rule needs to be made explicit.

## Default Sharing

When the same layer reference appears multiple times in a globally provided graph, Effect can share it.

```typescript
import { Context, Effect, Layer } from "effect"

class CounterStore extends Context.Tag("app/CounterStore")<
  CounterStore,
  { readonly next: Effect.Effect<number> }
>() {}

const makeCounterStore = (label: string) =>
  Layer.effect(
    CounterStore,
    Effect.logInfo("counter initialized", { label }).pipe(
      Effect.as({
        next: Effect.succeed(1)
      })
    )
  )

const SharedCounter = makeCounterStore("shared")
```

Reuse `SharedCounter` when you want one shared layer instance.

## Inline Constructor Anti-pattern

This is the parameterized constructor trap:

```typescript
const BranchA = ServiceALive.pipe(
  Layer.provide(makeCounterStore("shared"))
)

const BranchB = ServiceBLive.pipe(
  Layer.provide(makeCounterStore("shared"))
)
```

The two calls return two different layer references. Reference-identity memoization cannot treat them as the same layer.

Prefer:

```typescript
const SharedCounter = makeCounterStore("shared")

const BranchA = ServiceALive.pipe(
  Layer.provide(SharedCounter)
)

const BranchB = ServiceBLive.pipe(
  Layer.provide(SharedCounter)
)
```

Declare branch layers explicitly in examples and production code so type errors point at the composition boundary, not at a large anonymous graph.

## Layer Fresh

`Layer.fresh(layer)` explicitly disables sharing for that layer.

```typescript
const FreshBranchA = ServiceALive.pipe(
  Layer.provide(Layer.fresh(SharedCounter))
)

const FreshBranchB = ServiceBLive.pipe(
  Layer.provide(Layer.fresh(SharedCounter))
)
```

Use this when separate state or separate lifecycle is required.

## Layer Memoize

`Layer.memoize(layer)` returns a scoped effect that produces a memoized layer.

```typescript
import { Effect, Layer } from "effect"

const program = Effect.scoped(
  Effect.gen(function* () {
    const memoized = yield* Layer.memoize(SharedCounter)
    const live = Layer.merge(
      ServiceALive.pipe(Layer.provide(memoized)),
      ServiceBLive.pipe(Layer.provide(memoized))
    )
    return live
  })
)
```

Use this when memoization must be created inside a scoped construction flow.

## Decision Table

| Goal | Pattern |
|---|---|
| Share normal app dependencies | Store layer in a const |
| Avoid accidental duplicate construction | Do not call layer factories inline |
| Force independent instances | `Layer.fresh(layer)` |
| Build a memoized layer inside a scope | `Layer.memoize(layer)` |

## Cross-references

See also: [services-layers/03-effect-service.md](../services-layers/03-effect-service.md), [services-layers/11-layer-providemerge.md](../services-layers/11-layer-providemerge.md), [services-layers/12-layer-composition-gotchas.md](../services-layers/12-layer-composition-gotchas.md), [services-layers/13-layer-memoization.md](../services-layers/13-layer-memoization.md).
