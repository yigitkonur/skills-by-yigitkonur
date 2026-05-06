# Unions And Literals
Represent alternatives with literals, enums, nullable wrappers, and tagged unions instead of ad hoc branching.

## Canonical import

Use the Effect v3 package barrel for normal Schema code:

```typescript
import { Schema } from "effect"
```

## Key rules

- **Literals:** Use `Schema.Literal` for exact strings, numbers, booleans, null, or combinations.
- **Unions:** Use `Schema.Union` for alternative schemas.
- **Enums:** Use `Schema.Enums` when consuming a TypeScript enum-like object.
- **Null wrappers:** Use `Schema.NullOr`, `Schema.UndefinedOr`, or `Schema.NullishOr` at compatibility boundaries.
- **Tagged variants:** Prefer `_tag` discriminants for variant families that evolve over time.

## Example

```typescript
import { Schema } from "effect"

const Plan = Schema.Literal("free", "team", "enterprise")

const CardPayment = Schema.Struct({
  method: Schema.Literal("card"),
  token: Schema.NonEmptyString
})

const InvoicePayment = Schema.Struct({
  method: Schema.Literal("invoice"),
  purchaseOrder: Schema.NonEmptyString
})

const Payment = Schema.Union(CardPayment, InvoicePayment)

const Customer = Schema.Struct({
  plan: Plan,
  payment: Schema.NullOr(Payment)
})
```

## Operational guidance

- Use literal unions for small closed sets instead of accepting arbitrary strings.
- Use `Schema.Enums` only when a runtime enum object already exists and is the contract.
- Use tagged unions when variants have different fields.
- Use the same discriminator key across all variants.
- Prefer a required discriminator to shape-based guessing.
- Use `Schema.NullOr` for external protocols that explicitly send null.
- Use `Schema.optionalWith(..., { as: "Option" })` for domain optionality instead of null in business types.
- Do not use `Schema.Any` inside unions to make parsing pass; it will swallow errors.
- Annotate variant schemas with identifiers before generating JSON Schema.
- Use branded fields inside variants for IDs and slugs.
- Keep literal values stable when persisted or sent over queues.
- When adding a variant, update union decoders and downstream pattern matches together.
- Use `Schema.TaggedClass` for variant behavior and class identity.
- Use `Schema.TaggedError` for variant failures in Effect error channels.
- Use parser error formatters to expose which union branch failed at a boundary.
- Check `Unions And Literals` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Unions And Literals` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Unions And Literals` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Unions And Literals` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Unions And Literals` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Unions And Literals` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Unions And Literals` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Unions And Literals` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Unions And Literals` schemas at the boundary where unknown data first appears.

## Cross-references

See also: [04-schema-tagged-class.md](04-schema-tagged-class.md), [05-schema-tagged-error.md](05-schema-tagged-error.md), [19-error-formatter.md](19-error-formatter.md), [10-decoding.md](10-decoding.md).
