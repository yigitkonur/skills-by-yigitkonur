# Form Mode

Pass a Zod schema as the second argument. The client renders form fields, the user submits, and mcp-use validates the response server-side. Return type is inferred automatically.

```typescript
const result = await ctx.elicit(
  "Confirm deployment",
  z.object({
    environment: z.enum(["staging", "production"]).describe("Target environment"),
    confirm: z.boolean().default(false).describe("I understand this is irreversible"),
  })
);
```

## Field types

| Zod type | Renders as | Notes |
|---|---|---|
| `z.string()` | Text input | Add `.email()`, `.url()`, `.min()`, `.max()` for constraints |
| `z.number()` | Number input | Add `.int()`, `.min()`, `.max()` |
| `z.boolean()` | Checkbox / toggle | Add `.default()` to pre-fill |
| `z.enum([...])` | Dropdown / radio / segmented control | Values are the selectable options |
| Multi-select arrays | Use `untitledMultiEnum` / `titledMultiEnum` | Plain free-form arrays are not part of the elicitation field schema |

Always add `.describe()` — it becomes the field label/help text.

## Defaults

`.default(...)` fills in fields the user omits. Combined with optional fields, this gives you sane fallbacks.

```typescript
const result = await ctx.elicit("Preferences", z.object({
  theme: z.enum(["light", "dark"]).default("light"),
  notifications: z.boolean().default(true),
}));
// User submits {} → result.data === { theme: "light", notifications: true }
```

## Server-side validation

mcp-use runs the Zod schema against the returned data before your handler sees it. Invalid data never reaches the handler — instead the call rejects with a validation error you can `try/catch`.

What gets validated:

- Types and shape
- Constraints (`.min()`, `.max()`, `.email()`, `.url()`)
- Required vs optional fields
- Enum membership
- Custom Zod refinements (`.refine()`, `.superRefine()`)

## Schema design

| Practice | Why |
|---|---|
| `.describe()` every field | Field becomes self-documenting in the form |
| Prefer `z.enum()` over free text for known options | Prevents ambiguous input |
| Keep forms short (2-5 fields) | Better completion rates |
| Use validation constraints | User gets immediate feedback in the form |
| Make irreversible actions an explicit boolean | Reduces accidental approval |

## Timeout

Default is indefinite. Pass an options object to bound the wait:

```typescript
const result = await ctx.elicit(
  "Quick confirmation",
  z.object({ confirm: z.boolean() }),
  { timeout: 60000 } // 60s
);
```

A timeout rejects the promise — wrap in `try/catch`.

## Error handling

```typescript
try {
  const result = await ctx.elicit("Enter details", schema, { timeout: 30000 });
  if (result.action === "accept") {
    // result.data is validated and typed
  }
} catch (err) {
  return error(`Elicitation failed: ${err instanceof Error ? err.message : String(err)}`);
}
```

## Advanced enum patterns (SEP-1330)

The simplified Zod API covers ~95% of cases. For titled enum options, legacy `enumNames`, or multi-select arrays, use the verbose helpers from `mcp-use/server`:

```typescript
import {
  enumSchema, untitledEnum, titledEnum, legacyEnum,
  untitledMultiEnum, titledMultiEnum,
} from "mcp-use/server";

const result = await ctx.elicit({
  message: "Choose your options",
  requestedSchema: enumSchema({
    plan: titledEnum([
      { value: "free", title: "Free Tier" },
      { value: "pro",  title: "Pro Tier ($20/mo)" },
    ]),
    features: titledMultiEnum([
      { value: "api",      title: "API access" },
      { value: "webhooks", title: "Webhooks" },
    ]),
  }),
});
```

| Variant | Helper | JSON Schema shape |
|---|---|---|
| Untitled single-select | `untitledEnum` | `type: "string" + enum` |
| Titled single-select | `titledEnum` | `type: "string" + oneOf[{ const, title }]` |
| Legacy named enum | `legacyEnum` | `type: "string" + enum + enumNames` |
| Untitled multi-select | `untitledMultiEnum` | `type: "array" + items.enum` |
| Titled multi-select | `titledMultiEnum` | `type: "array" + items.anyOf[{ const, title }]` |

Use `.default()` for plain Zod forms. Use the verbose `enumSchema` API only when you need titled options or multi-select arrays.
