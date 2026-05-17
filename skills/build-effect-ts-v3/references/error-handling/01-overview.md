# Error Handling Overview
Use this when deciding whether a problem belongs in the typed error channel, the defect channel, or the interruption path.

## The core model

An Effect value carries three type parameters:

`Effect.Effect<A, E, R>`

`A` is the success value, `E` is the expected failure type, and `R` is the required context. Error handling in Effect starts by protecting the `E` channel from becoming an untyped dumping ground.

Expected failures are business or integration outcomes the caller can react to. Missing users, invalid input, unavailable upstream services, and authorization denials are failures. They should appear in `E`.

Defects are bugs, invariant violations, or unrecoverable runtime conditions. They do not appear in `E`. They live in the internal `Cause` and are normally allowed to terminate the fiber.

Interruption is cancellation. It is not a domain failure and should not be turned into a fake domain error unless you are at a boundary that explicitly needs cancellation reporting.

## Typed errors are not exceptions

Use tagged errors for recoverable cases:

```typescript
import { Data, Effect } from "effect"

class UserNotFound extends Data.TaggedError("UserNotFound")<{
  readonly userId: string
}> {}

const loadUser = (userId: string) =>
  Effect.gen(function* () {
    return yield* new UserNotFound({ userId })
  })
```

The error type of `loadUser` includes `UserNotFound`. Callers can recover with `Effect.catchTag` or `Effect.catchTags` and TypeScript knows which branch remains afterward.

## Failures vs defects

Use `Effect.fail` or a yieldable tagged error when the caller should decide what happens next. Use `Effect.die`, `Effect.dieMessage`, `Effect.orDie`, or `Effect.orDieWith` when a typed failure should become an unrecoverable defect.

Typical failure examples:

- `UserNotFound`
- `InvalidEmail`
- `PaymentDeclined`
- `RateLimited`
- `DatabaseUnavailable`

Typical defect examples:

- impossible branch reached
- corrupted in-memory invariant
- programmer bug
- library callback violated its contract
- intentionally escalated unrecoverable failure

## Prefer tagged errors

Tagged errors give every failure a stable `_tag`. That unlocks narrow recovery:

```typescript
import { Data, Effect } from "effect"

class RateLimited extends Data.TaggedError("RateLimited")<{
  readonly retryAfterSeconds: number
}> {}

class Unauthorized extends Data.TaggedError("Unauthorized")<{}> {}

const request = Effect.fail(new RateLimited({ retryAfterSeconds: 30 }))

const recovered = request.pipe(
  Effect.catchTag("RateLimited", (error) =>
    Effect.succeed(`retry after ${error.retryAfterSeconds}s`)
  )
)
```

After the `RateLimited` handler, only unhandled failure types remain in `E`. That is the main reason `catchTag` and `catchTags` should be the default recovery tools.

## The typed-error discipline

Use this decision order:

1. Can the caller reasonably recover or choose a different path?
   Put it in the `E` channel as a tagged error.
2. Is this a validation or decoding boundary?
   Return a typed validation or parse error; do not collapse it into a string.
3. Is this a bug or impossible condition?
   Use a defect and keep it out of the domain error union.
4. Is this cancellation?
   Preserve interruption unless the boundary explicitly models cancellation.

This keeps downstream code honest. A user interface can branch on `Unauthorized`; a retry loop can branch on `RateLimited`; a supervisor can inspect defects with `Cause`.

## What not to do

Avoid broad untyped failures:

```typescript
import { Effect } from "effect"

const bad = Effect.fail("request failed")
```

A string gives no stable `_tag`, no structured fields, and no safe recovery branch. It tends to force `catchAll` everywhere.

Avoid defect-shaped domain failures:

```typescript
import { Effect } from "effect"

const bad = Effect.dieMessage("user not found")
```

The caller cannot recover from this through the typed error channel. If a caller should handle it, model it as a tagged error.

## Recovery shape

Use these operators by default:

- `Effect.catchTag` for one tag or several tags handled by the same function.
- `Effect.catchTags` for tag-specific dispatch.
- `Effect.mapError` for pure remapping of the `E` channel.
- `Effect.catchAllCause` only when you need the full `Cause`.
- `Effect.catchAllDefect` only at supervision or process boundary code.

Use `catchAll` sparingly. It is valid v3, but it erases the benefits of discriminated recovery when used as the first tool.

## Boundary rule

At an external boundary, convert foreign errors into domain-specific tagged errors as soon as possible. Keep unknown values out of service internals.

```typescript
import { Data, Effect } from "effect"

class StorageUnavailable extends Data.TaggedError("StorageUnavailable")<{
  readonly operation: string
}> {}

const readObject = Effect.tryPromise({
  try: () => fetch("https://storage.example/object"),
  catch: () => new StorageUnavailable({ operation: "readObject" })
})
```

After this conversion, the rest of the program handles `StorageUnavailable`, not a foreign exception shape.

## Source anchors

In Effect 3.21.2 source:

- `Data.TaggedError` is exported from `Data.ts`.
- `Schema.TaggedError` is exported from `Schema.ts`.
- `catchTag`, `catchTags`, `catchAll`, `catchAllCause`, and `catchAllDefect` are exported from `Effect.ts`.
- `Cause` stores failures, defects, interruption, sequential composition, and parallel composition.
- `Exit.Failure` contains a `Cause<E>`.

## Cross-references

See also: [02-data-tagged-error.md](02-data-tagged-error.md), [03-schema-tagged-error.md](03-schema-tagged-error.md), [04-catch-tag.md](04-catch-tag.md), [07-cause-and-exit.md](07-cause-and-exit.md), [12-error-taxonomy.md](12-error-taxonomy.md).
