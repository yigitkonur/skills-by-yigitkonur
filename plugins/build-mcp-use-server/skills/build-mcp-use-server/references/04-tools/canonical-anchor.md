# Canonical Anchor — Complete Tool Example

*Read this when you want to see a real, complete tool written in v2 style.*

This example shows the modern mcp-use v2 tool pattern in one place, ready to copy and adapt.

```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({
  name: "product-server",
  version: "1.0.0",
  description: "Product catalog and search API",
});

/**
 * Canonical tool: search products by keyword with pagination.
 * - Exported const for mcp-env.d.ts typing
 * - inputSchema with .describe() on every field
 * - outputSchema for typed structured output
 * - annotations declaring behavioral hints
 */
export const searchProducts = server.tool(
  {
    name: "search-products",
    title: "Search Products",
    description:
      "Search products by keyword. Returns matching products sorted by relevance, " +
      "paginated by limit. Use when the user asks for product suggestions or lists.",
    inputSchema: z
      .object({
        query: z
          .string()
          .min(1)
          .max(200)
          .describe("Search keyword, e.g., 'blue shoes' or 'wireless charger'"),
        limit: z
          .number()
          .int()
          .min(1)
          .max(100)
          .default(20)
          .describe("Max results to return"),
        sort: z
          .enum(["relevance", "price_asc", "price_desc", "newest"])
          .default("relevance")
          .describe("Sort order for results"),
      })
      .strict(),
    outputSchema: z.object({
      results: z.array(
        z.object({
          id: z.string(),
          name: z.string(),
          price: z.number(),
          inStock: z.boolean(),
        })
      ),
      total: z.number(),
      executedAt: z.string(),
    }),
    annotations: {
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: false,
    },
  },
  async (input, ctx) => {
    // Log the search
    await ctx.sendLog("info", `Searching products: query="${input.query}" limit=${input.limit}`);

    // Simulate database call (replace with real query)
    const allProducts = await db.products.search(input.query);
    const sorted = allProducts.sort((a, b) => {
      if (input.sort === "price_asc") return a.price - b.price;
      if (input.sort === "price_desc") return b.price - a.price;
      if (input.sort === "newest") return b.createdAt - a.createdAt;
      return 0; // relevance (already ordered by search)
    });
    const paginated = sorted.slice(0, input.limit);

    // Return raw MCP envelope with structured output
    return {
      content: [
        {
          type: "text",
          text: `Found ${allProducts.length} products matching "${input.query}". Showing ${paginated.length}.`,
        },
      ],
      structuredContent: {
        results: paginated.map((p) => ({
          id: p.id,
          name: p.name,
          price: p.price,
          inStock: p.stock > 0,
        })),
        total: allProducts.length,
        executedAt: new Date().toISOString(),
      },
    };
  }
);

// Tool that returns an error
export const getProduct = server.tool(
  {
    name: "get-product",
    description: "Fetch a single product by ID.",
    inputSchema: z.object({
      id: z.string().uuid().describe("Product UUID"),
    }),
    outputSchema: z.object({
      id: z.string(),
      name: z.string(),
      description: z.string(),
      price: z.number(),
    }),
  },
  async (input, ctx) => {
    try {
      const product = await db.products.findById(input.id);
      if (!product) {
        return {
          isError: true,
          content: [
            { type: "text", text: `Product ${input.id} not found in database` },
          ],
        };
      }
      return {
        content: [{ type: "text", text: `Product: ${product.name}` }],
        structuredContent: product,
      };
    } catch (err) {
      return {
        isError: true,
        content: [
          {
            type: "text",
            text: `Database error: ${err instanceof Error ? err.message : "unknown"}`,
          },
        ],
      };
    }
  }
);

await server.listen(3000);
```

## Key Patterns Here

1. **Import from root** — `import { MCPServer } from "mcp-use"` (not `/server`)
2. **Export const for typing** — `export const toolName = server.tool(...)`
3. **Definition-first shape** — definition (arg 1), callback (arg 2)
4. **Field descriptions** — every input field has `.describe()`
5. **Strict object** — `.strict()` prevents hallucinated extra fields
6. **outputSchema required** — for Views and type safety
7. **Structured output** — return `structuredContent` matching schema
8. **Error handling** — return `{ isError: true, content: [...] }` instead of throwing
9. **Context methods** — `ctx.sendLog()`, `ctx.client.can()`, `ctx.auth.user`
10. **Raw MCP envelopes** — no helpers like `text()` or `object()`

Copy and adapt this shape for your server.
