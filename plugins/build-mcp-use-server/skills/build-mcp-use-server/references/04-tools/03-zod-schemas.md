# Zod Schemas

Canonical Zod reference for `mcp-use` tool input schemas. Schemas are converted to JSON Schema for the wire protocol, so `.describe()` on every field is mandatory — it is the LLM's only signal for what each field means.

## Primitives

```typescript
z.string().describe("User's email address")
z.number().describe("Quantity to order")
z.boolean().describe("Whether to include archived items")
```

## Constrained primitives

```typescript
z.string().min(1).max(100).describe("Between 1 and 100 chars")
z.string().email().describe("Valid email")
z.string().url().describe("Valid URL")
z.string().uuid().describe("UUID identifier")
z.string().regex(/^[A-Z]{2}-\d+$/).describe("Ticket ID like AB-123")
z.string().datetime({ offset: true }).describe("ISO 8601 datetime")
z.number().int().positive().describe("Whole positive number")
z.number().min(0).max(100).describe("Percentage 0-100")
z.number().int().min(1).max(1000).default(50).describe("Page size")
```

## Enums and literals

```typescript
z.enum(["asc", "desc"]).describe("Sort direction")
z.enum(["low", "medium", "high", "critical"]).describe("Priority")
z.enum(["created", "updated", "priority"]).default("created").describe("Sort field")
z.literal("v2").describe("API version")
```

## Optional and default

```typescript
z.object({
  query: z.string().min(1).describe("Search term — required"),
  page: z.number().int().positive().optional().describe("Page number, omit for first page"),
  limit: z.number().int().min(1).max(100).default(25).describe("Results per page"),
})
```

`.optional()` means the field can be omitted (`undefined` in handler). `.default(value)` means it can be omitted but always has a concrete value in the handler.

## Nested objects

```typescript
z.object({
  user: z.object({
    name: z.string().min(1).describe("Full name"),
    email: z.string().email().describe("Email address"),
    role: z.enum(["admin", "member", "viewer"]).describe("User role"),
  }).describe("User to create"),
  sendWelcomeEmail: z.boolean().default(true).describe("Send welcome email on creation"),
})
```

Keep nesting shallow. LLMs handle flat objects more reliably than deep trees.

## Arrays

```typescript
z.object({
  tags: z.array(z.string()).describe("Tags to apply"),
  userIds: z.array(z.string().uuid()).min(1).max(50).describe("User IDs to notify"),
  items: z.array(
    z.object({
      productId: z.string().describe("Product identifier"),
      quantity: z.number().int().positive().describe("Number of items"),
    })
  ).min(1).describe("Line items in the order"),
})
```

## Discriminated unions

Use `z.discriminatedUnion(key, [...])` when a field accepts different shapes based on a discriminator literal. The handler receives a properly narrowed type.

```typescript
const notification = z.discriminatedUnion("channel", [
  z.object({
    channel: z.literal("email"),
    address: z.string().email(),
    subject: z.string(),
  }),
  z.object({
    channel: z.literal("slack"),
    channelId: z.string(),
    mrkdwn: z.boolean(),
  }),
]);

server.tool(
  { name: "notify", schema: z.object({ notification }) },
  async ({ notification }) => {
    if (notification.channel === "email") {
      // notification.address is typed
    } else {
      // notification.channelId is typed
    }
    return text("Sent");
  }
);
```

## Records (dynamic keys)

```typescript
z.record(z.string(), z.string()).describe("Environment variables")
z.record(z.string(), z.number()).describe("Score per category")
```

## Intersections

Combine schemas with `.and()` or `z.intersection()`.

```typescript
const pagination = z.object({ page: z.number(), limit: z.number() });
const filters = z.object({ status: z.string() });

server.tool(
  { name: "list-items", schema: pagination.and(filters) },
  async ({ page, limit, status }) => text("Listing...")
);
```

## Recursive schemas

Use `z.lazy()` for self-referential structures.

```typescript
type Node = { name: string; children?: Node[] };
const nodeSchema: z.ZodType<Node> = z.lazy(() =>
  z.object({
    name: z.string(),
    children: z.array(nodeSchema).optional(),
  })
);
```

## `.refine()` and `.transform()`

`.refine()` adds custom validation; `.transform()` reshapes the parsed value.

```typescript
// Reject directory traversal
z.string()
  .regex(/^[\w\-. /]+$/)
  .refine((v) => !v.includes(".."), { message: "Path cannot contain '..'" });

// Parse JSON string into a typed object
z.string().transform((str, ctx) => {
  try {
    return JSON.parse(str);
  } catch {
    ctx.addIssue({ code: z.ZodIssueCode.custom, message: "Invalid JSON" });
    return z.NEVER;
  }
});
```

## `.strict()` — reject unknown fields

Always strict your top-level object schemas. Without it, Zod accepts unknown keys by default instead of treating them as validation errors, so the client may think an extra field mattered when it did not.

```typescript
z.object({
  id: z.string().describe("Record ID"),
  title: z.string().describe("New title"),
}).strict()  // Rejects { id: "1", title: "x", extra: true }
```

## Custom error messages

Customize messages to guide the LLM toward valid retries.

```typescript
z.string().min(10, {
  message: "Description must be at least 10 characters long to be useful.",
})
```

## `completable()` — prompts only

`completable()` is for `server.prompt()` argument autocomplete. It is **not supported** in `server.tool()` schemas in `mcp-use@1.26.0`. For the canonical prompt reference, see `../07-prompts/04-completable-arguments.md`. For resource template URI variable autocomplete, use `callbacks.complete` on the resource template definition.

## Cookbook patterns

| Need | Pattern |
|---|---|
| ISO 8601 datetime | `z.string().datetime({ offset: true })` |
| SemVer | `z.string().regex(/^\d+\.\d+\.\d+(-[\w.]+)?$/)` |
| HTTPS URL | `z.string().url().startsWith("https://")` |
| JSON string | `z.string().transform((str, ctx) => { try { return JSON.parse(str); } catch { ctx.addIssue({ code: z.ZodIssueCode.custom, message: "Invalid JSON" }); return z.NEVER; } })` |
| Safe path | `z.string().regex(/^[\w\-. /]+$/).refine(v => !v.includes(".."))` |

## Schema design checklist

- `.describe()` on every field.
- Use constraints (`min`, `max`, `email`, `uuid`, `regex`) — catch bad input before the handler.
- Use `.default()` to reduce required fields.
- Use `.strict()` on every top-level object to turn hallucinated extra fields into explicit validation errors.
- Keep schemas flat — split into multiple tools instead of deep nesting.
- Six fields max per tool. More than that means the tool is doing too much.
- Never `z.any()` or `z.unknown()` — see `08-tool-anti-patterns.md`.
