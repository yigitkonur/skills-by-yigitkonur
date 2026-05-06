# CatchAll Instead of CatchTag
Use this when code catches every failure even though the error channel has specific tagged failures.

## Symptom — Bad Code
```typescript
import { Data, Effect } from "effect"

class UserNotFoundError extends Data.TaggedError("UserNotFoundError")<{ readonly id: string }> {}
class DatabaseError extends Data.TaggedError("DatabaseError")<{ readonly reason: string }> {}

declare const loadUser: Effect.Effect<{ readonly id: string }, UserNotFoundError | DatabaseError>

const recovered = loadUser.pipe(
  Effect.catchAll(() => Effect.succeed({ id: "anonymous" }))
)
```

## Why Bad
The handler treats an expected missing user and a database outage as the same thing.
Known tags let callers recover narrowly and leave unrelated failures visible.
A catch-all belongs at translation boundaries or after narrower handlers.

## Fix — Correct Pattern
```typescript
import { Data, Effect } from "effect"

class UserNotFoundError extends Data.TaggedError("UserNotFoundError")<{ readonly id: string }> {}
class DatabaseError extends Data.TaggedError("DatabaseError")<{ readonly reason: string }> {}

declare const loadUser: Effect.Effect<{ readonly id: string }, UserNotFoundError | DatabaseError>

const recovered = loadUser.pipe(
  Effect.catchTag("UserNotFoundError", () => Effect.succeed({ id: "anonymous" }))
)
```

## Cross-references
See also: [tagged errors](../error-handling/03-schema-tagged-error.md), [catching errors](../error-handling/06-catch-all.md), [defects](../error-handling/08-defects.md).
