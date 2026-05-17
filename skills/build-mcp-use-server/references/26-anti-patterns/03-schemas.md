# Schemas

Schema mistakes that look fine in TypeScript but make the tool unusable for the model. For tool-shape concerns (god-tools, naming, descriptions), see `02-tool-design.md`.

## Don't use `z.any()` or `z.unknown()`

Both turn off validation and give the model zero guidance about what to send.

```typescript
// ❌ no validation, no LLM hint
server.tool({
  name: "process",
  schema: z.object({ data: z.any() }),
}, handler);
```

```typescript
// ✅ explicit shape with descriptions
server.tool({
  name: "process",
  schema: z.object({
    data: z.object({
      name: z.string().describe("Record name"),
      value: z.number().describe("Numeric value"),
    }).strict(),
  }),
}, handler);
```

If you genuinely don't know the shape, you're holding the wrong tool — split into typed sibling tools instead. `z.any()` is almost never the right answer.

## Don't accept `z.string()` when `z.enum()` works

If a field has a fixed set of valid values, encode them. The model uses the enum to know what to send; a free-form string forces it to guess.

```typescript
// ❌ string for a closed set
schema: z.object({
  status: z.string().describe("One of: open, closed, pending"),
})
```

```typescript
// ✅ enum — both validates and informs
schema: z.object({
  status: z.enum(["open", "closed", "pending"]).describe("Issue status"),
})
```

`z.literal(...)` for a single value, `z.enum([...])` for a set. Both are visible in the JSON Schema sent to the model.

## Don't omit `.describe()`

Field descriptions are the model's only context. Without them, the model has only the field *name* — which is often ambiguous (`id`, `value`, `key`, `data`).

```typescript
// ❌ unlabeled
schema: z.object({
  userId: z.string(),
  amount: z.number(),
  currency: z.string(),
})
```

```typescript
// ✅ describe every field
schema: z.object({
  userId: z.string().uuid().describe("Stripe customer UUID"),
  amount: z.number().int().describe("Amount in cents"),
  currency: z.string().length(3).describe("ISO 4217 currency code, e.g. USD"),
})
```

The same applies to the tool's top-level `description` — see `02-tool-design.md`.

## Don't make every field `.optional()`

Optional everywhere means the handler null-checks every field, the contract is unclear, and the model never knows whether to provide a value. Use `.default(...)` for things that have a sensible default; keep required fields required.

```typescript
// ❌ everything optional — defensive code everywhere
schema: z.object({
  query: z.string().optional(),     // is it required??
  limit: z.number().optional(),
  offset: z.number().optional(),
})
```

```typescript
// ✅ required where required, defaults where defaults
schema: z.object({
  query: z.string().min(1).describe("Search term"),
  limit: z.number().int().min(1).max(100).default(10).describe("Results per page"),
  offset: z.number().int().min(0).default(0).describe("Pagination offset"),
})
```

`.optional()` says "this field may be missing" — the handler must null-check. `.default(x)` says "if missing, use x" — the handler always sees a value.

## Don't use untyped `Record`

`z.record(z.string(), z.unknown())` is the same problem as `z.any()` for the values. Type the values explicitly.

```typescript
// ❌ untyped values — model hallucinates
schema: z.object({
  metadata: z.record(z.string(), z.unknown()),
})
```

```typescript
// ✅ explicit value type
schema: z.object({
  metadata: z.record(z.string(), z.string()).describe("String key-value tags"),
})
```

If the keys are also a closed set, prefer `z.object({...}).strict()` — closed records are clearer than open ones.

## Don't omit `.strict()` on top-level objects

By default, Zod silently strips unknown keys. The model can hallucinate extra fields (`limitt: 10`, a typo) and they pass validation as `undefined`. `.strict()` rejects unknown keys and surfaces the typo.

```typescript
// ❌ unknown keys silently dropped
schema: z.object({
  query: z.string(),
  limit: z.number(),
})
```

```typescript
// ✅ unknown keys rejected
schema: z.object({
  query: z.string(),
  limit: z.number(),
}).strict()
```

## Don't deeply nest

Deep nesting (more than 2–3 levels) is hard for the model to fill correctly. Flatten.

```typescript
// ❌ 4 levels deep
z.object({
  order: z.object({
    customer: z.object({
      address: z.object({
        geo: z.object({ lat: z.number(), lng: z.number() }),
      }),
    }),
  }),
})
```

```typescript
// ✅ flat
z.object({
  customerName: z.string().describe("Customer full name"),
  streetAddress: z.string().describe("Delivery street address"),
  latitude: z.number().describe("GPS latitude"),
  longitude: z.number().describe("GPS longitude"),
})
```

## Don't paper over wrong types with `.transform()`

`.transform()` is for normalization (`z.string().trim().toLowerCase()`, splitting CSV into arrays). It is **not** for compensating for bad input shapes. If the model is sending you "5" instead of `5`, fix the schema (`z.number()` vs `z.coerce.number()`) — don't post-process bad data.

| Use `.transform()` for | Don't use it for |
|---|---|
| `z.string().trim()` | Coercing wrong types |
| `z.string().toLowerCase()` | Hiding validation errors |
| `csv.split(",")` to array | Defaulting missing values (use `.default()`) |

## Quick checklist

| Don't | Do |
|---|---|
| `z.any()`, `z.unknown()` | Specific Zod type with `.describe()` |
| `z.string()` for closed sets | `z.enum([...])` |
| Untyped `z.record(...)` | Typed values, or `z.object({...}).strict()` |
| Field without `.describe()` | `.describe(...)` on every field |
| Everything `.optional()` | Required where required, `.default(...)` for fallbacks |
| Top-level objects without `.strict()` | `.strict()` to reject unknown keys |
| 3+ levels of nesting | Flatten to one or two levels |
| `.transform()` for type coercion | Fix the type; transform only normalizes |
