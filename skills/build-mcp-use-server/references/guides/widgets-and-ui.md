# Widgets and UI

Guide to building interactive UI widgets (MCP Apps) on the server and consuming them with React hooks and components on the client.

---

## Server-Side: MCP Apps / Widgets

MCP Apps are interactive UI widgets returned by tools. The LLM calls a tool, the server returns structured data, and a client-side widget renders it. The server controls what the LLM sees (`content`) separately from what the widget sees (`structuredContent`).

### The `widget()` Response Helper

Import from `mcp-use/server`. Returns a `CallToolResult` with three visibility channels:

| Field | LLM sees? | Widget sees? | Populated by |
|---|---|---|---|
| `content` | **Yes** | Yes | `output` or `message` |
| `structuredContent` | **No** | Yes (as `props`) | `props` |
| `_meta` | **No** | Yes (as `metadata`) | `metadata` |

```typescript
import { widget, text } from "mcp-use/server";

return widget({
  props: { city: "Paris", temperature: 22 },       // → useWidget().props
  output: text("Weather in Paris: 22°C, Sunny"),    // → LLM sees this
  metadata: { lastUpdated: Date.now() },            // → useWidget().metadata
  message: undefined,                               // optional text override (instead of output)
});
```

### Returning Widgets from Tools

Define a `widget` config on the tool and return `widget()` from the handler:

```typescript
import { widget, text } from "mcp-use/server";
import { z } from "zod";

server.tool(
  {
    name: "get-weather",
    description: "Get current weather for a city",
    schema: z.object({ city: z.string().describe("City name") }),
    widget: {
      name: "weather-display",   // must match .tsx file/folder in resources/
      invoking: "Fetching weather...",
      invoked: "Weather loaded",
    },
  },
  async ({ city }) => {
    const data = await fetchWeather(city);
    return widget({
      props: { city, temperature: data.temp, conditions: data.conditions },
      output: text(`Weather in ${city}: ${data.temp}°C, ${data.conditions}`),
    });
  }
);
```

> The widget `.tsx` must exist in `resources/`. Leave `exposeAsTool` unset/`false` when defining a custom tool.

### Widget Output

The `output` field controls what the LLM sees. Use any response helper:

```typescript
return widget({ props: items, output: text(`Showing ${items.length} results`) });
return widget({ props: items, output: object({ count: items.length, summary }) });
return widget({ props: items, message: `Found ${items.length} items` }); // shorthand
```

### Checking Client Support

```typescript
server.tool(
  { name: "show-dashboard", schema: z.object({}), widget: { name: "dashboard" } },
  async (_params, ctx) => {
    if (!ctx.client.supportsApps()) {
      return text("Your client does not support interactive widgets.");
    }
    return widget({ props: await loadDashboard(), output: text("Dashboard loaded") });
  }
);
```

### Streaming Tool Props

When an LLM streams tool call arguments, the widget receives partial input in real time via `partialToolInput` and `isStreaming` from `useWidget()`. `isStreaming` is `true` while the LLM is still generating arguments; `partialToolInput` holds the partial arguments parsed so far. Both revert once the complete tool input arrives and `props` is populated.

This is only available when the host supports it (e.g. MCP Inspector, MCP Apps clients). In ChatGPT Apps SDK or when using URL params, `partialToolInput` stays `null` and `isStreaming` stays `false`.

```tsx
import { useWidget } from "mcp-use/react";

const CodePreviewWidget: React.FC = () => {
  const { props, isPending, isStreaming, partialToolInput } = useWidget<{ code: string; language: string }>();

  if (isPending && !partialToolInput) {
    return <LoadingSpinner />;
  }

  // Show live preview during streaming, then final props when complete
  const displayCode = isStreaming && partialToolInput?.code != null
    ? partialToolInput.code
    : props.code ?? "";
  const displayLang = (isStreaming ? partialToolInput?.language : props.language) ?? "text";

  return (
    <pre data-language={displayLang}>
      {displayCode || "Waiting for input..."}
    </pre>
  );
};
```

### Protocol Adapters

Behind the scenes, mcp-use uses protocol adapters to transform widget configuration between the MCP Apps and ChatGPT Apps SDK protocols:

```typescript
import { McpAppsAdapter, AppsSdkAdapter } from "mcp-use/server";

// These are created automatically when you use type: "mcpApps"
const mcpAppsAdapter = new McpAppsAdapter();
const appsSdkAdapter = new AppsSdkAdapter();

// Transform your unified metadata to each protocol
const mcpAppsMetadata = mcpAppsAdapter.transformMetadata(yourMetadata);
const appsSdkMetadata = appsSdkAdapter.transformMetadata(yourMetadata);
```

You rarely need to interact with adapters directly — the `uiResource()` registration handles this automatically when `type: "mcpApps"` is used.

---

## MCP Apps Overview

MCP Apps is the **official standard** for interactive widgets in the Model Context Protocol ecosystem. It provides a standardized way to create rich, interactive user interfaces that work across MCP-compatible clients.

**mcp-use Advantage**: Write your widgets once using `type: "mcpApps"` and they work with **both** MCP Apps clients AND ChatGPT automatically.

### MCP Apps vs ChatGPT Apps SDK

