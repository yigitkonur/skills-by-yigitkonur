# Services And Layers Overview
Services and layers are Effect's typed dependency system: effects request capabilities through `R`, and layers build those capabilities.

## The Three Pieces

Effect dependency injection has three separate concepts.

| Concept | What it is | Typical type |
|---|---|---|
| Service | The capability shape an effect needs | `ClockService` |
| Tag | The typed key used to request the service | `Context.Tag` or `Effect.Service` class |
| Layer | The recipe that builds one or more services | `Layer.Layer<ClockService, never, never>` |

Do not collapse these concepts when reasoning about type errors. A service value is not a layer. A tag is not the implementation. A layer does not run the program; it is provided to a program.

## The R Channel

The third type parameter of `Effect.Effect<A, E, R>` is the context requirement.

```typescript
import { Context, Effect } from "effect"

class ClockService extends Context.Tag("app/ClockService")<
  ClockService,
  { readonly now: Effect.Effect<number> }
>() {}

const program = Effect.gen(function* () {
  const clock = yield* ClockService
  return yield* clock.now
})
```

The inferred type of `program` is:

```typescript
Effect.Effect<number, never, ClockService>
```

That means the program cannot run until a `ClockService` is supplied.

## What A Layer Does

A layer moves requirements from the program edge into a reusable construction graph.

```typescript
import { Context, Effect, Layer } from "effect"

class ClockService extends Context.Tag("app/ClockService")<
  ClockService,
  { readonly now: Effect.Effect<number> }
>() {}

const ClockLive = Layer.succeed(ClockService, {
  now: Effect.succeed(1_700_000_000)
})

const program = Effect.gen(function* () {
  const clock = yield* ClockService
  return yield* clock.now
})

const runnable = program.pipe(Effect.provide(ClockLive))
```

`ClockLive` has type `Layer.Layer<ClockService, never, never>`. It produces `ClockService`, cannot fail, and requires no other services.

`runnable` has type `Effect.Effect<number, never, never>`. The dependency is gone because the layer satisfied it.

## Read Layer Types Left To Right

For `Layer.Layer<ROut, E, RIn>`:

| Type slot | Meaning | Question |
|---|---|---|
| `ROut` | Services this layer produces | What can consumers use after construction? |
| `E` | Construction errors | How can startup fail? |
| `RIn` | Services this layer needs to build | What must be supplied before this layer can build? |

This is intentionally the opposite direction from `Effect.Effect<A, E, R>`, where the first parameter is the value produced by the program. For layers, the first parameter is the service output.

## Choose The Smallest Service Surface

Service interfaces should describe capabilities, not implementation details.

```typescript
import { Context, Effect } from "effect"

class UserRepository extends Context.Tag("app/UserRepository")<
  UserRepository,
  {
    readonly findName: (id: string) => Effect.Effect<string>
  }
>() {}
```

Keep the interface stable. Put database clients, HTTP clients, connection pools, caches, and config parsing inside the layer that implements it.

## Mental Model

Think in this order:

1. The program names the services it needs by yielding tags.
2. Each yielded tag appears in the program's `R` channel.
3. A layer that produces those tags removes them from `R`.
4. A layer may itself require other services; those appear in the layer's `RIn`.
5. Layer composition decides which produced services remain visible to the final program.

The last point is where most missing-service errors come from. `Layer.provide` hides the provider layer's outputs. `Layer.provideMerge` keeps them visible.

## Common Failure Signal

If a supposedly runnable program still has `R` requirements, the dependency graph is not complete.

```typescript
Effect.Effect<string, never, UserRepository>
```

This is not a runtime detail. It is a type-level statement that `UserRepository` is still missing at the edge.

## Boundary Placement

Build the dependency graph near the application boundary.

```typescript
const AppLive = Layer.mergeAll(
  ClockLive,
  UserRepositoryLive,
  AuditLog.Live
)

const main = program.pipe(Effect.provide(AppLive))
```

Inside library and service modules, return effects that still describe their requirements. At the app, test, or framework edge, provide the layer graph once.

## Cross-references

See also: [services-layers/02-context-tag.md](../services-layers/02-context-tag.md), [services-layers/03-effect-service.md](../services-layers/03-effect-service.md), [services-layers/10-layer-provide.md](../services-layers/10-layer-provide.md), [services-layers/11-layer-providemerge.md](../services-layers/11-layer-providemerge.md), [services-layers/12-layer-composition-gotchas.md](../services-layers/12-layer-composition-gotchas.md).
