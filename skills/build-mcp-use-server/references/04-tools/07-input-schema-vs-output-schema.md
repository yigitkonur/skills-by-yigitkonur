# `inputSchema` vs `outputSchema`

*Read this when deciding whether your tool needs an output schema.*

`inputSchema` is mandatory for every tool (even if empty). `outputSchema` is required only when the tool has a View (MCP App) or when downstream clients need typed parsing.

## `inputSchema` — Required

The Standard Schema (Zod v4, ArkType, Valibot, …) for arguments the client sends. Converted to JSON Schema and published on `tools/list`. SDK validates input before the handler runs.

```typescript
inputSchema: z.object({
  query: z.string().min(1).describe("Search keyword"),
  limit: z.number().int().min(1).max(100).default(20).describe("Max results"),
}).strict()
```

Even a no-argument tool needs a schema:

```typescript
inputSchema: z.object({})  // Empty object = no arguments
```

See `03-schemas-standard-schema-and-zod-v4.md` for the full reference.

## `outputSchema` — Optional, Required for Views

The Standard Schema for `structuredContent` in the response. Optional unless:

1. **Tool has a View** — required by `view: { name, ... }` binding. View receives props via `structuredContent`.
2. **Downstream type safety** — TypeScript clients, agents, or codegen need type inference.

```typescript
outputSchema: z.object({
  tickets: z.array(z.object({
    id: z.string(),
    title: z.string(),
    status: z.string(),
  })),
  total: z.number(),
})
```

## When `outputSchema` is Validated

SDK validates `structuredContent` against `outputSchema` **at runtime, after the handler returns**. Mismatch = error response. Tools without `outputSchema` skip output validation.

## Typical Patterns

| Scenario | inputSchema | outputSchema | Response |
|----------|---|---|---|
| Search tool (text result) | ✓ required | optional | `{ content: [{ type: "text", text: "..." }] }` |
| Search tool (with View) | ✓ required | ✓ required | `{ content: [...], structuredContent: { results: [...] } }` |
| Chart builder tool (View) | ✓ required | ✓ required | `{ content: [...], structuredContent: { svg: "..." } }` |
| No-argument tool | ✓ `z.object({})` | optional | `{ content: [...], structuredContent?: {...} }` |

See `02-registering-a-tool.md` and `canonical-anchor.md` for complete examples.

`outputSchema` describes a contract. `structuredContent` is the runtime value matching that contract. The relationship has a subtle trap:

If you return `object(...)` (or `mix(markdown(...), object(...))`), the helper emits `structuredContent` automatically. Some hosts then prefer `structuredContent` over `content[].text` for the model's view of the result.

That means: if `structuredContent` only contains pagination/metadata while the actual answer lives in `content[].text`, structured-first hosts surface a successful-looking call with no answer body.

The fix is the visibility contract — see `05-responses/08-content-vs-structured-content.md`. Both surfaces should carry the essential answer.

## Decision table

| Situation | Use `outputSchema`? | Default response helper |
|---|---|---|
| Conversational answer, no programmatic consumer | No | `text()` or `markdown()` |
| Widget rendering | Not for runtime validation | `widget()` |
| Code Mode / agent bridge consumer | Yes | `object()` or `mix(markdown(...), object(...))` |
| Public tool contract | Yes | `object()` or `mix(...)` |
| Internal exploratory tool | No | `text()` or `object()` without schema |

## Example

```typescript
server.tool(
  {
    name: "search-tickets",
    description: "Search tickets by status and keyword.",
    schema: z.object({
      query: z.string().min(1).describe("Search keyword"),
      status: z.enum(["open", "closed"]).describe("Status filter"),
    }).strict(),
    outputSchema: z.object({
      tickets: z.array(z.object({
        id: z.string(),
        title: z.string(),
        status: z.string(),
      })),
      total: z.number(),
    }),
    annotations: { readOnlyHint: true, idempotentHint: true, openWorldHint: false },
  },
  async ({ query, status }) => {
    const tickets = await db.searchTickets(query, status);
    return mix(
      markdown(`Found ${tickets.length} tickets matching "${query}".`),
      object({ tickets, total: tickets.length }),
    );
  }
);
```

The `mix()` covers both surfaces: the markdown summary for content-first clients, the structured object for typed/structured-first clients. Both contain the essential answer. Add tests if `outputSchema` is a public contract; `mcp-use@1.26.0` will not enforce it at runtime.
