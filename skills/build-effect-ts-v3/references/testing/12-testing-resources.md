# Testing Resources
Use scoped tests to verify finalizers run on success, failure, and interruption.

## Success Cleanup

Use `Effect.scoped` when the test must observe cleanup before the assertion.

```typescript
import { expect, it } from "@effect/vitest"
import { Effect, Ref } from "effect"

it.effect("runs finalizer on success", () =>
  Effect.gen(function* () {
    const released = yield* Ref.make(false)

    const value = yield* Effect.scoped(
      Effect.acquireRelease(
        Effect.succeed("resource"),
        () => released.set(true)
      )
    )

    expect(value).toBe("resource")
    expect(yield* released.get).toBe(true)
  })
)
```

The finalizer runs when the scoped region closes.

## Failure Cleanup

```typescript
import { expect, it } from "@effect/vitest"
import { Data, Effect, Ref } from "effect"

class UseFailed extends Data.TaggedError("UseFailed")<{}> {}

it.effect("runs finalizer on failure", () =>
  Effect.gen(function* () {
    const released = yield* Ref.make(false)

    const program = Effect.scoped(
      Effect.gen(function* () {
        yield* Effect.addFinalizer(() => released.set(true))
        return yield* Effect.fail(new UseFailed({}))
      })
    )

    const error = yield* Effect.flip(program)

    expect(error._tag).toBe("UseFailed")
    expect(yield* released.get).toBe(true)
  })
)
```

The typed failure remains inspectable. Cleanup is not a reason to erase the
error channel.

## Interruption Cleanup

```typescript
import { expect, it } from "@effect/vitest"
import { Effect, Fiber, Ref, TestClock } from "effect"

it.effect("runs finalizer on interruption", () =>
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

Advance virtual time enough to ensure the fiber has reached the sleeping point,
then interrupt it.

## Layer.scoped Resources

When the resource is a service, put acquisition in `Layer.scoped`.

```typescript
import { Context, Effect, Layer, Ref } from "effect"

class Connection extends Context.Tag("test/Connection")<
  Connection,
  { readonly query: Effect.Effect<string> }
>() {}

const ConnectionTest = (released: Ref.Ref<boolean>) =>
  Layer.scoped(
    Connection,
    Effect.acquireRelease(
      Effect.succeed({ query: Effect.succeed("ok") }),
      () => released.set(true)
    )
  )
```

The layer owns the resource lifetime. Use `it.layer` to share it across a suite
or `Effect.provide` to allocate it for one test.

## Do Not Manually Cleanup

Avoid tests that call cleanup methods manually after assertions. That tests a
different behavior from scoped resource safety. Model the resource with
`acquireRelease`, `addFinalizer`, or `Layer.scoped` and assert that Effect closes
the scope.

## Cleanup Matrix

Cover all exit paths when the resource is important:

| Exit path | Test shape |
|---|---|
| Success | Scoped region returns a value, then assert release |
| Typed failure | `Effect.flip` the scoped region, then assert release |
| Interruption | Fork the scoped region, interrupt, then assert release |
| Layer close | Build with `it.layer`, let suite scope close |

The first three paths can be verified inside a single `it.effect` body. Layer
close behavior usually belongs in a focused integration test because the suite
scope closes after the nested test callback finishes.

## Keep The Release Observable

Use a `Ref` or a spy service to observe cleanup. Avoid assertions based on
external process state or real files unless the resource itself is the boundary
under test.

## Source Anchors

Effect 3.21.2 exports `Effect.acquireRelease`, `Effect.addFinalizer`,
`Effect.scoped`, `Layer.scoped`, and `Fiber.interrupt`. The Vitest adapter's
`it.scoped` helper adds `Scope.Scope` for whole-test scoped workflows.

## Cross-references

See also: [04-it-scoped.md](04-it-scoped.md), [05-it-layer.md](05-it-layer.md), [06-test-clock.md](06-test-clock.md), [13-testing-concurrency.md](13-testing-concurrency.md).
