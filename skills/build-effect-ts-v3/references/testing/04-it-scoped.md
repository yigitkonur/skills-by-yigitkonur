# It Scoped
Use `it.scoped` when the test body needs a `Scope` so finalizers and scoped resources run deterministically.

## What It Adds

`it.scoped` is like `it.effect`, but the test body runs inside `Effect.scoped`
and has `Scope.Scope` available.

```typescript
import { expect, it } from "@effect/vitest"
import { Effect, Ref } from "effect"

it.scoped("runs finalizers when the test scope closes", () =>
  Effect.gen(function* () {
    const released = yield* Ref.make(false)

    yield* Effect.addFinalizer(() => released.set(true))

    expect(yield* released.get).toBe(false)
  })
)
```

The finalizer runs after the test body completes. To assert the final state
inside the same body, create a nested scope with `Effect.scoped`.

## Assert Finalizers Inside The Test

Use a nested scoped region when the assertion must observe cleanup before the
test returns.

```typescript
import { expect, it } from "@effect/vitest"
import { Effect, Ref } from "effect"

it.effect("observes cleanup after a nested scope", () =>
  Effect.gen(function* () {
    const released = yield* Ref.make(false)

    yield* Effect.scoped(
      Effect.gen(function* () {
        yield* Effect.addFinalizer(() => released.set(true))
      })
    )

    expect(yield* released.get).toBe(true)
  })
)
```

This pattern is clearer than relying on after-test hooks to inspect cleanup.

## Testing Acquire Release

`Effect.acquireRelease` is a natural fit for scoped tests.

```typescript
import { expect, it } from "@effect/vitest"
import { Effect, Ref } from "effect"

it.effect("releases acquired resources", () =>
  Effect.gen(function* () {
    const released = yield* Ref.make(false)

    const useResource = Effect.acquireRelease(
      Effect.succeed("resource"),
      () => released.set(true)
    )

    const value = yield* Effect.scoped(useResource)

    expect(value).toBe("resource")
    expect(yield* released.get).toBe(true)
  })
)
```

If the resource is needed across the whole test body, use `it.scoped`. If the
resource lifetime is only one assertion block, use `Effect.scoped` locally.

## Failure Still Releases

Finalizers run on failure too.

```typescript
import { expect, it } from "@effect/vitest"
import { Data, Effect, Ref } from "effect"

class Boom extends Data.TaggedError("Boom")<{}> {}

it.effect("releases after failure", () =>
  Effect.gen(function* () {
    const released = yield* Ref.make(false)

    const failing = Effect.scoped(
      Effect.gen(function* () {
        yield* Effect.addFinalizer(() => released.set(true))
        return yield* Effect.fail(new Boom({}))
      })
    )

    const error = yield* Effect.flip(failing)

    expect(error._tag).toBe("Boom")
    expect(yield* released.get).toBe(true)
  })
)
```

Keep the typed failure visible. Do not convert scoped failures into defects just
to make assertions easier.

## Interruptions Still Release

Interruption is another exit path finalizers must cover.

```typescript
import { expect, it } from "@effect/vitest"
import { Effect, Fiber, Ref, TestClock } from "effect"

it.effect("releases after interruption", () =>
  Effect.gen(function* () {
    const released = yield* Ref.make(false)

    const fiber = yield* Effect.scoped(
      Effect.gen(function* () {
        yield* Effect.addFinalizer(() => released.set(true))
        yield* Effect.sleep("1 hour")
      })
    ).pipe(Effect.fork)

    yield* TestClock.adjust("1 minute")
    yield* Fiber.interrupt(fiber)

    expect(yield* released.get).toBe(true)
  })
)
```

Use virtual time to get the fiber into a suspended state before interrupting it.

## When Not To Use It

Do not use `it.scoped` for ordinary tests that have no scoped requirements.
Plain `it.effect` has less type surface and is easier to read.

Use `it.layer` when the scoped resource is an application service shared by a
suite. Use `Layer.scoped` there, and let the suite-level runtime own cleanup.

## Source Anchors

The v3 adapter defines `scoped` as a tester whose environment includes both
`TestServices.TestServices` and `Scope.Scope`, then maps the body through
`Effect.scoped` before running it.

## Cross-references

See also: [01-overview.md](01-overview.md), [03-it-live.md](03-it-live.md), [08-test-layers.md](08-test-layers.md), [12-testing-resources.md](12-testing-resources.md).
