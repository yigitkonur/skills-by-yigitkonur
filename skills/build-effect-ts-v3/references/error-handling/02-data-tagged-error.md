# Data TaggedError
Use `Data.TaggedError` when you need lightweight typed errors with a stable `_tag` and yieldable failure behavior.

## API shape

`Data.TaggedError` is a v3 constructor exported from the `effect` barrel through `Data`. The source signature is:

`Data.TaggedError(tag)` returns a class constructor whose instances extend Effect's yieldable error base and include `readonly _tag: Tag`.

The common form is:

```typescript
import { Data } from "effect"

class UserNotFound extends Data.TaggedError("UserNotFound")<{
  readonly userId: string
}> {}
```

Instances are regular error values with structured fields:

```typescript
import { Data } from "effect"

class UserNotFound extends Data.TaggedError("UserNotFound")<{
  readonly userId: string
}> {}

const error = new UserNotFound({ userId: "user_123" })

const tag: "UserNotFound" = error._tag
const userId: string = error.userId
```

## Side-by-side with Schema.TaggedError

Both forms are valid in Effect v3. Use this comparison when choosing:

| Need | `Data.TaggedError` | `Schema.TaggedError` |
|---|---|---|
| Lightweight domain error | Good default | Also valid |
| Serializable across RPC or HTTP | Manual encoding discipline | Preferred |
| Runtime schema for fields | No | Yes |
| Minimal syntax | Shorter | More explicit |
| Field validation at boundary | Not by itself | Pair with Schema decoders |

Equivalent error definitions:

```typescript
import { Data, Schema } from "effect"

class DataUserNotFound extends Data.TaggedError("UserNotFound")<{
  readonly userId: string
}> {}

class SchemaUserNotFound extends Schema.TaggedError<SchemaUserNotFound>(
  "UserNotFound"
)("UserNotFound", {
  userId: Schema.String
}) {}
```

Equivalent yield behavior:

```typescript
import { Data, Effect, Schema } from "effect"

class DataUserNotFound extends Data.TaggedError("UserNotFound")<{
  readonly userId: string
}> {}

class SchemaUserNotFound extends Schema.TaggedError<SchemaUserNotFound>(
  "UserNotFound"
)("UserNotFound", {
  userId: Schema.String
}) {}

const dataProgram = Effect.gen(function* () {
  return yield* new DataUserNotFound({ userId: "user_123" })
})

const schemaProgram = Effect.gen(function* () {
  return yield* new SchemaUserNotFound({ userId: "user_123" })
})
```

Both programs fail through the typed error channel. Neither requires wrapping the instance in `Effect.fail`.

## Why instances are yieldable

The class returned by `Data.TaggedError` extends Effect's yieldable error base. Inside `Effect.gen`, yielding an instance is equivalent to failing with that instance, while preserving the concrete class type.

Use this:

```typescript
import { Data, Effect } from "effect"

class InvalidEmail extends Data.TaggedError("InvalidEmail")<{
  readonly value: string
}> {}

const parseEmail = (value: string) =>
  Effect.gen(function* () {
    if (!value.includes("@")) {
      return yield* new InvalidEmail({ value })
    }
    return value
  })
```

This gives TypeScript a clear exit point after the failing branch. The `return yield*` form is covered in [11-yield-fail-pattern.md](11-yield-fail-pattern.md).

## Add domain fields, not generic messages

Prefer structured fields callers can inspect:

```typescript
import { Data } from "effect"

class PaymentDeclined extends Data.TaggedError("PaymentDeclined")<{
  readonly paymentId: string
  readonly reason: "insufficient_funds" | "expired_card" | "blocked"
}> {}
```

The `_tag` identifies the case. Fields explain what the recovery code needs to know. Avoid a single generic `message` field unless the text is genuinely the domain payload.

## Catching Data tagged errors

`catchTag` narrows by `_tag`:

```typescript
import { Data, Effect } from "effect"

class PaymentDeclined extends Data.TaggedError("PaymentDeclined")<{
  readonly paymentId: string
}> {}

class FraudCheckUnavailable extends Data.TaggedError("FraudCheckUnavailable")<{}> {}

const charge = Effect.fail(new PaymentDeclined({ paymentId: "pay_123" }))

const handled = charge.pipe(
  Effect.catchTag("PaymentDeclined", (error) =>
    Effect.succeed({ status: "declined" as const, paymentId: error.paymentId })
  )
)
```

If the original `E` also contained `FraudCheckUnavailable`, that error remains in the output type. Only `PaymentDeclined` is removed.

## When Data.TaggedError is enough

Use it for:

- internal service domain errors
- local application workflows
- errors that do not cross a schema-aware transport boundary
- quick typed replacement for string failures
- tests and examples where serialization is not the point

If the error crosses RPC, HTTP, persistence, or message queues, prefer `Schema.TaggedError` so the shape is connected to a schema.

## Common mistakes

Do not use a plain class with `_tag` when the error is created inside `Effect.gen`. It can be caught by tag, but it is not yieldable by itself.

Do not collapse different recovery actions into one generic error. `Unauthorized`, `UserNotFound`, and `RateLimited` should be separate tags because callers react differently.

Do not use `Effect.dieMessage` for domain conditions. A missing record should be a typed failure, not a defect.

## Cross-references

See also: [01-overview.md](01-overview.md), [03-schema-tagged-error.md](03-schema-tagged-error.md), [04-catch-tag.md](04-catch-tag.md), [11-yield-fail-pattern.md](11-yield-fail-pattern.md), [13-error-remapping.md](13-error-remapping.md).
