# Throw Inside Effect.gen
Use this when expected domain failure is thrown inside an Effect generator instead of returned through the error channel.

## Symptom — Bad Code
```typescript
import { Effect } from "effect"

class UserNotFoundError extends Error {
  readonly _tag = "UserNotFoundError"
}

const loadUser = (id: string) =>
  Effect.gen(function* () {
    if (id.length === 0) {
      throw new UserNotFoundError("missing id")
    }
    return { id }
  })
```

## Why Bad
Throwing reports a defect instead of an expected typed failure.
Callers cannot recover with tag-specific handlers.
Use defects for programmer bugs, not normal domain branches.

## Fix — Correct Pattern
```typescript
import { Data, Effect } from "effect"

class UserNotFoundError extends Data.TaggedError("UserNotFoundError")<{
  readonly id: string
}> {}

const loadUser = (id: string) =>
  Effect.gen(function* () {
    if (id.length === 0) {
      return yield* Effect.fail(new UserNotFoundError({ id }))
    }
    return { id }
  })
```

## Cross-references
See also: [tagged errors](../error-handling/03-schema-tagged-error.md), [catching errors](../error-handling/06-catch-all.md), [defects](../error-handling/08-defects.md).
