# Widgets to Views: Complete Rewrite

*Read this to migrate MCP App widgets (v1) to Views (v2).*

MCP Apps are renamed to clarify: Views are React components in `views/` directory; they render tool results. The entire interaction model changed.

## File layout and directory structure

**v1**:
```
my-app-server/
├── index.ts
├── resources/
│   ├── product-search/
│   │   └── widget.tsx           # React component
│   └── results-table/
│       └── widget.tsx
```

**v2**:
```
my-app-server/
├── index.ts
├── views/
│   ├── product-search/
│   │   └── view.tsx             # React component + viewConfig export
│   └── results-table/
│       └── view.tsx
├── public/                        # Static assets (new)
├── .mcp-use/build/               # Generated at build time
│   └── views/                    # Compiled assets
└── package.json
```

**Key change**: `resources/widget.tsx` → `views/<name>/view.tsx` (one View per directory).

## Tool binding: widget field → view field

**v1**:
```typescript
server.tool({
  name: "search",
  schema: z.object({ query: z.string() }),
  widget: { name: "product-search", invoking: "Searching...", invoked: "Results ready" },
  cb: async ({ query }) => widget({ props: { query, results: [...] }, output: text(...) }),
});
```

**v2**:
```typescript
export const search = server.tool(
  {
    name: "search",
    inputSchema: z.object({ query: z.string() }),
    outputSchema: z.object({ query: z.string(), results: z.array(...) }),
    view: {
      name: "product-search",           // Folder name under `views/`
      description: "Search results",    // Optional; resource description
      csp: { connectDomains: [...] },   // Optional CSP config
      permissions: [...],               // Optional sandbox permissions
      prefersBorder: true,              // Optional host rendering hints
    },
  },
  async ({ query }) => ({
    content: [{ type: "text", text: `Found ${results.length} results` }],
    structuredContent: { query, results: [...] },
  })
);
```

**Changes**:
- `widget` → `view` (renamed field)
- Removed `invoking`/`invoked` strings (no longer in protocol)
- Added `outputSchema` (required for Views; enables type checking)
- Remove `widget()` helper from result; return raw envelope with `structuredContent`

## View component: Hooks and providers

**v1** (`widget.tsx`):
```typescript
import { useWidget, useWidgetState, useWidgetTheme } from "mcp-use/react";
import React from "react";

export default function SearchWidget() {
  const { props, isPending } = useWidget<{ query: string; results: any[] }>();
  const [expanded, setExpanded] = useWidgetState<boolean>(false);
  const { theme } = useWidgetTheme();

  if (isPending) return <p>Loading...</p>;

  return (
    <McpUseProvider autoSize>
      <div style={{ color: theme.textColor }}>
        <ul>
          {props?.results?.map((r) => (
            <li key={r.id}>{r.name}</li>
          ))}
        </ul>
      </div>
    </McpUseProvider>
  );
}
```

**v2** (`view.tsx`):
```typescript
import { useToolContext, useViewState, useViewTheme, ThemeProvider, ModelContext, ViewControls } from "mcp-use/react";
import type { ViewConfig } from "mcp-use/react";

export const viewConfig: ViewConfig = {
  displayModes: ["inline", "fullscreen"],
  autoResize: true,
};

export default function SearchView() {
  const ctx = useToolContext<"search">();
  const [expanded, setExpanded] = useViewState<boolean>(false);

  if (ctx.status === "pending") return <ThemeProvider><p>Loading...</p></ThemeProvider>;
  if (ctx.status === "error") return <ThemeProvider><p>Error: {ctx.error.message}</p></ThemeProvider>;

  const { query, results } = ctx.toolOutput;

  return (
    <ThemeProvider>
      <ModelContext content={`Showing ${results.length} results for "${query}"`}>
        <ul>
          {results.map((r) => (
            <li key={r.id}>{r.name}</li>
          ))}
        </ul>
      </ModelContext>
    </ThemeProvider>
  );
}
```

**Key changes**:
- `useWidget()` → `useToolContext<"search">()` (typed by tool name)
- Access data via `ctx.toolOutput` (from `structuredContent`), not `props`
- `useWidgetState()` → `useViewState()` (same, renamed)
- `useWidgetTheme()` → `useViewTheme()` (same, renamed)
- Remove `McpUseProvider` wrapper; use explicit providers: `<ThemeProvider>` + `<ErrorBoundary>`
- Add `<ModelContext>` to describe View state to the model (new pattern)
- Export `viewConfig?: ViewConfig` (optional but recommended for display modes)
- Status is now `"pending" | "ready" | "error"` (not `isPending` boolean)

## Accessing tool input during streaming

**v1**:
```typescript
const { props } = useWidget();
// Props only available after tool completes
```

**v2**:
```typescript
const ctx = useToolContext<"search">();
const { toolInput, toolOutput } = ctx;
// toolInput available immediately (from initial call args)
// toolOutput available once tool completes
// Access both during streaming to show partial input
```

## Model-visible state vs. ephemeral state

**v1** — Single state model (unclear what's visible to model):
```typescript
const [filter, setFilter] = useWidgetState({ category: "all" });
// Unclear if model sees this
```

**v2** — Explicit split:
```typescript
// Model-visible (serialized and sent to model)
const [filter, setFilter] = useViewState({ category: "all" });

// Ephemeral (local only)
const [isHovered, setIsHovered] = React.useState(false);

// UI description for model
<ModelContext content={`Filter: ${filter.category}`}>
  {/* Component that renders filtered results */}
</ModelContext>
```

`useViewState` data is serialized and visible to the model. React `useState` is local only.

## Tool calls from Views

**v1**:
```typescript
const { callTool } = useWidget();
const result = await callTool("get-details", { id: "123" });
```

**v2**:
```typescript
import { useCallTool } from "mcp-use/react";
const search = useCallTool(searchToolRef); // Typed call
const result = await search.callTool({ query: "widget" });

// Or dynamic (untyped):
const lookup = useDynamicTool<{ id: string }, { value: string }>("get-details");
const result = await lookup.callTool({ id: "123" });
```

## Assets and public files

**v1** — Manual:
```typescript
<img src="/_mcp-use/widget/product-search/logo.png" />
```

**v2** — Integrated:
```typescript
import { getPublicBaseUrl } from "mcp-use/react";

const baseUrl = getPublicBaseUrl();
<img src={`${baseUrl}/logo.png`} /> // Resolves to /_mcp-use/public/logo.png
```

Place static assets in `public/` directory at root. They're served at `/_mcp-use/public/<filename>`.

## CSP and permissions

**v1** — No CSP config; manual HTML headers:
```typescript
// No server-side CSP in v1 widgets
```

**v2** — Declarative CSP:
```typescript
export const search = server.tool(
  {
    name: "search",
    inputSchema: z.object({ ... }),
    outputSchema: z.object({ ... }),
    view: {
      name: "product-search",
      csp: {
        connectDomains: ["https://api.example.com"],
        resourceDomains: ["https://cdn.example.com"],
      },
      permissions: ["allow-scripts", "allow-forms"],
    },
  },
  async (...) => ({ ... })
);
```

CSP is merged from tool definition + env vars (`CSP_*_DOMAINS`) + auto-append (MCP origin).

## ViewConfig options

```typescript
export const viewConfig: ViewConfig = {
  displayModes: ["inline", "fullscreen", "pip"],  // Advertise supported modes
  autoResize: true,                                // Auto-size to content (default true)
};
```

Values are hints; host decides what to honor.

---

**Next**: See `07-v1-to-v2-sessions-transports-stdio-sse.md` for transport and stateless model changes.