| Feature | MCP Apps (Standard) | ChatGPT Apps SDK |
|---|---|---|
| **Protocol** | JSON-RPC 2.0 over `postMessage` | `window.openai` global API |
| **MIME Type** | `text/html;profile=mcp-app` | `text/html+skybridge` |
| **Specification** | MCP Apps (open standard) | OpenAI proprietary |
| **Architecture** | Double-iframe sandbox | Single iframe |
| **CSP Format** | camelCase (`connectDomains`) | snake_case (`connect_domains`) |
| **Client Support** | MCP Apps clients (Claude, Goose, etc.) | ChatGPT |
| **mcp-use Support** | Full support | Full support |

### Registering Widgets with `server.uiResource()`

Use `uiResource()` to register a widget entry point. The `mcpApps` type generates metadata for **both** the MCP Apps protocol and the ChatGPT Apps SDK protocol automatically.

```typescript
import { MCPServer } from "mcp-use/server";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  baseUrl: process.env.MCP_URL || "http://localhost:3000",
});

server.uiResource({
  type: "mcpApps",         // Works with BOTH MCP Apps AND ChatGPT
  name: "weather-display",
  htmlTemplate: `
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="UTF-8">
        <title>Weather Display</title>
      </head>
      <body>
        <div id="root"></div>
        <script type="module" src="/resources/weather-display.js"></script>
      </body>
    </html>
  `,
  metadata: {
    // Unified CSP configuration — works for both protocols
    csp: {
      connectDomains: ["https://api.weather.com"],
      resourceDomains: ["https://cdn.weather.com"],
    },
    prefersBorder: true,

    // Invocation status text shown in inspector and ChatGPT
    invoking: "Fetching weather...",   // auto-default: "Loading weather-display..."
    invoked: "Weather loaded",         // auto-default: "weather-display ready"

    // ChatGPT-specific metadata (optional)
    widgetDescription: "Displays current weather conditions",
  },
});
```

This single configuration automatically generates metadata for **both protocols**. For MCP Apps clients it uses MIME type `text/html;profile=mcp-app` with camelCase CSP fields; for ChatGPT it uses `text/html+skybridge` with `openai/`-prefixed metadata keys and snake_case CSP fields.

### Data Flow: What the LLM Sees vs What the Widget Sees

| Field | LLM sees it? | Widget sees it? | Purpose |
|---|---|---|---|
| `content` | **Yes** | Yes | Text summary for the model's context |
| `structuredContent` | **No** | Yes (as `props`) | Rendering data for the widget |
| `_meta` | **No** | Yes (as `metadata`) | Protocol + custom metadata |

```typescript
// Server: return data
server.tool({
  name: "search-products",
  schema: z.object({ query: z.string() }),
  widget: { name: "product-search-result" },
}, async ({ query }) => {
  const results = await db.search(query);

  return widget({
    // Widget rendering data — LLM does NOT see this
    props: { query, results },
    // Text summary — LLM sees this
    output: text(`Found ${results.length} products matching "${query}"`),
  });
});
```

```typescript
// Widget: read data
const { props, toolInput, isPending } = useWidget<ProductSearchProps>();

// props     = structuredContent from tool result (computed by server)
// toolInput = tool call arguments (what the model sent, e.g. { query: "mango" })
```

### Display Modes

Widgets can request different display modes from the host. The host may decline — always check `displayMode` for the actual state.

```typescript
const { displayMode, requestDisplayMode } = useWidget();

// Request fullscreen
await requestDisplayMode("fullscreen");

// Request picture-in-picture
await requestDisplayMode("pip");

// Return to inline
await requestDisplayMode("inline");
```

### Follow-Up Messages

Widgets can send messages to the conversation on behalf of the user using `sendFollowUpMessage`. This triggers a new LLM turn. Accepts a plain string (most common) or a full content block array per SEP-1865:

```typescript
const { sendFollowUpMessage } = useWidget();

// String shorthand (most common)
await sendFollowUpMessage("Tell me more about mangoes");

// Full content array — supports text, image, and resource blocks per SEP-1865
await sendFollowUpMessage([
  { type: "text", text: "Tell me more about mangoes" },
]);
```

When running inside ChatGPT (Apps SDK), only the text content of the blocks is used since `window.openai.sendFollowUpMessage` accepts a plain string prompt.

### Host Context: Locale, Theme, and More

`useWidget` exposes host context fields provided by the host:

| Field | Type | Description |
|---|---|---|
| `theme` | `"light" \| "dark"` | Current host theme |
| `locale` | `string` | BCP 47 locale (e.g. `"en-US"`, `"fr-FR"`) |
| `timeZone` | `string` | IANA timezone (e.g. `"America/New_York"`) |
| `safeArea` | `{ insets: { top, right, bottom, left } }` | Safe area for notched devices |
| `userAgent` | `{ device: { type }, capabilities: { hover, touch } }` | Device info |
| `maxHeight` | `number` | Max available height in pixels |
| `maxWidth` | `number \| undefined` | Max available width (MCP Apps only) |

### Response Metadata

The tool result's `_meta` field is available as `metadata` in `useWidget`. Use the `metadata` option in the `widget()` helper to pass extra data that doesn't belong in `structuredContent`:

