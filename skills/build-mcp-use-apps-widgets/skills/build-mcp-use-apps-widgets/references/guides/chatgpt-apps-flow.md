# ChatGPT Apps Compatibility

How MCP Apps widgets work as ChatGPT Apps, protocol bridging, and deployment for ChatGPT compatibility.

> **Deprecation notice**: The `type: "appsSdk"` (ChatGPT Apps SDK) pattern is **deprecated**. For new projects, use `type: "mcpApps"` which provides dual-protocol support — widgets work in both MCP Apps clients (Claude, Goose, etc.) and ChatGPT automatically. The `ui-widgets` doc page itself is marked Deprecated in the official navigation. Existing `appsSdk` widgets continue to function but migration to `mcpApps` is recommended.

---

## Overview

MCP Apps widgets are designed to work in both MCP Apps clients and ChatGPT simultaneously. The same widget code runs in both environments — the `useWidget` hook detects the runtime and adapts automatically.

```
┌──────────────────────────────────────┐
│  Widget Code (React + useWidget)     │
├──────────────────────────────────────┤
│  Runtime Detection Layer             │
├─────────────────┬────────────────────┤
│  MCP Apps Mode  │  ChatGPT Mode      │
│  (postMessage)  │  (window.openai)   │
└─────────────────┴────────────────────┘
```

When loaded inside ChatGPT, the widget detects `window.openai` and uses the OpenAI Apps SDK bridge. When loaded in an MCP Apps client, it uses JSON-RPC over `postMessage`.

### Protocol Options

| Registration Type | Protocol | ChatGPT | MCP Apps Clients | Status |
|-------------------|----------|---------|-----------------|--------|
| `type: "mcpApps"` | Both MCP Apps + ChatGPT | Yes | Yes | **Recommended** |
| `type: "appsSdk"` | ChatGPT Apps SDK only | Yes | No | **Deprecated** |

Use `type: "mcpApps"` for all new projects. Your widget code is identical regardless of the registration type — only the server registration differs.

### Auto-Registration from `resources/` Directory

The recommended way to create widgets is placing React components in the `resources/` directory. Widgets are **auto-discovered and registered at startup** — no `server.uiResource()` call needed.

```
my-mcp-server/
├── resources/
│   └── weather-display/
│       └── widget.tsx        ← auto-registered as "weather-display"
├── public/
└── index.ts
```

Each `widget.tsx` exports:
- A default React component (the widget UI)
- A named `widgetMetadata` export of type `WidgetMetadata` (description, props schema, metadata)

```typescript
// resources/weather-display/widget.tsx
import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

const propSchema = z.object({
  city: z.string(),
  temperature: z.number(),
  conditions: z.string(),
});

export const widgetMetadata: WidgetMetadata = {
  description: "Displays current weather conditions",
  props: propSchema,
  exposeAsTool: false,  // set true to auto-register widget as a tool
  metadata: {
    prefersBorder: true,
    autoResize: true,
    csp: {
      scriptDirectives: ["'unsafe-eval'"], // required for React bundles
    },
    widgetDescription: "Interactive weather card", // ChatGPT-specific
  },
};

type WeatherProps = z.infer<typeof propSchema>;

const WeatherDisplay: React.FC = () => {
  const { props, isPending, theme } = useWidget<WeatherProps>();
  const isDark = theme === "dark";
  // ... render
};

export default WeatherDisplay;
```

Widgets defined in `resources/` are used from tool handlers via the `widget` config on `server.tool()`. The `name` must match the directory name:

```typescript
server.tool(
  {
    name: "get-weather",
    schema: z.object({ city: z.string() }),
    widget: {
      name: "weather-display",  // matches resources/weather-display/
      invoking: "Fetching weather...",
      invoked: "Weather loaded",
    },
  },
  async ({ city }) => {
    const weather = await fetchWeather(city);
    return widget({
      props: { city, ...weather },
      message: `Current weather in ${city}: ${weather.conditions}, ${weather.temperature}°C`,
    });
  }
);
```

---

## The `window.openai` API Bridge

