# _meta and private data

*Read this when you have data that should not reach the model or not be validated by outputSchema.*

## _meta field (optional metadata)

Append non-schema data to results via `_meta`:

```typescript
return {
  content: [{ type: "text", text: "Found 3 users" }],
  structuredContent: { count: 3 },  // Validated by outputSchema
  _meta: {
    allItems: [...],                // Not in outputSchema; not sent to model
    timestamp: Date.now(),
    source: "production-db"
  },
};
```

**Use `_meta` for:**
- UI-only state (e.g., view props not in model-visible schema)
- Debugging/logging (source, timing, debug flags)
- Large payloads excluded from validation (e.g., full item arrays when schema only cares about count)

**Never use for:** Business-critical data, auth tokens, secrets.

## Views + _meta (MCP Apps)

When tool binds to a View:

```typescript
export const search = server.tool(
  {
    name: "search",
    outputSchema: z.object({ count: z.number() }),
    view: { name: "results" },
  },
  async ({ q }, ctx) => {
    const items = [...];
    return {
      content: [{ type: "text", text: `Found ${items.length}` }],
      structuredContent: { count: items.length },  // Model sees only count
      _meta: { items },                             // View sees full items
    };
  }
);

// In views/results/view.tsx:
const ctx = useToolContext<"search">();
const meta = ctx.meta as { items: Array<...> };
// Use meta.items for rendering
```

View does not validate against `outputSchema`; use `_meta` for large/detailed data.

## Privacy boundaries

- `content` — **model-visible** (readability)
- `structuredContent` — **model-visible + validated** (if `outputSchema` set)
- `_meta` — **UI/view-only** (not sent to model; not validated)

Use `_meta` to hide sensitive details (API keys, internal IDs, intermediate state) from model consumption.

## Example: large dataset

```typescript
server.tool(
  {
    name: "list-events",
    outputSchema: z.object({ count: z.number(), summary: z.string() }),
  },
  async (ctx) => {
    const events = await db.events.fetch(); // 10K items
    return {
      content: [{ type: "text", text: `${events.length} events this month` }],
      structuredContent: {
        count: events.length,
        summary: "See _meta for full event log"
      },
      _meta: { events }  // Large array; not sent to model
    };
  }
);
```

Model sees count and summary; View can access full events array via `_meta`.
