---
name: build-mcp-use-app
description: Use skill if you are building interactive, visual MCP Apps with the mcp-use TypeScript library — widget-based applications that render UI inside ChatGPT, Claude, Goose, and other MCP-compatible clients. Covers tool-to-widget binding, useWidget/useCallTool hooks, streaming preview, display modes, theming, CSP, McpUseProvider, widget state, follow-up messages, and deployment.
---

# Build MCP Use App

Build interactive, widget-based MCP Apps with the `mcp-use` TypeScript library (v1.21+, Node 22 LTS). MCP Apps render visual UI inside ChatGPT, Claude, Goose, and other MCP-compatible hosts. This skill covers the **app/widget side** — tool-to-widget binding, React hooks (`useWidget`, `useCallTool`, `useWidgetProps`, `useWidgetTheme`, `useWidgetState`), components (`McpUseProvider`, `Image`, `ErrorBoundary`, `ThemeProvider`, `WidgetControls`), streaming preview, display modes, theming, CSP, persistent state, and follow-up messages.

> **Not building UI?** Use `build-mcp-use-server` for plain MCP servers without widgets.

## Decision tree

```
What do you need?
│
├── New MCP App from scratch
│   ├── Minimal app with one widget ─────────► Quick start (below) + references/guides/quick-start.md
│   ├── Multi-widget app ────────────────────► Quick start + references/guides/widgets-and-ui.md
│   └── OAuth-protected app ─────────────────► references/guides/quick-start.md + references/guides/authentication.md
│
├── Tool-to-widget binding
│   ├── Binding a tool to a widget ──────────► Core API: Tool-to-widget binding (below)
│   ├── widget() response helper ────────────► Core API: Response helpers (below) + references/guides/response-helpers.md
│   └── Widget metadata & props schema ──────► Core API: Widget metadata (below)
│
├── Widget development (React)
│   ├── useWidget hook (props, state, theme) ► Core API: useWidget (below) + references/guides/widgets-and-ui.md
│   ├── useCallTool (call tools from widget) ► Core API: useCallTool (below) + references/guides/widgets-and-ui.md
│   ├── Helper hooks (props/theme/state) ────► Core API: Helper hooks (below)
│   ├── McpUseProvider wrapper ──────────────► Core API: McpUseProvider (below)
│   └── Image, ErrorBoundary, ThemeProvider ─► Core API: Utility components (below)
│
├── Streaming & live preview
│   ├── Streaming tool arguments ────────────► Core API: Streaming (below) + references/guides/streaming-and-preview.md
│   └── isPending / partialToolInput ────────► Core API: useWidget (below)
│
├── Display & theming
│   ├── Dark/light theme support ────────────► Core API: useWidget (below) — theme property
│   ├── Display modes (inline/pip/fullscreen) ► Core API: Display modes (below)
│   └── Safe area insets (mobile) ───────────► Core API: useWidget (below) — safeArea property
│
├── Widget interactions
│   ├── Follow-up messages ──────────────────► Core API: Follow-up messages (below)
│   ├── Persistent widget state ─────────────► Core API: Persistent state (below)
│   ├── Elicitation from widgets ────────────► references/guides/elicitation-and-sampling.md
│   └── Open external URLs ──────────────────► Core API: useWidget (below) — openExternal
│
├── Security & CSP
│   ├── Content Security Policy config ──────► Core API: CSP configuration (below)
│   ├── baseUrl for production ──────────────► Core API: MCPServer constructor (below)
│   └── External API domains ───────────────► Core API: CSP configuration (below)
│
├── Public assets & images
│   ├── Static files in public/ ─────────────► Project structure (below) — public/ directory
│   └── Image component usage ──────────────► Core API: Utility components (below)
│
├── Testing & debugging
│   ├── Inspector with widget preview ───────► references/guides/testing-and-debugging.md
│   ├── Widget debugger overlay ─────────────► Core API: McpUseProvider (below) — debugger prop
│   └── Common widget errors ───────────────► references/troubleshooting/common-errors.md
│
├── Production & deployment
│   ├── Deploy MCP App ──────────────────────► references/patterns/deployment.md
│   ├── ChatGPT Apps publishing ────────────► references/guides/chatgpt-apps-flow.md
│   ├── Hardening patterns ──────────────────► references/patterns/production-patterns.md
│   └── Anti-patterns ──────────────────────► references/patterns/anti-patterns.md
│
└── Complete examples
    ├── Widget recipes ──────────────────────► references/examples/widget-recipes.md
    └── Project templates ───────────────────► references/examples/project-templates.md
```

