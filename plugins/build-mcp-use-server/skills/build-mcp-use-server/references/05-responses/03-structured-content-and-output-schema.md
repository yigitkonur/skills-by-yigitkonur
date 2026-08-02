# Structured content and output schema

*Read this when your tool declares `outputSchema` or needs typed results.*

## The equivalence rule

When `outputSchema` is set, callback must return:
```typescript
{ content: [...], structuredContent: data }  // data matches outputSchema
```

Or error:
```typescript
{ isError: true, content: [...] }            // no structuredContent when error
```

## Example: inventory search

```typescript
export const search = server.tool(
  {
    name: "search-inventory",
    inputSchema: z.object({ sku: z.string() }),
    outputSchema: z.object({
      sku: z.string(),
      quantity: z.number(),
      location: z.string(),
    }),
  },
  async ({ sku }, ctx) => {
    const item = await db.get(sku);
    if (!item) {
      return {
        isError: true,
        content: [{ type: "text", text: `SKU not found: ${sku}` }],
      };
    }
    return {
      content: [{ type: "text", text: `Found ${item.sku} at ${item.location}` }],
      structuredContent: {
        sku: item.sku,
        quantity: item.qty,
        location: item.location,
      },
    };
  }
);
```

SDK validates `structuredContent` against `outputSchema` at runtime.

## Auto JSON appending

SDK auto-appends JSON text block when:
1. `structuredContent` is a non-object scalar (number, string, boolean, array of scalars)
2. No `type: "text"` block already in `content`

```typescript
// SDK adds JSON block automatically
return { structuredContent: [1, 2, 3] };
// Result: { content: [{ type: "text", text: "[1,2,3]" }], structuredContent: [1, 2, 3] }
```

For objects, SDK does **not** auto-append; return explicit text block.

## _meta privacy (separate from structuredContent)

Use `_meta` for UI-only or private data (not validated by `outputSchema`):

```typescript
return {
  content: [...],
  structuredContent: { count: items.length },
  _meta: { allItems: [...] }  // Not in schema, not sent to model
};
```

See `06-meta-and-private-data.md` for guidance on when to use `_meta` vs `structuredContent`.
