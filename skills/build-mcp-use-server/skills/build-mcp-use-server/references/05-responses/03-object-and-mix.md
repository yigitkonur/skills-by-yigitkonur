# `object()`, `array()`, `mix()`

Structured-data helpers. Use when a typed consumer needs the response — widget, Code Mode, agent bridge, or downstream parser.

## `object(data)`

Returns `TypedCallToolResult<T>` with `application/json` MIME. Populates both `content[0].text` (a pretty-printed JSON serialization) and `structuredContent` (the raw object).

```typescript
import { object } from "mcp-use/server";

server.tool(
  { name: "get-user", schema: z.object({ userId: z.string() }) },
  async ({ userId }) => {
    const user = await fetchUser(userId);
    return object({ userId: user.id, email: user.email, name: user.name });
  }
);
```

Pass a generic for explicit typing:

```typescript
type UserSummary = { id: string; name: string; plan: "free" | "pro" };
return object<UserSummary>({ id: "u_123", name: "Ada", plan: "pro" });
```

`result.structuredContent` is typed as `UserSummary`.

## `array(items)`

Wraps an array in `{ data: T[] }`. Passing an array directly to `object()` delegates to `array()` internally.

```typescript
import { array } from "mcp-use/server";

server.tool({ name: "list-items" }, async () => {
  const items = await getItems();
  return array(items);  // structuredContent: { data: items }
});
```

Return type: `TypedCallToolResult<{ data: T }>`.

## `mix(...responses)`

Merges multiple helper results into one response. Combines `content` arrays, `structuredContent` objects, and `_meta` keys.

```typescript
import { mix, text, image, object, markdown } from "mcp-use/server";

return mix(
  text("Analysis complete. See chart below:"),
  image(chartBase64, "image/png"),
);

return mix(
  markdown("## Quarterly Report\n\nGrowth was **18%** QoQ."),
  image(chartBase64, "image/png"),
  object({ revenue: [100, 118], growthRate: 0.18 }),
);

// Spread an array of helpers
const items = ["a", "b", "c"];
return mix(...items.map((i) => text(`Processed ${i}`)));
```

## Decision logic — text-only, object-only, or mixed

| Result is... | Use |
|---|---|
| A short conversational answer | `text()` or `markdown()` only |
| Strictly programmatic data with no narrative | `object()` only |
| Naturally JSON, but the model also benefits from a summary | `mix(markdown(summary), object(data))` |
| List of items | `array(items)` or `mix(markdown(summary), array(items))` |
| Structured data with attached image | `mix(object(data), image(...))` or `mix(markdown(summary), image(...), object(data))` |

When `outputSchema` is declared, the structured surface must carry the essential answer body — not just metadata or counts. See `08-content-vs-structured-content.md` for the visibility contract.

## Composition rules

1. Lead with the most user-readable helper.
2. Add structured payloads second.
3. Add binary attachments only when the client benefits.
4. Do not duplicate the same payload across multiple helpers.

```typescript
// Bad — same payload three times
return mix(text(bigJson), markdown(bigJson), text(bigJson));

// Good — one readable surface, one structured surface
return mix(text("Export complete."), object({ totalRows: 42 }));
```

## `mix()` with one argument is pointless

```typescript
// Bad
return mix(text("Done"));

// Good
return text("Done");
```

## Examples

```typescript
// Pure structured
server.tool({ name: "build-status" },
  async () => object({ status: "green", durationSeconds: 187 }));

// Mixed
server.tool({ name: "generate-report" },
  async () => {
    const chart = await renderChart();
    return mix(
      markdown("## Quarterly Report\n\nGrowth was **18%**."),
      image(chart, "image/png"),
      object({ revenue: [100, 118], growthRate: 0.18 }),
    );
  });
```