In ChatGPT, widgets communicate through the global `window.openai` object instead of postMessage. The `useWidget` hook handles this automatically, but understanding the underlying API helps with debugging.

### ChatGPT Runtime Detection

```typescript
// How useWidget() internally detects the runtime
const isChatGPT = typeof window !== "undefined" && "openai" in window;
const isMcpApps = typeof window !== "undefined" && window.parent !== window;
```

### What `window.openai` Provides

| API | MCP Apps Equivalent | Description |
|-----|---------------------|-------------|
| `window.openai.theme` | `useWidget().theme` | Current theme (`"light"` or `"dark"`) |
| `window.openai.callTool()` | `useWidget().callTool()` | Call a server tool |
| `window.openai.sendFollowUp()` | `useWidget().sendFollowUpMessage()` | Send follow-up message to chat |
| `window.openai.openExternal()` | `useWidget().openExternal()` | Open URL in browser |
| `window.openai.requestDisplayMode()` | `useWidget().requestDisplayMode()` | Request fullscreen/PiP |

### Why You Should NOT Access `window.openai` Directly

```typescript
// ❌ BAD — breaks in MCP Apps clients where window.openai doesn't exist
const theme = window.openai.theme;
window.openai.callTool("search", { query: "test" });

// ✅ GOOD — works in both ChatGPT and MCP Apps
const { theme, callTool } = useWidget();
await callTool("search", { query: "test" });
```

---

## MIME Type Mapping

Servers return widgets with different MIME types depending on the protocol:

| Protocol | MIME Type | Used By |
|----------|-----------|---------|
| MCP Apps | `text/html;profile=mcp-app` | Claude, MCP clients |
| ChatGPT | `text/html+skybridge` | ChatGPT |

### How mcp-use Handles This

When you register with `type: "mcpApps"`, mcp-use uses two protocol adapters internally:

```typescript
import { McpAppsAdapter, AppsSdkAdapter } from "mcp-use/server";

// These are created automatically when you use type: "mcpApps"
const mcpAppsAdapter = new McpAppsAdapter();
const appsSdkAdapter = new AppsSdkAdapter();

// Transform your unified metadata to each protocol
const mcpAppsMetadata = mcpAppsAdapter.transformMetadata(yourMetadata);
const appsSdkMetadata = appsSdkAdapter.transformMetadata(yourMetadata);
```

You don't need to interact with adapters directly — they are applied automatically. The `AppsSdkAdapter` detects ChatGPT clients and:
1. Converts MIME type to `"text/html+skybridge"`
2. Transforms metadata keys to `"openai/*"` prefixed format
3. Converts CSP from camelCase to snake_case

---

## CSP Mapping: camelCase ↔ snake_case

Widget metadata uses camelCase for CSP domains, but ChatGPT expects snake_case. The adapter converts automatically.

| MCP Apps (your code) | ChatGPT (auto-converted) | Description |
|---------------------|--------------------------|-------------|
| `connectDomains` | `connect_domains` | Domains for fetch, XHR, WebSocket |
| `resourceDomains` | `resource_domains` | Domains for scripts, styles, images |
| `baseUriDomains` | `base_uri_domains` | Domains for base URI (MCP Apps only) |
| `frameDomains` | `frame_domains` | Domains for iframe embeds |
| `redirectDomains` | `redirect_domains` | Domains for redirects (ChatGPT-specific) |
| `scriptDirectives` | `script_directives` | Custom script CSP directives |
| `styleDirectives` | `style_directives` | Custom style CSP directives |

### Example

```typescript
// Your widget metadata — always use camelCase
export const widgetMetadata: WidgetMetadata = {
  description: "Widget with external API access",
  props: z.object({ data: z.any() }),
  metadata: {
    csp: {
      connectDomains: ["https://api.example.com"],   // ← camelCase
      resourceDomains: ["https://cdn.example.com"],  // ← camelCase
    },
    prefersBorder: true,
  },
};

// ChatGPT sees:
// {
//   "connect_domains": ["https://api.example.com"],   ← snake_case
//   "resource_domains": ["https://cdn.example.com"],  ← snake_case
// }
```

---

## Apps SDK Metadata vs MCP Apps Metadata

