# Testing Overview
Use `@effect/vitest` when tests should run Effects directly with deterministic time, randomness, services, and scopes.

## What This Package Adds

`@effect/vitest` wraps Vitest with Effect-aware helpers:

| Helper | Use it for |
|---|---|
| `it.effect` | Normal Effect tests with `TestContext` provided |
| `it.live` | Tests that must use live default services |
| `it.scoped` | Tests that need a `Scope` and finalizer verification |
| `it.layer` | Suites that share a Layer-built runtime |
| `it.effect.prop` | Property tests whose body returns an Effect |

The important import rule is simple: when calling `it.effect`, import `it` from
`@effect/vitest`. Importing Vitest's plain `it` gives you only promise-based
tests and no Effect test environment.

## Minimal Setup

Install Vitest plus the Effect Vitest adapter:

`npm install --save-dev vitest @effect/vitest`

Then write tests that return Effects instead of manually running them:

```typescript
import { describe, expect, it } from "@effect/vitest"
import { Effect } from "effect"

describe("pricing", () => {
  it.effect("computes a total", () =>
    Effect.gen(function* () {
      const subtotal = yield* Effect.succeed(40)
      const tax = yield* Effect.succeed(4)

      expect(subtotal + tax).toBe(44)
    })
  )
})
```

No `Effect.runPromise` is needed inside the test body. The adapter runs the
Effect, maps failures to Vitest failures, and wires cancellation to Vitest's
test lifecycle.

## Default Test Context

`it.effect` provides Effect's `TestContext`. That context includes the services
needed for deterministic Effect tests, especially the virtual `TestClock`.

```typescript
import { expect, it } from "@effect/vitest"
import { Effect, TestClock } from "effect"

it.effect("sees virtual sleeps", () =>
  Effect.gen(function* () {
    const fiber = yield* Effect.sleep("10 seconds").pipe(Effect.fork)
    const sleeps = yield* TestClock.sleeps()

    expect(sleeps.length).toBe(1)

    yield* TestClock.adjust("10 seconds")
    yield* fiber
  })
)
```

If a test sleeps but never advances the test clock, the test can hang. Fork the
effect that waits, adjust the clock, then join or inspect the fiber.

## Package Boundary

Use `@effect/vitest` for test declarations. Use the `effect` package barrel for
Effect APIs.

```typescript
import { describe, expect, it } from "@effect/vitest"
import { Effect, Layer, TestClock } from "effect"
```

Do not deep-import Effect modules in examples or application tests unless a
build tool has a documented requirement. The repo-wide convention is the package
barrel.

## Test Doubles

Effect tests should replace services with layers. Do not replace modules with
runtime stubs when the code already depends on services.

```typescript
import { Context, Effect, Layer } from "effect"

class Mailer extends Context.Tag("test/Mailer")<
  Mailer,
  { readonly send: (address: string) => Effect.Effect<void> }
>() {}

const MailerTest = Layer.succeed(Mailer, {
  send: (_address) => Effect.void
})
```

Providing a layer preserves the same dependency shape production code uses.
The test sees the real program graph with a different implementation at the
service boundary.

## Assertion Style

Keep assertions inside the Effect body:

```typescript
import { expect, it } from "@effect/vitest"
import { Effect } from "effect"

it.effect("asserts inside the effect", () =>
  Effect.gen(function* () {
    const value = yield* Effect.succeed("ready")
    expect(value).toBe("ready")
  })
)
```

This keeps setup, execution, and assertion in one typed workflow. When the
program fails, the test fails through the Effect failure channel rather than a
separate promise wrapper.

## Choosing The Helper

| Need | Pick |
|---|---|
| Run an Effect under virtual time | `it.effect` |
| Use a real clock or live default services | `it.live` |
| Assert finalizers and scoped resources | `it.scoped` |
| Share an expensive service layer | `it.layer` |
| Generate inputs from schemas | `it.effect.prop` |

Default to `it.effect`. Move to the narrower helper only when the test requires
that capability.

## Common Mistakes

- Importing `it` from plain Vitest and then wondering why `it.effect` is absent.
- Calling `Effect.runPromise` inside every test instead of returning an Effect.
- Sleeping without `TestClock.adjust`.
- Replacing service dependencies with module stubs instead of test layers.
- Using live time in unit tests that can be virtual.

## Source Anchors

Effect 3.21.2 source shows:

- `@effect/vitest` exports `it` as `Vitest.Methods`.
- `it.effect` provides `TestServices.TestServices`.
- `it.scoped` adds `Scope.Scope`.
- `it.layer` builds a runtime from a Layer and reuses it across a suite.
- `TestContext.TestContext` provides the test services used by `it.effect`.

## Cross-references

See also: [02-it-effect.md](02-it-effect.md), [03-it-live.md](03-it-live.md), [05-it-layer.md](05-it-layer.md), [06-test-clock.md](06-test-clock.md), [08-test-layers.md](08-test-layers.md).
