# Recursive Schemas
Use Schema.suspend for self-recursive or mutually recursive schemas so evaluation stays lazy.

## Canonical import

Use the Effect v3 package barrel for normal Schema code:

```typescript
import { Schema } from "effect"
```

## Key rules

- **Problem:** Directly referencing a schema while defining itself evaluates too early.
- **Solution:** Wrap recursive references in `Schema.suspend(() => SchemaName)`.
- **Types:** Give recursive schemas explicit type annotations when TypeScript cannot infer the recursive type.
- **JSON Schema:** Use identifiers on recursive schemas for stable generated references.
- **Testing:** Decode small and nested examples to verify recursion and formatter paths.

## Example

```typescript
import { Schema } from "effect"

interface Comment {
  readonly id: string
  readonly body: string
  readonly replies: ReadonlyArray<Comment>
}

const Comment: Schema.Schema<Comment> = Schema.Struct({
  id: Schema.UUID,
  body: Schema.NonEmptyString,
  replies: Schema.Array(Schema.suspend(() => Comment))
}).annotations({ identifier: "Comment" })

const decoded = Schema.decodeUnknownSync(Comment)({
  id: "2f4b2c0e-04d9-4c21-87d7-f49838c47f25",
  body: "First",
  replies: []
})
```

## Operational guidance

- Use `Schema.suspend` for every recursive edge, not just the first one you notice.
- Name recursive interfaces explicitly so the decoded Type is understandable.
- Annotate recursive schemas with identifiers before JSON Schema generation.
- Keep recursive node fields minimal; add nested value schemas for complex payloads.
- Use arrays for child lists unless a non-empty invariant is required.
- For mutually recursive schemas, define both names first and suspend each cross-reference.
- Use `Schema.Union` with suspended members for recursive algebraic data types.
- Do not use broad `Schema.Any` to break cycles; it removes validation where it matters most.
- Run invalid nested examples to verify formatter paths include the recursive location.
- For property tests, watch generation size so recursive arbitrary values do not explode.
- For persistence, verify encoded shape does not contain class instances or non-JSON values.
- For trees with parent links, avoid recursive schemas that require cyclic runtime objects unless the format really supports them.
- For graph-like data, prefer IDs plus separate node records over direct cyclic object schemas.
- Check `Recursive Schemas` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Recursive Schemas` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Recursive Schemas` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Recursive Schemas` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Recursive Schemas` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Recursive Schemas` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Recursive Schemas` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Recursive Schemas` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.

## Cross-references

See also: [15-json-schema.md](15-json-schema.md), [16-arbitrary.md](16-arbitrary.md), [19-error-formatter.md](19-error-formatter.md), [09-unions-and-literals.md](09-unions-and-literals.md).