### `McpAppsMetadata` Fields

```typescript
interface McpAppsMetadata {
  csp?: {
    connectDomains?: string[];    // fetch, XHR, WebSocket
    resourceDomains?: string[];   // scripts, styles, images
    frameDomains?: string[];      // iframe embeds
    redirectDomains?: string[];   // redirects (ChatGPT-specific)
    scriptDirectives?: string[];  // custom script CSP directives
    styleDirectives?: string[];   // custom style CSP directives
  };
  prefersBorder?: boolean;           // host draws a border/frame around the widget
  autoResize?: boolean;              // MCP Apps clients auto-resize widget height
  supportsLocalStorage?: boolean;    // MCP Apps only
  widgetDescription?: string;        // shown to LLM; ChatGPT uses this for widget context
  widgetDomain?: string;             // custom domain (ChatGPT-specific)
  widgetAccessible?: boolean;        // accessibility flag (ChatGPT-specific)
  locale?: string;                   // BCP-47 locale (ChatGPT-specific)
  invoking?: string;                 // status text while tool is running
  invoked?: string;                  // status text after tool completes
}
```

> **`scriptDirectives`:** React widgets typically need `"'unsafe-eval'"` in `scriptDirectives` because bundlers include eval in their runtime. Add it when your widget uses a React bundle.

### Tool Registration Metadata

When using `type: "mcpApps"`, the unified `metadata` field is auto-converted for each protocol. When using the deprecated `type: "appsSdk"`, you must use `appsSdkMetadata` with `openai/*` keys directly.

```typescript
// Recommended: type: "mcpApps" — unified metadata, works for both
server.uiResource({
  type: "mcpApps",
  name: "chart",
  htmlTemplate: `...`,
  metadata: {
    csp: {
      connectDomains: ["https://api.example.com"],
      scriptDirectives: ["'unsafe-eval'"], // needed for React bundles
    },
    prefersBorder: true,
    autoResize: true,
    invoking: "Generating chart...",
    invoked: "Chart generated",
    widgetDescription: "Displays chart data", // ChatGPT-specific
  },
  exposeAsTool: false, // set true to auto-register widget as a callable tool
});

// MCP Apps clients see:
// { mimeType: "text/html;profile=mcp-app", _meta: { ui: { csp: { connectDomains: [...] }, prefersBorder: true } } }

// ChatGPT sees (auto-converted):
// {
//   mimeType: "text/html+skybridge",
//   _meta: {
//     "openai/outputTemplate": "ui://widget/chart.html",
//     "openai/toolInvocation/invoking": "Generating chart...",
//     "openai/toolInvocation/invoked": "Chart generated",
//     "openai/widgetPrefersBorder": true,
//     "openai/widgetCSP": { connect_domains: ["https://api.example.com"] }
//   }
// }
```

When invoking a widget from a tool, the `widget` config on the tool sets registration-time metadata:

```typescript
server.tool({
  name: "show-chart",
  description: "Display a chart",
  schema: z.object({ data: z.array(z.any()) }),
  widget: {
    name: "chart",        // Must match a widget in resources/
    invoking: "Generating chart...",
    invoked: "Chart generated",
  },
}, async ({ data }) => {
  return widget({
    props: { data },
    output: text(`Chart displayed with ${data.length} data points`),
  });
});
```

### Deprecated: Manual openai/* Metadata (appsSdk only)

For `type: "appsSdk"` (deprecated), you set `openai/*` metadata directly via `appsSdkMetadata`:

```typescript
// DEPRECATED — use type: "mcpApps" instead
server.uiResource({
  type: "appsSdk",
  name: "chart",
  htmlTemplate: `...`,
  appsSdkMetadata: {
    "openai/widgetCSP": {
      connect_domains: ["https://api.example.com"],
      resource_domains: ["https://cdn.example.com"],
    },
    "openai/widgetPrefersBorder": true,
    "openai/widgetDescription": "Displays chart data",
    "openai/widgetAccessible": true,
  },
});
```

