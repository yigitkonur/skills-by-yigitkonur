# Test Random
Use deterministic `Random` services to make random Effect code repeatable in tests.

## V3 Source Reality

In Effect 3.21.2, deterministic random testing is done through the public
`Random` service helpers:

| Helper | Use |
|---|---|
| `Random.make(seed)` | Reproducible pseudo-random sequence |
| `Random.fixed(values)` | Cycle through literal values |
| `Effect.withRandom(random)` | Provide a random implementation |
| `Effect.withRandomFixed(values)` | Provide a cycling implementation directly |

The mission corpus does not expose a separate public `TestRandom.ts` module.
Use the v3 APIs that exist in source.

## Fixed Values

`Effect.withRandomFixed` is the simplest deterministic test tool.

```typescript
import { expect, it } from "@effect/vitest"
import { Effect, Random } from "effect"

const pickBranch = Effect.gen(function* () {
  const high = yield* Random.nextBoolean
  return high ? "high" : "low"
})

it.effect("chooses a deterministic branch", () =>
  Effect.gen(function* () {
    const first = yield* pickBranch.pipe(Effect.withRandomFixed([true, false]))
    const second = yield* pickBranch.pipe(Effect.withRandomFixed([false, true]))

    expect(first).toBe("high")
    expect(second).toBe("low")
  })
)
```

Use fixed random values when a test needs exact branch coverage.

## Seeded Random

Use `Random.make` when the sequence should be pseudo-random but repeatable.

```typescript
import { expect, it } from "@effect/vitest"
import { Effect, Random } from "effect"

const roll = Random.nextIntBetween(1, 7)

it.effect("replays a seeded sequence", () =>
  Effect.gen(function* () {
    const seededA = Random.make("checkout-seed")
    const seededB = Random.make("checkout-seed")

    const first = yield* roll.pipe(Effect.withRandom(seededA))
    const replay = yield* roll.pipe(Effect.withRandom(seededB))

    expect(first).toBe(replay)
  })
)
```

Avoid asserting the exact numeric output of a seed unless the algorithm is the
contract. Usually you only need repeatability.

## Test A Random Service Dependency

If your application wraps randomness in a service, provide a test layer for that
service instead of controlling global default services.

```typescript
import { expect, it } from "@effect/vitest"
import { Context, Effect, Layer } from "effect"

class TokenGenerator extends Context.Tag("test/TokenGenerator")<
  TokenGenerator,
  { readonly next: Effect.Effect<string> }
>() {}

const TokenGeneratorTest = Layer.succeed(TokenGenerator, {
  next: Effect.succeed("token-1")
})

const issueToken = Effect.gen(function* () {
  const generator = yield* TokenGenerator
  return yield* generator.next
})

it.effect("uses the provided token generator", () =>
  Effect.gen(function* () {
    const token = yield* issueToken.pipe(Effect.provide(TokenGeneratorTest))

    expect(token).toBe("token-1")
  })
)
```

This keeps random decisions behind a domain boundary and makes tests clearer.

## Avoid Hidden Randomness

Do not create a random generator inside the service method if tests need
control. Inject it through a layer or use `Effect.withRandom` at the test edge.

```typescript
import { expect, it } from "@effect/vitest"
import { Effect, Random } from "effect"

const discount = Random.nextRange(0, 1).pipe(
  Effect.map((n) => n >= 0.5 ? "large" : "small")
)

it.effect("controls the discount branch", () =>
  Effect.gen(function* () {
    const value = yield* discount.pipe(Effect.withRandomFixed([0.8]))

    expect(value).toBe("large")
  })
)
```

The value sequence is part of the test input. Keep it near the assertion.

## Source Anchors

Effect 3.21.2 source exports `Random.next`, `nextBoolean`, `nextInt`,
`nextRange`, `nextIntBetween`, `shuffle`, `make`, and `fixed`. `Effect` exports
`withRandom` and `withRandomFixed`.

## Cross-references

See also: [02-it-effect.md](02-it-effect.md), [08-test-layers.md](08-test-layers.md), [09-stateful-test-layers.md](09-stateful-test-layers.md), [14-property-testing.md](14-property-testing.md).
