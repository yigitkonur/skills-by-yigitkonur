# It Effect
Use `it.effect` as the default way to test Effect programs without manually running them.

## Import Rule

`it.effect` exists on the `it` exported by `@effect/vitest`.

```typescript
import { describe, expect, it } from "@effect/vitest"
import { Effect } from "effect"

describe("invoice totals", () => {
  it.effect("adds tax", () =>
    Effect.gen(function* () {
      const subtotal = yield* Effect.succeed(100)
      const tax = yield* Effect.succeed(8)

      expect(subtotal + tax).toBe(108)
    })
  )
})
```

Do not import `it` from plain Vitest for Effect tests. Plain Vitest does not
decorate `it` with `.effect`, `.live`, `.scoped`, or `.layer`.

## Return An Effect

The test body returns an `Effect.Effect<A, E, R>`.

```typescript
import { expect, it } from "@effect/vitest"
import { Effect } from "effect"

const normalizeEmail = (email: string) =>
  Effect.succeed(email.trim().toLowerCase())

it.effect("normalizes email addresses", () =>
  Effect.gen(function* () {
    const email = yield* normalizeEmail("  ALICE@EXAMPLE.COM ")

    expect(email).toBe("alice@example.com")
  })
)
```

If the Effect fails, the test fails. If it succeeds and assertions pass, the
test passes.

## TestContext Is Provided

`it.effect` provides `TestContext`, so effects requiring test services compile
without extra setup.

```typescript
import { expect, it } from "@effect/vitest"
import { Effect, TestClock } from "effect"

it.effect("uses virtual time", () =>
  Effect.gen(function* () {
    const fiber = yield* Effect.sleep("1 minute").pipe(Effect.as("done"), Effect.fork)

    yield* TestClock.adjust("1 minute")

    const value = yield* fiber
    expect(value).toBe("done")
  })
)
```

The key pattern is fork first, adjust second, join last. A sleeping fiber cannot
advance the clock from inside itself.

## Provide Test Layers In The Body

Provide service replacements to the program under test with `Effect.provide`.

```typescript
import { expect, it } from "@effect/vitest"
import { Context, Effect, Layer } from "effect"

class Users extends Context.Tag("test/Users")<
  Users,
  { readonly findName: (id: string) => Effect.Effect<string> }
>() {}

const UsersTest = Layer.succeed(Users, {
  findName: (id) => Effect.succeed(id === "u1" ? "Ada" : "Unknown")
})

const greeting = (id: string) =>
  Effect.gen(function* () {
    const users = yield* Users
    const name = yield* users.findName(id)
    return `Hello ${name}`
  })

it.effect("provides service layers", () =>
  Effect.gen(function* () {
    const message = yield* greeting("u1").pipe(Effect.provide(UsersTest))
    expect(message).toBe("Hello Ada")
  })
)
```

This keeps the production dependency boundary intact. The test changes the
implementation, not the import graph.

## Use Assertions Directly

Vitest assertions can run inside the generator:

```typescript
import { expect, it } from "@effect/vitest"
import { Effect } from "effect"

it.effect("asserts several values", () =>
  Effect.gen(function* () {
    const first = yield* Effect.succeed(1)
    const second = yield* Effect.succeed(2)

    expect(first).toBeLessThan(second)
    expect(first + second).toBe(3)
  })
)
```

Avoid returning assertion data to an outer promise-based test. The useful
runtime context is already inside the Effect body.

## Testing Expected Failures

Use `Effect.flip` when the failure is the expected value.

```typescript
import { expect, it } from "@effect/vitest"
import { Data, Effect } from "effect"

class MissingUser extends Data.TaggedError("MissingUser")<{
  readonly id: string
}> {}

const loadUser = (id: string) =>
  Effect.fail(new MissingUser({ id }))

it.effect("asserts typed failures", () =>
  Effect.gen(function* () {
    const error = yield* Effect.flip(loadUser("u404"))

    expect(error._tag).toBe("MissingUser")
    expect(error.id).toBe("u404")
  })
)
```

`Effect.flip` swaps the error and success channels, making typed failures easy
to inspect without promise rejection assertions.

## Table Tests

`it.effect.each` is useful when cases are data and the body still returns an
Effect.

```typescript
import { expect, it } from "@effect/vitest"
import { Effect } from "effect"

const cases = [
  ["ALICE", "alice"],
  ["Bob", "bob"]
] as const

it.effect.each(cases)("lowercases %s", ([input, expected]) =>
  Effect.gen(function* () {
    const result = yield* Effect.succeed(input.toLowerCase())
    expect(result).toBe(expected)
  })
)
```

Use this for pure case matrices. Use property tests when the input space is
large or schema-shaped.

## Timeouts And Options

The third argument accepts Vitest test options or a timeout number.

```typescript
import { expect, it } from "@effect/vitest"
import { Effect } from "effect"

it.effect(
  "finishes within the test timeout",
  () =>
    Effect.gen(function* () {
      const value = yield* Effect.succeed("ok")
      expect(value).toBe("ok")
    }),
  { timeout: 1_000 }
)
```

Do not use timeouts to hide virtual-clock mistakes. If a test uses `sleep`,
advance the `TestClock`.

## Source Anchors

The v3 adapter implementation wraps a Vitest test function, suspends the Effect
body, provides the test environment, runs it, and maps failed exits back into
Vitest failures. That is why the body should stay as an Effect instead of being
manually run by the test author.

## Cross-references

See also: [01-overview.md](01-overview.md), [06-test-clock.md](06-test-clock.md), [08-test-layers.md](08-test-layers.md), [11-testing-errors.md](11-testing-errors.md), [14-property-testing.md](14-property-testing.md).
