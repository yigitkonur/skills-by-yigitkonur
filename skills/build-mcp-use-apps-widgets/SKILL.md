---
name: build-mcp-use-apps-widgets
description: Use skill if you are building interactive MCP Apps with mcp-use widgets for ChatGPT, Claude, and MCP hosts — useWidget hooks, streaming preview, theming, CSP, and deployment.
---

# Build MCP Apps & Widgets

Build interactive, widget-based MCP Apps with the `mcp-use` TypeScript library (v1.21+, Node 22 LTS). MCP Apps render visual UI inside ChatGPT, Claude, Goose, and other MCP-compatible hosts. This skill covers the **app/widget side** — tool-to-widget binding, React hooks, streaming preview, display modes, theming, CSP, persistent state, follow-up messages, and deployment.

> **Not building UI?** Use `build-mcp-use-server` for plain MCP servers without widgets.
> **Building a client that connects to MCP servers?** Use `build-mcp-use-client`.

---

## Behavioral flow — what to do when this skill is invoked

```
Step 1 — Detect what exists in the user's CWD

  Run `tree -L 3` or `ls -R`. Look for signs of an existing mcp-use app/widget:
    - package.json with "mcp-use" dependency
    - resources/ directory with widget.tsx files
    - Files importing from "mcp-use/react" (useWidget, McpUseProvider, useCallTool)
    - widget() response helper usage in server code
    - widgetMetadata exports in widget files
    - MCPServer with widget-bound tools (widget: { name: "..." })

Step 2A — If a matching MCP App IS found:

  Launch 4 subagents to explore the codebase in parallel. Each reads relevant
  reference files and surfaces: what's good, what's wrong, what's missing.

  Subagent 1 — Server-side analysis
    Explore: tool definitions, widget bindings, response helpers, Zod schemas,
    MCPServer config, baseUrl, middleware.
    Read: references/guides/tools-and-schemas.md, references/guides/response-helpers.md,
          references/guides/server-configuration.md

  Subagent 2 — Widget components analysis
    Explore: useWidget usage, props handling, isPending guards, theming, McpUseProvider
    wrapping, Image component usage, widgetMetadata exports, ErrorBoundary.
    Read: references/guides/widgets-and-ui.md, references/guides/widget-components.md,
          references/guides/streaming-and-preview.md

  Subagent 3 — Inter-widget communication & state
    Explore: useCallTool usage, sendFollowUpMessage, persistent state (setState),
    display modes, elicitation, notifications.
    Read: references/guides/widgets-and-ui.md, references/guides/session-management.md,
          references/guides/elicitation-and-sampling.md,
          references/guides/notifications-and-subscriptions.md,
          references/patterns/mcp-apps-patterns.md

  Subagent 4 — Production & deployment readiness
    Explore: CSP config, baseUrl, authentication setup, deployment config,
    anti-patterns, testing setup.
    Read: references/guides/authentication.md, references/patterns/deployment.md,
          references/patterns/production-patterns.md, references/patterns/anti-patterns.md,
          references/guides/testing-and-debugging.md,
          references/troubleshooting/common-errors.md

  After all subagents report back:
    1. Synthesize findings — prioritize by severity (broken > missing > suboptimal)
    2. Apply improvements directly — do not just list suggestions
    3. Only ask if genuinely ambiguous (conflicting signals, unclear intent)

Step 2B — If NO matching MCP App is found:

  Check surrounding context first:
    - Is there a plain MCP server (mcp-use/server imports, no widgets)?
        → Suggest adding widget support to existing tools
    - Is there a React app without MCP?
        → Suggest MCP client integration
    - Is there any codebase context at all?
        → Adapt approach to what exists

  If no useful context — ask up to 10 questions with 5+ options each:

    1. What will the widgets display?
       (data dashboard, product search, forms/wizards, charts/graphs, content viewer,
        media gallery, settings panel, other)
    2. How many widgets needed initially? (1, 2-3, 4-6, 7+)
    3. Will widgets call other tools? (useCallTool for inter-widget communication)
       (no, yes — read-only data, yes — mutations, yes — chained workflows)
    4. Theme support needed? (light only, dark only, both, custom theme system)
    5. External API calls from widgets? (none, 1-2 domains, many — need CSP config)
    6. Authentication needed? (none, Auth0, WorkOS, Supabase, Keycloak, custom)
    7. Streaming preview? (no, yes — show partial results while tool executes)
    8. Deployment target? (mcp-use deploy, Docker, Cloudflare, Vercel, AWS, other cloud)
    9. ChatGPT Apps SDK compatibility needed? (yes, no, unsure)
   10. Persistent widget state needed? (no, yes — favorites/preferences, yes — complex state)

  Then scaffold and build based on answers.
```

