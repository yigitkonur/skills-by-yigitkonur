# Effect Provide
Use `Effect.provide` at program edges to supply layers, contexts, runtimes, or managed runtimes to an effect.

## Provide A Layer

The common case is providing a layer to an effect.

```typescript
import { Context, Effect, Layer } from "effect"

class ClockService extends Context.Tag("app/ClockService")<
  ClockService,
  { readonly now: Effect.Effect<number> }
>() {}

const ClockLive = Layer.succeed(ClockService, {
  now: Effect.succeed(1)
})

const program = Effect.gen(function* () {
  const clock = yield* ClockService
  return yield* clock.now
})

const runnable = program.pipe(
  Effect.provide(ClockLive)
)
```

`Effect.provide` removes any effect requirements satisfied by the provided environment.

## Provide A Service Value

Use `Effect.provideService` for a single already-built service value.

```typescript
const testProgram = program.pipe(
  Effect.provideService(ClockService, {
    now: Effect.succeed(42)
  })
)
```

This is ideal for small tests. Use a layer when construction is effectful, scoped, or reused.

## Provide Multiple Layers

Compose layers first, then provide once.

```typescript
const AppLive = Layer.mergeAll(
  ClockLive,
  LoggerLive,
  UserRepositoryLive
)

const runnable = program.pipe(
  Effect.provide(AppLive)
)
```

This keeps the app dependency graph visible at the edge.

## Local Override

Local provision is valid when a small region needs a different implementation.

```typescript
const withFixedClock = program.pipe(
  Effect.provideService(ClockService, {
    now: Effect.succeed(0)
  })
)
```

Prefer app-edge provision for normal services. Local provision can make large programs harder to reason about when used heavily.

## Boundary Rule

Do not call `Effect.runPromise` or `Effect.runSync` inside service code. Build effects and return them. Run effects only at process, test, script, or framework boundaries.

`ManagedRuntime` is the framework-edge version of the same rule.

## Provide Order

Local provides compose inside out through the pipe.

```typescript
const runnable = program.pipe(
  Effect.provideService(ClockService, { now: Effect.succeed(0) }),
  Effect.provide(LoggerLive)
)
```

Use this sparingly. For normal application wiring, a named `AppLive` layer is easier to inspect and share.

## Choosing The Provision Tool

| You have | Use |
|---|---|
| A single already-built service value | `Effect.provideService` |
| An effect that builds the service value | `Effect.provideServiceEffect` |
| A layer graph | `Effect.provide` |
| A framework-owned runtime | `ManagedRuntime.make` then `runtime.runPromise` |

If the service has lifecycle, prefer a layer over `provideServiceEffect` so acquisition and release are modeled together.

## Testing Rule

Tests can provide tiny service values directly, but integration tests should usually provide the same layer graph shape as production with test implementations swapped in.

That catches layer composition mistakes earlier, especially `provide` vs `provideMerge` mistakes.

## Avoid Repeated Local Graphs

Repeated local provision can hide duplicate construction.

```typescript
const first = program.pipe(Effect.provide(AppLive))
const second = program.pipe(Effect.provide(AppLive))
```

That may be fine for tests. For a server, use a managed runtime or provide once at the long-lived edge so scoped resources are owned by the application lifecycle.

## Cross-references

See also: [services-layers/01-overview.md](../services-layers/01-overview.md), [services-layers/06-layer-succeed.md](../services-layers/06-layer-succeed.md), [services-layers/10-layer-provide.md](../services-layers/10-layer-provide.md), [services-layers/14-managed-runtime.md](../services-layers/14-managed-runtime.md).