```typescript
// Server side
return widget({
  props: { items: filteredItems },
  metadata: { totalCount: 1000, nextCursor: "abc123" },
  output: text(`Showing ${filteredItems.length} of 1000 results`),
});

// Widget side
const { props, metadata } = useWidget();
// props    = { items: [...] }           (from structuredContent)
// metadata = { totalCount, nextCursor } (from _meta)
```

### State Management

State in an MCP Apps widget falls into three categories:

| State type | Where it lives | Lifetime | Example |
|---|---|---|---|
| **Business data** | MCP server / backend | Long-lived | Tasks, search results, documents |
| **UI state** | Widget instance | Per-widget | Selected row, expanded panel, filter |
| **Cross-session** | Your backend | Across conversations | Saved preferences, workspace settings |

**UI state** uses `setState` from `useWidget`. Under the hood: in ChatGPT it calls `window.openai.setWidgetState()` for host-managed persistence; in MCP Apps it updates local React state **and** sends `ui/update-model-context` to the host so the model can reason about UI state on future turns.

```typescript
type MyState = { favorites: string[] };

const { props, state, setState } = useWidget<Props, Output, Meta, MyState>();

const favorites = state?.favorites ?? [];

const toggleFavorite = (id: string) => {
  const current = state?.favorites ?? [];
  const next = current.includes(id)
    ? current.filter(f => f !== id)
    : [...current, id];
  setState({ favorites: next });
};
```

**Cross-session state** must be stored on your backend. Use `callTool` from the widget to read/write preferences via your server's tools — don't rely on `localStorage`.

### Protocol-Specific Metadata

While mcp-use handles protocol differences automatically, you can provide protocol-specific metadata when needed:

```typescript
server.uiResource({
  type: "mcpApps",
  name: "my-widget",
  htmlTemplate: `...`,
  metadata: {
    // Shared metadata (used by both)
    csp: { connectDomains: ["https://api.example.com"] },
    prefersBorder: true,

    // MCP Apps specific (ignored by ChatGPT)
    autoResize: true,
    supportsLocalStorage: true,

    // ChatGPT specific (ignored by MCP Apps clients)
    widgetDescription: "Special description for ChatGPT",
    widgetDomain: "https://chatgpt.com",
  },
});
```

### Migration from Apps SDK (`type: "appsSdk"`)

If you have existing widgets using `type: "appsSdk"`, migrate to dual-protocol support by changing the type and metadata format:

**Before (ChatGPT only):**
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

**After (Universal compatibility):**
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

**Field Mapping Reference:**

| Apps SDK (`appsSdkMetadata`) | MCP Apps (`metadata`) | Notes |
|---|---|---|
| `"openai/widgetCSP"` | `csp` | CSP configuration object |
| `connect_domains` | `connectDomains` | Array of connection domains |
| `resource_domains` | `resourceDomains` | Array of resource domains |
| `frame_domains` | `frameDomains` | Array of frame domains |
| `redirect_domains` | `redirectDomains` | Array of redirect domains (ChatGPT-specific) |
| `script_directives` | `scriptDirectives` | Array of script CSP directives |
| `style_directives` | `styleDirectives` | Array of style CSP directives |
| `"openai/widgetPrefersBorder"` | `prefersBorder` | Boolean |
| `"openai/widgetDomain"` | `domain` | String (custom domain) |
| `"openai/widgetDescription"` | `widgetDescription` | String (widget description) |
| `"openai/widgetAccessible"` | `widgetAccessible` | Boolean (ChatGPT-specific) |
| `"openai/locale"` | `locale` | String (ChatGPT-specific) |
| `"openai/toolInvocation/invoking"` | `invoking` | Status text while tool runs (auto-defaulted) |
| `"openai/toolInvocation/invoked"` | `invoked` | Status text after tool completes (auto-defaulted) |

Your **widget code** requires **no changes** — only the server registration changes.

---

## Content Security Policy (CSP)

CSP controls which domains your widgets can fetch from, load scripts/styles from, and embed. Widgets run in sandboxed iframes, so CSP must explicitly allow any external resources.

### Automatic Configuration

When `baseUrl` is set (via `MCPServer` constructor or `MCP_URL` environment variable), mcp-use automatically configures CSP. The server origin is auto-injected into each widget's `connectDomains`, `resourceDomains`, and `baseUriDomains` — you don't need to add it manually.

```typescript
const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  baseUrl: process.env.MCP_URL, // Required for production
});
```

### Per-Widget Configuration

For widgets that need additional domains (APIs, CDNs, etc.), configure CSP in `metadata.csp` using camelCase:

```typescript
export const widgetMetadata: WidgetMetadata = {
  description: "Display weather",
  props: propSchema,
  metadata: {
    csp: {
      connectDomains: ["https://api.weather.com"],
      resourceDomains: ["https://cdn.weather.com"],
      baseUriDomains: ["https://myserver.com"],
      frameDomains: ["https://trusted-embed.com"],
      redirectDomains: ["https://oauth.provider.com"],
    },
  },
};
```

### CSP Field Reference

| MCP Apps (camelCase) | Apps SDK (snake_case) | Description |
|---|---|---|
| `connectDomains` | `connect_domains` | Domains for fetch, XHR, WebSocket |
| `resourceDomains` | `resource_domains` | Domains for scripts, styles, images |
| `baseUriDomains` | `base_uri_domains` | Domains for base URI (MCP Apps) |
| `frameDomains` | `frame_domains` | Domains for iframe embeds |
| `redirectDomains` | `redirect_domains` | Domains for redirects (ChatGPT-specific) |
| `scriptDirectives` | `script_directives` | Custom script CSP directives (not all clients support, e.g. ChatGPT) |
| `styleDirectives` | `style_directives` | Custom style CSP directives |