## Quick start

Minimal MCP App with a widget:

**`index.ts`** — server entry with tool-to-widget binding:

```typescript
import { MCPServer, widget, text, object } from "mcp-use/server";  // mcp-use ^1.21.0
import { z } from "zod";                                              // zod ^4.0.0

const server = new MCPServer({
  name: "my-app",
  version: "1.0.0",
  description: "Interactive MCP App with widgets",
  baseUrl: process.env.MCP_URL || "http://localhost:3000",
});

server.tool(
  {
    name: "search-products",
    description: "Search products and display results in a visual widget",
    schema: z.object({ query: z.string().describe("Search query") }),
    widget: {
      name: "product-search-result",       // must match resources/<name>/widget.tsx
      invoking: "Searching...",
      invoked: "Results loaded",
    },
  },
  async ({ query }) => {
    const results = [
      { id: "1", name: "Widget Pro", price: 29.99 },
      { id: "2", name: "Widget Max", price: 49.99 },
    ].filter(p => p.name.toLowerCase().includes(query.toLowerCase()));

    return widget({
      props: { query, results },
      output: text(`Found ${results.length} products for "${query}"`),
    });
  }
);

// Non-widget tool (callable from widgets via useCallTool)
server.tool(
  {
    name: "get-product-details",
    description: "Get detailed product information",
    schema: z.object({ productId: z.string().describe("Product ID to look up") }),
  },
  async ({ productId }) => object({ id: productId, name: "Widget Pro", price: 29.99, reviews: 4.5 })
);

await server.listen();
```

**`resources/product-search/widget.tsx`** — widget component:

```tsx
import { McpUseProvider, useWidget, useCallTool, Image } from "mcp-use/react";

interface Props {
  query: string;
  results: Array<{ id: string; name: string; price: number }>;
}

const ProductSearch: React.FC = () => {
  const { props, isPending, theme } = useWidget<Props>();
  const { callTool, data, isPending: detailsPending } = useCallTool("get-product-details");

  if (isPending) {
    return <div className="animate-pulse p-4">Searching...</div>;
  }

  return (
    <div data-theme={theme} className="p-4">
      <h2>Results for &quot;{props.query}&quot;</h2>
      <div className="grid gap-2">
        {props.results.map(product => (
          <div key={product.id} className="border rounded p-3">
            <h3>{product.name}</h3>
            <p>${product.price}</p>
            <button onClick={() => callTool({ productId: product.id })}>
              {detailsPending ? "Loading..." : "View Details"}
            </button>
          </div>
        ))}
      </div>
      {data && <pre>{JSON.stringify(data.structuredContent, null, 2)}</pre>}
    </div>
  );
};

const App: React.FC = () => (
  <McpUseProvider autoSize>
    <ProductSearch />
  </McpUseProvider>
);

export default App;
```

Run: `npx mcp-use dev`
Test: opens Inspector at `http://localhost:3000` with widget preview

## Project structure

```
my-mcp-app/
├── index.ts                  # Server entry + tool definitions
├── resources/
│   ├── product-search/
│   │   ├── widget.tsx        # Main widget component (default export)
│   │   ├── components/       # Sub-components (optional)
│   │   ├── hooks/            # Custom hooks (optional)
│   │   └── types.ts          # TypeScript types (optional)
│   ├── weather-display/
│   │   └── widget.tsx
│   └── styles.css            # Shared styles (optional)
├── public/                   # Static assets (images, icons)
│   └── fruits/
│       └── apple.png
├── package.json
└── tsconfig.json
```

## Core API

### MCPServer constructor

```typescript
const server = new MCPServer({
  name: "my-app",
  version: "1.0.0",
  description: "What the app does",
  baseUrl: process.env.MCP_URL || "http://localhost:3000",  // REQUIRED for production (CSP auto-config)
  title: "My App",                           // optional — display name for clients
  icons: [{ src: "icon.svg", mimeType: "image/svg+xml", sizes: ["512x512"] }],
  favicon: "favicon.ico",                    // optional — relative to public/
  oauth: oauthAuth0Provider(),               // optional
  sessionStore: new RedisSessionStore(),     // optional
  cors: { origin: ["https://myapp.com"] },   // optional
});
```

### Tool-to-widget binding

