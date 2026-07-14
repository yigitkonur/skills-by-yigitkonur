# Testing Errors
Use `Effect.flip`, `Effect.exit`, and typed error assertions to test failures without promise rejection wrappers.

## Prefer Effect.flip For Expected Errors

When failure is the expected outcome, `Effect.flip` makes the error the success
value.

```typescript
import { expect, it } from "@effect/vitest"
import { Data, Effect } from "effect"

class InvalidEmail extends Data.TaggedError("InvalidEmail")<{
  readonly input: string
}> {}

const parseEmail = (input: string) =>
  input.includes("@")
    ? Effect.succeed(input.toLowerCase())
    : Effect.fail(new InvalidEmail({ input }))

it.effect("asserts the typed error", () =>
  Effect.gen(function* () {
    const error = yield* Effect.flip(parseEmail("not-an-email"))

    expect(error._tag).toBe("InvalidEmail")
    expect(error.input).toBe("not-an-email")
  })
)
```

`Effect.flip(eff)` swaps `E` and `A`. The original error channel becomes the
success channel and can be asserted directly.

## Use Exit For Shape Assertions

Use `Effect.exit` when the test cares whether the program succeeded or failed,
not just the typed failure value.

```typescript
import { expect, it } from "@effect/vitest"
import { Effect, Exit } from "effect"

it.effect("inspects the exit", () =>
  Effect.gen(function* () {
    const exit = yield* Effect.exit(parseEmail("missing-at"))

    expect(Exit.isFailure(exit)).toBe(true)
  })
)
```

`Effect.exit` always succeeds with an `Exit`, so the test can inspect completion
without failing early.

## Assert Success When Failure Would Be A Bug

```typescript
import { expect, it } from "@effect/vitest"
import { Effect, Exit } from "effect"

it.effect("expects success", () =>
  Effect.gen(function* () {
    const exit = yield* Effect.exit(parseEmail("ada@example.com"))

    if (Exit.isFailure(exit)) {
      expect.fail("expected email parsing to succeed")
    }

    expect(exit.value).toBe("ada@example.com")
  })
)
```

Use `expect.fail` after an `Exit` check when TypeScript needs a branch split for
the success value.

## Assert Recovery

Recovery should be tested as normal Effect behavior.

```typescript
import { expect, it } from "@effect/vitest"
import { Effect } from "effect"

const parseOrGuest = (input: string) =>
  parseEmail(input).pipe(
    Effect.catchTag("InvalidEmail", () => Effect.succeed("guest@example.com"))
  )

it.effect("recovers from a tagged error", () =>
  Effect.gen(function* () {
    const email = yield* parseOrGuest("bad")

    expect(email).toBe("guest@example.com")
  })
)
```

Use `catchTag` or `catchTags` for typed recovery in tests and production code.

## Assert Layer Construction Failures

Layer construction can fail too. Wrap the provided program in `Effect.exit`.

```typescript
import { Context, Data, Effect, Exit, Layer } from "effect"
import { expect, it } from "@effect/vitest"

class ConfigError extends Data.TaggedError("ConfigError")<{}> {}

class ApiConfig extends Context.Tag("test/ApiConfig")<
  ApiConfig,
  { readonly baseUrl: string }
>() {}

const BadConfig = Layer.fail(new ConfigError({}))

const needsConfig = Effect.gen(function* () {
  const config = yield* ApiConfig
  return config.baseUrl
})

it.effect("sees layer build failures", () =>
  Effect.gen(function* () {
    const exit = yield* Effect.exit(needsConfig.pipe(Effect.provide(BadConfig)))

    expect(Exit.isFailure(exit)).toBe(true)
  })
)
```

This catches failures before the service is available.

## Avoid Promise Rejection Assertions

Inside `it.effect`, do not switch to `Effect.runPromise` just to use rejection
matchers. Keep the assertion in the Effect workflow:

| Need | Use |
|---|---|
| Assert typed error payload | `Effect.flip` |
| Assert success or failure shape | `Effect.exit` |
| Assert cause details | `Effect.cause` or `Effect.sandbox` |
| Assert recovery | `catchTag` / `catchTags` |

This keeps tests typed and avoids splitting runtime behavior across two APIs.

## Source Anchors

Effect 3.21.2 exports `Effect.flip`, `Effect.exit`, `Effect.cause`,
`Effect.sandbox`, `Exit.isFailure`, and `Exit.isSuccess`. `@effect/vitest`
converts unhandled Effect failures into Vitest failures.

## Cross-references

See also: [02-it-effect.md](02-it-effect.md), [08-test-layers.md](08-test-layers.md), [10-spy-layers.md](10-spy-layers.md), [error-handling/07-cause-and-exit.md](../error-handling/07-cause-and-exit.md).
