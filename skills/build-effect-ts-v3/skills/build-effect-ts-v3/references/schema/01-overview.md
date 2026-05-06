# Schema Overview
Establish Schema as the Effect v3 boundary validator and the replacement for stale package habits.

## Canonical import

Use the Effect v3 package barrel for normal Schema code:

```typescript
import { Schema } from "effect"
```

## Key rules

- **Boundary rule:** Decode untrusted input once at the edge, then pass typed values through the rest of the program.
- **Import rule:** Use the Effect package barrel for Schema. The old standalone package is a migration trap.
- **Mental model:** A schema has a decoded Type, an encoded input shape, and optional requirements from services used by transformations.
- **Default choice:** Start with Schema.Struct for plain data, Schema.Class for domain objects with methods, and brands for IDs.
- **Boundary examples:** HTTP bodies, config payloads, message queues, files, CLI arguments, and persisted JSON all enter as unknown.

## Example

```typescript
import { Schema } from "effect"

const UserId = Schema.UUID.pipe(Schema.brand("UserId"))
const User = Schema.Struct({
  id: UserId,
  email: Schema.String.pipe(Schema.pattern(/^[^@]+@[^@]+\.[^@]+$/)),
  displayName: Schema.NonEmptyString
})

const parseUser = Schema.decodeUnknownEither(User)

const accepted = parseUser({
  id: "2f4b2c0e-04d9-4c21-87d7-f49838c47f25",
  email: "ada@example.com",
  displayName: "Ada"
})
```

## Operational guidance

- Prefer `decodeUnknown*` at boundaries because the input is not trusted yet.
- Use `decode*` only when the input already has the schema encoded type.
- Use `encode*` when leaving your domain model for JSON, storage, or transport.
- Add annotations while designing public schemas; they feed error messages and JSON Schema output.
- The canonical import is shown in every normal example in this directory.
- File 20 is the only migration banner that names the deprecated standalone package.
- For anti-pattern catalog coverage, link this slice to `../anti-patterns/19-deprecated-effect-schema.md` once that mission exists.
- Check `Schema Overview` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Schema Overview` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Schema Overview` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Schema Overview` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Schema Overview` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Schema Overview` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Schema Overview` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Schema Overview` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Schema Overview` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.
- Verify at least one valid value and one invalid value when the schema guards a public boundary.
- Keep transforms, filters, and brands separated so the reason for each constraint is visible.
- Use annotations when generated documentation, formatter output, or client contracts need metadata.
- Do not add compatibility branches unless an existing external contract requires them.
- Keep decoded domain values free of nullish sentinel values unless the domain explicitly models them.
- When source and older examples disagree, follow the Effect v3 source.
- If a schema becomes hard to read, extract smaller named schemas instead of adding comments around complexity.
- Check `Schema Overview` schemas at the boundary where unknown data first appears.
- Keep schema names stable when generated artifacts or external clients depend on them.
- Prefer named reusable schemas over repeating inline validators in several files.

## Cross-references

See also: [20-deprecated-effect-schema.md](20-deprecated-effect-schema.md), [02-schema-struct.md](02-schema-struct.md), [10-decoding.md](10-decoding.md), [15-json-schema.md](15-json-schema.md), [../anti-patterns/19-deprecated-effect-schema.md](../anti-patterns/19-deprecated-effect-schema.md).