Your CSP domains are merged with your server's base URL automatically. For ChatGPT, OpenAI's required domains (`*.oaistatic.com`, etc.) are also added. For MCP Apps clients, only the domains you declare are used.

### Environment Variables

```
# Base URL — auto-included in widget CSP
MCP_URL=https://myserver.com

# Additional domains (comma-separated) — appended to widget CSP
CSP_URLS=https://api.example.com,https://cdn.example.com
```

- **MCP_URL**: Base URL for widget assets and public files. Also used by the server to configure CSP.
- **CSP_URLS**: (Optional) Additional domains to whitelist. Required for static deployments where widget assets are served from different domains.

### Static Deployments

When widgets are served from static storage (e.g., Supabase Storage) while the MCP server runs elsewhere, set:
- **MCP_URL**: Where widget assets are stored
- **MCP_SERVER_URL**: Where the MCP server runs (for API calls)
- **CSP_URLS**: Domains for storage and API access

### Inspector Debugging

The mcp-use Inspector provides a **CSP Mode Toggle**:
- **Permissive** — Relaxed CSP for debugging
- **Widget-Declared** — Enforces the widget's declared CSP (production-like)

CSP violations are logged in the console. Use Widget-Declared mode to catch CSP issues before production deployment.

---

## Client-Side: React Hooks and Components

Import all client-side APIs from `mcp-use/react`.

### `useWidget()` — Widget State in React

Primary hook for widget components. Provides a **universal, protocol-agnostic** interface that automatically detects whether it's running in MCP Apps (JSON-RPC over postMessage) or ChatGPT Apps SDK (`window.openai` API). Your widget code stays identical across both protocols.

**Import:**
```typescript
import { useWidget } from "mcp-use/react";
```

**Type Parameters** (all optional, in order):
```typescript
useWidget<
  TProps,    // Props type (from structuredContent)
  TOutput,   // Output type (from structuredContent / tool output)
  TMetadata, // Metadata type (from _meta)
  TState     // State type (for widgetState)
>();
```

**Return Values — Props and State:**

| Property | Type | Description |
|---|---|---|
| `props` | `Partial<TProps>` | Widget props (from `structuredContent`). Empty `{}` when `isPending` is true |
| `output` | `TOutput \| null` | Tool output from the last execution |
| `metadata` | `TMetadata \| null` | Response metadata from the tool (from `_meta`) |
| `state` | `TState \| null` | Persisted widget state |
| `setState` | `(state: TState \| ((prev: TState \| null) => TState)) => Promise<void>` | Update widget state (persisted and shown to model) |

**Return Values — Layout and Theme:**

| Property | Type | Description |
|---|---|---|
| `theme` | `"light" \| "dark"` | Current theme (auto-syncs with host) |
| `displayMode` | `"inline" \| "pip" \| "fullscreen"` | Current display mode |
| `safeArea` | `SafeArea` | Safe area insets for mobile layout |
| `maxHeight` | `number` | Maximum height available (pixels) |
| `maxWidth` | `number \| undefined` | Max available width (MCP Apps only) |
| `userAgent` | `UserAgent` | Device capabilities (`device`, `capabilities`) |
| `locale` | `string` | Current locale (e.g., `"en-US"`) |
| `timeZone` | `string` | IANA timezone (e.g., `"America/New_York"`) |
| `mcp_url` | `string` | MCP server base URL for making API requests |

**Return Values — Actions:**

| Method | Signature | Description |
|---|---|---|
| `callTool` | `(name: string, args: Record<string, unknown>) => Promise<CallToolResponse>` | Call a tool on the MCP server |
| `sendFollowUpMessage` | `(content: string \| MessageContentBlock[]) => Promise<void>` | Send a follow-up message; string shorthand or full content block array (SEP-1865) |
| `openExternal` | `(href: string) => void` | Open an external URL in a new tab |
| `requestDisplayMode` | `(mode: DisplayMode) => Promise<{ mode: DisplayMode }>` | Request a different display mode |
| `notifyIntrinsicHeight` | `(height: number) => Promise<void>` | Notify the host about intrinsic height changes for auto-sizing |

**Return Values — Availability and Streaming:**

| Property | Type | Description |
|---|---|---|
| `isAvailable` | `boolean` | Whether the widget API is available |
| `isPending` | `boolean` | Whether the tool is currently executing. When `true`, props will be empty `{}` |
| `partialToolInput` | `Partial<TProps> \| null` | Partial/streaming tool arguments updated in real time. `null` when not streaming. Only set when the host sends `tool-input-partial`; stays `null` in ChatGPT Apps SDK. |
| `isStreaming` | `boolean` | Whether tool arguments are currently being streamed. `false` in ChatGPT Apps SDK or when the host does not stream. |

**Return Values — Host Identity (MCP Apps only):**