The core MCP App pattern — bind a tool to a widget folder:

```typescript
server.tool(
  {
    name: "tool-name",
    description: "Agent-facing description of what this tool does",
    schema: z.object({
      param: z.string().describe("What this parameter means"),
    }),
    widget: {
      name: "widget-folder-name",  // MUST match resources/<name>/widget.tsx
      invoking: "Status while tool runs...",
      invoked: "Status when tool completes",
    },
  },
  async (args, ctx) => {
    return widget({
      props: { /* → useWidget().props — structured data, hidden from LLM */ },
      output: text("..."),            // → visible to LLM as tool result
      metadata: { /* → useWidget().metadata — optional extra data */ },
    });
  }
);
```

### Response helpers

| Helper | Use for |
|--------|---------|
| `widget({ props, output, metadata })` | **Primary for MCP Apps** — returns visual widget UI |
| `text(str)` | Plain text visible to LLM (also used as `output` inside `widget()`) |
| `object(obj)` | Structured JSON — for data-only tools or `useCallTool` results |
| `markdown(str)` | Rich formatted text for LLM |
| `error(str)` | Expected failures (sets `isError: true`) |
| `image(b64, mime)` | Base64 images |
| `audio(b64, mime)` | Audio content |
| `binary(b64, mime)` | Arbitrary binary data |
| `html(str)` | HTML content |
| `xml(str)` | XML content |
| `css(str)` | CSS stylesheets |
| `javascript(str)` | JavaScript code |
| `array(items)` | Array of items |
| `resource(uri, mimeOrContent, text?)` | Resource references |
| `mix(...)` | Multiple content types combined |

Deep dive: `references/guides/response-helpers.md`

### useWidget hook

The primary widget hook — provides all widget context:

```typescript
const {
  props,                 // TProps — widget props from tool result
  isPending,             // boolean — true while tool is executing
  output,                // TOutput — tool output (if any)
  metadata,              // TMetadata — extra metadata from tool
  state,                 // TState — persisted widget state
  setState,              // (state: TState) => Promise<void> — update persisted state
  theme,                 // "light" | "dark"
  displayMode,           // "inline" | "pip" | "fullscreen"
  requestDisplayMode,    // (mode: string) => void — request mode change
  callTool,              // call another tool (prefer useCallTool instead)
  sendFollowUpMessage,   // (msg: string) => void — send message on behalf of user
  openExternal,          // (url: string) => void — open URL in new tab
  isStreaming,            // boolean — true during streaming
  partialToolInput,      // Partial<TProps> — partial args during streaming
  safeArea,              // { top, right, bottom, left } — mobile insets
  maxHeight,             // number — max widget height
  userAgent,             // string — device info
  locale,                // string — host locale
  mcp_url,               // string — server base URL
  hostInfo,              // { name, version } — host application
  hostCapabilities,      // host capability flags
  isAvailable,           // boolean — true when widget API is present
  notifyIntrinsicHeight, // (height: number) => void — notify host of height
} = useWidget<TProps, TOutput, TMetadata, TState>();
```

### useCallTool hook

Call MCP tools from within a widget:

```typescript
const {
  callTool,        // (args, options?) => void — fire-and-forget
  callToolAsync,   // (args) => Promise<result> — async/await
  data,            // last successful result
  isPending,       // boolean
  isSuccess,       // boolean
  isError,         // boolean
  error,           // Error | null
  status,          // "idle" | "pending" | "success" | "error"
  isIdle,          // boolean
} = useCallTool("tool-name");

// Fire-and-forget with callbacks:
callTool({ arg1: "value" }, {
  onSuccess: (data) => console.log(data.structuredContent),
  onError: (err) => console.error(err),
});

// Async/await:
const result = await callToolAsync({ arg1: "value" });
console.log(result.structuredContent);
```

### Helper hooks

Focused hooks when you only need one piece of widget context:

```typescript
const props = useWidgetProps<Props>();                          // just props
const theme = useWidgetTheme();                                 // just "light" | "dark"
const [state, setState] = useWidgetState<State>(initialState);  // just state
```

### McpUseProvider

Wraps widget content — required at the root of every widget:

```tsx
<McpUseProvider autoSize debugger viewControls="fullscreen">
  <MyWidget />
</McpUseProvider>
```

| Prop | Type | Description |
|------|------|-------------|
| `autoSize` | `boolean` | Auto-notify host of widget height changes |
| `debugger` | `boolean` | Show debug overlay with props/state inspector |
| `viewControls` | `boolean \| "pip" \| "fullscreen"` | Show display mode controls |

