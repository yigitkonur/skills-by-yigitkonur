# catchTags
Use `Effect.catchTags` when several tagged failures need different handlers in one recovery block.

## What catchTags does

`Effect.catchTags` accepts an object keyed by `_tag`. Each key receives the error type for that tag. Handled tags are removed from the remaining error channel; handler failures are added.

Use it when dispatch is part of the local policy.

## Basic dispatch

```typescript
import { Data, Effect } from "effect"

class UserNotFound extends Data.TaggedError("UserNotFound")<{
  readonly userId: string
}> {}

class DatabaseUnavailable extends Data.TaggedError("DatabaseUnavailable")<{
  readonly operation: string
}> {}

const loadUser = Effect.fail(new UserNotFound({ userId: "user_123" })) as Effect.Effect<
  string,
  UserNotFound | DatabaseUnavailable
>

const recovered = loadUser.pipe(
  Effect.catchTags({
    UserNotFound: (error) => Effect.succeed(`anonymous:${error.userId}`),
    DatabaseUnavailable: (error) =>
      Effect.fail(new DatabaseUnavailable({ operation: error.operation }))
  })
)
```

Each handler receives the narrowed class for its tag.

## Prefer explicit tag keys

The object form documents recovery policy:

- `UserNotFound` can be turned into an anonymous profile.
- `InvalidInput` can be returned to the caller.
- `DatabaseUnavailable` may remain a failure for retry or supervision.

That is clearer than a broad handler with conditional checks.

## Handler result types

Handlers can produce success values, new failures, or require services:

```typescript
import { Data, Effect } from "effect"

class SessionExpired extends Data.TaggedError("SessionExpired")<{}> {}
class Unauthorized extends Data.TaggedError("Unauthorized")<{}> {}
class AuditUnavailable extends Data.TaggedError("AuditUnavailable")<{}> {}

const action = Effect.fail(new SessionExpired({})) as Effect.Effect<
  "ok",
  SessionExpired | Unauthorized
>

const handled = action.pipe(
  Effect.catchTags({
    SessionExpired: () => Effect.succeed("refresh" as const),
    Unauthorized: () => Effect.fail(new AuditUnavailable({}))
  })
)
```

The output value type includes `"ok" | "refresh"`, and the output error type includes `AuditUnavailable`.

## When not to use catchTags

Do not use `catchTags` when all handled tags share the same behavior. Use the variadic `catchTag` form instead.

Do not centralize every error in one outer `catchTags` block. Local operations should recover what they understand and let the rest remain typed.

Do not map every tag into one generic error unless the boundary truly requires it. You lose machine-readable intent.

## Exhaustiveness mindset

`catchTags` does not require every tag in `E` to be handled. That is a feature. Remaining errors keep flowing upward.

Use the type that remains after the handler as a design signal:

- If a remaining error belongs here, add a handler.
- If it belongs to the caller, leave it in `E`.
- If it should never happen, revisit the upstream model before converting it to a defect.

## Error remapping

A handler may translate infrastructure detail into a domain error:

```typescript
import { Data, Effect } from "effect"

class SqlUnavailable extends Data.TaggedError("SqlUnavailable")<{}> {}
class UserRepositoryUnavailable extends Data.TaggedError(
  "UserRepositoryUnavailable"
)<{}> {}

const query = Effect.fail(new SqlUnavailable({}))

const repositoryError = query.pipe(
  Effect.catchTags({
    SqlUnavailable: () => Effect.fail(new UserRepositoryUnavailable({}))
  })
)
```

For pure one-to-one remapping, `Effect.mapError` may be shorter. Use `catchTags` when remapping needs effects or tag-specific branching.

## Source note

The Effect 3.21.2 `catchTags` signature keys the handler object by tags from `Extract<E, { _tag: string }>["_tag"]`. Unknown keys are rejected when the input error type is known.

That means misspelled tag names are usually type errors, not runtime surprises. This is another reason to prefer tagged error classes over strings or generic `Error` values.

## Practical routing

Use `catchTags` in reference material when the example teaches policy. Use `catchTag` when the example teaches one narrow recovery. Use `mapError` when the example teaches pure translation.

## Cross-references

See also: [04-catch-tag.md](04-catch-tag.md), [06-catch-all.md](06-catch-all.md), [09-recovery-patterns.md](09-recovery-patterns.md), [12-error-taxonomy.md](12-error-taxonomy.md), [13-error-remapping.md](13-error-remapping.md).
