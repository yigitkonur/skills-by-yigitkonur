# It Layer
Use `it.layer` when a group of tests should share a Layer-built runtime.

## Why Use It

`it.layer(layer)("name", callback)` builds the layer once for the suite and
passes a scoped `it` object into the callback.

```typescript
import { expect, it } from "@effect/vitest"
import { Context, Effect, Layer } from "effect"

class Users extends Context.Tag("test/Users")<
  Users,
  { readonly name: (id: string) => Effect.Effect<string> }
>() {}

const UsersTest = Layer.succeed(Users, {
  name: (id) => Effect.succeed(id === "u1" ? "Ada" : "Unknown")
})

it.layer(UsersTest)("users", (it) => {
  it.effect("finds a known user", () =>
    Effect.gen(function* () {
      const users = yield* Users
      const name = yield* users.name("u1")

      expect(name).toBe("Ada")
    })
  )
})
```

The nested `it` has the provided layer in its runtime. The test body can access
`Users` without calling `Effect.provide` in every test.

## Share Expensive Setup

Use `it.layer` for setup that should be allocated once per suite:

| Setup | Why suite sharing helps |
|---|---|
| In-memory database service | Avoid repeated initialization |
| HTTP client test adapter | Reuse deterministic handlers |
| Layer graph with many services | Reduce repeated boilerplate |
| Scoped resource layer | Close once after the suite |

For small one-off service doubles, `Effect.provide(TestLayer)` inside
`it.effect` is often clearer.

## Nested Layers

The `it` object passed to a layer suite can create nested layer suites.

```typescript
import { expect, it } from "@effect/vitest"
import { Context, Effect, Layer } from "effect"

class Config extends Context.Tag("test/Config")<
  Config,
  { readonly region: string }
>() {}

class Endpoint extends Context.Tag("test/Endpoint")<
  Endpoint,
  { readonly url: string }
>() {}

const ConfigTest = Layer.succeed(Config, { region: "us" })

const EndpointTest = Layer.effect(
  Endpoint,
  Effect.gen(function* () {
    const config = yield* Config
    return { url: `https://api.${config.region}.example` }
  })
)

it.layer(ConfigTest)("configured", (it) => {
  it.layer(EndpointTest)("endpoint", (it) => {
    it.effect("uses the outer layer", () =>
      Effect.gen(function* () {
        const endpoint = yield* Endpoint
        expect(endpoint.url).toBe("https://api.us.example")
      })
    )
  })
})
```

Nested `it.layer` uses `Layer.provideMerge` internally so the inner layer can
depend on services from the outer layer.

## Options

Layer suites accept a timeout option for building and closing the runtime:

```typescript
import { expect, it } from "@effect/vitest"
import { Effect, Layer } from "effect"

const Ready = Layer.effectDiscard(Effect.sleep("5 millis"))

it.layer(Ready, { timeout: "1 second" })("ready layer", (it) => {
  it.effect("runs after setup", () =>
    Effect.gen(function* () {
      expect(true).toBe(true)
    })
  )
})
```

Keep layer startup deterministic. A long timeout should be a boundary-test
choice, not a substitute for controlled test services.

## Avoid Cross-Test State Leaks

`it.layer` shares the runtime. If the layer contains a `Ref`, all tests in that
suite see the same `Ref`.

```typescript
import { expect, it } from "@effect/vitest"
import { Context, Effect, Layer, Ref } from "effect"

class Counter extends Context.Tag("test/Counter")<
  Counter,
  { readonly next: Effect.Effect<number> }
>() {}

const CounterSuite = Layer.effect(
  Counter,
  Ref.make(0).pipe(
    Effect.map((ref) => ({
      next: Ref.updateAndGet(ref, (n) => n + 1)
    }))
  )
)

it.layer(CounterSuite)("counter", (it) => {
  it.effect("observes shared state", () =>
    Effect.gen(function* () {
      const counter = yield* Counter
      const first = yield* counter.next

      expect(first).toBeGreaterThan(0)
    })
  )
})
```

Shared state is useful for expensive fixtures, but risky for unit isolation. If
each test needs fresh state, provide `Layer.effect` inside each `it.effect` body
or make a fresh nested layer per test group.

## Source Anchors

The v3 implementation creates a runtime with `Layer.toRuntimeWithMemoMap`,
opens a scope in `beforeAll`, and closes that scope in `afterAll`. Nested layer
suites reuse the memo map and compose with the outer environment.

## Cross-references

See also: [01-overview.md](01-overview.md), [08-test-layers.md](08-test-layers.md), [09-stateful-test-layers.md](09-stateful-test-layers.md), [12-testing-resources.md](12-testing-resources.md).
