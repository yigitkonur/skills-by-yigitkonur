# JSON Schema
Generate JSON Schema from Effect Schema and remember JSONSchema.make defaults to Draft-07, not 2020-12.

## Canonical import

Use the Effect v3 package barrel for normal Schema code:

```typescript
import { Schema } from "effect"
```

## Key rules

- **Default:** `JSONSchema.make(schema)` outputs JSON Schema Draft-07 by default.
- **Targets:** The source supports explicit targets including 2019-09, 2020-12, and OpenAPI 3.1, but default remains Draft-07.
- **Annotations:** identifier, title, description, default, examples, and jsonSchema annotations shape output.
- **Tuples:** Draft-07 tuple output uses `items` plus `additionalItems`; 2020-12 uses different keywords only when explicitly targeted.
- **Verification:** Check generated output before publishing schemas to clients.

## Example

```typescript
import { Schema } from "effect"

const Point = Schema.Tuple(
  Schema.element(Schema.Number).annotations({
    title: "X",
    description: "X coordinate"
  }),
  Schema.element(Schema.Number).annotations({
    title: "Y",
    description: "Y coordinate"
  })
).annotations({ identifier: "Point" })
```

```typescript
import { Schema } from "effect"

const PositiveScore = Schema.Number.pipe(
  Schema.between(0, 100),
  Schema.annotations({
    identifier: "PositiveScore",
    title: "Positive score",
    jsonSchema: { minimum: 0, maximum: 100 }
  })
)
```

## Operational guidance

- Import JSON Schema helpers from the same `effect` package barrel in implementation code; do not use the deprecated standalone Schema package.
- The source for `JSONSchema.make` marks `jsonSchema7` as the default target.
- The default `$schema` URI is `http://json-schema.org/draft-07/schema#`.
- Do not state that default output is Draft 2020-12; that is false unless the target option is explicit.
- Use `{ target: "jsonSchema2020-12" }` only when the consumer specifically requires that dialect.
- Use `{ target: "openApi3.1" }` for OpenAPI 3.1 integration where supported by the consuming tool.
- Identifiers create reusable definitions under `$defs` and references.
- Title and description annotations become JSON Schema documentation keywords.
- Default and examples annotations are emitted when values can be represented as JSON.
- Custom `jsonSchema` annotations can express fragments for custom filters or unsupported primitive encodings.
- Generated schemas describe the encoded side of transforms; verify this for every custom transform.
- Tuple output is a common place agents hallucinate the wrong dialect.
- For Draft-07 tuples, expect `items` as an array and `additionalItems: false`.
- For Draft 2020-12 tuples, expect `prefixItems` only when explicitly targeting that dialect.
- For recursive schemas, identifiers are important so references can be emitted predictably.
- For branded strings, generated JSON Schema should still show the underlying string constraints.
- For custom filters, add `jsonSchema` annotations if clients need machine-readable constraints.
- Link this file from anti-pattern coverage for hallucinated JSON Schema dialect claims.
- Check `JSON Schema` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `JSON Schema` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `JSON Schema` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `JSON Schema` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `JSON Schema` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `JSON Schema` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `JSON Schema` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `JSON Schema` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.

## Cross-references

See also: [14-annotations.md](14-annotations.md), [18-recursive-schemas.md](18-recursive-schemas.md), [12-transforms.md](12-transforms.md), [../anti-patterns/18-ai-hallucinations.md](../anti-patterns/18-ai-hallucinations.md).
