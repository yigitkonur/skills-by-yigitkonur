# Sandboxing
Use `Effect.sandbox` when recovery needs the full `Cause<E>` in the typed error channel.

## What sandbox does

`Effect.sandbox(effect)` changes the error channel from `E` to `Cause.Cause<E>`:

`Effect<A, E, R>` becomes `Effect<A, Cause.Cause<E>, R>`.

That lets ordinary error combinators inspect failures, defects, interruptions, and cause composition.

`Effect.unsandbox` reverses the transformation:

`Effect<A, Cause.Cause<E>, R>` becomes `Effect<A, E, R>`.

## Basic sandboxing

```typescript
import { Cause, Data, Effect } from "effect"

class UserNotFound extends Data.TaggedError("UserNotFound")<{}> {}

const program = Effect.fail(new UserNotFound({}))

const inspected = program.pipe(
  Effect.sandbox,
  Effect.catchAll((cause) =>
    Effect.logError(Cause.pretty(cause)).pipe(
      Effect.as("reported")
    )
  )
)
```

The handler receives `Cause.Cause<UserNotFound>`.

## Restore with unsandbox

Use `unsandbox` after cause-aware handling if the normal typed error channel should continue:

```typescript
import { Cause, Data, Effect } from "effect"

class UserNotFound extends Data.TaggedError("UserNotFound")<{}> {}

const program = Effect.fail(new UserNotFound({}))

const restored = program.pipe(
  Effect.sandbox,
  Effect.mapError((cause) => Cause.map(cause, (error) => error)),
  Effect.unsandbox
)
```

This example does not change the error. It shows the shape: inspect or transform `Cause<E>`, then unsandbox when you are done.

## When to sandbox

Use sandboxing for:

- preserving finalizer failures
- distinguishing defects from typed failures in one recovery flow
- converting a cause into a sanitized boundary error
- testing cause structure
- logging a full cause before re-exposing typed errors

Do not sandbox just to catch a normal domain error. Use `catchTag` or `catchTags`.

## Cause-aware boundary mapping

```typescript
import { Cause, Data, Effect } from "effect"

class BoundaryFailure extends Data.TaggedError("BoundaryFailure")<{
  readonly kind: "failure" | "defect" | "interrupt"
}> {}

const classify = <E>(cause: Cause.Cause<E>) =>
  Cause.isDie(cause)
    ? "defect" as const
    : Cause.isInterrupted(cause)
      ? "interrupt" as const
      : "failure" as const

const boundary = Effect.dieMessage("unexpected").pipe(
  Effect.sandbox,
  Effect.catchAll((cause) =>
    Effect.fail(new BoundaryFailure({ kind: classify(cause) }))
  )
)
```

This is useful when a protocol has a small set of safe boundary error categories.

## sandbox vs catchAllCause

Use `catchAllCause` when you only need one cause-aware recovery point.

Use `sandbox` when you want to keep composing with ordinary error operators after moving `Cause<E>` into `E`.

```typescript
import { Cause, Effect } from "effect"

const direct = Effect.dieMessage("boom").pipe(
  Effect.catchAllCause((cause) => Effect.logError(Cause.pretty(cause)))
)

const composable = Effect.dieMessage("boom").pipe(
  Effect.sandbox,
  Effect.catchAll((cause) => Effect.logError(Cause.pretty(cause)))
)
```

Both are valid. Choose the one that keeps the local recovery clearer.

## Do not expose raw causes blindly

`Cause.pretty` can include sensitive implementation detail. At external boundaries, emit a sanitized tagged error or protocol response and keep raw cause details in internal logs or traces.

Do not make `Cause<E>` part of public domain APIs unless callers are Effect-aware and intentionally need it.

## Testing with sandbox

Sandboxing is useful in tests that assert defects or interruption:

```typescript
import { Cause, Effect } from "effect"

const program = Effect.dieMessage("boom").pipe(
  Effect.sandbox,
  Effect.either,
  Effect.map((outcome) =>
    outcome._tag === "Left" ? Cause.isDie(outcome.left) : false
  )
)
```

For normal domain failures, prefer asserting typed tags through `Effect.either` or `Effect.exit`.

## Cross-references

See also: [06-catch-all.md](06-catch-all.md), [07-cause-and-exit.md](07-cause-and-exit.md), [08-defects.md](08-defects.md), [12-error-taxonomy.md](12-error-taxonomy.md), [13-error-remapping.md](13-error-remapping.md).
