# Primitive Schemas
Choose built-in primitive schemas and refined constructors before writing custom validators.

## Canonical import

Use the Effect v3 package barrel for normal Schema code:

```typescript
import { Schema } from "effect"
```

## Key rules

- **Strings:** Use `Schema.String`, `Schema.NonEmptyString`, `Schema.Trim`, `Schema.Trimmed`, and pattern filters for text.
- **Numbers:** Use `Schema.Number`, `Schema.NumberFromString`, `Schema.Int`, `Schema.Finite`, and bounds filters.
- **Booleans:** Use `Schema.Boolean` for real booleans and `Schema.BooleanFromString` for string-backed config or query input.
- **Dates:** Use `Schema.DateFromString`, `Schema.DateFromNumber`, or `Schema.DateFromSelf` based on the wire shape.
- **BigInt:** Use BigInt schemas only when JSON encoding strategy is explicit.

## Example

```typescript
import { Schema } from "effect"

const Query = Schema.Struct({
  q: Schema.NonEmptyString,
  page: Schema.NumberFromString.pipe(
    Schema.int(),
    Schema.greaterThanOrEqualTo(1)
  ),
  includeArchived: Schema.optionalWith(Schema.BooleanFromString, {
    default: () => false
  }),
  createdAfter: Schema.optional(Schema.DateFromString)
})

const query = Schema.decodeUnknownSync(Query)({
  q: "schema",
  page: "1",
  includeArchived: "false"
})
```

## Operational guidance

- Use primitive schemas as building blocks; refine them with filters instead of custom declarations first.
- Use `Schema.NonEmptyString` when an empty string would fail business logic later.
- Use `Schema.Trim` when the boundary should transform surrounding whitespace away.
- Use `Schema.Trimmed` when whitespace should be rejected rather than transformed.
- Use `Schema.pattern` for local format checks such as prefixes, slugs, or simple codes.
- Use `Schema.NumberFromString` for query strings, form posts, and config values that arrive as strings.
- Use `Schema.Int` or `Schema.int()` for integer-only numeric values.
- Use `Schema.Finite` when `NaN` and infinities are not acceptable.
- Use numeric bounds on the schema, not scattered checks after decoding.
- Use `Schema.BooleanFromString` for exact string booleans; do not accept arbitrary truthy strings unless documented.
- Use date transforms only when the encoded form is known and stable.
- Use `Schema.DateFromString` when the wire sends date strings.
- Use `Schema.DateFromSelf` when the runtime input must already be a Date object.
- Use BigInt schemas carefully because JSON does not carry bigint directly.
- Use annotations to document important primitive constraints for generated schema and parser messages.
- Use brands after primitive constraints when a primitive has domain identity.
- Prefer built-ins over `Schema.filter` when a named built-in exists; names improve diagnostics.
- Keep primitive parsing at the system edge; inside the domain use the decoded type.
- Do not use nullable primitives as a domain shortcut; model optionality explicitly.
- When a primitive schema becomes complex, name it once and reuse it.
- Check `Primitive Schemas` schemas at the boundary where unknown data first appears.
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

See also: [06-branded-types.md](06-branded-types.md), [13-filters.md](13-filters.md), [12-transforms.md](12-transforms.md), [10-decoding.md](10-decoding.md).
