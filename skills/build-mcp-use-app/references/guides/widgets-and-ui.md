# Widgets and UI — MCP Apps Development Guide

The primary guide for building interactive UI widgets with mcp-use. Widgets (MCP Apps) are React components rendered inside chat clients like ChatGPT and Claude, powered by MCP tools on the server.

---

## What Are MCP Apps Widgets?

MCP Apps are interactive UI components returned by MCP tools. When a user asks a question, the LLM calls a tool, the server returns structured data, and a widget renders it as a rich interactive UI — not just text.

```
User: "Show me the weather in Paris"
  ↓
LLM calls get-weather tool with { city: "Paris" }
  ↓
Server fetches weather data, returns widget({ props, output })
  ↓
Client renders WeatherWidget with temperature, conditions, etc.
```

The server controls two independent channels:
- **`content`** (LLM sees) — text/markdown the LLM uses for conversation
- **`structuredContent`** (Widget sees) — JSON props the React widget renders

---

## Project Setup for MCP Apps

### Scaffold with create-mcp-use-app

```bash
npx create-mcp-use-app my-app --template mcp-apps
cd my-app
npm run dev
```

This creates a project pre-configured for widget development with React, Tailwind, and all necessary tooling.

### Manual Setup

```bash
mkdir my-mcp-app && cd my-mcp-app
npm init -y
npm install mcp-use zod@^4.0.0
npm install -D typescript @types/node @types/react @mcp-use/cli
```

**package.json** — key fields:

```json
{
  "type": "module",
  "scripts": {
    "dev": "mcp-use dev",
    "build": "mcp-use build",
    "start": "mcp-use start"
  }
}
```

**tsconfig.json** — must include React JSX and widget paths:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "jsx": "react-jsx",
    "strict": true,
    "outDir": "./dist",
    "rootDir": "./src",
    "declaration": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["src", "resources/**/*", ".mcp-use/**/*"]
}
```

---

## Widget File Structure

Widgets live in the `resources/` directory. Each widget is a folder with a `widget.tsx` entry point:

```
my-mcp-app/
├── resources/                     # Widget components
│   ├── weather-display/
│   │   ├── widget.tsx             # Entry point (default export + widgetMetadata)
│   │   └── components/
│   │       └── WeatherCard.tsx
│   └── product-search/
│       ├── widget.tsx
│       ├── components/
│       │   ├── ProductCard.tsx
│       │   └── Carousel.tsx
│       └── types.ts
├── public/                        # Static assets (icons, images)
│   ├── icon.svg
│   └── products/
│       └── placeholder.png
├── src/
│   ├── server.ts                  # MCP server entry point
│   └── tools/
│       ├── weather.ts             # Tool registrations
│       └── products.ts
├── package.json
└── tsconfig.json
```

### Widget Entry Point (`widget.tsx`)

Every widget must export:
1. **`default`** — A React component (the widget UI)
2. **`widgetMetadata`** — Metadata describing the widget for the host and LLM

```tsx
// resources/weather-display/widget.tsx
import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

// Metadata for LLM and host
export const widgetMetadata: WidgetMetadata = {
  description: "Displays weather conditions with temperature and forecast",
  props: z.object({
    city: z.string(),
    temperature: z.number(),
    conditions: z.string(),
  }),
  metadata: {
    csp: {
      connectDomains: ["https://api.weather.com"],
      resourceDomains: ["https://cdn.weather-icons.com"],
    },
    prefersBorder: true,
  },
};

// Widget component
function WeatherContent() {
  const { props, isPending, theme } = useWidget<{
    city: string;
    temperature: number;
    conditions: string;
  }>();

  if (isPending) return <div className="animate-pulse p-4">Loading...</div>;

  return (
    <div className={theme === "dark" ? "bg-gray-900 text-white p-4" : "bg-white text-gray-900 p-4"}>
      <h2 className="text-xl font-bold">{props.city}</h2>
      <p className="text-3xl">{props.temperature}°C</p>
      <p>{props.conditions}</p>
    </div>
  );
}

// Default export wrapped in McpUseProvider
export default function Widget() {
  return (
    <McpUseProvider autoSize>
      <WeatherContent />
    </McpUseProvider>
  );
}
```

---

## Widget Registration Flow

### 1. Define the Server Tool with Widget Config

```typescript
// src/tools/weather.ts
import { widget, text } from "mcp-use/server";
import type { MCPServer } from "mcp-use/server";
import { z } from "zod";