| Property | Type | Description |
|---|---|---|
| `hostInfo` | `{ name: string; version: string } \| undefined` | Name and version of the MCP Apps host, from the `ui/initialize` handshake. `undefined` in ChatGPT Apps SDK. |
| `hostCapabilities` | `Record<string, unknown> \| undefined` | Capabilities advertised by the MCP Apps host (SEP-1865 `HostCapabilities`). `undefined` in ChatGPT Apps SDK. |

**Default Values:**

| Field | Default |
|---|---|
| `theme` | `"light"` |
| `displayMode` | `"inline"` |
| `safeArea` | `{ insets: { top: 0, bottom: 0, left: 0, right: 0 } }` |
| `maxHeight` | `600` |
| `userAgent` | `{ device: { type: "desktop" }, capabilities: { hover: true, touch: false } }` |
| `locale` | `"en"` |
| `props` | `{}` |
| `output` | `null` |
| `metadata` | `null` |
| `state` | `null` |

**Widget Lifecycle:**

Widgets render **before** the tool execution completes:

1. **First render** (`isPending = true`): Widget mounts immediately. `props` is `{}`, `output` and `metadata` are `null`. Use this phase to show loading states.
2. **Streaming phase** (optional, `isStreaming = true`): If the host streams tool arguments, `partialToolInput` is updated in real time. Only available in MCP Apps hosts that send `ui/notifications/tool-input-partial`.
3. **After tool completes** (`isPending = false`): `props` contains the actual widget data, `output` and `metadata` are available.

```tsx
const MyWidget: React.FC = () => {
  const { props, isPending } = useWidget<MyWidgetProps>();

  if (isPending) {
    return <LoadingSpinner />;
  }

  // Safe to access props now
  return (
    <div>
      {props.city} - {props.temperature}°C
    </div>
  );
};
```

**Usage note:** Components must NOT accept props via React props. Instead, read them from the hook:

```tsx
// ❌ Don't do this
const MyWidget: React.FC<MyProps> = ({ city, temperature }) => { ... }

// ✅ Do this
const MyWidget: React.FC = () => {
  const { props } = useWidget<MyProps>();
  const { city, temperature } = props;
}
```

**Complete Example:**

```tsx
import { useWidget } from "mcp-use/react";

interface ProductProps {
  productId: string;
  name: string;
  price: number;
}

interface ProductOutput {
  reviews: Array<{ rating: number; comment: string }>;
}

interface ProductState {
  favorites: string[];
}

const ProductWidget: React.FC = () => {
  const {
    props,
    output,
    state,
    setState,
    theme,
    displayMode,
    safeArea,
    callTool,
    sendFollowUpMessage,
    openExternal,
    requestDisplayMode,
    notifyIntrinsicHeight,
    isAvailable,
    hostInfo,
    hostCapabilities,
  } = useWidget<ProductProps, ProductOutput, {}, ProductState>();

  const handleAddToFavorites = async () => {
    const newFavorites = [...(state?.favorites || []), props.productId];
    await setState({ favorites: newFavorites });
  };

  const handleGetReviews = async () => {
    const result = await callTool("get-product-reviews", {
      productId: props.productId,
    });
    // Handle result
  };

  return (
    <div data-theme={theme}>
      <h1>{props.name}</h1>
      <p>${props.price}</p>
      <button onClick={handleAddToFavorites}>Add to Favorites</button>
      <button onClick={handleGetReviews}>Get Reviews</button>
    </div>
  );
};
```

### Helper Hooks

**`useWidgetProps<T>()`** — Get only the widget props:

```typescript
import { useWidgetProps } from "mcp-use/react";

const props = useWidgetProps<{ city: string; temperature: number }>();
// { city: "Paris", temperature: 22 }
```

**`useWidgetTheme()`** — Get only the theme:

```typescript
import { useWidgetTheme } from "mcp-use/react";

const theme = useWidgetTheme(); // 'light' | 'dark'
```

**`useWidgetState<T>()`** — Get state management:

```typescript
import { useWidgetState } from "mcp-use/react";

const [favorites, setFavorites] = useWidgetState<string[]>([]);

await setFavorites(["item1", "item2"]);
await setFavorites((prev) => [...prev, "newItem"]); // functional update
```

### `useCallTool(name)` — Tool Calling

Type-safe hook for calling MCP tools from within widgets. When paired with automatic type generation (`mcp-use dev`), it provides full TypeScript IntelliSense for tool inputs and outputs.

**Import:**
```typescript
import { useCallTool } from "mcp-use/react";
```

**State Machine** (discriminated union similar to TanStack Query):

```typescript
type State =
  | { status: "idle"; data: undefined; error: undefined }
  | { status: "pending"; data: undefined; error: undefined }
  | { status: "success"; data: CallToolResult; error: undefined }
  | { status: "error"; data: undefined; error: Error }
```

**Return Values:**

| Property | Type | Description |
|---|---|---|
| `status` | `"idle" \| "pending" \| "success" \| "error"` | Current state of the tool call |
| `isIdle` | `boolean` | True when no call has been made |
| `isPending` | `boolean` | True while the tool is executing |
| `isSuccess` | `boolean` | True when the tool call succeeded |
| `isError` | `boolean` | True when the tool call failed |
| `data` | `CallToolResult \| undefined` | Tool result (only available when `isSuccess`) |
| `error` | `Error \| undefined` | Error object (only available when `isError`) |
| `callTool` | `Function` | Fire-and-forget method with optional callbacks |
| `callToolAsync` | `Function` | Promise-based method for async/await |