> For `type: "mcpApps"`, you can additionally pass `appsSdkMetadata` for ChatGPT-specific overrides that don't have an equivalent in the unified `metadata` format. Prefer `metadata` for all shared configuration.

---

## Data Flow: props vs toolInput vs metadata

The tool result has three fields with different visibility. Understanding them prevents a common mistake of using the wrong field in a widget.

| Field | LLM sees it? | Widget sees it? | Purpose |
|-------|-------------|-----------------|---------|
| `content` | Yes | Yes | Text summary for the model's context |
| `structuredContent` | No | Yes (as `props`) | Rendering data for the widget |
| `_meta` | No | Yes (as `metadata`) | Protocol and custom metadata |

```typescript
// Server side — split between what the LLM sees and what the widget sees
return widget({
  props: { query: "mango", results: [...] }, // → useWidget().props (LLM does NOT see this)
  metadata: { totalCount: 1000, nextCursor: "abc123" }, // → useWidget().metadata
  output: text(`Found 16 products matching "mango"`), // → content (LLM sees this)
});

// Widget side
const { props, toolInput, metadata, isPending } = useWidget<SearchProps>();
// props     = { query: "mango", results: [...] }     ← structuredContent (computed by server)
// toolInput = { query: "mango" }                      ← original tool call args from the model
// metadata  = { totalCount: 1000, nextCursor: "..." } ← from _meta
```

`toolInput` and `props` are intentionally separate:
- **`toolInput`** — what the model decided to pass (e.g. `{ query: "mango" }`)
- **`props`** — what the server computed and returned (e.g. `{ query: "mango", results: [...16 items] }`)

---

## Widget Description and `prefersBorder`

The `description` field in `widgetMetadata` serves as context for the LLM to understand when to invoke the tool. In ChatGPT, this maps to the Apps SDK widget description.

```typescript
export const widgetMetadata: WidgetMetadata = {
  // This description is shown to the LLM in both environments
  description: "Interactive product search results with filtering and sorting. Shows product cards with images, prices, and ratings.",

  props: z.object({ products: z.array(z.any()) }),

  metadata: {
    // prefersBorder: tells the host whether to draw a border/frame
    prefersBorder: true,   // true → host draws a border (good for cards/panels)
    // prefersBorder: false → no border (good for fullscreen/immersive widgets)
  },
};
```

---

## Display Modes in ChatGPT

ChatGPT supports the same display modes as MCP Apps, but with slightly different behavior:

| Mode | ChatGPT Behavior | MCP Apps Behavior |
|------|-------------------|-------------------|
| `inline` | Embedded in chat message | Embedded in chat flow |
| `pip` | Picture-in-picture overlay | Picture-in-picture window |
| `fullscreen` | Takes full ChatGPT panel | Takes full client viewport |

### Requesting Display Modes

```tsx
const { displayMode, requestDisplayMode } = useWidget();

// Works identically in both environments
await requestDisplayMode("fullscreen");
await requestDisplayMode("inline");
await requestDisplayMode("pip");
```

---

## Testing in ChatGPT

### Local Development

1. Start your MCP server:
   ```bash
   npm run dev
   ```

2. Use `ngrok` or similar tunnel to expose your local server:
   ```bash
   ngrok http 3000
   ```

3. In the ChatGPT plugin/action setup, point to your ngrok URL:
   ```
   https://abc123.ngrok.io/mcp
   ```

### Testing Checklist

| Test | What to Verify |
|------|----------------|
| Widget renders | Content appears in chat after tool call |
| Theme matches | Widget respects ChatGPT's dark/light mode |
| Tool calls work | `useCallTool` and `callTool` execute successfully |
| Display modes | Fullscreen/PiP transitions work |
| CSP compliance | External API calls and images load without errors |
| Follow-up messages | `sendFollowUpMessage` appears in chat |
| External links | `openExternal` opens in browser |

### Common ChatGPT Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Widget shows blank | CSP blocking resources | Add domains to `connectDomains`/`resourceDomains` |
| Theme doesn't match | Missing `ThemeProvider` | Use `McpUseProvider` which includes it |
| Tool calls fail | Incorrect tool name | Ensure tool name matches server registration exactly |
| "Not accessible" error | Missing widget metadata | Export `widgetMetadata` with description |

