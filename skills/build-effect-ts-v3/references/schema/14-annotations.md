# Annotations
Add Schema annotations for names, docs, defaults, examples, parser messages, generated JSON Schema, and derived instances.

## Canonical import

Use the Effect v3 package barrel for normal Schema code:

```typescript
import { Schema } from "effect"
```

## Key rules

- **Purpose:** Annotations attach metadata to schemas and property signatures.
- **Documentation:** Use identifier, title, description, examples, and default for public contracts.
- **Messages:** Use message and parseIssueTitle to tune parser output.
- **JSON Schema:** Annotations drive `$defs`, field docs, defaults, examples, and custom fragments.
- **Derivations:** arbitrary, pretty, and equivalence annotations customize derived helpers.

## Example

```typescript
import { Schema } from "effect"

const Email = Schema.String.pipe(
  Schema.pattern(/^[^@]+@[^@]+\.[^@]+$/),
  Schema.brand("Email")
).annotations({
  identifier: "Email",
  title: "Email address",
  description: "A deliverable user email address",
  examples: ["ada@example.com"],
  message: () => "expected a valid email address"
})

const Signup = Schema.Struct({
  email: Schema.propertySignature(Email).annotations({
    title: "Primary email"
  }),
  marketingOptIn: Schema.optionalWith(Schema.Boolean, {
    default: () => false
  })
}).annotations({ identifier: "Signup" })
```

## Operational guidance

- Use `identifier` on exported schemas so JSON Schema can place shared definitions under stable names.
- Use `title` for short human-readable labels.
- Use `description` for one or two sentences that help generated docs or error views.
- Use `examples` with values from the decoded side that can be encoded to JSON when generating JSON Schema.
- Use `default` when the public contract has a meaningful default value.
- Use property-signature annotations for field-level metadata.
- Use schema annotations for reusable type-level metadata.
- Use `message` for validation text that users may see.
- Use `parseIssueTitle` when the default issue title is too technical.
- Use `parseOptions` annotations sparingly for nested parsing behavior.
- Use `jsonSchema` annotations for standard JSON Schema keywords that custom filters cannot infer.
- Use `arbitrary` annotations when derived fast-check values need custom generation.
- Use `equivalence` annotations when derived equality needs domain-specific behavior.
- Do not use annotations as a hidden behavior system; they should clarify schema behavior.
- Keep public annotation text stable because generated artifacts may depend on it.
- Do not copy long product docs into annotations; link or keep docs elsewhere.
- When annotation metadata affects clients, verify generated JSON Schema after changes.
- When formatter messages change, update tests that assert parse output.
- Prefer annotations near the schema they describe over scattered post-processing.
- Check `Annotations` schemas at the boundary where unknown data first appears.
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

See also: [15-json-schema.md](15-json-schema.md), [19-error-formatter.md](19-error-formatter.md), [16-arbitrary.md](16-arbitrary.md), [17-equivalence-and-order.md](17-equivalence-and-order.md).