**Fire-and-forget with callbacks:**

```tsx
const { callTool } = useCallTool("create-booking");

callTool(
  { flightId: "123", passenger: "John Doe" },
  {
    onSuccess: (data) => {
      console.log("Booking confirmed:", data.structuredContent);
    },
    onError: (error) => {
      console.error("Booking failed:", error);
    },
    onSettled: (data, error, input) => {
      console.log("Request complete", { data, error, input });
    }
  }
);
```

| Callback | Signature | Description |
|---|---|---|
| `onSuccess` | `(data: CallToolResult, input: any) => void` | Called when tool succeeds |
| `onError` | `(error: Error, input: any) => void` | Called when tool fails |
| `onSettled` | `(data?, error?, input: any) => void` | Called after success or error |

**Async/await pattern:**

```tsx
const { callToolAsync } = useCallTool("search-flights");

const handleSearch = async () => {
  try {
    const result = await callToolAsync({ destination: "Tokyo", date: "2024-12-01" });
    console.log("Found flights:", result.structuredContent.flights);
  } catch (error) {
    console.error("Search failed:", error);
  }
};
```

**Response structure:**

```typescript
interface CallToolResult {
  content: Array<TextContent | ImageContent | EmbeddedResource>;
  isError?: boolean;
  structuredContent?: any;      // Strongly typed based on tool definition
  metadata?: Record<string, unknown>; // MCP Apps specific
}
```

**Environment support:** The protocol is detected automatically. In MCP Apps it uses JSON-RPC over `postMessage`; in ChatGPT Apps SDK it uses `window.openai.callTool()`. Your code stays identical.

**Type generation integration:** When using `mcp-use dev`, types are auto-generated from your tool schemas into `.mcp-use/tool-registry.d.ts`. The hook uses these types to provide IntelliSense for tool names, inputs, and outputs.

**Manual type generation (without `mcp-use dev`):** Use `generateHelpers()`:

```typescript
import { generateHelpers } from "mcp-use/react";

type MyToolMap = {
  "search-flights": {
    input: { destination: string; date?: string };
    output: { flights: Array<{ id: string; price: number }> };
  };
};

const { useCallTool } = generateHelpers<MyToolMap>();
const { callTool, data } = useCallTool("search-flights"); // fully typed
```

**Basic usage example:**

```tsx
import { useCallTool } from "mcp-use/react";
import { useState } from "react";

const FlightSearchWidget = () => {
  const [destination, setDestination] = useState("");
  const { callTool, data, isPending, isError, error } = useCallTool("search-flights");

  const handleSearch = () => {
    callTool({ destination }, {
      onSuccess: (result) => {
        console.log(`Found ${result.structuredContent.flights.length} flights`);
      },
    });
  };

  return (
    <div className="widget">
      <input
        type="text"
        value={destination}
        onChange={(e) => setDestination(e.target.value)}
        placeholder="Enter destination"
        disabled={isPending}
      />
      <button onClick={handleSearch} disabled={isPending || !destination}>
        {isPending ? "Searching..." : "Search Flights"}
      </button>
      {isError && <div className="error">Error: {error.message}</div>}
      {data && (
        <ul className="results">
          {data.structuredContent.flights.map((flight) => (
            <li key={flight.id}>
              {flight.departure} → {flight.arrival} - ${flight.price}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
```

### `useMcp({ url })` — Single Server Connection

Manages connection, auth, and state for a single MCP server:

| State | Meaning |
|---|---|
| `discovering` | Checking server existence and capabilities |
| `pending_auth` | Auth required, waiting for user action |
| `authenticating` | OAuth popup/redirect in progress |
| `ready` | Connected — tools, resources, prompts available |
| `failed` | Connection or auth failed — check `error` |

```typescript
import { useMcp } from "mcp-use/react";

function App() {
  const mcp = useMcp({
    url: "http://localhost:3000/mcp",
    headers: { Authorization: "Bearer TOKEN" },
    autoReconnect: 3000,
  });

  if (mcp.state !== "ready") return <p>{mcp.state}...</p>;
  return <p>Connected — {mcp.tools.length} tools available</p>;
}
```

Key result fields: `state`, `error`, `tools`, `resources`, `prompts`, `callTool()`, `readResource()`, `authenticate()`, `retry()`, `disconnect()`, `serverInfo`.

### `McpClientProvider` — Multi-Server Provider

Wraps your app to manage multiple MCP server connections with optional persistence:

```tsx
import { McpClientProvider, LocalStorageProvider } from "mcp-use/react";

<McpClientProvider
  mcpServers={{
    linear: { url: "https://mcp.linear.app/sse" },
    github: { url: "https://mcp.github.com/mcp" },
  }}
  storageProvider={new LocalStorageProvider("my-servers")}
  enableRpcLogging={true}
>
  <App />
</McpClientProvider>
```

### `useMcpClient()` — Multi-Server Access

Access all servers and management functions inside `McpClientProvider`:

```tsx
import { useMcpClient } from "mcp-use/react";

const { servers, addServer, removeServer, updateServer } = useMcpClient();
addServer("slack", { url: "https://mcp.slack.com/mcp" });
```

### `useMCPServer(name)` — Get Specific Server