---

## Deployment for ChatGPT Compatibility

### Server Requirements

1. **HTTPS required** — ChatGPT only loads widgets from HTTPS endpoints
2. **CORS headers** — Must allow ChatGPT origin
3. **Public accessibility** — Server must be reachable from the internet

### Production Deployment

```typescript
import { MCPServer } from "mcp-use/server";

const server = new MCPServer({
  name: "my-widget-app",
  version: "1.0.0",
  allowedOrigins: [
    "https://chat.openai.com",
    "https://chatgpt.com",
    "https://myapp.example.com",
  ],
});

// Register tools with widgets...

await server.listen(process.env.PORT ? parseInt(process.env.PORT) : 3000);
```

### Docker Deployment

```dockerfile
FROM node:22-slim AS build
WORKDIR /app
COPY package*.json tsconfig.json ./
COPY src ./src
COPY resources ./resources
COPY public ./public
RUN npm ci && npx mcp-use build

FROM node:22-slim
WORKDIR /app
COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules ./node_modules
COPY package*.json ./
ENV NODE_ENV=production
EXPOSE 3000
CMD ["npx", "mcp-use", "start"]
```

### Environment Variables

```env
PORT=3000
NODE_ENV=production
# Add any API keys your tools need
OPENWEATHER_API_KEY=your-key-here
```

---

## Follow-Up Messages

Widgets can send messages to the conversation on behalf of the user using `sendFollowUpMessage`. This triggers a new LLM turn:

```tsx
const { sendFollowUpMessage } = useWidget();

// String shorthand (most common) — works in both environments
<button onClick={() => sendFollowUpMessage("Tell me more about mangoes")}>
  Ask the AI
</button>

// Full content array (SEP-1865) — supports text, image, and resource blocks
// NOTE: In ChatGPT, only the text content of blocks is used because
// window.openai.sendFollowUpMessage() accepts a plain string prompt
<button onClick={() => sendFollowUpMessage([
  { type: "text", text: "Tell me more about mangoes" },
])}>
  Ask the AI
</button>
```

Per the MCP Apps specification this maps to the `ui/message` JSON-RPC request with `role: "user"` and a `content` array. In ChatGPT, only the text portions are forwarded.

---

## Widget State: Protocol Differences

`setState` from `useWidget` persists UI state with different mechanisms per protocol:

```typescript
type MyState = { favorites: string[] };

const { state, setState } = useWidget<Props, Output, Meta, MyState>();

const favorites = state?.favorites ?? [];

const toggleFavorite = (id: string) => {
  const current = state?.favorites ?? [];
  const next = current.includes(id)
    ? current.filter(f => f !== id)
    : [...current, id];
  setState({ favorites: next });
};
```

What happens under the hood differs per runtime:
- **ChatGPT**: Calls `window.openai.setWidgetState()` — host manages persistence across message reloads
- **MCP Apps**: Updates local React state and sends `ui/update-model-context` to the host — the model can reason about UI state on future turns. Each call overwrites the previous context.

For state that must persist across conversations, store it on your backend and read/write via `callTool` — do not rely on `localStorage`.

---

## Checking Client Support

Detect whether the connected client supports widgets before returning them:

```typescript
server.tool(
  {
    name: "show-dashboard",
    description: "Show the analytics dashboard",
    schema: z.object({}),
    widget: { name: "dashboard", invoking: "Loading...", invoked: "Ready" },
  },
  async (_params) => {
    return widget({
      props: { visitors: 12453, pageViews: 45231 },
      output: text("Dashboard loaded with 12,453 visitors"),
    });
  }
);
```

The `output` (or `message`) field is what text-only clients see — always provide a meaningful text fallback in `content` so CLI tools and non-widget clients receive useful information.

---

## MCP Apps Bridge API (Advanced)

For widgets that need direct protocol access, mcp-use exposes the bridge:

