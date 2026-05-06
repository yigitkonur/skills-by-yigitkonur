# Schema.Class
Use Schema.Class when decoded values need constructors, methods, getters, or class identity.

## Canonical import

Use the Effect v3 package barrel for normal Schema code:

```typescript
import { Schema } from "effect"
```

## Key rules

- **Class purpose:** `Schema.Class<Self>(identifier)(fields)` creates a schema-backed class constructor.
- **Constructor validation:** Constructors validate through the schema and return class instances, not plain records.
- **Behavior:** Methods and getters live on the class prototype and are available after decoding.
- **Struct relationship:** The field map follows Struct rules; the decoded result adds class identity and behavior.
- **Use boundary:** Use Class for rich domain values, not for every DTO.

## Example

```typescript
import { Schema } from "effect"

class EmailAddress extends Schema.Class<EmailAddress>("EmailAddress")({
  value: Schema.NonEmptyString.pipe(
    Schema.pattern(/^[^@]+@[^@]+\.[^@]+$/)
  )
}) {
  get domain(): string {
    return this.value.slice(this.value.indexOf("@") + 1)
  }

  normalized(): string {
    return this.value.toLowerCase()
  }
}

const decoded = Schema.decodeUnknownSync(EmailAddress)({
  value: "Ada@Example.com"
})

const domain = decoded.domain
```

## Operational guidance

- Use the self generic: `Schema.Class<MyClass>("MyClass")` keeps the decoded type precise.
- The identifier is used by annotations, diagnostics, and generated schema references.
- Class fields still accept `Schema.optional` and `Schema.optionalWith` property signatures.
- Put invariant-preserving helpers on the class when they belong to the value itself.
- Keep IO, database access, and service calls out of class methods; classes should stay value-oriented.
- Use `new EmailAddress({ value })` at trusted construction sites and decoding helpers at unknown boundaries.
- Use `Class.make` when you need the static constructor helper shape from Effect source examples.
- Prefer getters for derived values that are cheap and deterministic.
- Prefer methods for named domain operations that read clearer than free functions.
- Do not use Class just to avoid writing `Schema.Struct`; instance identity has a runtime and API cost.
- Use Struct for request bodies, response bodies, and simple records where behavior is not needed.
- Use Class for value objects such as EmailAddress, Money, Slug, or DateRange.
- Use brands when the only difference from a primitive is identity, not behavior.
- Class can be extended with additional fields, but avoid inheritance unless the domain shape truly shares behavior.
- When changing fields, check encoders because class schemas transform between plain encoded data and class instances.
- Annotate public classes with `identifier`, `title`, and `description` when exporting JSON Schema.
- Decoding a class produces the class instance; encoding produces the encoded field object.
- Treat class constructors as validation boundaries; do not bypass them with casts.
- If a class needs tagged variants, use `Schema.TaggedClass` instead of adding `_tag` manually.
- If a class represents an error, use `Schema.TaggedError` so it integrates with Effect error channels.
- Check `Schema.Class` schemas at the boundary where unknown data first appears.
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

See also: [02-schema-struct.md](02-schema-struct.md), [04-schema-tagged-class.md](04-schema-tagged-class.md), [05-schema-tagged-error.md](05-schema-tagged-error.md), [11-encoding.md](11-encoding.md).
