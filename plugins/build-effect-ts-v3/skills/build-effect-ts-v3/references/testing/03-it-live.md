# It Live
Use `it.live` only when the test must run with live default services instead of the Effect test environment.

## Default Is Not Live

`it.effect` gives you the test environment. That is what most unit tests want:
virtual time, deterministic test services, and no real waiting.

```typescript
import { expect, it } from "@effect/vitest"
import { Clock, Effect } from "effect"

it.live("reads the live clock", () =>
  Effect.gen(function* () {
    const millis = yield* Clock.currentTimeMillis

    expect(Number.isFinite(millis)).toBe(true)
  })
)
```

Use `it.live` for tests where the live default services are part of the thing
being verified. Do not use it just because a test involving time currently
hangs; that usually means the test forgot to adjust `TestClock`.

## Real Time Actually Passes

With `it.live`, `Effect.sleep` waits on real time:

```typescript
import { expect, it } from "@effect/vitest"
import { Effect } from "effect"

it.live("waits on real time", () =>
  Effect.gen(function* () {
    const started = Date.now()

    yield* Effect.sleep("5 millis")

    expect(Date.now()).toBeGreaterThanOrEqual(started)
  })
)
```

Keep live-time sleeps tiny and rare. Most time-dependent behavior is better
tested by `it.effect` plus `TestClock.adjust`.

## When To Use It

Good uses:

| Scenario | Why live services matter |
|---|---|
| Boundary smoke test | You want the runtime's real default services |
| Adapter integration | The adapter depends on current live time |
| Performance sanity check | Virtual time would hide real scheduling cost |

Poor uses:

| Scenario | Better helper |
|---|---|
| Timeout logic | `it.effect` with `TestClock.adjust` |
| Retry schedules | `it.effect` with virtual time |
| Finalizer assertions | `it.scoped` |
| Shared dependency graph | `it.layer` |

## Use Live Narrowly

Make the live part the smallest part of the test. If the program mostly depends
on services, still provide test layers for those services.

```typescript
import { expect, it } from "@effect/vitest"
import { Context, Effect, Layer } from "effect"

class ClockedId extends Context.Tag("test/ClockedId")<
  ClockedId,
  { readonly make: Effect.Effect<string> }
>() {}

const ClockedIdTest = Layer.succeed(ClockedId, {
  make: Effect.succeed("fixed-id")
})

it.live("can still provide test services", () =>
  Effect.gen(function* () {
    const service = yield* ClockedId
    const id = yield* service.make

    expect(id).toBe("fixed-id")
  }).pipe(Effect.provide(ClockedIdTest))
)
```

`it.live` controls the default services. Your application services are still
ordinary requirements that can be supplied with layers.

## Avoid Using It For Unit Time

This is the common wrong move:

```typescript
import { expect, it } from "@effect/vitest"
import { Effect } from "effect"

it.live("works but pays real time", () =>
  Effect.gen(function* () {
    yield* Effect.sleep("10 millis")
    expect(true).toBe(true)
  })
)
```

If the behavior is "after ten minutes, expire the cache", live time makes the
test slow and flaky. Use `TestClock` instead.

## Scoped Live Variant

`@effect/vitest` also exposes `it.scopedLive` for tests that need both live
default services and a `Scope`.

```typescript
import { expect, it } from "@effect/vitest"
import { Effect, Ref } from "effect"

it.scopedLive("runs scoped code with live services", () =>
  Effect.gen(function* () {
    const released = yield* Ref.make(false)
    yield* Effect.addFinalizer(() => released.set(true))

    expect(yield* released.get).toBe(false)
  })
)
```

Prefer plain `it.scoped` unless live defaults are specifically required.

## Source Anchors

The v3 source defines `live` as a tester with requirement `never`, while
`effect` is a tester requiring `TestServices.TestServices`. This is the semantic
difference: `it.live` does not provide `TestContext`.

## Cross-references

See also: [01-overview.md](01-overview.md), [02-it-effect.md](02-it-effect.md), [04-it-scoped.md](04-it-scoped.md), [06-test-clock.md](06-test-clock.md).