### WidgetControls

Optional component for custom control placement:

```tsx
<WidgetControls debugger viewControls position="top-right" showLabels>
  <MyWidget />
</WidgetControls>
```

### Utility components

```tsx
import { ErrorBoundary, Image, ThemeProvider } from "mcp-use/react";

// ErrorBoundary — catches widget render errors gracefully
<ErrorBoundary>
  <MyComponent />
</ErrorBoundary>

// Image — handles URL resolution for public/ assets
<Image src="/fruits/apple.png" alt="Apple" />

// ThemeProvider — provides theme context to children
<ThemeProvider>
  <MyWidget />
</ThemeProvider>
```

### Widget metadata

Type-safe props schema and CSP configuration via `widgetMetadata` export:

```typescript
// resources/my-widget/widget.tsx (named export alongside default component)
import { type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

export const widgetMetadata: WidgetMetadata = {
  description: "Display search results",
  props: z.object({
    query: z.string(),
    results: z.array(z.object({
      id: z.string(),
      name: z.string(),
      price: z.number(),
    })),
  }),
};
```

### CSP configuration

Declare external domains in `widgetMetadata` when your widget calls external APIs:

```typescript
export const widgetMetadata: WidgetMetadata = {
  description: "Weather display widget",
  props: propSchema,
  metadata: {
    csp: {
      connectDomains: ["https://api.weather.com"],   // fetch/XHR targets
      resourceDomains: ["https://cdn.weather.com"],  // images, fonts, scripts
      frameDomains: [],                               // iframe sources
    },
  },
};
```

### Streaming tool arguments (live preview)

Show partial results while the tool is still streaming arguments:

```tsx
const { props, isPending, isStreaming, partialToolInput } = useWidget<Props>();

// Phase 1: No data yet — show skeleton
if (isPending && !partialToolInput) {
  return <LoadingSkeleton />;
}

// Phase 2: Streaming — show partial data
// Phase 3: Complete — show full data
const displayData = isStreaming && partialToolInput
  ? partialToolInput
  : props;

return <ResultsGrid data={displayData} isStreaming={isStreaming} />;
```

### Display modes

Request fullscreen or picture-in-picture from within a widget:

```tsx
const { displayMode, requestDisplayMode } = useWidget();

return (
  <div>
    <span>Current: {displayMode}</span>
    <button onClick={() => requestDisplayMode("fullscreen")}>⛶ Expand</button>
    <button onClick={() => requestDisplayMode("pip")}>⧉ Pop Out</button>
    <button onClick={() => requestDisplayMode("inline")}>↩ Inline</button>
  </div>
);
```

### Follow-up messages

Send messages on behalf of the user from within a widget:

```tsx
const { sendFollowUpMessage } = useWidget();

<button onClick={() => sendFollowUpMessage("Show me more details about product X")}>
  Ask for more details
</button>
```

### Persistent state

Widget state that persists across conversations:

```tsx
interface MyState { favorites: string[] }

const { state, setState } = useWidget<Props, unknown, unknown, MyState>();

const toggleFavorite = async (itemId: string) => {
  const current = state?.favorites ?? [];
  const updated = current.includes(itemId)
    ? current.filter(id => id !== itemId)
    : [...current, itemId];
  await setState({ favorites: updated });  // always await setState
};
```

## Rules

1. **Widget folder name MUST match** the `widget.name` in tool config — `resources/<widget-name>/widget.tsx`.
2. **Always handle `isPending`** — widgets render BEFORE the tool completes; guard all `props` access.
3. **Support both themes** — always read `theme` from `useWidget()` and apply to the root element.
4. **Use `widget()` helper** for visual tools, `text()`/`object()` for data-only tools.
5. **Set `baseUrl`** in production — required for correct CSP auto-configuration.
6. **Use `useCallTool`** for widget-to-tool communication — never raw `fetch()` to MCP endpoints.
7. **Use `Image` component** for public assets — handles URL resolution across hosts.
8. **Add `.describe()`** to all Zod schema fields — LLMs use descriptions to choose correct arguments.
9. **Declare CSP domains** in `widgetMetadata` for any external API calls from widgets.
10. **Always wrap in `McpUseProvider`** — required for host communication and auto-sizing.

## Common pitfalls

