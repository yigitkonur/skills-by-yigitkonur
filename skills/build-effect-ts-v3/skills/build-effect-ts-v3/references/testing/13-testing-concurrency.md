# Testing Concurrency
Use fibers, refs, deferred values, and `TestClock` to make concurrent Effect tests deterministic.

## Start With Deterministic Ordering

Use `Deferred` to coordinate fibers without racing real timers.

```typescript
import { expect, it } from "@effect/vitest"
import { Deferred, Effect, Ref } from "effect"

it.effect("orders two fibers explicitly", () =>
  Effect.gen(function* () {
    const gate = yield* Deferred.make<void>()
    const events = yield* Ref.make<ReadonlyArray<string>>([])

    const worker = Effect.gen(function* () {
      yield* Deferred.await(gate)
      yield* events.update((all) => [...all, "worker"])
    })

    const fiber = yield* Effect.fork(worker)

    yield* events.update((all) => [...all, "test"])
    yield* Deferred.succeed(gate, void 0)
    yield* fiber

    expect(yield* events.get).toEqual(["test", "worker"])
  })
)
```

Prefer explicit gates over hoping the scheduler runs in a particular order.

## Test Parallel Work

Use `Effect.all` with explicit concurrency when running collections.

```typescript
import { expect, it } from "@effect/vitest"
import { Effect, Ref } from "effect"

it.effect("processes several items", () =>
  Effect.gen(function* () {
    const seen = yield* Ref.make<ReadonlyArray<number>>([])

    yield* Effect.all(
      [1, 2, 3].map((n) => seen.update((all) => [...all, n])),
      { concurrency: 3 }
    )

    expect((yield* seen.get).sort()).toEqual([1, 2, 3])
  })
)
```

Do not assert insertion order for parallel work unless the program guarantees
that order.

## Test Interruption

```typescript
import { expect, it } from "@effect/vitest"
import { Effect, Fiber, Ref, TestClock } from "effect"

it.effect("interrupts a suspended fiber", () =>
  Effect.gen(function* () {
    const completed = yield* Ref.make(false)

    const fiber = yield* Effect.gen(function* () {
      yield* Effect.sleep("1 hour")
      yield* completed.set(true)
    }).pipe(Effect.fork)

    yield* TestClock.adjust("1 minute")
    yield* Fiber.interrupt(fiber)

    expect(yield* completed.get).toBe(false)
  })
)
```

Virtual time avoids slow tests and makes the interruption point reproducible.

## Test Racing Behavior

```typescript
import { expect, it } from "@effect/vitest"
import { Effect, TestClock } from "effect"

it.effect("picks the faster branch", () =>
  Effect.gen(function* () {
    const fiber = yield* Effect.race(
      Effect.sleep("1 minute").pipe(Effect.as("slow")),
      Effect.sleep("10 seconds").pipe(Effect.as("fast"))
    ).pipe(Effect.fork)

    yield* TestClock.adjust("10 seconds")

    const winner = yield* fiber
    expect(winner).toBe("fast")
  })
)
```

Advance to the first deadline and assert the expected winner. Avoid live races
in unit tests.

## Test Finalizers Under Concurrency

```typescript
import { expect, it } from "@effect/vitest"
import { Effect, Fiber, Ref, TestClock } from "effect"

it.effect("cleans interrupted concurrent work", () =>
  Effect.gen(function* () {
    const released = yield* Ref.make(false)

    const fiber = yield* Effect.scoped(
      Effect.gen(function* () {
        yield* Effect.addFinalizer(() => released.set(true))
        yield* Effect.sleep("1 hour")
      })
    ).pipe(Effect.fork)

    yield* TestClock.adjust("1 second")
    yield* Fiber.interrupt(fiber)

    expect(yield* released.get).toBe(true)
  })
)
```

This combines the resource and concurrency checks in one deterministic test.

## Assertion Guidance

| Concurrent behavior | Stable assertion |
|---|---|
| All branches ran | Sort values or assert set membership |
| One branch wins | Drive virtual time to the winning boundary |
| Fiber waits | Use `Deferred` or `TestClock.sleeps()` |
| Fiber interrupts | Assert final state after `Fiber.interrupt` |
| Cleanup runs | Assert a `Ref` changed after interruption |

## Source Anchors

Effect 3.21.2 exports `Effect.fork`, `Effect.all`, `Effect.race`,
`Fiber.interrupt`, `Deferred`, `Ref`, and `TestClock.adjust`. These are enough
to make most concurrent unit tests deterministic.

## Cross-references

See also: [06-test-clock.md](06-test-clock.md), [10-spy-layers.md](10-spy-layers.md), [12-testing-resources.md](12-testing-resources.md), [14-property-testing.md](14-property-testing.md).
