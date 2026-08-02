# MCP Apps Detection

*Read this when conditionally returning structured content for views.*

Detect whether a client supports MCP apps (views) and adapt your response accordingly.

## Detection Method

Use `ctx.client.supportsViews()` to check if the client declares the `io.modelcontextprotocol/ui` extension:

```typescript
if (ctx.client.supportsViews()) {
  // Client supports MCP apps — can return structuredContent
}
```

## Usage: Conditional Structured Content

```typescript
export const searchProducts = server.tool(
  {
    name: "search_products",
    description: "Search product catalog",
    inputSchema: z.object({
      query: z.string(),
    }),
    outputSchema: z.object({
      products: z.array(
        z.object({
          id: z.string(),
          name: z.string(),
          price: z.number(),
        })
      ),
    }),
    view: {
      name: "product-list",
      description: "Render product search results",
    },
  },
  async ({ query }, ctx) => {
    const products = await db.searchProducts(query);

    // Return both text and structured content
    return {
      content: [
        {
          type: "text",
          text: `Found ${products.length} products matching "${query}"`,
        },
      ],
      structuredContent: {
        products: products.map((p) => ({
          id: p.id,
          name: p.name,
          price: p.price,
        })),
      },
    };

    // Note: supportsViews() check is optional here
    // — if client doesn't support views, it ignores structuredContent
    // and renders the text block instead. The tool always returns both.
  }
);
```

## Fallback Pattern

For tools with rich output that may run on text-only clients:

```typescript
export const generateChart = server.tool(
  {
    name: "generate_chart",
    inputSchema: z.object({ data: z.array(z.number()) }),
    outputSchema: z.object({ chart: z.unknown() }),
    view: { name: "chart-renderer" },
  },
  async ({ data }, ctx) => {
    const chartConfig = generateChartJSON(data);

    if (ctx.client.supportsViews()) {
      // Return rich structured content
      return {
        content: [
          {
            type: "text",
            text: `Chart for data: ${data.join(", ")}`,
          },
        ],
        structuredContent: {
          chart: chartConfig,
        },
      };
    } else {
      // Text-only fallback
      return {
        content: [
          {
            type: "text",
            text: `Data: ${data.join(", ")}\n\nStats: min=${Math.min(...data)}, max=${Math.max(...data)}`,
          },
        ],
      };
    }
  }
);
```

## Key points

- **Always include text.** MCP apps are optional rendering layers. Always provide a `text` content block for clients without view support.
- **No breaking on missing support.** If a client doesn't support views, it silently ignores `structuredContent` and renders the text block. Your tool should not fail.
- **View binding is optional.** You can return `structuredContent` without declaring a tool-level `view`. The client decides whether to render it; view config just hints at the best renderer.
- **Per-request decision.** Check `supportsViews()` per callback if your tool's behavior changes based on client support. Otherwise, always return both text and structured content.

See `references/18-mcp-apps/` for detailed MCP app development (React components, CSP, asset serving).