| Mistake | Fix |
|---------|-----|
| Widget folder name ≠ tool's `widget.name` | Ensure exact match: `widget: { name: "foo" }` → `resources/foo/widget.tsx` |
| Not handling `isPending` state | Always show loading UI before accessing `props` |
| Missing `baseUrl` in production | Set `MCP_URL` env var or pass `baseUrl` to constructor |
| Using `fetch()` to call MCP tools | Use `useCallTool` hook — it handles auth, serialization, errors |
| Hardcoded theme colors | Read `theme` from `useWidget()`, apply via `data-theme` or conditional classes |
| Missing CSP for external APIs | Add `connectDomains` / `resourceDomains` to `widgetMetadata.metadata.csp` |
| Not using `Image` for public assets | Use `<Image src="/path" />` — it resolves URLs correctly across hosts |
| Calling `setState` synchronously | Always `await setState()` — it returns a Promise |
| No `McpUseProvider` wrapper | Wrap widget root — required for host communication and auto-sizing |
| Accessing `props` without `isPending` guard | Destructure `props` only after `if (isPending) return <Loading />` check |
| Using `window.openai` directly | Use `useWidget()` hooks — they abstract host-specific APIs |
| Missing `widgetMetadata` export | Add typed `widgetMetadata` for prop validation and CSP |

## Do this, not that

```typescript
// ✅ DO: Import widget hooks from mcp-use/react
import { useWidget, useCallTool, McpUseProvider } from "mcp-use/react";

// ❌ DON'T: Import from internal paths
import { useWidget } from "mcp-use/src/react/useWidget";
```

```typescript
// ✅ DO: Import server helpers from mcp-use/server
import { MCPServer, widget, text, object } from "mcp-use/server";

// ❌ DON'T: Import from @modelcontextprotocol/sdk directly
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
```

```typescript
// ✅ DO: Return widget() for visual tools
return widget({ props: { data }, output: text("Summary for LLM") });

// ❌ DON'T: Return text() when a widget should render
return text(JSON.stringify(data));
```

```tsx
// ✅ DO: Handle loading state before accessing props
const { props, isPending } = useWidget<Props>();
if (isPending) return <Skeleton />;
return <div>{props.results.map(r => <Item key={r.id} item={r} />)}</div>;

// ❌ DON'T: Assume props are immediately available
const { props } = useWidget<Props>();
return <div>{props.results.map(...)}</div>;  // CRASHES when isPending
```

```tsx
// ✅ DO: Use useCallTool for widget-to-tool calls
const { callTool, data } = useCallTool("get-details");
<button onClick={() => callTool({ id: "123" })}>Load</button>

// ❌ DON'T: Use fetch() to call MCP tools
const res = await fetch("/mcp/tools/get-details", { body: JSON.stringify({ id: "123" }) });
```

```tsx
// ✅ DO: Use Image component for public assets
<Image src="/fruits/apple.png" alt="Apple" />

// ❌ DON'T: Use raw img tags with relative paths
<img src="/fruits/apple.png" alt="Apple" />  // breaks in hosted environments
```

```tsx
// ✅ DO: Support both themes
const { theme } = useWidget();
<div data-theme={theme} className={theme === "dark" ? "bg-gray-900" : "bg-white"}>

// ❌ DON'T: Hardcode colors
<div className="bg-white text-black">  // broken in dark mode
```

## Build workflow

New MCP App:

1. **Scaffold** — `npx create-mcp-use-app my-app --template mcp-apps` → `references/guides/quick-start.md`
2. **Configure** — MCPServer with `baseUrl`, name, version → Core API: MCPServer constructor (above)
3. **Define tools** — register tools with `widget` config and Zod schemas → `references/guides/tools-and-schemas.md`
4. **Create widgets** — `resources/<widget-name>/widget.tsx` with default export component → Core API: useWidget (above)
5. **Add `widgetMetadata`** — Zod props schema + CSP (if external APIs) → Core API: Widget metadata (above)
6. **Wire `useCallTool`** — for inter-tool communication from widgets → Core API: useCallTool (above)
7. **Handle loading** — `isPending` and `isStreaming` states with skeleton UI → Core API: Streaming (above)
8. **Support themes** — read `theme` from `useWidget()`, apply via `data-theme` → Rules #3 (above)
9. **Test** — `npx mcp-use dev` opens Inspector with widget preview → `references/guides/testing-and-debugging.md`
10. **Deploy** — `mcp-use deploy` or manual → `references/patterns/deployment.md`

