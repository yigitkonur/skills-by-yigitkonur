# Transforms
Use transforms for reversible shape changes and transformOrFail for transformations that can fail.

## Canonical import

Use the Effect v3 package barrel for normal Schema code:

```typescript
import { Schema } from "effect"
```

## Key rules

- **Transform:** `Schema.transform` maps between two valid schema shapes with synchronous total decode and encode functions.
- **Failure:** Use `Schema.transformOrFail` when decode or encode can fail with parse issues.
- **Built-ins:** Prefer built-in transforms such as NumberFromString and DateFromString when they fit.
- **Direction:** Always reason about both decode and encode direction before adding a transform.
- **Boundary:** Transforms are boundary tools; do not hide arbitrary business logic inside them.

## Example

```typescript
import { Schema } from "effect"

const IsoDateString = Schema.String.pipe(
  Schema.pattern(/^\d{4}-\d{2}-\d{2}$/)
)

const DateOnly = Schema.transform(
  IsoDateString,
  Schema.DateFromSelf,
  {
    decode: (value) => new Date(`${value}T00:00:00.000Z`),
    encode: (date) => date.toISOString().slice(0, 10)
  }
).annotations({ identifier: "DateOnly" })

const decoded = Schema.decodeUnknownSync(DateOnly)("2026-05-05")
const encoded = Schema.encodeSync(DateOnly)(decoded)
```

## Operational guidance

- Use built-in transforms before writing custom ones: `NumberFromString`, `BooleanFromString`, `DateFromString`, `DateFromNumber`.
- Use `Schema.transform` when both directions are total for already-validated inputs.
- Use `Schema.transformOrFail` when parsing can reject values after the input schema accepts them.
- Do not use transforms for side effects, service calls, logging, or persistence.
- The `from` schema describes the encoded input; the `to` schema describes the decoded type.
- The decode function maps from the from type to the to encoded representation.
- The encode function maps back from the to encoded representation to the from type.
- Keep transform names and identifiers explicit because errors otherwise become difficult to interpret.
- Annotate custom transforms when JSON Schema cannot infer the desired public shape.
- Use filters for refinements that do not change shape.
- Use brands for nominal identity after validation, not transforms.
- Round-trip test custom transforms: decode valid wire values, encode decoded values, and reject invalid wire values.
- If a transform maps strings to Dates, define timezone behavior explicitly.
- If a transform maps money, prefer integer cents and document currency handling.
- If a transform maps external keys, keep rename mappings close to the adapter.
- If a transform needs asynchronous validation, keep it in Effect via transformOrFail and provide required services at the boundary.
- Do not transform untrusted unknown directly; decode through the from schema first.
- Prefer small named transforms composed into structs over inline transform blocks in large schemas.
- Generated JSON Schema usually describes the encoded side, so verify output for custom transforms.
- When transform semantics are surprising, move detail to a reference comment near the schema.
- Check `Transforms` schemas at the boundary where unknown data first appears.
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

See also: [13-filters.md](13-filters.md), [11-encoding.md](11-encoding.md), [15-json-schema.md](15-json-schema.md), [07-primitives.md](07-primitives.md).