```typescript
import { getMcpAppsBridge } from 'mcp-use/react';

function MyWidget() {
  const bridge = getMcpAppsBridge();

  // All methods return promises
  const result = await bridge.callTool('search', { query: 'hello' });
  const data = await bridge.readResource('file:///data.json');
  await bridge.sendMessage({ type: 'info', text: 'Processing...' });
  await bridge.openLink('https://example.com');
  await bridge.requestDisplayMode('fullscreen');

  return <div>My Widget</div>;
}
```

Most widgets will not need the bridge directly. `useWidget()` provides a simplified API that works across both protocols automatically.

---

## Migration from `appsSdk` to `mcpApps`

If you have existing widgets using `type: "appsSdk"`, migrate to `type: "mcpApps"` for dual-protocol support. Widget code requires no changes — only server registration changes.

### Before (ChatGPT only — deprecated):

```typescript
server.uiResource({
  type: "appsSdk",
  name: "my-widget",
  htmlTemplate: `...`,
  appsSdkMetadata: {
    "openai/widgetCSP": {
      connect_domains: ["https://api.example.com"],
      resource_domains: ["https://cdn.example.com"],
    },
    "openai/widgetPrefersBorder": true,
    "openai/widgetDescription": "My widget description",
  },
});
```

### After (Universal compatibility):

```typescript
server.uiResource({
  type: "mcpApps",
  name: "my-widget",
  htmlTemplate: `...`,
  metadata: {
    csp: {
      connectDomains: ["https://api.example.com"],
      resourceDomains: ["https://cdn.example.com"],
    },
    prefersBorder: true,
    widgetDescription: "My widget description",
  },
});
```

### Migration Checklist

1. `type: "appsSdk"` → `type: "mcpApps"`
2. `appsSdkMetadata: { ... }` → `metadata: { ... }`
3. `"openai/widgetCSP"` → `csp`
4. `connect_domains` → `connectDomains` (snake_case → camelCase)
5. `resource_domains` → `resourceDomains` (snake_case → camelCase)
6. Remove `"openai/"` prefix from all other keys
7. Test in both ChatGPT and an MCP Apps client

### Field Mapping Reference

| Apps SDK (`appsSdkMetadata`) | MCP Apps (`metadata`) | Notes |
|------------------------------|----------------------|-------|
| `"openai/widgetCSP"` | `csp` | CSP object |
| `connect_domains` | `connectDomains` | Array of connection domains |
| `resource_domains` | `resourceDomains` | Array of resource domains |
| `frame_domains` | `frameDomains` | Array of frame domains |
| `redirect_domains` | `redirectDomains` | ChatGPT-specific |
| `script_directives` | `scriptDirectives` | Script CSP directives (add `"'unsafe-eval'"` for React) |
| `style_directives` | `styleDirectives` | Style CSP directives |
| `"openai/widgetPrefersBorder"` | `prefersBorder` | Boolean |
| `"openai/widgetDomain"` | `domain` | String |
| `"openai/widgetDescription"` | `widgetDescription` | String |
| `"openai/widgetAccessible"` | `widgetAccessible` | Boolean (ChatGPT-specific) |
| `"openai/locale"` | `locale` | BCP-47 locale string (ChatGPT-specific) |
| `"openai/toolInvocation/invoking"` | `invoking` | Status text while tool runs |
| `"openai/toolInvocation/invoked"` | `invoked` | Status text after completion |

---

## Quick Reference: Protocol Mapping

| Feature | MCP Apps | ChatGPT |
|---------|----------|---------|
| Widget MIME | `text/html;profile=mcp-app` | `text/html+skybridge` |
| Communication | `postMessage` JSON-RPC | `window.openai.*` |
| Theme source | postMessage event | `window.openai.theme` |
| CSP format | camelCase | snake_case |
| Meta prefix | Standard `_meta` | `openai/*` |
| Tool output | `ui://` template ref | `openai/outputTemplate` |
| Detection | `window.parent !== window` | `"openai" in window` |
| State persistence | `ui/update-model-context` | `window.openai.setWidgetState()` |
| Follow-up messages | `ui/message` JSON-RPC | `window.openai.sendFollowUpMessage()` |
| Registration type | `type: "mcpApps"` (recommended) | `type: "appsSdk"` (deprecated) |