---

## Curiosity-driven reference routing

Read the reference files below when you encounter the matching situation. Every reference file in this skill is listed here — use them.

**Getting started & scaffolding:**
- Starting from scratch? `references/guides/quick-start.md` has the `create-mcp-use-app` scaffolder, templates, and first-run walkthrough. Also see `references/examples/project-templates.md` for full project structures.

**Server-side (tool registration, config, responses):**
- Registering tools with widget bindings and Zod schemas? `references/guides/tools-and-schemas.md` covers `server.tool()`, the `widget` config object, `ctx` object, annotations, and schema best practices.
- Configuring MCPServer (CORS, CSP auto-injection, baseUrl, middleware, env vars)? `references/guides/server-configuration.md` has the full `ServerConfig` interface and middleware patterns.
- Using `widget()`, `text()`, `object()`, `mix()`, or any of the 15 response helpers? `references/guides/response-helpers.md` covers typed responses, `_meta`, MIME handling, and composition.
- Setting up resources (static data, URI templates) or prompts (templates with autocomplete)? `references/guides/resources-and-prompts.md` explains when to use resources vs tools vs prompts alongside widgets.
- Need session stores (InMemory, FileSystem, Redis) or stream managers? `references/guides/session-management.md` covers session lifecycle, idle timeouts, and distributed streaming.
- Setting up OAuth (Auth0, WorkOS, Supabase, Keycloak)? `references/guides/authentication.md` has zero-config env var setup and `ctx.auth` usage in tool handlers.
- Need `ctx.elicit()` to request user input or `ctx.sample()` for LLM completions mid-tool? `references/guides/elicitation-and-sampling.md` covers both interactive patterns.
- Broadcasting progress, notifications, or resource subscriptions to clients? `references/guides/notifications-and-subscriptions.md` has `sendToolsListChanged()`, progress reporting, and subscription patterns.
- Choosing transports (stdio, httpStream, SSE) or deploying serverless (Supabase Edge, Cloudflare, Deno)? `references/guides/transports.md` has the transport decision matrix and serverless handler patterns.
- Using the CLI (`mcp-use dev`, `build`, `deploy`, `generate-types`)? `references/guides/cli-reference.md` documents all commands and flags.
- Advanced features (server proxy, user context, autocomplete, capability detection)? `references/guides/advanced-features.md` covers `ctx.client.can()`, `completable()`, and proxy setups.

**Widget development (React hooks, components, UI):**
- Building a widget component? The `useWidget` hook returns 25+ properties including `props`, `isPending`, `isStreaming`, `partialToolInput`, `theme`, `displayMode`, `safeArea`, `locale`, `state`, `setState`, `callTool`, `sendFollowUpMessage`, and more. Read `references/guides/widgets-and-ui.md` for the complete interface and lifecycle.
- Need the `McpUseProvider`, `Image`, `ErrorBoundary`, `ThemeProvider`, or `WidgetControls` component API? `references/guides/widget-components.md` has every prop, default value, and composition pattern.
- Need streaming preview in your widget? The difference between `toolInput`, `partialToolInput`, and `props` trips up everyone. Read `references/guides/streaming-and-preview.md` to understand the 3-phase lifecycle (pending → streaming → complete).
- Publishing to ChatGPT? There's a dual-protocol setup (MCP Apps + ChatGPT Apps SDK) with metadata mapping, `scriptDirectives` for React bundles, and auto-registration from `resources/`. Read `references/guides/chatgpt-apps-flow.md` for the complete flow.
- Widget calling external APIs? CSP is enforced in sandboxed iframes. Read `references/guides/widget-components.md` for the `WidgetMetadata.metadata.csp` fields — miss one `connectDomain` and your fetch calls silently fail.

