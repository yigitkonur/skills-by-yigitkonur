# Layer Composition Gotchas
Most missing-service type errors come from using `Layer.provide` when the final program still needs the provider service.

## Recognize The Error

The common TypeScript error is:

```text
Effect<A, E, SomeService> is not assignable to Effect<A, E, never>
```

You may also see the diagnostic phrase:

```text
Missing 'SomeService' in the expected Effect context
```

Both mean the same thing: a service is still present in the `R` channel at a boundary that expected `never`.

## The Wrong Pattern

This example intentionally hides `SomeService` with `Layer.provide`, then asks the program to use `SomeService`.

```typescript
import { Context, Effect, Layer } from "effect"

class SomeService extends Context.Tag("app/SomeService")<
  SomeService,
  {
    readonly prefix: string
  }
>() {}

class MyService extends Context.Tag("app/MyService")<
  MyService,
  {
    readonly label: (name: string) => Effect.Effect<string>
  }
>() {}

const SomeServiceLive = Layer.succeed(SomeService, {
  prefix: "test"
})

const MyServiceLive = Layer.effect(
  MyService,
  Effect.gen(function* () {
    const some = yield* SomeService
    return {
      label: (name: string) => Effect.succeed(`${some.prefix}:${name}`)
    }
  })
)

const WrongTestLive = MyServiceLive.pipe(
  Layer.provide(SomeServiceLive)
)

const program = Effect.gen(function* () {
  const my = yield* MyService
  const some = yield* SomeService
  const label = yield* my.label("alice")
  return `${label}:${some.prefix}`
})

// @ts-expect-error SomeService was hidden by Layer.provide.
const runnable: Effect.Effect<string, never, never> = program.pipe(
  Effect.provide(WrongTestLive)
)
```

`WrongTestLive` produces only `MyService`. It used `SomeServiceLive` internally and then hid `SomeService` from the final output.

The final assignment expects no remaining requirements, but the effect still requires `SomeService`. That is why TypeScript reports `Effect<A, E, SomeService> is not assignable to Effect<A, E, never>` or `Missing 'SomeService' in the expected Effect context`.

## The Fix

Use `Layer.provideMerge` instead of `Layer.provide` when the program needs both the dependent service and the provider service.

```typescript
import { Context, Effect, Layer } from "effect"

class SomeService extends Context.Tag("app/SomeService")<
  SomeService,
  {
    readonly prefix: string
  }
>() {}

class MyService extends Context.Tag("app/MyService")<
  MyService,
  {
    readonly label: (name: string) => Effect.Effect<string>
  }
>() {}

const SomeServiceLive = Layer.succeed(SomeService, {
  prefix: "test"
})

const MyServiceLive = Layer.effect(
  MyService,
  Effect.gen(function* () {
    const some = yield* SomeService
    return {
      label: (name: string) => Effect.succeed(`${some.prefix}:${name}`)
    }
  })
)

const RightTestLive = MyServiceLive.pipe(
  Layer.provideMerge(SomeServiceLive)
)

const program = Effect.gen(function* () {
  const my = yield* MyService
  const some = yield* SomeService
  const label = yield* my.label("alice")
  return `${label}:${some.prefix}`
})

const runnable: Effect.Effect<string, never, never> = program.pipe(
  Effect.provide(RightTestLive)
)
```

`RightTestLive` produces `MyService | SomeService`, so `Effect.provide` can satisfy both requirements.

## How To Debug The Type

Read the types in two passes:

1. What does the program require?
2. What does the layer produce?

If the program requires `MyService | SomeService` but the layer produces only `MyService`, the final effect still needs `SomeService`.

## Decision Table

| You are composing | Final program needs provider output? | Use |
|---|---:|---|
| Service needs config internally | No | `Layer.provide` |
| Test body needs config too | Yes | `Layer.provideMerge` |
| Several independent services | Not a dependency relationship | `Layer.mergeAll` |
| Service default owns hidden deps | No | `Layer.provide` |
| App environment exposes base services | Yes | `Layer.provideMerge` |

## The Test Trap

Tests often need both the service under test and its supporting services.

```typescript
const TestLive = MyServiceLive.pipe(
  Layer.provideMerge(SomeServiceLive)
)
```

This is why `provideMerge` is usually the safer test composition default. It prevents the support layer from disappearing before the test body can yield it.

## The Application Trap

Application layers often grow incrementally.

```typescript
const AppLive = MyServiceLive.pipe(
  Layer.provideMerge(SomeServiceLive)
)
```

If the app root later provides a program that yields both services, this composition still works. If the app root should expose only `MyService`, switch to `Layer.provide` intentionally.

## Do Not Silence The R Channel

Never cast the effect requirement away. The `R` channel is the dependency graph. If TypeScript says a service remains, the graph is incomplete for that boundary.

Fix the layer composition, or change the program so it does not request the service.

## Fast Triage

When the error appears, do this before editing code:

1. Search for the missing service name in the program body.
2. Search for the layer that produces that service.
3. Inspect whether that layer was passed through `Layer.provide`.
4. If the program still yields the provider service, change that composition point to `Layer.provideMerge`.

This keeps the fix local. The type error usually does not require redesigning every service.

## Cross-references

See also: [services-layers/09-layer-merge.md](../services-layers/09-layer-merge.md), [services-layers/10-layer-provide.md](../services-layers/10-layer-provide.md), [services-layers/11-layer-providemerge.md](../services-layers/11-layer-providemerge.md), [services-layers/16-layer-tap-debug.md](../services-layers/16-layer-tap-debug.md), [services-layers/17-fresh-vs-memoize.md](../services-layers/17-fresh-vs-memoize.md).
