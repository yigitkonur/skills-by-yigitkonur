# The Tool `view` Field

*Read this when binding a UI view to a tool — the v2 replacement for v1's `server.uiResource()` + `widget` config.*

In v2 a view is declared **on the tool definition**, not registered as a separate UI resource. The framework derives the view resource, its `ui://` URI, and the wire metadata from this one field.

## Shape

```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";

server.tool(
  {
    name: "search-products",
    description: "Search the product catalog.",
    inputSchema: z.object({ query: z.string().describe("Search text") }),
    outputSchema: productResultsSchema, // REQUIRED when view is set
    view: {
      name: "product-search",   // must match views/product-search/view.tsx
      description: "Product results grid",   // optional resource description
      csp: { connectDomains: ["https://api.example.com"] }, // optional, see 05-csp-metadata.md
      permissions: {},           // optional sandbox permissions (@modelcontextprotocol/ext-apps)
      domain: "https://views.example.com",  // optional dedicated-origin hint
      prefersBorder: true,       // optional: ask host to draw a border
    },
  },
  async ({ query }) => {
    const results = await search(query);
    return {
      content: [{ type: "text", text: `Found ${results.length} products.` }],
      structuredContent: { query, results }, // becomes the view's props; typed by outputSchema
    };
  }
);
```

## Rules

- **`outputSchema` is required for view binding.** The view's props are the tool result's `structuredContent`, and the schema is their type contract. Omitting it is a registration-time error, not a style choice.
- **`view.name` must exactly match the folder name** under `views/` (`views/<name>/view.tsx`). Mismatch means the view resource resolves to nothing — see `references/27-troubleshooting/04-view-rendering-issues.md`.
- **Always return model-visible `content` alongside `structuredContent`.** Hosts without view support (and the model itself) only see `content` — this is the text fallback.
- `visibility: "app"` on the tool definition hides the tool from the model while keeping it callable from views (for view-internal refresh/pagination tools). Default is model-visible.
- The deprecated v1 `widget({ props, output })` helper still works but raw envelopes are canonical — see `references/05-responses/07-deprecated-v1-helpers.md`.

## What the framework emits on the wire

- `tools/list` entries carry `_meta.ui` (including visibility) so hosts know the tool has a view.
- The view resource is served at `ui://views/<name>.html` with MIME `text/html;profile=mcp-app`, carrying `_meta.ui` with `csp`, `permissions`, `domain`, and `prefersBorder`.
- CSP is merged three ways (author `view.csp` > `CSP_*_DOMAINS` env > auto-append) — details in `references/18-mcp-apps/server-surface/05-csp-metadata.md`.

## Related

- Folder conventions and registration mechanics: `references/18-mcp-apps/server-surface/02-register-views-and-folder-conventions.md`
- Per-view runtime config export: `references/18-mcp-apps/server-surface/03-viewconfig.md`
- The complete worked example: `references/18-mcp-apps/canonical-anchor.md`
- Migrating v1 `uiResource`/`widgetMetadata` code: `references/28-migration/06-v1-to-v2-widgets-to-views.md`
