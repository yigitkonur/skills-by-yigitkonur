# Deprecated Schema Package
Migrate stale standalone Schema imports to the built-in Effect v3 Schema barrel import.

## Canonical import

Use the Effect v3 package barrel for normal Schema code:

```typescript
import { Schema } from "effect"
```

## Key rules

- **Migration banner:** Schema has lived in the `effect` package since Effect 3.10.
- **Rule:** New code in this skill must import Schema from `effect`.
- **Scope:** This file is intentionally the only schema reference that names the deprecated standalone package.
- **Replacement:** Change the package specifier, not the Schema namespace usage.
- **Audit:** Search docs and examples for stale imports before shipping an Effect v3 skill.

## Example

```typescript
import { Schema } from "@effect/schema"

import { Schema } from "effect"
```

## Operational guidance

- The migration is usually a one-line import change for examples that already use the `Schema` namespace.
- Do not teach new agents to install or import the old standalone package.
- Do not deep-import Schema modules from Effect internals.
- Use the package barrel so examples match modern Effect v3 projects.
- When copying older community examples, rewrite the import before evaluating the API usage.
- After rewriting the import, still verify APIs against the v3 source because old examples may contain other stale patterns.
- Keep this banner short so the normal docs do not repeat deprecated names.
- If a project still depends on the old package, treat that as migration work, not a new-skill pattern.
- The rest of this schema directory should only show the modern import.
- Check `Deprecated Schema Package` schemas at the boundary where unknown data first appears.
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

See also: [01-overview.md](01-overview.md), [10-decoding.md](10-decoding.md), [15-json-schema.md](15-json-schema.md).