Retrieve a single server by ID. Returns `undefined` if not found. Throws if called outside `McpClientProvider`:

```tsx
import { useMCPServer } from "mcp-use/react";

const linear = useMCPServer("linear");
if (linear?.state === "ready") console.log(linear.tools.length);
```

---

## React Components

### `<McpUseProvider />`

Universal provider component that works with **both** MCP Apps and ChatGPT Apps SDK protocols. Automatically includes StrictMode, ThemeProvider, optional WidgetControls, and ErrorBoundary.

**Import:**
```typescript
import { McpUseProvider } from "mcp-use/react";
```

**Props:**

| Prop | Type | Default | Description |
|---|---|---|---|
| `children` | `React.ReactNode` | **required** | The widget content to wrap |
| `debugger` | `boolean` | `false` | Enable debug button in WidgetControls |
| `viewControls` | `boolean \| "pip" \| "fullscreen"` | `false` | Enable view controls. `true` shows both, `"pip"` shows only pip, `"fullscreen"` shows only fullscreen |
| `autoSize` | `boolean` | `true` | Automatically notify the host about container height changes using ResizeObserver |

**What's included** (in order, outermost to innermost):
1. **StrictMode** — React's development mode checks
2. **ThemeProvider** — Protocol-aware theme management (syncs with both MCP Apps and ChatGPT)
3. **WidgetControls** (conditional) — Debug and view controls if enabled
4. **ErrorBoundary** — Error handling for graceful failures
5. **Auto-sizing container** (conditional) — ResizeObserver wrapper if `autoSize={true}` (default: enabled)

> **Breaking change (v1.20.1):** `McpUseProvider` no longer includes `BrowserRouter`. If your widget uses `react-router` for navigation, add it explicitly:
> ```tsx
> import { BrowserRouter } from "react-router";
> <McpUseProvider>
>   <BrowserRouter>
>     <MyWidget />
>   </BrowserRouter>
> </McpUseProvider>
> ```

```tsx
import { McpUseProvider } from "mcp-use/react";

// Basic
<McpUseProvider>
  <div>My widget content</div>
</McpUseProvider>

// With all options
<McpUseProvider debugger viewControls autoSize>
  <MyWidgetContent />
</McpUseProvider>
```

### `<WidgetControls />`

Adds debug and view-control buttons to a widget. Props:

| Prop | Type | Default | Description |
|---|---|---|---|
| `children` | `React.ReactNode` | **required** | The widget content to wrap |
| `debugger` | `boolean` | `false` | Enable debug button that opens an overlay with widget diagnostics |
| `viewControls` | `boolean \| "pip" \| "fullscreen"` | `false` | Enable view controls. `true` shows both; `"pip"` shows only pip; `"fullscreen"` shows only fullscreen |
| `position` | `"top-left" \| "top-center" \| "top-right" \| "center-left" \| "center-right" \| "bottom-left" \| "bottom-center" \| "bottom-right"` | `"top-right"` | Position of the control buttons |
| `attachTo` | `HTMLElement \| null` | `undefined` | Element to attach controls to for custom positioning |
| `showLabels` | `boolean` | `true` | Show labels on control buttons |
| `className` | `string` | `""` | Additional CSS classes applied to the container |

```tsx
import { WidgetControls } from "mcp-use/react";

<WidgetControls debugger viewControls position="top-right">
  <div>Widget content</div>
</WidgetControls>
```

### `<ErrorBoundary />`

Catches React errors in the child tree and displays a fallback UI:

```tsx
import { ErrorBoundary } from "mcp-use/react";

<ErrorBoundary>
  <RiskyComponent />
</ErrorBoundary>
```

### `<ThemeProvider />`

Manages dark mode class and `data-theme` attribute on `document.documentElement`, preventing a flash of incorrect theme using `useLayoutEffect`. Also sets `color-scheme` for CSS `light-dark()` function support.

**Priority:** 1) `useWidget()` theme (from MCP Apps or ChatGPT Apps SDK widget API), 2) system preference (`prefers-color-scheme`).

Automatically listens to system theme changes via `MediaQueryList`.

```tsx
import { ThemeProvider } from "mcp-use/react";

<ThemeProvider><App /></ThemeProvider>
```

### `<Image />`

Automatically resolves `/`-prefixed relative paths to the correct MCP public URL. Absolute URLs (`http://`, `https://`) and `data:` URIs pass through unchanged. Accepts all standard `<img>` HTML attributes.

**Source resolution priority:**
1. If `src` starts with `http://`, `https://`, or `data:` — used unchanged.
2. If `window.__mcpPublicAssetsUrl` is set (static deployments, e.g. Supabase Storage) — prefixed with that value.
3. Otherwise — prefixed with `window.__mcpPublicUrl` (dynamic serving, e.g. `http://localhost:3000/mcp-use/public`).

```tsx
import { Image } from "mcp-use/react";

<Image src="/icons/logo.png" alt="Logo" />
// → http://localhost:3000/mcp-use/public/icons/logo.png (dynamic)
// → https://cdn.example.com/icons/logo.png (static deployment)
```

---

## MCP Apps Bridge API (Advanced)

For widgets that need direct protocol access, mcp-use provides the MCP Apps bridge:

