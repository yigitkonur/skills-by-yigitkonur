# Widgets to Views: Complete Rewrite

*Read this to migrate MCP App widgets (v1) to Views (v2).*

v1 widgets become v2 Views: React components under `views/` that render tool results. The MCP Apps standard remains the protocol; the mcp-use file layout, binding, hooks, state, and result channels changed.

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
    outputSchema: z.object({ query: z.string(), count: z.number() }),
    view: {
      name: "product-search",           // Folder name under `views/`
      description: "Search results",    // Optional; resource description
      csp: { connectDomains: [...] },   // Optional CSP config
      permissions: { camera: {} },      // Optional — object of named capabilities, not a string array
      prefersBorder: true,              // Optional host rendering hints
    },
  },
  async ({ query }) => {
    const results = await searchProducts(query);
    return {
      content: [{ type: "text", text: `Found ${results.length} results` }],
      structuredContent: { query, count: results.length }, // Model-visible, schema-checked
      _meta: { results },                                    // View-only data
    };
  }
);
```

**Changes**:
- `widget` → `view` (renamed field)
- Removed `invoking`/`invoked` strings (no longer in protocol)
- Added `outputSchema` (required for Views; enables type checking)
- Remove `widget()` helper from result; return raw envelope with `structuredContent` and/or `_meta`

**Visibility changed, not just syntax**: v1's `widget({ props, output })` kept `props` hidden from the model (only `output`'s text was model-visible). v2's `structuredContent` is validated against `outputSchema` **and sent to the model** — it is not a drop-in replacement for `props`. For View-only data that should stay out of model context, put it in the result's `_meta` field instead and read it with `useToolContext().meta`:

```typescript
async ({ query }) => {
  const results = await search(query);
  return {
    content: [{ type: "text", text: `Found ${results.length} results` }],
    structuredContent: { count: results.length },  // model-visible, outputSchema-checked
    _meta: { results },                             // View-only, unchecked — closest match to v1 `props`
  };
}
```

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
import { useToolContext, useViewState, ThemeProvider, ModelContext } from "mcp-use/react";
import type { ViewConfig } from "mcp-use/react";

type SearchMeta = {
  results: Array<{ id: string; name: string }>;
};

export const viewConfig: ViewConfig = {
  displayModes: ["inline", "fullscreen"],
  autoResize: true,
};

export default function SearchView() {
  const ctx = useToolContext<"search">();
  const [state, setState] = useViewState({ expanded: false }); // Root state MUST be an object

  if (ctx.status === "pending") return <ThemeProvider><p>Loading...</p></ThemeProvider>;
  if (ctx.status === "error") return <ThemeProvider><p>Error: {ctx.error.message}</p></ThemeProvider>;

  const { query, count } = ctx.toolOutput;
  const results = (ctx.meta as SearchMeta | undefined)?.results ?? [];

  return (
    <ThemeProvider>
      <ModelContext content={`Showing ${count} results for "${query}"`}>
        <button onClick={() => setState({ expanded: !state.expanded })}>
          {state.expanded ? "Collapse" : "Expand"}
        </button>
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
- Access schema-backed, model-visible data via `ctx.toolOutput`; access View-only result data via `ctx.meta` (narrow/validate it yourself) instead of v1 `props`
- `useWidgetState()` → `useViewState()` — **root state must now be a JSON-serializable object** (`{ expanded: false }`, not a bare `boolean`/`string`); it also cannot contain the reserved `_uiContext` key
- `useWidgetTheme()` → `useViewTheme()` (same, renamed)
- Remove the aggregate `McpUseProvider`; the framework owns bootstrap, connection, resizing, and its required top-level error boundary. Compose optional presentation components such as `<ThemeProvider>`, `<ViewControls>`, or your own nested `<ErrorBoundary>` only when needed.
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
import { useCallTool, useDynamicTool } from "mcp-use/react";

// Typed call — pass the tool NAME as a string, not the imported ToolRef.
// Types are derived automatically from mcp-env.d.ts's RegisteredTools map.
// Do not `import { search } from "../../index.js"` into a View file — the
// View bundle must not include server code.
const details = useCallTool("get-details");
const result = await details.callTool({ id: "123" });

// Dynamic (untyped) — for tools registered from a loop/config/OpenAPI doc,
// which cannot export a static ToolRef:
const lookup = useDynamicTool<{ id: string }, { value: string }>("get-details");
const result2 = await lookup.callTool({ id: "123" });
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
        // Also available: frameDomains, baseUriDomains (4 categories total)
      },
      // permissions is an object of named capabilities the view may request
      // from the host, not an iframe `sandbox` attribute string list:
      permissions: { camera: {}, microphone: {}, geolocation: {}, clipboardWrite: {} },
    },
  },
  async (...) => ({ ... })
);
```

Merge order (high → low priority): author `view.csp` → `CSP_*_DOMAINS` env vars (or the `CSP_URLS` shortcut for all four categories) → MCP auto-append (`MCP_URL` → `connectDomains`; assets origin → `resourceDomains`).

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