**Patterns, deployment, and troubleshooting:**
- Building multi-widget apps with shared state, widget composition, or orchestrated workflows? `references/patterns/mcp-apps-patterns.md` has patterns for widget-to-widget communication and layout.
- Hardening for production (graceful shutdown, caching, retries, connection pooling)? `references/patterns/production-patterns.md` covers operational readiness.
- Deploying via `mcp-use deploy`, Docker, cloud platforms, or static hosting? `references/patterns/deployment.md` has deployment recipes for every target.
- Reviewing code for common mistakes in widget design, tool binding, or state management? `references/patterns/anti-patterns.md` catalogs what NOT to do.
- Testing with Inspector, widget preview, curl, or Claude Desktop? `references/guides/testing-and-debugging.md` covers the full testing workflow.
- Hit a specific error message? `references/troubleshooting/common-errors.md` catalogs 25+ errors with exact fixes.

**Complete examples:**
- Need a working widget example (dashboard, form, data table, chart)? `references/examples/widget-recipes.md` has copy-paste recipes.
- Need a server example with widget-bound tools? `references/examples/server-recipes.md` has complete server files.

---

## Quick start

Minimal MCP App — one server with one widget-bound tool:

**`index.ts`** — server entry:

```typescript
import { MCPServer, widget, text, object } from "mcp-use/server";
import { z } from "zod";

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
      name: "product-search",        // MUST match resources/product-search/widget.tsx
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
    schema: z.object({ productId: z.string().describe("Product ID") }),
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

**Run:** `npx mcp-use dev`
**Test:** Opens Inspector at `http://localhost:3000` with widget preview.

---

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

---

## Core API — Widget development

### useWidget hook

The primary widget hook — provides all widget context. Import from `mcp-use/react`.

```typescript
import { useWidget } from "mcp-use/react";

const {
  // Data
  props,                 // Partial<TProps> — server-computed widget data; {} while isPending
  toolInput,             // any — full tool call args (available after tool completes)
  output,                // TOutput | null — tool output visible to LLM
  metadata,              // TMetadata | null — extra metadata from tool (_meta)

  // Lifecycle
  isPending,             // boolean — true while tool is executing
  isStreaming,           // boolean — true during streaming
  partialToolInput,      // Partial<TProps> | null — incremental args during streaming
  isAvailable,           // boolean — true when widget API is present

  // State
  state,                 // TState | null — persisted widget state
  setState,              // (state | updater) => Promise<void> — always await this

  // Display
  theme,                 // "light" | "dark" (default: "light")
  displayMode,           // "inline" | "pip" | "fullscreen" (default: "inline")
  requestDisplayMode,    // (mode) => Promise<{ mode: DisplayMode }>
  safeArea,              // { insets: { top, right, bottom, left } } — mobile insets
  maxHeight,             // number — max widget height in pixels (default: 600)
  maxWidth,              // number | undefined — max widget width (MCP Apps only)

  // Locale & environment
  locale,                // string — BCP 47 locale (default: "en")
  timeZone,              // string — IANA timezone
  mcp_url,               // string — server base URL
  userAgent,             // { device: { type }, capabilities }
  hostInfo,              // { name, version } | undefined — MCP Apps only
  hostCapabilities,      // Record<string, unknown> | undefined

  // Actions
  callTool,              // (name, args) => Promise<CallToolResponse>
  sendFollowUpMessage,   // (string | MessageContentBlock[]) => Promise<void>
  openExternal,          // (href: string) => void — open URL in new tab
  notifyIntrinsicHeight, // (height: number) => Promise<void>
} = useWidget<TProps, TOutput, TMetadata, TState>();
```

**Defaults:** `theme: "light"`, `displayMode: "inline"`, `maxHeight: 600`, `locale: "en"`, `props: {}`, `output/metadata/state: null`, `safeArea: all 0`.

### useCallTool hook

Call MCP tools from within a widget. Import from `mcp-use/react`.

