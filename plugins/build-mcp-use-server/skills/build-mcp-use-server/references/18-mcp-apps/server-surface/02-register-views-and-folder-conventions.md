# Register Views and Folder Conventions

*Read this when setting up View source files or integrating the View build manifest with a server.*

The CLI discovers View modules, produces a `ViewsManifest`, and primes the server before mount. Normal server authors rely on the CLI or Next.js integration; `registerViews` exists for build/tooling integration, not routine application registration.

## Source Convention

```text
my-server/
├── index.ts                         # Default-exports the MCPServer
├── mcp-env.d.ts                     # CLI-generated Register.tools augmentation
├── views/
│   ├── product-search/
│   │   └── view.tsx
│   ├── dashboard/
│   │   └── view.tsx
│   └── chart-builder/
│       └── view.tsx
├── public/
├── package.json
└── tsconfig.json
```

Discovery is exactly one directory level deep: `views/<name>/view.tsx`.

- The folder name must equal the bound tool's `view.name`.
- A deeper path such as `views/admin/dashboard/view.tsx` is not discovered.
- Directories without `view.tsx` are ignored.
- A missing or empty `views/` directory produces an empty manifest; tool-only servers need no View folder.

## View Module Exports

```typescript
// views/product-search/view.tsx
import { ThemeProvider, useToolContext } from "mcp-use/react";
import type { ViewConfig } from "mcp-use/react";

export const viewConfig: ViewConfig = {
  displayModes: ["inline", "fullscreen"],
  autoResize: true,
};

export default function ProductSearch() {
  const ctx = useToolContext<"search-products">();

  if (ctx.status === "pending") return <p>Loading...</p>;
  if (ctx.status === "error") return <p>Error: {ctx.error.message}</p>;

  return (
    <ThemeProvider>
      {ctx.toolOutput.results.map((result) => (
        <div key={result.id}>{result.name}</div>
      ))}
    </ThemeProvider>
  );
}
```

The default component is required. `viewConfig` is optional and is read by generated bootstrap code.

## Normal Author Workflow

```typescript
// index.ts
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({ name: "my-app", version: "1.0.0" });

server.tool(
  {
    name: "search-products",
    inputSchema: z.object({ query: z.string() }),
    outputSchema: z.object({
      query: z.string(),
      results: z.array(z.object({ id: z.string(), name: z.string() })),
    }),
    view: { name: "product-search" },
  },
  async ({ query }) => ({
    content: [{ type: "text", text: `Found results for ${query}` }],
    structuredContent: { query, results: [] },
  })
);

export default server;
```

Use `mcp-use dev`, `mcp-use build`, `mcp-use start`, or the Next.js adapter. Do not add a manual registration call or `.listen()` to a CLI-owned entry.

## What `registerViews` Is

Beta.66 publicly exports `registerViews` as a `unique symbol`. The production build wrapper uses it in this shape:

```typescript
import { registerViews } from "mcp-use";

server[registerViews](viewsManifest);
```

This is a **tooling/build integration API** for generated wrappers or a custom pipeline that already owns a valid `ViewsManifest`. It is not the normal author API, and hand-authoring manifests is discouraged. Do not call or document internal string-keyed priming aliases.

Priming may happen only once and before the server starts; repeating it or priming after startup throws.

## Dev Manifest

For each discovered View, dev creates an external manifest entry with Vite-served URLs:

```json
{
  "product-search": {
    "kind": "external",
    "entry": "/@id/__x00__virtual:mcp-use/views/product-search",
    "css": [],
    "scripts": ["/@vite/client"]
  }
}
```

Vite serves modules and HMR. No physical per-View HTML file is created.

## Production Manifest and Assets

The build manifest at `.mcp-use/build/manifest.json` contains `buildId`, `entryPoint`, `createdAt`, and `views`.

Default external View entry:

```json
{
  "views": {
    "product-search": {
      "kind": "external",
      "entry": "assets/product-search-ABC123.js",
      "css": ["assets/product-search-DEF456.css"]
    }
  }
}
```

Inline View entry:

```json
{
  "views": {
    "product-search": {
      "kind": "inline",
      "js": "/* minified module source */",
      "css": "/* aggregated styles */"
    }
  }
}
```

Representative external build tree:

```text
.mcp-use/build/
├── index.js
├── manifest.json
└── views/
    ├── product-search/
    │   └── assets/
    │       ├── product-search-ABC123.js
    │       └── product-search-DEF456.css
    ├── dashboard/
    │   └── assets/
    │       └── dashboard-GHI789.js
    └── public/                      # Copy of project public/ assets
```

There is no emitted `views/<name>/index.html`. On `resources/read`, the server uses the manifest to synthesize a complete HTML document. External entries become absolute `<script>`/`<link>` URLs; inline entries become embedded `<script type="module">` and `<style>` blocks.

## Exact Binding Validation

Binding failures are surfaced during tool registration or mount/build validation:

| Condition | Outcome |
|-|-|
| View-bound tool has no `outputSchema` | Throw immediately while registering the tool |
| Two tools bind the same View name | Throw while registering the second tool |
| A tool binds a View but no manifest was primed | Throw at mount/build validation |
| A tool's View name is absent from the manifest | Throw at mount/build validation |
| A manifest View has no owning tool | Warn, but continue |

`mcp-use build` runs the same mount-time validation before emitting the final server bundle.

## Next Steps

- Tool binding and wire keys: `01-tool-view-field.md`
- Runtime config and HMR snapshot behavior: `03-viewconfig.md`
- Asset URL resolution and HTML synthesis: `04-assets-mcp-url-and-serving.md`
- CSP and permissions: `05-csp-metadata.md`
