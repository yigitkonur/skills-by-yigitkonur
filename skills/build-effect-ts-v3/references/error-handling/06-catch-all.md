# Broad Catching
Use broad catching only when the whole remaining error channel has one valid recovery policy or when you intentionally need a full `Cause`.

## The broad tools

Effect v3 exposes several broad recovery operators:

- `Effect.catchAll` handles every typed failure in `E`.
- `Effect.catchAllCause` handles the full `Cause<E>`, including defects and interruption.
- `Effect.catchAllDefect` handles defects.
- `Effect.catchSome` handles selected typed failures by returning `Option`.
- `Effect.catchSomeCause` and `Effect.catchSomeDefect` are partial variants for cause and defect inspection.

These are valid v3 APIs. They are not the default for domain error handling.

## catchAll

Use `catchAll` when every remaining typed failure has the same recovery:

```typescript
import { Data, Effect } from "effect"

class PrimaryUnavailable extends Data.TaggedError("PrimaryUnavailable")<{}> {}
class ReplicaUnavailable extends Data.TaggedError("ReplicaUnavailable")<{}> {}

const read = Effect.fail(new PrimaryUnavailable({})) as Effect.Effect<
  string,
  PrimaryUnavailable | ReplicaUnavailable
>

const fallback = read.pipe(
  Effect.catchAll(() => Effect.succeed("stale-cache"))
)
```

This is reasonable because both failures intentionally recover to the same stale cache value.

## catchAllCause

Use `catchAllCause` when you need defect, interruption, or cause composition information:

```typescript
import { Cause, Effect } from "effect"

const task = Effect.dieMessage("unexpected invariant")

const inspected = task.pipe(
  Effect.catchAllCause((cause) =>
    Effect.logError(Cause.pretty(cause)).pipe(
      Effect.as("reported")
    )
  )
)
```

The handler receives `Cause<E>`, not just a domain error. This is boundary or supervision code.

## catchAllDefect

Use `catchAllDefect` for controlled defect reporting:

```typescript
import { Effect } from "effect"

const task = Effect.dieMessage("render invariant failed")

const reported = task.pipe(
  Effect.catchAllDefect((defect) =>
    Effect.logError(String(defect)).pipe(
      Effect.as("defect-reported")
    )
  )
)
```

Do not use it to hide programmer bugs in normal service code. It belongs at edges where reporting, metrics, or graceful shutdown are required.

## catchSome

Use `catchSome` when matching cannot be expressed by `_tag` alone:

```typescript
import { Data, Effect, Option } from "effect"

class HttpFailure extends Data.TaggedError("HttpFailure")<{
  readonly status: number
}> {}

const request = Effect.fail(new HttpFailure({ status: 404 }))

const recovered = request.pipe(
  Effect.catchSome((error) =>
    error.status === 404
      ? Option.some(Effect.succeed("missing"))
      : Option.none()
  )
)
```

Prefer `catchTag` when a tag is enough. Use `catchSome` for predicates inside one tag.

## Narrow before broad

A common pattern is:

1. `catchTag` for the precise cases the current layer owns.
2. `catchTags` for local dispatch.
3. `mapError` for pure remapping.
4. `catchAll` only after the remaining union is intentionally homogeneous.
5. `catchAllCause` only at cause-aware boundaries.

This order preserves typed discipline while still allowing broad recovery when justified.

## Broad catching risks

Broad catching can:

- hide new error variants introduced upstream
- erase retry policy differences
- force string parsing
- accidentally swallow defects
- make tests pass while production behavior degrades

If a broad handler contains a conditional tree, that is usually a sign it should be `catchTags` or `catchSome`.

## Cross-references

See also: [04-catch-tag.md](04-catch-tag.md), [05-catch-tags.md](05-catch-tags.md), [07-cause-and-exit.md](07-cause-and-exit.md), [08-defects.md](08-defects.md), [14-sandboxing.md](14-sandboxing.md).
