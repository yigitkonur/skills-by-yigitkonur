# Collection Schemas
Validate arrays, tuples, records, and Effect collection types with collection-specific schemas.

## Canonical import

Use the Effect v3 package barrel for normal Schema code:

```typescript
import { Schema } from "effect"
```

## Key rules

- **Arrays:** Use `Schema.Array(value)` for zero-or-more lists and `Schema.NonEmptyArray(value)` when empty is invalid.
- **Tuples:** Use `Schema.Tuple` when position and arity matter.
- **Records:** Use `Schema.Record({ key, value })` for JSON objects with dynamic keys.
- **Maps and sets:** Use `Schema.HashMap` and `Schema.HashSet` when the domain should use Effect collections.
- **Boundary shape:** Pick the schema that matches the encoded shape, then transform to the domain collection if needed.

## Example

```typescript
import { Schema } from "effect"

const Label = Schema.NonEmptyString.pipe(
  Schema.pattern(/^[a-z][a-z0-9-]*$/)
)

const SearchRequest = Schema.Struct({
  tags: Schema.NonEmptyArray(Label),
  cursor: Schema.optional(Schema.Tuple(Schema.String, Schema.Number)),
  weights: Schema.Record({ key: Label, value: Schema.Number })
})

const decoded = Schema.decodeUnknownSync(SearchRequest)({
  tags: ["effect", "schema"],
  cursor: ["next", 42],
  weights: { effect: 1, schema: 2 }
})
```

## Operational guidance

- Use arrays for JSON lists, not Effect collection types, unless the decoded domain benefits from them.
- Use `NonEmptyArray` when later code assumes at least one element.
- Use tuple schemas for fixed-position data such as coordinates or cursors.
- Annotate tuple elements with `Schema.element(...).annotations(...)` when generated JSON Schema needs element labels.
- Use records when keys are dynamic and share a key schema.
- Constrain record keys with a pattern when arbitrary strings are not valid.
- Use `Schema.HashMap({ key, value })` when the decoded type should be a HashMap.
- Use `Schema.HashSet(value)` when the decoded type should deduplicate and use Effect HashSet operations.
- Use `Schema.Array` at HTTP boundaries if the wire shape is a JSON array.
- Avoid accepting both singleton and array forms unless compatibility requires it; use `ArrayEnsure` only with a documented reason.
- Keep collection item schemas named when they are reused across several collections.
- Apply item brands before putting values into a collection schema.
- Do not model a list as `Record<number, T>`; use arrays or tuples.
- When parsing large arrays, prefer async decoding and explicit parse options where needed.
- Generated JSON Schema for tuples differs by target; default output uses Draft-07 tuple keywords.
- For nested collections, keep the schema readable with named constants.
- Use `Schema.NonEmptyArray` for command batches when an empty command list is invalid.
- Check `Collection Schemas` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Collection Schemas` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Collection Schemas` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Collection Schemas` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Collection Schemas` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Collection Schemas` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Collection Schemas` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Collection Schemas` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Collection Schemas` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Collection Schemas` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.

## Cross-references

See also: [07-primitives.md](07-primitives.md), [15-json-schema.md](15-json-schema.md), [10-decoding.md](10-decoding.md), [16-arbitrary.md](16-arbitrary.md).
