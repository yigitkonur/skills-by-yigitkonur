# catchTag
Use `Effect.catchTag` when one tag, or several tags handled identically, can be recovered without flattening the whole error union.

## What catchTag does

`Effect.catchTag` matches failures by their `_tag` field. In v3 it supports a single tag or a non-empty variadic list of tags followed by one handler.

The important type behavior is removal: handled tags are removed from the remaining `E` channel. That is why `catchTag` is usually better than `catchAll`.

## Single tag

```typescript
import { Data, Effect } from "effect"

class UserNotFound extends Data.TaggedError("UserNotFound")<{
  readonly userId: string
}> {}

class DatabaseUnavailable extends Data.TaggedError("DatabaseUnavailable")<{}> {}

const load = Effect.fail(new UserNotFound({ userId: "user_123" })) as Effect.Effect<
  string,
  UserNotFound | DatabaseUnavailable
>

const recovered = load.pipe(
  Effect.catchTag("UserNotFound", (error) =>
    Effect.succeed(`anonymous:${error.userId}`)
  )
)
```

After recovery, `DatabaseUnavailable` still remains in `E`. `UserNotFound` does not.

## Variadic tags, same handler

Use the variadic form when multiple tags share exactly the same recovery action:

```typescript
import { Data, Effect } from "effect"

class CacheMiss extends Data.TaggedError("CacheMiss")<{}> {}
class ReplicaLag extends Data.TaggedError("ReplicaLag")<{}> {}
class DatabaseUnavailable extends Data.TaggedError("DatabaseUnavailable")<{}> {}

const readModel = Effect.fail(new CacheMiss({})) as Effect.Effect<
  string,
  CacheMiss | ReplicaLag | DatabaseUnavailable
>

const withPrimaryFallback = readModel.pipe(
  Effect.catchTag("CacheMiss", "ReplicaLag", () =>
    Effect.succeed("read-from-primary")
  )
)
```

The handler receives `CacheMiss | ReplicaLag`. Only use this form when the same code is correct for every listed tag.

## Same handler vs dispatch

Use `catchTag` with multiple tags for one recovery strategy:

- cache miss and replica lag both fall back to primary
- unauthorized and session expired both redirect to sign-in
- stale version and conflict both re-read state

Use `catchTags` when each tag needs different logic:

- `UserNotFound` returns a placeholder
- `DatabaseUnavailable` schedules retry
- `Unauthorized` returns a permission response

## Keep handlers narrow

Handlers should preserve typed detail:

```typescript
import { Data, Effect } from "effect"

class RateLimited extends Data.TaggedError("RateLimited")<{
  readonly retryAfterSeconds: number
}> {}

const request = Effect.fail(new RateLimited({ retryAfterSeconds: 10 }))

const delayed = request.pipe(
  Effect.catchTag("RateLimited", (error) =>
    Effect.sleep(`${error.retryAfterSeconds} seconds`).pipe(
      Effect.as("retry-later")
    )
  )
)
```

The handler uses the structured field instead of parsing text.

## Avoid catchAll as the first tool

This is too broad:

```typescript
import { Data, Effect } from "effect"

class UserNotFound extends Data.TaggedError("UserNotFound")<{}> {}
class DatabaseUnavailable extends Data.TaggedError("DatabaseUnavailable")<{}> {}

const program = Effect.fail(new UserNotFound({})) as Effect.Effect<
  string,
  UserNotFound | DatabaseUnavailable
>

const flattened = program.pipe(
  Effect.catchAll(() => Effect.succeed("fallback"))
)
```

It handles both tags with no type-level distinction. Use it only when every failure in the current union truly has the same recovery behavior.

## Ordering

Place specific `catchTag` handlers near the operation that knows the recovery policy. Let higher layers see only unrecovered failures.

For example:

- repository layer handles cache miss
- application service handles authorization
- HTTP layer maps remaining domain errors into protocol responses
- process boundary logs or reports defects

This preserves local intent and prevents outer layers from becoming giant switchboards.

## Source note

The Effect 3.21.2 `catchTag` signature accepts a non-empty readonly array of tag literals followed by one handler. The handler receives `Extract<E, { _tag: K[number] }>` and the output error excludes the handled tags.

## Cross-references

See also: [02-data-tagged-error.md](02-data-tagged-error.md), [03-schema-tagged-error.md](03-schema-tagged-error.md), [05-catch-tags.md](05-catch-tags.md), [06-catch-all.md](06-catch-all.md), [13-error-remapping.md](13-error-remapping.md).
