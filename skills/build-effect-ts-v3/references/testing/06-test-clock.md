# Test Clock
Use `TestClock` to test time-dependent Effect code instantly and deterministically.

## Core Rule

`it.effect` provides a virtual clock. Effects that call `Effect.sleep` suspend
until the test advances time with `TestClock.adjust` or `TestClock.setTime`.

```typescript
import { expect, it } from "@effect/vitest"
import { Effect, TestClock } from "effect"

it.effect("sleeps for one hour instantly", () =>
  Effect.gen(function* () {
    const fiber = yield* Effect.sleep("1 hour").pipe(
      Effect.as("awake"),
      Effect.fork
    )

    yield* TestClock.adjust("1 hour")

    const result = yield* fiber
    expect(result).toBe("awake")
  })
)
```

This test does not wait an hour. The sleep is registered on the virtual clock,
the clock is advanced, and the fiber resumes immediately.

## Fork Before Adjust

If the current fiber sleeps, it cannot advance the clock after the sleep line.
Put the sleeping program in a fiber first.

```typescript
import { expect, it } from "@effect/vitest"
import { Effect, Fiber, TestClock } from "effect"

const expires = Effect.sleep("30 minutes").pipe(Effect.as("expired"))

it.effect("advances a sleeping workflow", () =>
  Effect.gen(function* () {
    const fiber = yield* Effect.fork(expires)

    yield* TestClock.adjust("30 minutes")

    const value = yield* Fiber.join(fiber)
    expect(value).toBe("expired")
  })
)
```

Use either `yield* fiber` or `Fiber.join(fiber)` depending on which is clearer
in the local codebase.

## Inspect Pending Sleeps

`TestClock.sleeps()` returns the scheduled wake-up times.

```typescript
import { expect, it } from "@effect/vitest"
import { Effect, TestClock } from "effect"

it.effect("records a pending sleep", () =>
  Effect.gen(function* () {
    const fiber = yield* Effect.sleep("5 seconds").pipe(Effect.fork)
    const sleeps = yield* TestClock.sleeps()

    expect(sleeps.length).toBe(1)

    yield* TestClock.adjust("5 seconds")
    yield* fiber
  })
)
```

This is useful when debugging a test that appears blocked on virtual time.

## Test Timeouts

Virtual time makes timeout tests precise:

```typescript
import { expect, it } from "@effect/vitest"
import { Effect, Option, TestClock } from "effect"

it.effect("times out after the configured duration", () =>
  Effect.gen(function* () {
    const fiber = yield* Effect.sleep("10 minutes").pipe(
      Effect.timeout("1 minute"),
      Effect.fork
    )

    yield* TestClock.adjust("1 minute")

    const result = yield* fiber
    expect(Option.isNone(result)).toBe(true)
  })
)
```

The test clock advances the timeout boundary. There is no real-minute delay.

## Test Retries And Schedules

Any schedule that sleeps can be driven by the test clock.

```typescript
import { expect, it } from "@effect/vitest"
import { Data, Effect, Ref, Schedule, TestClock } from "effect"

class Busy extends Data.TaggedError("Busy")<{}> {}

it.effect("retries on a virtual interval", () =>
  Effect.gen(function* () {
    const attempts = yield* Ref.make(0)

    const operation = Ref.updateAndGet(attempts, (n) => n + 1).pipe(
      Effect.flatMap((n) => n < 3 ? Effect.fail(new Busy({})) : Effect.succeed(n))
    )

    const fiber = yield* operation.pipe(
      Effect.retry(Schedule.spaced("10 seconds")),
      Effect.fork
    )

    yield* TestClock.adjust("20 seconds")

    const result = yield* fiber
    expect(result).toBe(3)
  })
)
```

Advance enough virtual time for all scheduled retries you expect.

## Set Absolute Time

Use `TestClock.setTime` when code depends on clock instants rather than elapsed
durations.

```typescript
import { expect, it } from "@effect/vitest"
import { Clock, Effect, TestClock } from "effect"

it.effect("sets the current virtual millis", () =>
  Effect.gen(function* () {
    yield* TestClock.setTime(1_700_000_000_000)

    const now = yield* Clock.currentTimeMillis
    expect(now).toBe(1_700_000_000_000)
  })
)
```

Prefer elapsed durations for behavior tests and absolute time for timestamp
formatting or deadline logic.

## Save And Restore

`TestClock.save` captures a restore effect.

```typescript
import { expect, it } from "@effect/vitest"
import { Clock, Effect, TestClock } from "effect"

it.effect("restores virtual time", () =>
  Effect.gen(function* () {
    const restore = yield* TestClock.save

    yield* TestClock.adjust("1 hour")
    yield* restore

    const now = yield* Clock.currentTimeMillis
    expect(now).toBe(0)
  })
)
```

Use this when one test has multiple independent time scenarios in one body.

## Live Time Escape Hatch

Use `it.live` only when real time is the subject of the test. A unit test that
uses sleep, timeout, retry, debounce, cache TTL, or scheduled cleanup should
normally use `it.effect` plus `TestClock.adjust`.

## Source Anchors

Effect 3.21.2 source exposes `TestClock.adjust`, `adjustWith`, `setTime`,
`save`, and `sleeps`. `TestContext.TestContext` provides the default test clock
used by `@effect/vitest` `it.effect`.

## Cross-references

See also: [01-overview.md](01-overview.md), [02-it-effect.md](02-it-effect.md), [03-it-live.md](03-it-live.md), [13-testing-concurrency.md](13-testing-concurrency.md).
