# From neverthrow
Use this guide to migrate neverthrow-style results into Effect workflows and Effect's `Either` data type.

## Core Mapping

neverthrow is useful for explicit success and failure in synchronous or promise-returning code. Effect keeps that explicitness and adds lazy execution, interruption, scheduling, typed resource handling, and environment requirements.

| neverthrow shape | Effect shape |
|---|---|
| `Ok<A>` | `Either.right(a)` or `Effect.succeed(a)` |
| `Err<E>` | `Either.left(e)` or `Effect.fail(e)` |
| `Result<A, E>` | `Either.Either<A, E>` for pure values |
| `ResultAsync<A, E>` | `Effect.Effect<A, E, never>` |
| `map` | `Either.map` or `Effect.map` |
| `andThen` | `Either.flatMap` or `Effect.flatMap` |
| `match` | `Either.match` or Effect recovery combinators |

Use `Either` when the value is already computed. Use `Effect` when the computation should remain lazy, asynchronous, retryable, or interruptible.

## Side-by-side: Pure Validation

| neverthrow | Effect `Either` |
|---|---|
| ```typescript
import { err, ok, Result } from "neverthrow";

type NameError = { readonly _tag: "NameError"; readonly value: string };

const parseName = (value: string): Result<string, NameError> =>
  value.trim().length > 0
    ? ok(value.trim())
    : err({ _tag: "NameError", value });
``` | ```typescript
import { Either } from "effect";

type NameError = { readonly _tag: "NameError"; readonly value: string };

const parseName = (value: string): Either.Either<string, NameError> =>
  value.trim().length > 0
    ? Either.right(value.trim())
    : Either.left({ _tag: "NameError", value });
``` |

Do not force pure validation into `Effect` unless the caller is already composing an Effect workflow.

## Side-by-side: Async Result

| neverthrow `ResultAsync` | Effect |
|---|---|
| ```typescript
import { ResultAsync } from "neverthrow";

type User = { readonly id: string };
type UserError = { readonly _tag: "UserError"; readonly id: string };

const loadUser = (id: string): ResultAsync<User, UserError> =>
  ResultAsync.fromPromise(
    fetch(`/api/users/${id}`).then((r) => r.json() as Promise<User>),
    () => ({ _tag: "UserError", id }),
  );
``` | ```typescript
import { Data, Effect } from "effect";

type User = { readonly id: string };

class UserError extends Data.TaggedError("UserError")<{
  readonly id: string;
  readonly cause: unknown;
}> {}

const loadUser = (
  id: string,
): Effect.Effect<User, UserError, never> =>
  Effect.tryPromise({
    try: () => fetch(`/api/users/${id}`).then((r) => r.json() as Promise<User>),
    catch: (cause) => new UserError({ id, cause }),
  });
``` |

The Effect version keeps the error typed and adds runtime features without changing the success value.

## Converting Effect to Either

Use `Effect.either` when a caller wants a value-level success or failure:

```typescript
import { Effect, Either } from "effect";

const loadUserEither = (
  id: string,
): Effect.Effect<Either.Either<User, UserError>, never, never> =>
  Effect.either(loadUser(id));
```

This does not run the effect. It changes the success type to `Either.Either<User, UserError>` and removes the failure channel.

## Converting Either to Effect

```typescript
import { Effect, Either } from "effect";

const fromParsedName = (
  value: Either.Either<string, NameError>,
): Effect.Effect<string, NameError, never> =>
  Either.match(value, {
    onLeft: (error) => Effect.fail(error),
    onRight: (name) => Effect.succeed(name),
  });
```

This is useful when pure validation is the first step in a larger workflow.

## Side-by-side: Match and Recover

| neverthrow match | Effect recovery |
|---|---|
| ```typescript
const label = parseName(input).match(
  (name) => name.toUpperCase(),
  () => "ANONYMOUS",
);
``` | ```typescript
import { Effect } from "effect";

const label = (input: string): Effect.Effect<string, never, never> =>
  Either.match(parseName(input), {
    onLeft: () => Effect.succeed("ANONYMOUS"),
    onRight: (name) => Effect.succeed(name.toUpperCase()),
  });
``` |

Use value-level matching when you stay in `Either`. Use typed recovery when composing Effect workflows.

## Error Classes

For larger migrations, prefer `Data.TaggedError` classes over plain objects:

```typescript
import { Data } from "effect";

class PaymentDeclinedError extends Data.TaggedError("PaymentDeclinedError")<{
  readonly paymentId: string;
  readonly reason: string;
}> {}
```

Tagged classes give a stable `_tag`, structured fields, and compatibility with `Effect.catchTag`.

## Migration Steps

1. Keep pure neverthrow validation as `Either` first.
2. Convert `ResultAsync<A, E>` leaf functions to `Effect<A, E, never>`.
3. Replace `andThen` chains with `Effect.flatMap` or `Effect.gen`.
4. Use `Effect.either` only at interop boundaries that still expect value-level failure.
5. Use `Either.match` with `Effect.fail` and `Effect.succeed` to lift pure validation into larger workflows.
6. Replace plain object errors with tagged error classes when recovery by tag is useful.

## Anti-patterns

| Anti-pattern | Replacement |
|---|---|
| Wrapping an `Either` in `Effect.succeed` when the failure should short-circuit | Match the `Either` into `Effect.fail` or `Effect.succeed` |
| Running the effect only to build an `Either` in library code | Return `Effect.either(program)` |
| Migrating every pure validation into async workflows | Keep pure validation as `Either` |
| Using one generic error object for all branches | Use tagged errors for recoverable branches |
| Treating value-level failure and typed Effect failure as the same boundary | Choose one representation per API surface |

## Cross-references

See also: [03-from-trycatch.md](03-from-trycatch.md), [04-from-fp-ts.md](04-from-fp-ts.md), [07-gradual-adoption.md](07-gradual-adoption.md), [08-portable-utility.md](08-portable-utility.md).