export function registerWeatherTools(server: MCPServer) {
  server.tool(
    {
      name: "get-weather",
      description: "Get current weather for a city",
      schema: z.object({ city: z.string().describe("City name") }),
      widget: {
        name: "weather-display",   // Must match folder name in resources/
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
}
```

### 2. The `widget()` Response Helper

The `widget()` function creates a `CallToolResult` with three visibility channels:

| Field | LLM sees? | Widget sees? | Populated by |
|-------|-----------|-------------|-------------|
| `content` | **Yes** | Yes | `output` or `message` |
| `structuredContent` | **No** | Yes (as `props`) | `props` |
| `_meta` | **No** | Yes (as `metadata`) | `metadata` |

```typescript
import { widget, text } from "mcp-use/server";

return widget({
  props: { city: "Paris", temperature: 22 },       // → useWidget().props
  output: text("Weather in Paris: 22°C, Sunny"),    // → LLM sees this
  metadata: { lastUpdated: Date.now() },            // → useWidget().metadata
});
```

### 3. Check Client Support

Not all MCP clients support widgets. Always provide a text fallback:

```typescript
server.tool(
  { name: "show-dashboard", schema: z.object({}), widget: { name: "dashboard" } },
  async (_params, ctx) => {
    if (!ctx.client.supportsApps()) {
      return text("Your client does not support interactive widgets.\n\nData: ...");
    }
    return widget({ props: await loadDashboard(), output: text("Dashboard loaded") });
  }
);
```

---

## All Hooks and Components

### Primary Hooks

| Hook | Purpose | Import |
|------|---------|--------|
| `useWidget<TProps, TOutput, TMeta, TState>()` | Full widget state, props, actions | `mcp-use/react` |
| `useCallTool("tool-name")` | Call MCP tools with state machine | `mcp-use/react` |
| `useWidgetProps<T>()` | Convenience — just props | `mcp-use/react` |
| `useWidgetTheme()` | Convenience — just theme | `mcp-use/react` |
| `useWidgetState<T>(initial?)` | Convenience — just state/setState | `mcp-use/react` |

### `useWidget()` Key Return Values

```typescript
const {
  props,                // Widget data from structuredContent
  isPending,            // true while tool executes
  isStreaming,           // true while LLM streams tool arguments
  partialToolInput,     // Partial props during streaming
  theme,                // "light" | "dark"
  displayMode,          // "inline" | "pip" | "fullscreen"
  state, setState,      // Persistent state (survives page reload)
  callTool,             // Call another MCP tool
  sendFollowUpMessage,  // Send message to chat
  openExternal,         // Open URL in browser
  requestDisplayMode,   // Request fullscreen/pip/inline
  metadata,             // Response metadata
  locale,               // User locale
  safeArea,             // Safe area insets
  maxHeight,            // Max widget height (default 600)
} = useWidget();
```

### `useCallTool()` — Tool Calling

```tsx
const { callTool, callToolAsync, data, isPending, isError, error } = useCallTool("search");

// Fire-and-forget
callTool({ query: "shoes" }, {
  onSuccess: (result) => console.log(result.structuredContent),
  onError: (err) => console.error(err),
});

// Async/await
const result = await callToolAsync({ query: "shoes" });
```

### Components

| Component | Purpose | Key Props |
|-----------|---------|-----------|
| `McpUseProvider` | Universal wrapper (StrictMode + Theme + ErrorBoundary + auto-size) | `autoSize`, `debugger`, `viewControls` |
| `WidgetControls` | Debug and view control buttons | `debugger`, `viewControls`, `position` |
| `ErrorBoundary` | Catches render errors | `children` |
| `ThemeProvider` | Dark/light mode sync | `children` |
| `Image` | CSP-aware image (`/`-prefix resolved to MCP public URL) | `src`, `alt` |

### McpUseProvider Usage

Always wrap your widget content in `McpUseProvider`:

```tsx
import { McpUseProvider } from "mcp-use/react";

export default function Widget() {
  return (
    <McpUseProvider autoSize debugger={false} viewControls="fullscreen">
      <MyWidgetContent />
    </McpUseProvider>
  );
}
```

Internally composes: `StrictMode` → `ThemeProvider` → `WidgetControls` → `ErrorBoundary` → auto-size wrapper.

---

## Public Assets

Static files in the `public/` directory are served automatically and accessible in widgets:

```
public/
├── icon.svg
├── favicon.ico
└── images/
    └── logo.png
```

Access in widgets via the `Image` component:

```tsx
import { Image } from "mcp-use/react";

<Image src="/images/logo.png" alt="Logo" />
// → Resolved to http://localhost:3000/mcp-use/public/images/logo.png
```

External URLs and data URIs pass through unchanged:

```tsx
<Image src="https://cdn.example.com/photo.jpg" alt="External" />
<Image src="data:image/png;base64,..." alt="Inline" />
```

---

## Development Workflow

### Start Development Server

```bash
npm run dev
# or: npx mcp-use dev src/server.ts
```

This launches:
- **MCP server** at `http://localhost:3000/mcp`
- **Inspector** at `http://localhost:3000/inspector`
- **HMR** — edit tools or widgets and changes apply instantly
- **Type generation** — `.mcp-use/tool-registry.d.ts` auto-generated for type-safe `useCallTool`

### Inspector Features

The built-in Inspector lets you:
1. Browse all registered tools, resources, and prompts
2. Invoke tools and see widget rendering
3. Test streaming behavior
4. Inspect widget props, state, and metadata
5. Toggle dark/light theme for testing

### Hot Module Reloading

| Change | Effect |
|--------|--------|
| Edit widget.tsx | Widget reloads instantly in Inspector |
| Edit tool handler | New handler takes effect without restart |
| Add/remove widget | Widget list updates in connected clients |
| Change widgetMetadata | Metadata refreshed on next tool call |

### Build for Production

```bash
npm run build    # npx mcp-use build
npm run start    # npx mcp-use start
```

---

## Widget Output Options

The `output` field in `widget()` controls what the LLM sees. Use any response helper:

```typescript
// Text output (most common)
return widget({ props: data, output: text(`Found ${data.length} results`) });

// Structured JSON output
return widget({ props: data, output: object({ count: data.length, summary }) });

// Message shorthand (equivalent to text)
return widget({ props: data, message: `Found ${data.length} items` });
```

---

## OpenAI Apps SDK Integration

For ChatGPT-compatible clients, mcp-use automatically adapts the protocol:

```typescript
import { AppsSdkAdapter } from "mcp-use/server";

// Automatic — transforms widget metadata for ChatGPT:
//   MIME type → "text/html+skybridge"
//   CSP      → snake_case (connect_domains, resource_domains)
//   Metadata → _meta["openai/*"] prefixed keys
```

Manual OpenAI metadata (advanced use cases):

```typescript
server.tool({
  name: "show_chart",
  schema: z.object({ data: z.array(z.any()) }),
  _meta: {
    "openai/outputTemplate": "ui://widgets/chart",
    "openai/toolInvocation/invoking": "Generating chart...",
    "openai/toolInvocation/invoked": "Chart generated",
    "openai/widgetAccessible": true,
  },
}, handler);
```

---

## Client-Side Hooks for App Builders

These hooks are for building MCP client applications (not widgets):

### `useMcp({ url })` — Single Server Connection

```typescript
import { useMcp } from "mcp-use/react";

const mcp = useMcp({ url: "http://localhost:3000/mcp", autoReconnect: 3000 });
// mcp.state: "discovering" | "pending_auth" | "authenticating" | "ready" | "failed"
// mcp.tools, mcp.resources, mcp.callTool(), mcp.authenticate()
```

### `McpClientProvider` + `useMcpClient` — Multi-Server

```tsx
import { McpClientProvider, useMcpClient, useMcpServer } from "mcp-use/react";

<McpClientProvider
  mcpServers={{
    linear: { url: "https://mcp.linear.app/sse" },
    github: { url: "https://mcp.github.com/mcp" },
  }}
>
  <App />
</McpClientProvider>

// Inside App:
const { servers, addServer, removeServer } = useMcpClient();
const linear = useMcpServer("linear");
```

### `generateHelpers()` — Type-Safe Hooks

```typescript
import { generateHelpers } from "mcp-use/react";

type MyTools = {
  "search": { input: { query: string }; output: { results: Item[] } };
};

const { useCallTool } = generateHelpers<MyTools>();
// useCallTool("search") is now fully typed
```

---

## Quick Reference

| Import | Package | Purpose |
|--------|---------|---------|
| `widget`, `text`, `object` | `mcp-use/server` | Response helpers for tool handlers |
| `AppsSdkAdapter` | `mcp-use/server` | OpenAI Apps SDK protocol adapter |
| `useMcp` | `mcp-use/react` | Single-server connection hook |
| `useCallTool` | `mcp-use/react` | Tool calling with state machine |
| `McpClientProvider` | `mcp-use/react` | Multi-server provider |
| `useMcpClient` | `mcp-use/react` | Access servers map + management |
| `useMcpServer` | `mcp-use/react` | Get specific server by ID |
| `useWidget` | `mcp-use/react` | Widget state in components |
| `useWidgetProps` | `mcp-use/react` | Convenience — just props |
| `useWidgetTheme` | `mcp-use/react` | Convenience — just theme |
| `useWidgetState` | `mcp-use/react` | Convenience — just state/setState |
| `generateHelpers` | `mcp-use/react` | Type-safe hook factory |
| `McpUseProvider` | `mcp-use/react` | All-in-one widget provider |
| `WidgetControls` | `mcp-use/react` | Debug / view control buttons |
| `ErrorBoundary` | `mcp-use/react` | React error boundary |
| `ThemeProvider` | `mcp-use/react` | Dark mode management |
| `Image` | `mcp-use/react` | Path-resolving image component |

---

## Related Guides

- **[Widget Components](./widget-components.md)** — Complete API reference for all hooks and components
- **[Streaming and Preview](./streaming-and-preview.md)** — Live preview with streaming tool arguments
- **[ChatGPT Apps Flow](./chatgpt-apps-flow.md)** — ChatGPT compatibility and deployment
- **[MCP Apps Patterns](../patterns/mcp-apps-patterns.md)** — Production patterns for widgets
- **[Widget Recipes](../examples/widget-recipes.md)** — Complete widget examples
