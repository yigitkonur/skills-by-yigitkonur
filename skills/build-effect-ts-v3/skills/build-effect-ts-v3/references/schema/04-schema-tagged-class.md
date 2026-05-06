# Schema.TaggedClass
Model tagged domain variants as schema-backed classes with stable `_tag` discriminants.

## Canonical import

Use the Effect v3 package barrel for normal Schema code:

```typescript
import { Schema } from "effect"
```

## Key rules

- **Purpose:** `Schema.TaggedClass` creates variant classes with a constructor-provided payload and a defaulted `_tag`.
- **Discriminants:** The tag is part of the decoded and encoded shape, so it works with `Schema.Union`.
- **When to use:** Use it for events, commands, messages, and domain states that need methods or class identity.
- **When not to use:** For data-only variants, `Schema.TaggedStruct` or `Schema.Struct` plus `Schema.Literal` can be enough.
- **Interoperability:** Tagged classes are especially useful when decoding transport data into domain variant instances.

## Example

```typescript
import { Schema } from "effect"

class UserCreated extends Schema.TaggedClass<UserCreated>("UserCreated")(
  "UserCreated",
  {
    userId: Schema.UUID.pipe(Schema.brand("UserId")),
    email: Schema.String.pipe(Schema.pattern(/^[^@]+@[^@]+\.[^@]+$/))
  }
) {}

class UserDisabled extends Schema.TaggedClass<UserDisabled>("UserDisabled")(
  "UserDisabled",
  {
    userId: Schema.UUID.pipe(Schema.brand("UserId")),
    reason: Schema.NonEmptyString
  }
) {}

const UserEvent = Schema.Union(UserCreated, UserDisabled)
```

## Operational guidance

- The `_tag` field is supplied by the class constructor default; callers pass only the payload fields.
- Use the same string for identifier and tag unless you have a documented naming reason.
- Keep tag strings stable because serialized messages and event logs may depend on them.
- Decode at the message boundary so downstream handlers receive variant class instances.
- Use `Schema.Union` over tagged classes to parse the whole variant family.
- Do not create a tag field manually when `TaggedClass` can own it.
- Use `TaggedClass` when variants carry behavior or need class identity.
- Use plain tagged structs when variants are only transport records.
- Use brands inside payload fields so event IDs do not collapse into plain strings.
- Annotate the union or each variant with identifiers before generating JSON Schema.
- Pattern matching by `_tag` stays predictable because the tag is a literal field.
- Keep payloads small; nested payload objects should get their own schemas.
- Avoid optional tag fields. The tag is the discriminator and must be present.
- If the variant is an Effect failure, use `Schema.TaggedError` instead.
- If variants cross process boundaries, test both decoding and encoding.
- Check `Schema.TaggedClass` schemas at the boundary where unknown data first appears.
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

See also: [03-schema-class.md](03-schema-class.md), [05-schema-tagged-error.md](05-schema-tagged-error.md), [09-unions-and-literals.md](09-unions-and-literals.md), [06-branded-types.md](06-branded-types.md).
