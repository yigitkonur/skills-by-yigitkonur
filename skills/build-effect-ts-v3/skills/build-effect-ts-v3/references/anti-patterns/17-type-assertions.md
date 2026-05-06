# Type Assertions to Silence Effect Types
Use this when casts remove Effect errors, requirements, or decoded value uncertainty instead of fixing the source.

## Symptom — Bad Code
```typescript
import { Effect } from "effect"

declare const readUser: Effect.Effect<{ readonly id: string }, Error, "Database">

const unsafeProgram = readUser as any as Effect.Effect<{ readonly id: string }>
```

## Why Bad
The cast removes a required service and a failure without doing the work.
Effect types are the dependency graph and failure model.
This often appears after an assistant cannot satisfy a layer or schema requirement.

## Fix — Correct Pattern
```typescript
import { Context, Effect, Layer } from "effect"

class Database extends Context.Tag("Database")<Database, { readonly readUser: Effect.Effect<{ readonly id: string }, Error> }>() {}

declare const DatabaseLive: Layer.Layer<Database>

const program = Effect.gen(function* () {
  const database = yield* Database
  return yield* database.readUser
}).pipe(Effect.provide(DatabaseLive))
```

## Cross-references
See also: [schema decoding](../schema/10-decoding.md), [schema overview](../schema/01-overview.md), [migration](../migration/01-overview.md).
