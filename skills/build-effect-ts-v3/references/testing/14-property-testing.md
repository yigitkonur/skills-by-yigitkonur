# Property Testing
Use `it.effect.prop` with schemas to generate many Effect test cases without leaving the Effect runtime.

## Effect Property Tests

`@effect/vitest` supports property tests whose body returns an Effect.

```typescript
import { expect, it } from "@effect/vitest"
import { Effect, Schema } from "effect"

const Name = Schema.NonEmptyString

it.effect.prop("trims without adding characters", [Name], ([name]) =>
  Effect.gen(function* () {
    const trimmed = yield* Effect.succeed(name.trim())

    expect(trimmed.length).toBeLessThanOrEqual(name.length)
  })
)
```

The adapter converts schemas into arbitrary generators and runs the Effect body
for generated cases.

## Object Arbitraries

Use an object when named generated fields improve readability.

```typescript
import { expect, it } from "@effect/vitest"
import { Effect, Schema } from "effect"

const UserInput = {
  id: Schema.NonEmptyString,
  age: Schema.NumberFromString
}

it.effect.prop("keeps decoded age numeric", UserInput, ({ id, age }) =>
  Effect.gen(function* () {
    const user = yield* Effect.succeed({ id, age })

    expect(typeof user.age).toBe("number")
  })
)
```

Use schemas that describe the decoded values the program accepts.

## Property Tests With Services

Property tests can still provide layers.

```typescript
import { expect, it } from "@effect/vitest"
import { Context, Effect, Layer, Schema } from "effect"

class Slugger extends Context.Tag("test/Slugger")<
  Slugger,
  { readonly slug: (input: string) => Effect.Effect<string> }
>() {}

const SluggerTest = Layer.succeed(Slugger, {
  slug: (input) => Effect.succeed(input.toLowerCase().replaceAll(" ", "-"))
})

it.effect.prop("slug output has no spaces", [Schema.NonEmptyString], ([input]) =>
  Effect.gen(function* () {
    const slugger = yield* Slugger
    const slug = yield* slugger.slug(input)

    expect(slug.includes(" ")).toBe(false)
  }).pipe(Effect.provide(SluggerTest))
)
```

Generated inputs do not change the service pattern. Provide test layers as
usual.

## Fast-Check Options

Pass fast-check options through the test options object.

```typescript
import { expect, it } from "@effect/vitest"
import { Effect, Schema } from "effect"

it.effect.prop(
  "string length is never negative",
  [Schema.String],
  ([value]) =>
    Effect.gen(function* () {
      expect(value.length).toBeGreaterThanOrEqual(0)
    }),
  { fastCheck: { numRuns: 50 } }
)
```

Keep property counts high enough to matter and low enough for the suite to stay
fast.

## Test Decode Round Trips

Schema property tests are a good fit for decode and encode invariants.

```typescript
import { expect, it } from "@effect/vitest"
import { Effect, Schema } from "effect"

const Product = Schema.Struct({
  id: Schema.NonEmptyString,
  price: Schema.Number
})

it.effect.prop("encodes and decodes products", [Product], ([product]) =>
  Effect.gen(function* () {
    const encoded = yield* Schema.encode(Product)(product)
    const decoded = yield* Schema.decodeUnknown(Product)(encoded)

    expect(decoded).toEqual(product)
  })
)
```

When this fails, either the schema transform is not symmetric or the property is
too strong for that schema.

## When Not To Use Properties

Property tests are not a replacement for scenario tests:

| Need | Better test |
|---|---|
| One exact typed failure | `it.effect` with `Effect.flip` |
| Time boundary | `it.effect` with `TestClock.adjust` |
| Resource cleanup | `it.scoped` or nested `Effect.scoped` |
| Complex service graph reuse | `it.layer` |

Use properties when broad generated input coverage is the point.

## Keep Generators Valid

Prefer schemas that generate valid domain values. Do not generate arbitrary
unknown data and then discard most of it with filters unless the rejection path
is what you are testing.

If a schema needs custom arbitrary behavior, route to the schema arbitrary
reference and keep the property test focused on the invariant.

## Source Anchors

The v3 adapter implements `it.effect.prop` by converting `Schema` values with
Effect's `Arbitrary.make` and running `fc.asyncProperty` under the Effect test
runner. Test options can include a `fastCheck` field.

## Cross-references

See also: [02-it-effect.md](02-it-effect.md), [07-test-random.md](07-test-random.md), [11-testing-errors.md](11-testing-errors.md), [schema/16-arbitrary.md](../schema/16-arbitrary.md).
