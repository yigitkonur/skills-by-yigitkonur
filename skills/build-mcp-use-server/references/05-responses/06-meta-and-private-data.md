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
const view = useToolContext<"search">();
if (view.status === "pending") return <Skeleton />;
if (view.status === "error") return <ErrorBanner message={view.error.message} />;
// view.status === "ready": view.toolOutput is typed structuredContent (Register-inferred output type)
const items = (view.meta as { items: Array<...> } | undefined)?.items;
// Use items for rendering
```

`useToolContext` returns a `ToolContextHandle` — a three-way discriminated union on `status` (`"pending" | "ready" | "error"`), not a plain object. `toolOutput` (typed `structuredContent`) is only populated once `status === "ready"`; `meta` is `Record<string, unknown> | undefined` on both `"ready"` and `"error"`, and always `undefined` while `"pending"`. `meta` is not validated against `outputSchema`; use it for large/detailed view-only data.

## Privacy boundaries

- `content` — **model-visible + View-visible** (readability) — the View reads it as `useToolContext().content` (raw `ContentBlock[]`); not validated
- `structuredContent` — **model-visible + View-visible + validated** (if `outputSchema` set) — the View reads it as `useToolContext().toolOutput`, typed by the tool's `outputSchema`
- `_meta` — **View-only** (not sent to model; not validated) — the View reads it as `useToolContext().meta`

Use `_meta` for non-secret auxiliary data that may be disclosed to the connected host/View but should stay out of model context — for example, internal record IDs, presentation data, or intermediate state whose client disclosure is acceptable. Never put API keys, bearer tokens, credentials, or other secrets in `_meta`; data the View does not need should remain server-side.

## Example: large dataset

```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({
  name: "event-server",
  version: "1.0.0",
});

const events = Array.from({ length: 10_000 }, (_, index) => ({
  id: `event-${index + 1}`,
  label: `Event ${index + 1}`,
}));

server.tool(
  {
    name: "list-events",
    outputSchema: z.object({ count: z.number(), summary: z.string() }),
  },
  async (_input, _ctx) => {
    return {
      content: [{ type: "text", text: `${events.length} events this month` }],
      structuredContent: {
        count: events.length,
        summary: "See _meta for full event log",
      },
      _meta: { events }, // Client/View-visible; never put secrets here.
    };
  }
);
```

Model sees count and summary; View can access full events array via `_meta`.