```typescript
import { useCallTool } from "mcp-use/react";

const {
  callTool,        // (args, callbacks?) => void — fire-and-forget
  callToolAsync,   // (args) => Promise<CallToolResult> — async/await
  data,            // CallToolResult | undefined — last successful result
  isPending,       // boolean
  isSuccess,       // boolean
  isError,         // boolean
  error,           // Error | undefined (NOT null)
  status,          // "idle" | "pending" | "success" | "error"
  isIdle,          // boolean
} = useCallTool("tool-name");

// Fire-and-forget with callbacks:
callTool({ arg1: "value" }, {
  onSuccess: (data, input) => console.log(data.structuredContent),
  onError: (err, input) => console.error(err),
  onSettled: (data, err, input) => { /* runs after success or error */ },
});

// Async/await:
const result = await callToolAsync({ arg1: "value" });
console.log(result.structuredContent);
```

### Helper hooks

Focused hooks when you only need one piece of widget context:

```typescript
import { useWidgetProps, useWidgetTheme, useWidgetState } from "mcp-use/react";

const props = useWidgetProps<Props>();                          // just props
const theme = useWidgetTheme();                                 // just "light" | "dark"
const [state, setState] = useWidgetState<State>(initialState);  // just state
```

### McpUseProvider

Required wrapper at the root of every widget:

```tsx
import { McpUseProvider } from "mcp-use/react";

<McpUseProvider autoSize debugger viewControls="fullscreen">
  <MyWidget />
</McpUseProvider>
```

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | `ReactNode` | *required* | Widget content |
| `autoSize` | `boolean` | `false` | Auto-notify host of height changes via ResizeObserver |
| `debugger` | `boolean` | `false` | Show debug overlay with props/state inspector |
| `viewControls` | `boolean \| "pip" \| "fullscreen"` | `false` | Display mode controls; `true` = both pip and fullscreen |

Internally composes: `StrictMode` → `ThemeProvider` → `WidgetControls` → `ErrorBoundary` → auto-size wrapper.

> **Breaking change (v1.20.1):** `McpUseProvider` no longer includes `BrowserRouter`. Add `<BrowserRouter>` explicitly if using `react-router`.

### Widget metadata & CSP

Type-safe props schema and CSP configuration via `widgetMetadata` named export:

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
  metadata: {
    csp: {
      connectDomains: ["https://api.weather.com"],    // fetch/XHR/WebSocket targets
      resourceDomains: ["https://cdn.weather.com"],   // images, fonts, scripts, styles
      baseUriDomains: ["https://myserver.com"],        // base URI (MCP Apps only)
      frameDomains: ["https://trusted-embed.com"],    // iframe sources
      redirectDomains: ["https://oauth.provider.com"], // redirects (ChatGPT-specific)
    },
    prefersBorder: true,
    invoking: "Fetching weather...",
    invoked: "Weather loaded",
  },
};
```

When `baseUrl` is set (or `MCP_URL` env var), your server domain is auto-injected into CSP. `CSP_URLS` env var adds extra domains globally. `MCP_SERVER_URL` sets a separate server URL for static widget deployments.

### Utility components

All from `mcp-use/react`: `ErrorBoundary` (catches render errors), `Image` (resolves public/ asset URLs across hosts — always use instead of `<img>`), `ThemeProvider` (provides theme context). See `references/guides/widget-components.md` for full API.

---

## Core API — Server-side

### Tool-to-widget binding

The core MCP App pattern — bind a tool to a widget folder. Server imports from `mcp-use/server`, widget/React imports from `mcp-use/react`.

```typescript
import { MCPServer, widget, text } from "mcp-use/server";

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
      props: { /* structured data → useWidget().props, hidden from LLM */ },
      output: text("..."),  // visible to LLM as tool result
    });
  }
);
```

For the full MCPServer constructor options, session stores, stream managers, CORS config, and server methods — read `references/guides/server-configuration.md`.

### Response helpers

All imported from `mcp-use/server`. Key helpers for widget apps:

- `widget({ props, output })` — primary for MCP Apps, returns visual widget UI
- `text(str)` — plain text visible to LLM (also used as `output` inside `widget()`)
- `object(obj)` — structured JSON for data-only tools or `useCallTool` results
- `error(str)` — expected failures (`isError: true`)
- `mix(...items)` — combine multiple content types

Full list of all 15 helpers: `references/guides/response-helpers.md`.

### toolInput vs partialToolInput vs props

Three values for the same data at different lifecycle stages. `toolInput`: full tool call args the LLM sent (available after `isPending === false`). `partialToolInput`: incremental args while `isStreaming` (use for live preview). `props`: server-computed data from `structuredContent` (available after `isPending === false` — use for full rendering). Deep dive: `references/guides/streaming-and-preview.md`.

### Streaming tool arguments (live preview)

```tsx
const { props, isPending, isStreaming, partialToolInput } = useWidget<Props>();

