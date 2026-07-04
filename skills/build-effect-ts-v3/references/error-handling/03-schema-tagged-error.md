# Schema TaggedError
Use `Schema.TaggedError` when a typed error must also have a schema-backed, serializable shape.

## API shape

`Schema.TaggedError` is the v3 schema-backed tagged error class builder. In Effect 3.21.2 it is exported from `Schema.ts` and imported from the `effect` barrel:

```typescript
import { Schema } from "effect"

class UserNotFound extends Schema.TaggedError<UserNotFound>(
  "UserNotFound"
)("UserNotFound", {
  userId: Schema.String
}) {}
```

The first call supplies the class identifier. The second call supplies the tag and field schemas. The resulting class has `_tag`, fields, schema metadata, and yieldable error behavior.

## Side-by-side with Data.TaggedError

Both forms are valid in Effect v3. The schema-backed form is the better default at transport boundaries:

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

const failWithData = Effect.gen(function* () {
  return yield* new DataUserNotFound({ userId: "user_123" })
})

const failWithSchema = Effect.gen(function* () {
  return yield* new SchemaUserNotFound({ userId: "user_123" })
})
```

The failing behavior is equivalent. The schema version carries runtime structure for decoding, encoding, documentation, and transport integration.

## Why prefer it for boundaries

Use `Schema.TaggedError` for errors crossing:

- RPC boundaries
- HTTP APIs
- queues or pub/sub topics
- persisted workflow state
- frontend/backend contracts
- generated client interfaces

At those boundaries, the error is part of the protocol. A schema-backed class makes the shape explicit and reusable.

## Field design

Fields should be protocol data, not incidental debugging text:

```typescript
import { Schema } from "effect"

class RateLimited extends Schema.TaggedError<RateLimited>(
  "RateLimited"
)("RateLimited", {
  operation: Schema.String,
  retryAfterSeconds: Schema.Number
}) {}
```

The caller can decide whether to retry, show a wait state, or schedule background work. That decision should not require parsing text.

## Custom message

You can add a computed message for diagnostics while keeping structured fields as the contract:

```typescript
import { Schema } from "effect"

class AuthorizationDenied extends Schema.TaggedError<AuthorizationDenied>(
  "AuthorizationDenied"
)("AuthorizationDenied", {
  subject: Schema.String,
  action: Schema.String
}) {
  get message(): string {
    return `${this.subject} cannot perform ${this.action}`
  }
}
```

The message is for humans and logs. Recovery code should branch on `_tag` and fields.

## Decoding foreign input

When an error arrives from the outside world, decode before treating it as trusted:

```typescript
import { Effect, Schema } from "effect"

class AuthorizationDenied extends Schema.TaggedError<AuthorizationDenied>(
  "AuthorizationDenied"
)("AuthorizationDenied", {
  subject: Schema.String,
  action: Schema.String
}) {}

const decodeAuthorizationDenied = (input: unknown) =>
  Schema.decodeUnknown(AuthorizationDenied)(input).pipe(
    Effect.mapError(() => new AuthorizationDenied({
      subject: "unknown",
      action: "decode"
    }))
  )
```

This keeps unknown data at the boundary and turns parse failure into a typed error the caller can handle.

## Yielding schema tagged errors

Schema tagged errors are yieldable like Data tagged errors:

```typescript
import { Effect, Schema } from "effect"

class InvalidPageSize extends Schema.TaggedError<InvalidPageSize>(
  "InvalidPageSize"
)("InvalidPageSize", {
  requested: Schema.Number,
  maximum: Schema.Number
}) {}

const validatePageSize = (requested: number) =>
  Effect.gen(function* () {
    const maximum = 100
    if (requested > maximum) {
      return yield* new InvalidPageSize({ requested, maximum })
    }
    return requested
  })
```

The `return yield*` form terminates the generator branch and narrows control flow for the success path.

## Catching schema tagged errors

`catchTag` and `catchTags` care about `_tag`, so schema and data tagged errors are handled the same way:

```typescript
import { Effect, Schema } from "effect"

class InvalidPageSize extends Schema.TaggedError<InvalidPageSize>(
  "InvalidPageSize"
)("InvalidPageSize", {
  requested: Schema.Number,
  maximum: Schema.Number
}) {}

const program = Effect.fail(new InvalidPageSize({ requested: 250, maximum: 100 }))

const recovered = program.pipe(
  Effect.catchTag("InvalidPageSize", (error) =>
    Effect.succeed({ pageSize: error.maximum })
  )
)
```

The handler sees a narrowed `InvalidPageSize` with schema-defined fields.

## Version boundary

This file documents the Effect v3 `Schema.TaggedError` API. Do not use similarly named v4-only helpers in v3 code. The v3 form is the two-call class builder shown above.

## When not to use it

Use `Data.TaggedError` when:

- the error is purely internal
- no runtime schema is needed
- the extra schema syntax distracts from a small local workflow
- a test only needs a lightweight discriminated failure

The goal is not to make every error schema-backed. The goal is to make every recoverable error typed, tagged, and shaped deliberately.

## Cross-references

See also: [01-overview.md](01-overview.md), [02-data-tagged-error.md](02-data-tagged-error.md), [04-catch-tag.md](04-catch-tag.md), [12-error-taxonomy.md](12-error-taxonomy.md), [13-error-remapping.md](13-error-remapping.md).
