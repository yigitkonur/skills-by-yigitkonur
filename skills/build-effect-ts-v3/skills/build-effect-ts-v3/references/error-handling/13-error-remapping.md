# Error Remapping
Use remapping to translate lower-level failures into the vocabulary of the current layer without losing typed structure.

## Why remap

Each layer should expose errors its callers understand. A repository can know about SQL errors. A domain service should usually expose domain or application errors. An HTTP adapter should expose protocol responses.

Remapping is not flattening. Preserve tags and structured fields.

## mapError

Use `Effect.mapError` for pure one-to-one translation:

```typescript
import { Data, Effect } from "effect"

class SqlUnavailable extends Data.TaggedError("SqlUnavailable")<{
  readonly queryName: string
}> {}

class UserRepositoryUnavailable extends Data.TaggedError(
  "UserRepositoryUnavailable"
)<{
  readonly operation: string
}> {}

const query = Effect.fail(new SqlUnavailable({ queryName: "findUser" }))

const repository = query.pipe(
  Effect.mapError((error) =>
    new UserRepositoryUnavailable({ operation: error.queryName })
  )
)
```

Use this when no effectful work is needed to create the new error.

## catchTag remapping

Use `catchTag` when only one error in a union should be translated:

```typescript
import { Data, Effect } from "effect"

class CacheMiss extends Data.TaggedError("CacheMiss")<{}> {}
class SqlUnavailable extends Data.TaggedError("SqlUnavailable")<{}> {}
class UserNotFound extends Data.TaggedError("UserNotFound")<{
  readonly userId: string
}> {}

const load = Effect.fail(new CacheMiss({})) as Effect.Effect<
  string,
  CacheMiss | SqlUnavailable
>

const mapped = load.pipe(
  Effect.catchTag("CacheMiss", () =>
    Effect.fail(new UserNotFound({ userId: "user_123" }))
  )
)
```

`SqlUnavailable` remains untouched.

## catchTags remapping

Use `catchTags` when different lower-level tags map differently:

```typescript
import { Data, Effect } from "effect"

class DriverUnavailable extends Data.TaggedError("DriverUnavailable")<{}> {}
class DuplicateKey extends Data.TaggedError("DuplicateKey")<{}> {}
class StoreUnavailable extends Data.TaggedError("StoreUnavailable")<{}> {}
class Conflict extends Data.TaggedError("Conflict")<{}> {}

const write = Effect.fail(new DuplicateKey({})) as Effect.Effect<
  void,
  DriverUnavailable | DuplicateKey
>

const domainWrite = write.pipe(
  Effect.catchTags({
    DriverUnavailable: () => Effect.fail(new StoreUnavailable({})),
    DuplicateKey: () => Effect.fail(new Conflict({}))
  })
)
```

Each mapping preserves a distinct policy.

## Preserve cause when needed

If you need defect or interruption context, use sandboxing or cause-aware operators rather than `mapError`:

```typescript
import { Cause, Data, Effect } from "effect"

class BoundaryFailure extends Data.TaggedError("BoundaryFailure")<{
  readonly renderedCause: string
}> {}

const boundary = Effect.dieMessage("unexpected").pipe(
  Effect.catchAllCause((cause) =>
    Effect.fail(new BoundaryFailure({ renderedCause: Cause.pretty(cause) }))
  )
)
```

Only do this at a boundary that intentionally exposes a sanitized cause representation.

## Avoid generic remapping

This is usually too lossy:

```typescript
import { Data, Effect } from "effect"

class OperationFailed extends Data.TaggedError("OperationFailed")<{}> {}

const bad = Effect.fail("anything").pipe(
  Effect.mapError(() => new OperationFailed({}))
)
```

The caller cannot tell whether to retry, show validation, request sign-in, or report an outage. Prefer distinct tags.

## Remapping checklist

- Does the new tag belong to the current layer?
- Are retryable and non-retryable cases still separate?
- Are field names useful to the caller?
- Did defects remain defects unless intentionally converted at a boundary?
- Did you avoid parsing human text?

If any answer is no, remodel the error union before adding handlers.

## Cross-references

See also: [04-catch-tag.md](04-catch-tag.md), [05-catch-tags.md](05-catch-tags.md), [06-catch-all.md](06-catch-all.md), [12-error-taxonomy.md](12-error-taxonomy.md), [14-sandboxing.md](14-sandboxing.md).
