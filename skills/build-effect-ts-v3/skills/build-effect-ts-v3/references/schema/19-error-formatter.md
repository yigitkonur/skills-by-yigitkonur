# Error Formatter
Format parse failures with TreeFormatter for humans and ArrayFormatter for structured field errors.

## Canonical import

Use the Effect v3 package barrel for normal Schema code:

```typescript
import { Schema } from "effect"
```

## Key rules

- **Purpose:** Parse failures carry structured issues; format them at user-facing boundaries.
- **TreeFormatter:** Use tree formatting for readable diagnostics in logs, CLIs, and developer errors.
- **ArrayFormatter:** Use array formatting when UI fields or API responses need path-indexed issues.
- **Annotations:** Messages, titles, and field annotations improve formatter output.
- **Boundary:** Format errors at the edge; inside Effect code keep typed parse failures available.

## Example

```typescript
import { Schema } from "effect"

const Signup = Schema.Struct({
  email: Schema.String.pipe(
    Schema.pattern(/^[^@]+@[^@]+\.[^@]+$/),
    Schema.annotations({
      message: () => "expected a valid email address"
    })
  ),
  name: Schema.NonEmptyString
})

const parsed = Schema.decodeUnknownEither(Signup)({
  email: "not-an-email",
  name: ""
})
```

## Operational guidance

- In implementation, import ParseResult from the same `effect` package barrel when formatting parse errors.
- Use `ParseResult.TreeFormatter.formatErrorSync(error)` for a human-readable string from a ParseError.
- Use `ParseResult.TreeFormatter.formatIssueSync(issue)` when you have a ParseIssue directly.
- Use `ParseResult.ArrayFormatter.formatErrorSync(error)` for structured issues with `_tag`, `path`, and `message`.
- Use ArrayFormatter output for API validation responses and form field mapping.
- Use TreeFormatter output for CLI output, logs, and developer diagnostics.
- Add `message` annotations to custom filters so users do not see only predicate titles.
- Add property annotations for field names and descriptions that help generated docs, not as a substitute for messages.
- Keep raw parse issue structures internal unless the API contract explicitly documents them.
- Do not discard parse details with Option helpers when the caller needs validation feedback.
- Use `{ errors: "all" }` when formatter output should include multiple field errors.
- Use default first-error behavior when one error is enough and performance matters.
- For nested arrays, check formatter paths in tests so UI mapping stays correct.
- Check `Error Formatter` schemas at the boundary where unknown data first appears.
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

See also: [10-decoding.md](10-decoding.md), [13-filters.md](13-filters.md), [14-annotations.md](14-annotations.md), [09-unions-and-literals.md](09-unions-and-literals.md).
