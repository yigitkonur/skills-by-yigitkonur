# `inputSchema` vs `outputSchema`

`schema` (the input schema) is almost always required. `outputSchema` is opt-in and, in `mcp-use@1.26.0`, should be treated as a TypeScript/codegen hint rather than a runtime wire contract.

**Version note:** `mcp-use@1.26.0` declares `outputSchema` in `dist/src/server/types/tool.d.ts`, but runtime `toolRegistration` in `dist/src/server/index.js` does not pass it to `registerTool`; package runtime behavior wins.

## `schema` — input

The Zod schema for arguments the client sends. Converted to JSON Schema and published on `tools/list`. Validated before the handler runs. Almost every tool has one — the only exception is a no-argument tool (use `z.object({})`).

```typescript
schema: z.object({
  query: z.string().min(1).describe("Search keyword"),
  limit: z.number().int().min(1).max(100).default(20).describe("Max results"),
}).strict()
```

See `03-zod-schemas.md` for the full pattern reference.

## `outputSchema` — output

The Zod schema for `structuredContent` in the response. Optional. In `mcp-use@1.26.0`:

- TypeScript can infer the response type for typed helpers (`useCallTool()`, generated tool maps, Code Mode workflows).
- The runtime does **not** publish it on `tools/list`.
- The runtime does **not** validate `structuredContent` against it before sending.

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

## When to add `outputSchema`

Add it when **at least one** of these is true:

- Generated React helpers or typed `useCallTool()` consumers need an output type.
- A Code Mode workflow processes the JSON.
- An agent bridge or downstream parser explicitly requires structured output.
- The tool defines a long-lived public contract.

Do **not** add `outputSchema` because JSON looks tidy, and do not assume it protects runtime responses in 1.26.0. For broad conversational compatibility, a concise `text()` or `markdown()` response is the safer default.

## Interaction with `structuredContent`

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