```typescript
import { getMcpAppsBridge } from 'mcp-use/react';

function MyWidget() {
  const bridge = getMcpAppsBridge();

  // Call an MCP tool
  const result = await bridge.callTool('search', { query: 'hello' });

  // Read an MCP resource
  const data = await bridge.readResource('file:///data.json');

  // Send a message to the host
  await bridge.sendMessage({ type: 'info', text: 'Processing...' });

  // Open a link
  await bridge.openLink('https://example.com');

  // Request display mode change
  await bridge.requestDisplayMode('fullscreen');

  return <div>My Widget</div>;
}
```

Most widgets won't need the bridge directly. The `useWidget()` hook provides a simplified API that works across both protocols automatically.

---

## Quick Reference

| Import | Package | Purpose |
|---|---|---|
| `widget`, `text`, `object` | `mcp-use/server` | Response helpers for tool handlers |
| `McpAppsAdapter`, `AppsSdkAdapter` | `mcp-use/server` | Protocol adapters (MCP Apps / ChatGPT) |
| `useMcp` | `mcp-use/react` | Single-server connection hook |
| `useCallTool` | `mcp-use/react` | Tool calling with state machine |
| `McpClientProvider` | `mcp-use/react` | Multi-server provider |
| `useMcpClient` | `mcp-use/react` | Access servers map + management |
| `useMCPServer` | `mcp-use/react` | Get specific server by ID |
| `useWidget` | `mcp-use/react` | Widget state in components |
| `useWidgetProps` | `mcp-use/react` | Props-only convenience hook |
| `useWidgetTheme` | `mcp-use/react` | Theme-only convenience hook |
| `useWidgetState` | `mcp-use/react` | State-only convenience hook |
| `generateHelpers` | `mcp-use/react` | Type-safe hook factory |
| `getMcpAppsBridge` | `mcp-use/react` | Direct MCP Apps protocol bridge |
| `McpUseProvider` | `mcp-use/react` | All-in-one widget provider |
| `WidgetControls` | `mcp-use/react` | Debug / view control buttons |
| `ErrorBoundary` | `mcp-use/react` | React error boundary |
| `ThemeProvider` | `mcp-use/react` | Dark mode management |
| `Image` | `mcp-use/react` | Path-resolving image component |

---

## `widget()` Helper — Parameter Reference

| Field | Type | Required | Description |
|---|---|---|---|
| `props` | `Record<string, any>` | No | Sent to the widget as `props`. Stored in `structuredContent`. LLM does NOT see this. Defaults to `{}` if omitted. |
| `output` | `CallToolResult` | No | LLM-visible content (`text`, `object`, etc.). If neither `output` nor `message` is set, an empty text content block is used. |
| `message` | `string` | No | Shorthand for a plain text content entry. Takes precedence over `output` when both are set. |
| `metadata` | `Record<string, unknown>` | No | Extra data for the widget. Exposed as `useWidget().metadata`. Stored in `_meta`. |

---

## Widget Lifecycle States — Tool `widget` Config

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | Widget identifier that matches the resources entry |
| `invoking` | `string` | No | Message shown while tool is running. Auto-defaults to `"Loading {name}..."` |
| `invoked` | `string` | No | Message shown after tool completes. Auto-defaults to `"{name} ready"` |
| `error` | `string` | No | Fallback text when the tool fails |

```typescript
server.tool(
  {
    name: 'load-dashboard',
    description: 'Load the sales dashboard widget.',
    widget: {
      name: 'sales-dashboard',
      invoking: 'Loading dashboard…',
      invoked: 'Dashboard ready.',
      error: 'Dashboard failed to load.',
    },
  },
  async () => widget({ props: { ready: true }, output: text('Dashboard ready.') })
);
```

---

## Serving Widget Assets with Hono Routes

mcp-use exposes a Hono-compatible router on `MCPServer`. Use `server.get()` or `server.route()` to serve custom assets or API endpoints used by widgets.

| Method | Signature | Use Case |
|---|---|---|
| `server.get(path, handler)` | `GET` handler | Static assets, read-only data for widgets |
| `server.post(path, handler)` | `POST` handler | Widget actions or mutating operations |
| `server.use(path, middleware)` | Middleware | Auth, CORS, logging for widget endpoints |
| `server.route(path, router)` | Router mount | Bundle a full Hono router |

```typescript
import { MCPServer } from 'mcp-use/server';

const server = new MCPServer({ name: 'ui-demo', version: '1.0.0' });

server.get('/public/icons/sales.svg', (c) => {
  return c.text('<svg>...</svg>', 200, { 'Content-Type': 'image/svg+xml' });
});

server.post('/api/widget/refresh', async (c) => {
  const payload = await c.req.json();
  const refreshed = await refreshWidget(payload.widgetId);
  return c.json({ refreshed });
});
```

---

## UI Debugging Checklist

1. Confirm `server.uiResource()` entry is registered with correct `name` and `htmlTemplate`.
2. Verify widget file exists under `resources/`.
3. Ensure `structuredContent` matches widget props shape.
4. Use `McpUseProvider debugger` for on-screen state inspection.
5. Regenerate types with `mcp-use generate-types` after schema updates.
6. Test CSP in Inspector with Widget-Declared mode before deploying to production.
7. Verify `isPending` / `isStreaming` lifecycle transitions in the Inspector.
