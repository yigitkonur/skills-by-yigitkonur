# Error Taxonomy
Use this taxonomy to decide what kind of error you are modeling and which recovery strategy is appropriate.

## Taxonomy table

| error category | examples | should retry? | how to handle |
|---|---|---:|---|
| Domain absence | `UserNotFound`, `OrderMissing` | No | Return a typed tagged error; caller chooses fallback or user response |
| Domain rejection | `PaymentDeclined`, `Unauthorized` | No | Keep distinct tags; do not collapse into infrastructure errors |
| Validation | `InvalidEmail`, `MissingField` | No | Accumulate when useful; return field-level tagged errors |
| Transient infrastructure | `DatabaseUnavailable`, `RateLimited` | Yes, with policy | Include retry metadata; recover with retry or propagate to supervisor |
| Permanent infrastructure | `UnsupportedProvider`, `SchemaMismatch` | Usually no | Map to a typed boundary or configuration error |
| Foreign exception | unknown callback or promise rejection | Maybe | Convert at the boundary into a typed tagged error or defect |
| Defect | invariant failure, programmer bug | No | Use `Effect.die`, `dieMessage`, `orDie`, or report through `Cause` |
| Interruption | fiber cancellation, timeout cancellation | No direct retry | Preserve cancellation semantics; do not model as domain failure |
| Cancel requested by domain | user canceled checkout | No | If it is business state, model as a domain tagged error |
| Boundary protocol error | malformed request, decode failure | No until input changes | Use schema-backed tagged errors or protocol response mapping |

## Domain errors

Domain errors are expected outcomes in the business model. They should be tagged and specific:

```typescript
import { Data } from "effect"

class OrderAlreadyShipped extends Data.TaggedError("OrderAlreadyShipped")<{
  readonly orderId: string
}> {}
```

Do not merge unrelated domain errors because they share an HTTP status or UI message.

## Validation errors

Validation errors are deterministic until the input changes. Retrying the same input is wasteful.

Use accumulation when the caller needs all field failures:

```typescript
import { Data, Effect } from "effect"

class MissingField extends Data.TaggedError("MissingField")<{
  readonly field: string
}> {}

const validateName = (name: string) =>
  name.length > 0
    ? Effect.succeed(name)
    : Effect.fail(new MissingField({ field: "name" }))
```

## Transient infrastructure

Transient infrastructure failures need metadata:

```typescript
import { Data } from "effect"

class RateLimited extends Data.TaggedError("RateLimited")<{
  readonly operation: string
  readonly retryAfterSeconds: number
}> {}
```

The retry policy should read fields, not parse messages. If no retry metadata exists, model the best typed shape you can and apply a conservative policy at the boundary.

## Foreign errors

Foreign errors enter through promises, callbacks, decoders, drivers, and platform APIs. Convert them immediately:

```typescript
import { Data, Effect } from "effect"

class EmailProviderUnavailable extends Data.TaggedError(
  "EmailProviderUnavailable"
)<{
  readonly operation: string
}> {}

const sendEmail = Effect.tryPromise({
  try: () => fetch("https://mail.example/send"),
  catch: () => new EmailProviderUnavailable({ operation: "send" })
})
```

After conversion, internal services should not depend on unknown foreign shapes.

## Defects

Defects are not retryable domain outcomes. They mean the fiber hit a bug or unrecoverable condition. Report them, preserve the cause, and avoid hiding them under generic tagged errors.

Use `orDie` only when escalation is intentional:

```typescript
import { Data, Effect } from "effect"

class RequiredConfigMissing extends Data.TaggedError("RequiredConfigMissing")<{}> {}

const boot = Effect.fail(new RequiredConfigMissing({})).pipe(
  Effect.orDie
)
```

## Interruption and cancellation

Interruption is a runtime cancellation signal. Do not convert it into `OperationFailed`.

If cancellation is a business event, model that separately:

```typescript
import { Data } from "effect"

class CheckoutCanceled extends Data.TaggedError("CheckoutCanceled")<{
  readonly checkoutId: string
}> {}
```

That is different from a fiber being interrupted by timeout or shutdown.

## Retry rule

Retry only when all are true:

1. The operation is idempotent or has a safe retry protocol.
2. The error category is transient.
3. The retry policy is bounded.
4. The caller still wants the work.

Validation, authorization, not-found, and domain rejection errors usually fail until input or permissions change.

## Boundary mapping rule

At every boundary, map from the boundary vocabulary into the next layer's vocabulary:

- driver errors become repository errors
- repository errors become application errors
- application errors become protocol responses
- defects become internal reports plus sanitized protocol failures

The mapping should preserve retry semantics. A retryable infrastructure failure should not become a non-retryable validation error.

## Anti-collapse examples

Keep these separate:

| Do not collapse | Reason |
|---|---|
| `UserNotFound` and `DatabaseUnavailable` | one is absence, one is transient infrastructure |
| `Unauthorized` and `SessionExpired` | one may need permission changes, one may refresh |
| `InvalidEmail` and `EmailProviderUnavailable` | one is input, one is integration health |
| `CheckoutCanceled` and fiber interruption | one is business state, one is runtime cancellation |

When tags stay specific, callers can choose the correct policy without guessing.

## Minimum useful fields

Each error should carry enough data for the next decision:

- not-found errors need the missing identifier
- validation errors need the field or path
- retryable errors need operation and retry guidance when known
- authorization errors need subject and action when safe
- boundary errors need a stable public code or tag

Avoid stuffing raw foreign error objects into domain errors. Preserve internal details in logs or traces and expose typed, intentional fields.

## Cross-references

See also: [01-overview.md](01-overview.md), [09-recovery-patterns.md](09-recovery-patterns.md), [10-error-accumulation.md](10-error-accumulation.md), [13-error-remapping.md](13-error-remapping.md), [14-sandboxing.md](14-sandboxing.md).