Adding a widget to an existing app:

1. Create `resources/<widget-name>/widget.tsx` with default export component
2. Register tool in `index.ts` with `widget: { name: "<widget-name>" }` config
3. Return `widget({ props, output })` from tool handler
4. Handle `isPending` in the widget component
5. Test with Inspector — widget preview appears in tool results

## Companion packages

| Package | Purpose |
|---------|---------|
| `@mcp-use/cli` | Dev server with HMR + widget hot reload, `generate-types`, `deploy` |
| `@mcp-use/inspector` | Built-in web debugger with widget preview at `/inspector` |
| `create-mcp-use-app` | Project scaffolder — `npx create-mcp-use-app my-app --template mcp-apps` |

## Reference routing

| File | Read when |
|------|-----------|
| `references/guides/quick-start.md` | Starting a new MCP App project from scratch |
| `references/guides/widgets-and-ui.md` | Deep dive on widget development, React hooks, components, and host integration |
| `references/guides/tools-and-schemas.md` | Registering tools with widget bindings, Zod schemas, ctx object |
| `references/guides/response-helpers.md` | Using widget() and all 15 response helpers, typed responses |
| `references/guides/streaming-and-preview.md` | Implementing streaming tool arguments and live preview in widgets |
| `references/guides/authentication.md` | Setting up OAuth for protected MCP Apps |
| `references/guides/session-management.md` | Session stores, stream managers, idle timeouts |
| `references/guides/server-configuration.md` | MCPServer config, CORS, CSP, baseUrl, middleware |
| `references/guides/elicitation-and-sampling.md` | Requesting user input (ctx.elicit) or LLM completions (ctx.sample) |
| `references/guides/notifications-and-subscriptions.md` | Broadcasting notifications, progress, resource subscriptions |
| `references/guides/cli-reference.md` | Using @mcp-use/cli: dev, build, start, deploy, generate-types |
| `references/guides/transports.md` | Transport selection (httpStream for MCP Apps), serverless handlers |
| `references/guides/advanced-features.md` | Server proxy, user context, autocomplete, capability detection |
| `references/guides/testing-and-debugging.md` | Testing with Inspector, widget preview, curl, Claude Desktop |
| `references/guides/chatgpt-apps-flow.md` | Dual-protocol support for ChatGPT Apps SDK alongside MCP |
| `references/guides/resources-and-prompts.md` | MCP resources and prompts fundamentals (useful alongside widget tools) |
| `references/guides/widget-components.md` | McpUseProvider, Image, ErrorBoundary, ThemeProvider, WidgetControls API reference |
| `references/patterns/production-patterns.md` | Hardening: shutdown, caching, retries, connection pooling |
| `references/patterns/deployment.md` | Deploying via npm, Docker, cloud platforms, mcp-use deploy |
| `references/patterns/anti-patterns.md` | Common mistakes in widget design, tool binding, state management |
| `references/patterns/mcp-apps-patterns.md` | Patterns for multi-widget apps, widget composition, shared state |
| `references/examples/widget-recipes.md` | Complete widget examples: dashboards, forms, data tables, charts |
| `references/examples/server-recipes.md` | Complete server examples with widget-bound tools |
| `references/examples/project-templates.md` | Project template structures for MCP Apps |
| `references/troubleshooting/common-errors.md` | Specific error messages and fixes (25+ errors cataloged) |

## Guardrails

- NEVER skip `isPending` check in widgets — props are undefined while tool executes.
- NEVER hardcode widget URLs — use `mcp_url` from `useWidget()` for server references.
- NEVER use `fetch()` to call MCP tools from widgets — use `useCallTool` hook.
- NEVER forget CSP declarations for external API domains — widgets run in sandboxed iframes.
- NEVER reference `window.openai` or host-specific globals — use `useWidget()` hooks.
- NEVER store sensitive data in widget state — it is visible to the model and persisted.
- ALWAYS set `baseUrl` in production — required for CSP auto-configuration.
- ALWAYS support both light and dark themes — read `theme` from `useWidget()`.
- ALWAYS wrap widget root in `McpUseProvider` — required for host communication.
- ALWAYS use `Image` component for `public/` assets — raw `<img>` breaks in hosted environments.
- ALWAYS `await setState()` calls — state updates are asynchronous.
- ALWAYS test widgets with Inspector (`npx mcp-use dev`) before deploying.
