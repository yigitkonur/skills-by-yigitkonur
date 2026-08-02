# When to Use Views vs. Tools-Only

*Read this when deciding whether a tool needs an interactive view.*

Not every tool needs a view. Use this decision matrix to choose.

## Decision Matrix

| Need | Tools-Only | View (MCP Apps) | Why |
|-|-|-|-|
| Return structured data (JSON, objects) | ✓ | ✓ | Both work; views add interactivity |
| User selects from results | ✗ | ✓ | View can render clickable list; tools-only needs follow-up message |
| Real-time updates / progress | ✗ | ✓ | View can poll or subscribe; tools-only tool runs once |
| Complex layout (charts, galleries, tables) | ✗ | ✓ | HTML + CSS in views; tools-only limited to text |
| Tool runs deterministically (no user input) | ✓ | — | Tools-only is simpler; no view needed |
| Tool returns plain text (summaries, reports) | ✓ | — | View overhead unjustified |
| Multi-step interaction (filter, sort, drill-down) | ✗ | ✓ | View calls other tools via `useCallTool()` |
| Render in full-screen or iframe | ✗ | ✓ | Views support display modes |

## Quick Test: "Is This a View?"

Ask: *Does the output need interaction beyond reading a text response?*

- **Yes** → Use a view. Example: "display 100 search results; let user click to see details."
- **No** → Tools-only is simpler. Example: "calculate and return a number; model decides next step."

## Examples

### Tools-Only (No View Needed)

```typescript
// Calculate tax
export const calculateTax = server.tool(
  {
    name: "calculate-tax",
    description: "Calculate sales tax",
    inputSchema: z.object({ amount: z.number() }),
    outputSchema: z.object({ tax: z.number(), total: z.number() }),
    // No `view` field
  },
  async ({ amount }) => ({
    content: [{ type: "text", text: `Tax: $${tax.toFixed(2)}, Total: $${total.toFixed(2)}` }],
    structuredContent: { tax, total },
  })
);
```

### Needs a View

```typescript
// Search with results list and drill-down
export const searchProducts = server.tool(
  {
    name: "search-products",
    description: "Search products by keyword",
    inputSchema: z.object({ query: z.string() }),
    outputSchema: productResultsSchema,
    view: { name: "product-list" },  // User clicks items to see details
  },
  async ({ query }) => ({
    content: [{ type: "text", text: `Found ${results.length} products` }],
    structuredContent: { query, results },
  })
);
```

In the view (`views/product-list/view.tsx`), user clicks a product to call a detail tool via `useCallTool()`.

## Performance Note

Views have latency overhead (iframe setup, React hydration, asset download). For lightweight tools returning small results, tools-only is faster and more predictable. For tools where the model needs visual output to decide next steps, views are essential.

## See Also

- `references/18-mcp-apps/server-surface/01-tool-view-field.md` — how to bind a view to a tool
- `references/18-mcp-apps/view-react/02-usetoolcontext.md` — how to read tool context in a view
- `references/18-mcp-apps/view-react/03-usecalltool.md` — how to call other tools from a view
