# Branded Types
Use Schema.brand with real validation constraints so IDs and constrained primitives do not collapse into bare strings.

## Canonical import

Use the Effect v3 package barrel for normal Schema code:

```typescript
import { Schema } from "effect"
```

## Key rules

- **Purpose:** Brands create nominal types on top of validated values.
- **Anti-pattern:** A bare string alias gives no runtime validation and no type separation between different IDs.
- **Required constraint:** Brand only after a real schema constraint such as UUID, NonEmptyString, pattern, or numeric bounds.
- **Boundary:** Decode unknown data into branded values at the edge and then pass brands through services.
- **Composition:** Brands work with Struct, Class, TaggedClass, TaggedError, and JSON Schema annotations.

## Example

```typescript
import { Schema } from "effect"

type BareUserId = string

type BareOrderId = string

const sendReceipt = (userId: BareUserId, orderId: BareOrderId) => ({
  userId,
  orderId
})

sendReceipt("order_123", "user_456")
```

```typescript
import { Schema } from "effect"

const UserId = Schema.NonEmptyString.pipe(
  Schema.pattern(/^user_[a-z0-9]+$/),
  Schema.brand("UserId")
)

const OrderId = Schema.NonEmptyString.pipe(
  Schema.pattern(/^order_[a-z0-9]+$/),
  Schema.brand("OrderId")
)

const ReceiptRequest = Schema.Struct({
  userId: UserId,
  orderId: OrderId
})

type UserId = Schema.Schema.Type<typeof UserId>
type OrderId = Schema.Schema.Type<typeof OrderId>

const request = Schema.decodeUnknownSync(ReceiptRequest)({
  userId: "user_456",
  orderId: "order_123"
})
```

## Operational guidance

- Never brand `Schema.String` without a constraint unless the boundary truly accepts every string.
- Use `Schema.UUID.pipe(Schema.brand("UserId"))` for UUID-backed entity IDs.
- Use `Schema.NonEmptyString.pipe(Schema.pattern(...), Schema.brand(...))` for prefixed IDs.
- Use `Schema.Number.pipe(Schema.int(), Schema.greaterThan(0), Schema.brand("PositiveInt"))` for numeric IDs or counts.
- Decode once and carry the branded value through the domain; do not re-parse every function argument.
- Expose constructor helpers only when they call Schema decoding or trusted construction.
- Do not cast strings into branded values to silence types; that removes the runtime guarantee.
- Keep brand names stable and specific: `UserId`, `WorkspaceSlug`, `PositiveCents`.
- Use separate brands for values that share a wire representation but mean different things.
- Use annotations on the branded schema when it appears in public JSON Schema output.
- Brands are type-level markers; the encoded JSON usually remains the underlying primitive.
- Use brands inside Struct and Class fields rather than duplicating validators inline.
- When two services disagree about ID format, put the transform at the adapter boundary.
- For slugs, combine `NonEmptyString`, lower-case patterns, and length constraints.
- For emails, prefer a locally documented pattern over pretending regex is complete email validation.
- For money, brand an integer cents schema rather than using floating numbers.
- For external provider IDs, include the provider prefix in the brand name or regex.
- If a branded value is created from configuration, decode it through `Schema.Config` or the Config module boundary.
- If a brand needs methods, use `Schema.Class`; if it only needs identity, keep it as a brand.
- The trace test: every brand should answer what invalid value it rejects.
- Check `Branded Types` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.

## Cross-references

See also: [07-primitives.md](07-primitives.md), [13-filters.md](13-filters.md), [02-schema-struct.md](02-schema-struct.md), [15-json-schema.md](15-json-schema.md).
