# Generic Error Types
Use this when failures are modeled as broad Error values or vague tags that cannot drive domain recovery.

## Symptom — Bad Code
```typescript
import { Effect } from "effect"

class NotFoundError extends Error {
  readonly _tag = "NotFoundError"
}

declare const loadUser: (id: string) => Effect.Effect<{ readonly id: string }, NotFoundError>
declare const loadOrder: (id: string) => Effect.Effect<{ readonly id: string }, NotFoundError>
```

## Why Bad
The same tag now means two different domain facts.
Callers must inspect messages, call-site context, or stack traces.
Effect error channels work best with stable tags and typed payloads.

## Fix — Correct Pattern
```typescript
import { Data, Effect } from "effect"

class UserNotFoundError extends Data.TaggedError("UserNotFoundError")<{ readonly userId: string }> {}
class OrderNotFoundError extends Data.TaggedError("OrderNotFoundError")<{ readonly orderId: string }> {}

declare const loadUser: (id: string) => Effect.Effect<{ readonly id: string }, UserNotFoundError>
declare const loadOrder: (id: string) => Effect.Effect<{ readonly id: string }, OrderNotFoundError>
```

## Notes
Prefer names like `UserNotFoundError`, `InvalidEmailAddressError`, or `PaymentProviderRejectedError` over generic transport-shaped names.

## Cross-references
See also: [tagged errors](../error-handling/03-schema-tagged-error.md), [catching errors](../error-handling/06-catch-all.md), [defects](../error-handling/08-defects.md).
