# Register Views and Folder Conventions

*Read this when you are setting up the server file structure, registering views at startup, or running the build/dev pipeline.*

Views are discovered from the `views/` directory by the framework and registered via `registerViews()`. The dev and build commands (`mcp-use dev`, `mcp-use build`) handle registration automatically.

## File Structure

Place React view components in the `views/` directory tree, one folder per view:

```
my-server/
├── index.ts                        # Server entry; import tools
├── views/
│   ├── product-search/
│   │   └── view.tsx                # React component + optional viewConfig export
│   ├── dashboard/
│   │   └── view.tsx
│   └── chart-builder/
│       └── view.tsx
├── public/                         # Static assets (served as /_mcp-use/public/)
├── .mcp-use/                       # Generated at build/dev time
│   └── build/
│       └── views/                  # Compiled view bundles
├── package.json
└── tsconfig.json
```

**Key conventions:**
- View folder name (e.g., `product-search`) must exactly match the tool's `view.name` field
- Each view folder contains at minimum a `view.tsx` file (the React component)
- Nested folders within `views/` are allowed (e.g., `views/admin/user-dashboard/view.tsx`)
- The framework auto-discovers all `.tsx` files matching `views/**/view.tsx` pattern

## View File Exports

Each `view.tsx` must export:

1. **Default export** — the React component (required)
2. **`viewConfig` export** — optional runtime configuration object

```typescript
// views/product-search/view.tsx
import { useToolContext, ThemeProvider } from "mcp-use/react";
import type { ViewConfig } from "mcp-use/react";

export const viewConfig: ViewConfig = {
  displayModes: ["inline", "fullscreen"],
  autoResize: true,
};

export default function ProductSearch() {
  const ctx = useToolContext<"search-products">();

  if (ctx.status === "pending") return <ThemeProvider><p>Loading...</p></ThemeProvider>;
  if (ctx.status === "error") return <ThemeProvider><p>Error: {ctx.error.message}</p></ThemeProvider>;

  return (
    <ThemeProvider>
      <div>
        {ctx.toolOutput.results.map((r) => (
          <div key={r.id}>{r.name}</div>
        ))}
      </div>
    </ThemeProvider>
  );
}
```

## registerViews() and Manifest

The framework calls `registerViews(viewsManifest, options?)` internally to prime the view registry from build or dev manifest data. You do not call this directly — it is managed by the CLI.

**In development** (`mcp-use dev`):
- Watches `views/` directory for changes
- Emits origin-absolute Vite URLs (e.g., `/src/views/product-search/view.tsx?import`)
- Fast Refresh enabled on save (HMR via WebSocket)

**In production** (`mcp-use build`):
- Compiles views into `.mcp-use/build/views/<name>/` 
- Emits JS/CSS asset paths or inline bundles
- No HMR; framework loads precompiled bundles

## CLI Configuration

Pass custom view or MCP directories to `mcp-use dev` and `mcp-use build`:

```bash
# Use views/ and index.ts by default
mcp-use dev

# Explicit directory
mcp-use dev --views-dir ./my-views --entry ./src/index.ts

# For build
mcp-use build --views-dir ./my-views
```

**Env var precedence:**
1. `--views-dir` flag (highest)
2. Default: `views/` folder (or `<mcp-dir>/views/` if `--mcp-dir` is set)

## Integration with Server Entry

Your server entry (`index.ts`) imports and exports tools with `view` fields. The framework connects the tool definitions (via `view.name`) to the compiled view files (via folder name) at registration time.

```typescript
// index.ts
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({ name: "my-app", version: "1.0.0" });

export const searchProducts = server.tool(
  {
    name: "search-products",
    description: "Search products",
    inputSchema: z.object({ query: z.string() }),
    outputSchema: z.object({ query: z.string(), results: z.array(z.any()) }),
    view: { name: "product-search" },  // Links to views/product-search/view.tsx
  },
  async ({ query }) => ({
    content: [{ type: "text", text: `Found results for ${query}` }],
    structuredContent: { query, results: [] },
  })
);

export default server;
```

## Build Output

After `mcp-use build`:

```
.mcp-use/build/
├── views/
│   ├── product-search/
│   │   ├── assets/
│   │   │   ├── index-ABC123.js
│   │   │   └── index-DEF456.css
│   │   └── index.html  (synthesized; contains asset refs)
│   └── dashboard/
│       └── ...
└── (server bundle, manifest, etc.)
```

Each view's HTML document references or embeds the compiled JS/CSS based on build flags (`--inline` embeds, default externalizes).

## Next Steps

- **View runtime config:** references/18-mcp-apps/server-surface/03-viewconfig.md
- **Asset serving and URL rewriting:** references/18-mcp-apps/server-surface/04-assets-mcp-url-and-serving.md
- **CSP metadata and sandbox permissions:** references/18-mcp-apps/server-surface/05-csp-metadata.md
