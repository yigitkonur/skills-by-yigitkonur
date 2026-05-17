# Yield Without Star
Use this when a generator block yields an Effect value but receives the Effect object instead of its success value.

## Symptom — Bad Code
```typescript
import { Effect } from "effect"

declare const loadUser: (id: string) => Effect.Effect<{ readonly id: string }>

const program = Effect.gen(function* () {
  const user = yield loadUser("u-1")
  return user.id
})
```

## Why Bad
Plain `yield` follows JavaScript generator semantics.
It does not bind the success type of an Effect.
This is a high-signal assistant mistake in Effect generator code.

## Fix — Correct Pattern
```typescript
import { Effect } from "effect"

declare const loadUser: (id: string) => Effect.Effect<{ readonly id: string }>

const program = Effect.gen(function* () {
  const user = yield* loadUser("u-1")
  return user.id
})
```

## Cross-references
See also: [core generators](../core/05-generators.md), [creating effects](../core/02-creating-effects.md), [error handling](../error-handling/01-overview.md).
