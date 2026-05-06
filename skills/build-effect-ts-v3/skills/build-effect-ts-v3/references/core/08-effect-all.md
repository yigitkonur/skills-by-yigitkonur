# Effect All
Use `Effect.all` to collect independent effects with explicit result shape, failure mode, and concurrency.

## What `Effect.all` Does

`Effect.all` combines an iterable, tuple, or record of effects into one effect.
The success shape mirrors the input shape unless `discard: true` is used.

```typescript
import { Effect } from "effect"

const program = Effect.all(
  [
    Effect.succeed(1),
    Effect.succeed("two")
  ],
  { concurrency: 2 }
)
```

The result succeeds with `[1, "two"]` as a tuple. If any effect fails in default
mode, the combined effect fails.

## Record Mode

Use record mode when names matter more than position.

```typescript
import { Effect } from "effect"

const program = Effect.all(
  {
    user: loadUser("u1"),
    settings: loadSettings("u1")
  },
  { concurrency: 2 }
)

declare const loadUser: (id: string) => Effect.Effect<string, "MissingUser">
declare const loadSettings: (id: string) => Effect.Effect<string, "MissingSettings">
```

The success value is `{ user: string, settings: string }`. This is usually
clearer than tuple destructuring when there are more than two values.

## Default Mode

Default mode short-circuits on the first failure.

```typescript
import { Effect } from "effect"

const program = Effect.all(
  [
    fetchProfile("u1"),
    fetchOrders("u1")
  ],
  { concurrency: 2 }
)

declare const fetchProfile: (
  id: string
) => Effect.Effect<string, "ProfileError">
declare const fetchOrders: (
  id: string
) => Effect.Effect<ReadonlyArray<string>, "OrdersError">
```

If either effect fails, the combined effect fails with that error type. With
concurrent execution, other already-started fibers are interrupted according to
normal Effect semantics.

## Either Mode

Use `{ mode: "either" }` when every effect should report success or failure as
data and the combined effect itself should not fail with those errors.

```typescript
import { Effect, Either } from "effect"

const program = Effect.all(
  [
    validateEmail("a@example.com"),
    validateEmail("bad")
  ],
  { concurrency: 2, mode: "either" }
).pipe(
  Effect.map((results) =>
    results.map((result) =>
      Either.match(result, {
        onLeft: (error) => `invalid: ${error}`,
        onRight: (email) => `valid: ${email}`
      })
    )
  )
)

declare const validateEmail: (
  input: string
) => Effect.Effect<string, "InvalidEmail">
```

Each position becomes `Either.Either<A, E>`. The error channel for the original
failures is removed from the combined effect.

## Validate Mode

Use `{ mode: "validate" }` when you want to run every effect and accumulate
failures.

```typescript
import { Effect } from "effect"

const program = Effect.all(
  [
    checkName("Ada"),
    checkName("")
  ],
  { concurrency: 2, mode: "validate" }
)

declare const checkName: (
  input: string
) => Effect.Effect<string, "EmptyName">
```

For iterables, validate mode fails with an array of `Option.Option<E>` values
that preserves input positions. For records and tuples, the returned shape
tracks which entries succeeded or failed according to the source typings.

## Concurrency

For more than five effects, specify concurrency deliberately.

```typescript
import { Effect } from "effect"

const program = Effect.all(
  userIds.map((id) => fetchUser(id)),
  { concurrency: 8 }
)

declare const userIds: ReadonlyArray<string>
declare const fetchUser: (
  id: string
) => Effect.Effect<string, "FetchUserFailed">
```

Use `concurrency: 1` for sequential collection. Use a bounded number for I/O.
Use `"unbounded"` only when the input size is already small and controlled.

See [concurrency/07-bounded-parallelism.md](../concurrency/07-bounded-parallelism.md)
and [anti-patterns/05-unbounded-parallelism.md](../anti-patterns/05-unbounded-parallelism.md)
before using unbounded fan-out.

## Discarding Results

Use `discard: true` when only effects matter.

```typescript
import { Effect } from "effect"

const program = Effect.all(
  [
    Effect.log("starting"),
    Effect.log("warming cache")
  ],
  { concurrency: 2, discard: true }
)
```

The success type becomes `void`, which avoids retaining unused arrays or
records.

## When Not To Use It

Do not use `Effect.all` when each step depends on the previous result. Use
`Effect.gen` or `flatMap`.

Do not use it to process a large dynamic collection without a concurrency
limit. Use `Effect.forEach` with `{ concurrency: N }` when mapping inputs to
effects.

Do not use default mode when you need all validation errors. Use validate mode,
`Effect.validateAll`, or `Effect.partition`.

## Cross-references

See also: [effect foreach](09-effect-foreach.md), [short-circuiting](11-short-circuiting.md), [generators](05-generators.md), [zip and tap](10-zip-and-tap.md).
