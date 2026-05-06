# Encoding
Encode typed domain values back to transport, storage, or JSON-compatible shapes deliberately.

## Canonical import

Use the Effect v3 package barrel for normal Schema code:

```typescript
import { Schema } from "effect"
```

## Key rules

- **Purpose:** Encoding walks from decoded Type back to the schema encoded representation.
- **Helpers:** Use `Schema.encode`, `encodeSync`, `encodeEither`, `encodePromise`, and unknown variants to match the caller.
- **Class behavior:** Encoding class instances emits their encoded field shape.
- **Transforms:** Transforms must define encode as carefully as decode.
- **Boundary:** Encode at outbound edges, not throughout internal domain logic.

## Example

```typescript
import { Schema } from "effect"

class User extends Schema.Class<User>("User")({
  id: Schema.UUID.pipe(Schema.brand("UserId")),
  email: Schema.String.pipe(Schema.pattern(/^[^@]+@[^@]+\.[^@]+$/))
}) {
  get domain(): string {
    return this.email.slice(this.email.indexOf("@") + 1)
  }
}

const user = Schema.decodeUnknownSync(User)({
  id: "2f4b2c0e-04d9-4c21-87d7-f49838c47f25",
  email: "ada@example.com"
})

const wire = Schema.encodeSync(User)(user)
```

## Operational guidance

- Use `Schema.encodeSync` only when encoding cannot require async effects or services.
- Use `Schema.encode` when encoding belongs inside Effect code.
- Use `Schema.encodeEither` in pure tests and adapters.
- Use `Schema.encodePromise` at promise-based framework edges.
- Use `Schema.encodeUnknown*` when the value being encoded is not statically trusted.
- Encoding validates the decoded value against the schema type side before producing the encoded side.
- For classes, do not hand-build output records if the schema encoder already owns the mapping.
- For transforms, test decode then encode round trips for representative values.
- For outbound APIs, annotate schemas once and reuse the same schema for encoding and JSON Schema output.
- Do not encode in the middle of domain workflows just to satisfy a downstream function; pass domain values until the boundary.
- Use brands freely; encoding generally erases the brand to the underlying primitive.
- When a value cannot be represented in JSON, add a transform or a documented custom JSON Schema annotation.
- Prefer explicit outbound schemas over reusing inbound schemas when the shapes intentionally differ.
- If encoding fails, treat it as a bug in trusted domain construction or an invalid transform.
- Keep encoded field names stable; changes are external contract changes.
- Check `Encoding` schemas at the boundary where unknown data first appears.
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

See also: [10-decoding.md](10-decoding.md), [12-transforms.md](12-transforms.md), [03-schema-class.md](03-schema-class.md), [15-json-schema.md](15-json-schema.md).
