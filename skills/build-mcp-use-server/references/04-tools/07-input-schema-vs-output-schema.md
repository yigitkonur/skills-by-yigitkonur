# `inputSchema` vs `outputSchema`

*Read this when deciding whether your tool needs an output schema.*

`inputSchema` is optional in the type contract but recommended for every tool; omit it only when the tool accepts an untyped argument record. `outputSchema` is required only when the tool has a View (MCP App) or when downstream clients need typed parsing.

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

If you set `structuredContent` in your raw return, some hosts prefer it over `content[].text` for the model's view of the result.

That means: if `structuredContent` only contains pagination/metadata while the actual answer lives in `content[].text`, structured-first hosts surface a successful-looking call with no answer body.

The fix is the visibility contract: both surfaces should carry the essential answer.

## Decision table

Return raw MCP envelopes in every case — `text()`, `markdown()`, `widget()`, `object()`, and `mix()` are v1 helpers, exported from `mcp-use` for compatibility only and marked `@deprecated` (see `../05-responses/07-deprecated-v1-helpers.md`). New code should not call them.

| Situation | Use `outputSchema`? | Raw envelope |
|---|---|---|
| Conversational answer, no programmatic consumer | No | `{ content: [{ type: "text", text }] }` |
| Widget rendering (MCP App View) | Yes — required by `view` binding | `{ content: [...], structuredContent }` |
| Code Mode / agent bridge consumer | Yes | `{ content: [{ type: "text", text: JSON.stringify(data) }], structuredContent: data }` |
| Public tool contract | Yes | `{ content: [...], structuredContent }` |
| Internal exploratory tool | No | `{ content: [{ type: "text", text }] }` |

## Example

```typescript
server.tool(
  {
    name: "search-tickets",
    description: "Search tickets by status and keyword.",
    inputSchema: z.object({
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
    return {
      content: [{ type: "text", text: `Found ${tickets.length} tickets matching "${query}".` }],
      structuredContent: { tickets, total: tickets.length },
    };
  }
);
```

The example returns both `content` (a summary for content-first clients) and `structuredContent` (an object for typed/structured-first clients). Both contain the essential answer.
