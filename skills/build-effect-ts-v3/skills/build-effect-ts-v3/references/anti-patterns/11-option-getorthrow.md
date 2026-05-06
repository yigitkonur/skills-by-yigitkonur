# Option GetOrThrow
Use this when an Option is unwrapped by throwing instead of matching both cases.

## Symptom — Bad Code
```typescript
import { Effect, Option } from "effect"

declare const findEmail: Effect.Effect<Option.Option<string>>

const program = findEmail.pipe(
  Effect.map((email) => Option.getOrThrow(email).toLowerCase())
)
```

## Why Bad
The type says absence is expected, but the implementation turns none into a crash.
Callers lose recovery through the typed error channel.
The branch decision is hidden inside unsafe extraction.

## Fix — Correct Pattern
```typescript
import { Effect, Option } from "effect"

declare const findEmail: Effect.Effect<Option.Option<string>>

const program = findEmail.pipe(
  Effect.map((email) =>
    Option.match(email, {
      onNone: () => "missing-email",
      onSome: (value) => value.toLowerCase()
    })
  )
)
```

## Cross-references
See also: [Option](../data-types/02-option.md), [pattern matching](../pattern-matching/01-overview.md), [schema nullability](../data-types/02-option.md).
