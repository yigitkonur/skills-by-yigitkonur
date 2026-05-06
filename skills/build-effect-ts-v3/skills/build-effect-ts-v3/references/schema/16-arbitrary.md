# Arbitrary
Derive fast-check Arbitrary values from schemas and add annotations when generation needs help.

## Canonical import

Use the Effect v3 package barrel for normal Schema code:

```typescript
import { Schema } from "effect"
```

## Key rules

- **Purpose:** Effect exposes Arbitrary derivation for Schema so tests can generate values that satisfy schema constraints.
- **Default:** Built-in primitives, structs, arrays, brands, and many collections have derivation support.
- **Custom annotations:** Use `arbitrary` annotations when a custom declaration, transform, or filter needs a better generator.
- **Validation:** Generated values should decode successfully through the same schema.
- **Scope:** Use arbitrary generation for property tests, not as production sample data.

## Example

```typescript
import { Schema } from "effect"

const Slug = Schema.NonEmptyString.pipe(
  Schema.pattern(/^[a-z][a-z0-9-]*$/),
  Schema.brand("Slug")
).annotations({
  identifier: "Slug",
  examples: ["effect-schema"]
})

const Article = Schema.Struct({
  slug: Slug,
  title: Schema.NonEmptyString,
  tags: Schema.Array(Slug)
}).annotations({ identifier: "Article" })
```

## Operational guidance

- In implementation, derive fast-check values with the Arbitrary helper exported from the `effect` package barrel.
- The source exposes `Arbitrary.make(schema)` and `Arbitrary.makeLazy(schema)`.
- Derivation targets the schema decoded type, not arbitrary unknown input.
- Filters narrow generated values where the derivation can understand the constraint.
- Custom predicates may need an `arbitrary` annotation to avoid inefficient filtering or unsupported derivation.
- Use examples annotations for docs; use arbitrary annotations for generated test values.
- For branded values, generate underlying valid primitives and let the schema brand them.
- For recursive schemas, use lazy derivation carefully and keep size behavior in mind.
- Do not assume every custom declaration can derive arbitrary values automatically.
- Use property tests to assert encode/decode round trips for transforms.
- Keep arbitrary annotations deterministic in shape and free of production side effects.
- If generation is expensive, prefer a smaller domain-specific generator.
- If a generated value fails decoding, the schema or annotation is wrong and should be fixed.
- Check `Arbitrary` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Arbitrary` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Arbitrary` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Arbitrary` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Arbitrary` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Arbitrary` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Arbitrary` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Arbitrary` schemas at the boundary where unknown data first appears.

## Cross-references

See also: [13-filters.md](13-filters.md), [12-transforms.md](12-transforms.md), [18-recursive-schemas.md](18-recursive-schemas.md), [14-annotations.md](14-annotations.md).