// Phase 1: No data yet — show skeleton
if (isPending && !partialToolInput) {
  return <LoadingSkeleton />;
}

// Phase 2: Streaming — show partial data / Phase 3: Complete — show full data
const displayData = isStreaming && partialToolInput ? partialToolInput : props;

return <ResultsGrid data={displayData} isStreaming={isStreaming} />;
```

### Display modes, follow-up messages, persistent state

```tsx
// Display modes — request fullscreen or PiP from within a widget
const { displayMode, requestDisplayMode } = useWidget();
await requestDisplayMode("fullscreen"); // or "pip" or "inline"

// Follow-up messages — send messages on behalf of the user
const { sendFollowUpMessage } = useWidget();
sendFollowUpMessage("Show me more details");
sendFollowUpMessage([{ type: "text", text: "Analyze this" }]); // MessageContentBlock[]

// Persistent state — survives across conversations. Always await setState.
const { state, setState } = useWidget<Props, unknown, unknown, MyState>();
await setState(prev => ({ ...prev, count: (prev?.count ?? 0) + 1 }));
```

### server.uiResource()

Expose a widget as a standalone MCP resource (not tied to a tool call):

```typescript
server.uiResource({
  type: "mcpApps",               // use "mcpApps" — supports both MCP Apps and ChatGPT Apps SDK
  name: "dashboard-widget",
  htmlTemplate: "<div id='root'></div><script>...</script>",
  metadata: {
    csp: { connectDomains: ["https://api.example.com"] },
    prefersBorder: true,
  },
});
```

> `type: "appsSdk"` is deprecated. Always use `type: "mcpApps"`.

### getMcpAppsBridge

Low-level bridge for direct protocol access (prefer `useWidget`/`useCallTool` hooks). Provides `callTool()`, `readResource()`, `sendMessage()`, `openLink()`, `requestDisplayMode()`. Import from `mcp-use/react`. See `references/guides/widgets-and-ui.md` for the full API.

---

## Build workflow

**New MCP App:**

1. **Scaffold** — `npx create-mcp-use-app my-app --template mcp-apps` → `references/guides/quick-start.md`
2. **Configure** — MCPServer with `baseUrl`, name, version → `references/guides/server-configuration.md`
3. **Define tools** — register tools with `widget` config and Zod schemas → `references/guides/tools-and-schemas.md`
4. **Create widgets** — `resources/<widget-name>/widget.tsx` with default export
5. **Add `widgetMetadata`** — Zod props schema + CSP (if external APIs)
6. **Wire `useCallTool`** — for inter-tool communication from widgets
7. **Handle loading** — `isPending` and `isStreaming` states with skeleton UI → `references/guides/streaming-and-preview.md`
8. **Support themes** — read `theme` from `useWidget()`, apply via `data-theme`
9. **Test** — `npx mcp-use dev` opens Inspector with widget preview → `references/guides/testing-and-debugging.md`
10. **Deploy** — `mcp-use deploy` or manual → `references/patterns/deployment.md`

**Adding a widget to an existing MCP App:** Create `resources/<name>/widget.tsx` with default export, register tool with `widget: { name: "<name>" }`, return `widget({ props, output })`, handle `isPending`, test with Inspector.

---

## Rules

1. **Widget folder name MUST match** the `widget.name` in tool config — `resources/<widget-name>/widget.tsx`.
2. **Always handle `isPending`** — widgets render BEFORE the tool completes; guard all `props` access.
3. **Support both themes** — read `theme` from `useWidget()` and apply to the root element.
4. **Use `widget()` helper** for visual tools, `text()`/`object()` for data-only tools.
5. **Set `baseUrl`** in production — required for correct CSP auto-configuration.
6. **Use `useCallTool`** for widget-to-tool communication — never raw `fetch()` to MCP endpoints.
7. **Use `Image` component** for public assets — handles URL resolution across hosts.
8. **Add `.describe()`** to all Zod schema fields — LLMs use descriptions to choose correct arguments.
9. **Declare CSP domains** in `widgetMetadata` for any external API calls from widgets.
10. **Always wrap in `McpUseProvider`** — required for host communication and auto-sizing.
11. **Server imports from `mcp-use/server`** — `MCPServer`, `widget`, `text`, `object`, etc.
12. **Widget/React imports from `mcp-use/react`** — `useWidget`, `useCallTool`, `McpUseProvider`, `Image`, etc.

---

## Common pitfalls

| Mistake | Fix |
|---------|-----|
| Widget folder name does not match tool's `widget.name` | Exact match required: `widget: { name: "foo" }` → `resources/foo/widget.tsx` |
| Not handling `isPending` state | Always show loading UI before accessing `props` — they are `{}` while pending |
| Missing `baseUrl` in production | Set `MCP_URL` env var or pass `baseUrl` to MCPServer constructor |
| Using `fetch()` to call MCP tools from widgets | Use `useCallTool` hook — it handles auth, serialization, errors |
| Hardcoded theme colors | Read `theme` from `useWidget()`, apply via `data-theme` or conditional classes |
| Missing CSP for external APIs | Add `connectDomains`/`resourceDomains` to `widgetMetadata.metadata.csp` |
| Not using `Image` for public assets | Use `<Image src="/path" />` — raw `<img>` breaks in hosted environments |
| Calling `setState` without await | Always `await setState()` — it returns a Promise; fire-and-forget loses errors |
| No `McpUseProvider` wrapper | Wrap widget root — required for host communication and auto-sizing |
| Accessing `props` without `isPending` guard | Destructure `props` only after `if (isPending) return <Loading />` check |
| Using `window.openai` directly | Use `useWidget()` hooks — they abstract host-specific APIs |
| Missing `widgetMetadata` export | Add typed `widgetMetadata` for prop validation and CSP |
| Using `type: "appsSdk"` in `uiResource` | Use `type: "mcpApps"` — `appsSdk` is deprecated |
| Forgetting `BrowserRouter` after v1.20.1 | `McpUseProvider` no longer includes it — add explicitly if using react-router |
| `error` from `useCallTool` treated as nullable | `error` is `Error \| undefined`, not `Error \| null` |
| Importing server helpers in widget code | Server: `mcp-use/server`. Widget/React: `mcp-use/react`. Never mix. |

---

## Guardrails

- NEVER skip `isPending` check — props are `{}` while tool executes; accessing properties crashes.
- NEVER use `fetch()` to call MCP tools from widgets — use `useCallTool` hook.
- NEVER forget CSP for external APIs — widgets run in sandboxed iframes; missing `connectDomains` = silent failure.
- NEVER reference `window.openai` or host-specific globals — use `useWidget()` hooks.
- NEVER store sensitive data in widget state — visible to model and persisted.
- NEVER mix imports — server: `mcp-use/server`, widget/React: `mcp-use/react`.
- ALWAYS set `baseUrl` in production — required for CSP auto-configuration.
- ALWAYS support both themes — read `theme` from `useWidget()`, apply via `data-theme`.
- ALWAYS wrap widget root in `McpUseProvider` — required for host communication.
- ALWAYS use `<Image>` for `public/` assets — raw `<img>` breaks in hosted environments.
- ALWAYS `await setState()` — state updates are async; fire-and-forget loses errors.
- ALWAYS use `type: "mcpApps"` for `uiResource()` — `appsSdk` is deprecated.

---

## Companion packages

`@mcp-use/cli` (dev server with HMR + widget hot reload, `generate-types`, `deploy`), `@mcp-use/inspector` (built-in web debugger with widget preview), `create-mcp-use-app` (project scaffolder).
