# Schema.TaggedError
Define typed Effect failures with Schema.TaggedError and annotate public HTTP errors separately.

## Canonical import

Use the Effect v3 package barrel for normal Schema code:

```typescript
import { Schema } from "effect"
```

## Key rules

- **Purpose:** `Schema.TaggedError` creates schema-backed errors that are yieldable in Effect error channels.
- **Shape:** It adds a stable `_tag`, validates fields, and preserves Error behavior.
- **Message:** Provide a getter when the default field dump is not the right user-facing message.
- **HTTP APIs:** When used with HttpApi, attach HTTP annotations at the API layer or with the platform helper, not by inventing fields.
- **Boundary:** Decode unknown external error payloads only when accepting them from outside the process.

## Example

```typescript
import { Schema } from "effect"

const UserId = Schema.UUID.pipe(Schema.brand("UserId"))

class UserNotFound extends Schema.TaggedError<UserNotFound>("UserNotFound")(
  "UserNotFound",
  {
    userId: UserId
  }
) {
  get message(): string {
    return `User not found: ${this.userId}`
  }
}

const failure = new UserNotFound({
  userId: Schema.decodeUnknownSync(UserId)(
    "2f4b2c0e-04d9-4c21-87d7-f49838c47f25"
  )
})
```

## Operational guidance

- Use `Schema.TaggedError`, not a plain `Error`, when callers should catch by `_tag`.
- The constructor validates the payload; invalid payloads fail at construction.
- Keep error fields serializable when errors can cross an RPC or HTTP boundary.
- Use branded IDs inside errors so handlers cannot accidentally pass the wrong entity ID.
- Add a `message` getter when logs or responses need a stable message string.
- Do not add HTTP status fields to every error class by default; HTTP mapping belongs at the API boundary.
- For Effect HTTP APIs, use the platform `HttpApiSchema` annotations where that package is in scope.
- Keep domain errors transport-neutral unless the domain itself is an HTTP adapter.
- Use `catchTag` or `catchTags` in Effect code to recover typed failures.
- For validation failures, let Schema parse errors describe invalid input rather than creating a custom domain error too early.
- When multiple errors share fields, compose field schemas, not error inheritance, unless behavior is shared.
- Use `Schema.Union` if you need to accept an external serialized error family.
- Encode errors before crossing process boundaries; decode them only on the receiving side.
- Annotate public error schemas with identifiers for generated references.
- Keep internal defect information out of schema-backed error payloads.
- Prefer exact, small payloads over storing the original untrusted input.
- If the error needs no behavior and never enters an Effect error channel, a tagged struct may be enough.
- Check `Schema.TaggedError` schemas at the boundary where unknown data first appears.
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

See also: [04-schema-tagged-class.md](04-schema-tagged-class.md), [09-unions-and-literals.md](09-unions-and-literals.md), [10-decoding.md](10-decoding.md), [14-annotations.md](14-annotations.md).
