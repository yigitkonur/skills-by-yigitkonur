# Null or Undefined in Domain Types
Use this when core domain records model absence with nullable values instead of Option.

## Symptom — Bad Code
```typescript
import { Effect } from "effect"

type User = {
  readonly id: string
  readonly email: string | null
}

declare const loadUser: Effect.Effect<User>

const domain = loadUser.pipe(
  Effect.map((user) => user.email?.toLowerCase())
)
```

## Why Bad
Nullable values force every consumer to rediscover the absence rule.
Effect code has `Option` and pattern matching so the none case is explicit.
Keep transport nullability at schema or adapter boundaries.

## Fix — Correct Pattern
```typescript
import { Effect, Option } from "effect"

type User = {
  readonly id: string
  readonly email: Option.Option<string>
}

declare const loadUser: Effect.Effect<User>

const domain = loadUser.pipe(
  Effect.map((user) =>
    Option.match(user.email, {
      onNone: () => "missing-email",
      onSome: (email) => email.toLowerCase()
    })
  )
)
```

## Cross-references
See also: [Option](../data-types/02-option.md), [pattern matching](../pattern-matching/01-overview.md), [schema nullability](../data-types/02-option.md).
