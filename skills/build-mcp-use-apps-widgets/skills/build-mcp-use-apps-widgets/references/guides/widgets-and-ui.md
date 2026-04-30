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

The server controls three channels:
- **`content`** — text/markdown used by the conversation and by text-only clients; keep it concise and complete.
- **`structuredContent`** — JSON props the React widget renders; treat it as potentially model-visible, especially in ChatGPT/OpenAI Apps.
- **`_meta`** — private, bulky, or UI-only widget hydration data.

### Dual-Protocol Support

A single widget definition works with both ChatGPT (Apps SDK) and MCP Apps-compatible clients (Claude, Goose, etc.) automatically. The server generates metadata for both protocols with no code changes required.

| Protocol | Name | MIME Type |
|----------|------|-----------|
| ChatGPT | OpenAI Apps SDK | `text/html+skybridge` |
| MCP Apps | SEP-1865 Extension | `text/html;profile=mcp-app` |

---

## Project Setup for MCP Apps

### Scaffold with create-mcp-use-app

```bash
npx create-mcp-use-app my-app --template mcp-apps --no-skills
cd my-app
npx mcp-use dev
```

This creates a project pre-configured for widget development with React, Tailwind, and all necessary tooling. For the first verification pass, run `npm run build`, `npx mcp-use generate-types`, then `npx mcp-use dev`.

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
import React from "react";
import { z } from "zod";

const propSchema = z.object({
  city: z.string().describe("The city name"),
  temperature: z.number().describe("Temperature in Celsius"),
  conditions: z.string().describe("Weather conditions"),
  humidity: z.number().describe("Humidity percentage"),
  windSpeed: z.number().describe("Wind speed in km/h"),
});

// Metadata for LLM and host
export const widgetMetadata: WidgetMetadata = {
  description: "Display weather information with dual-protocol support (works with ChatGPT and MCP Apps clients)",
  props: propSchema,
  exposeAsTool: false,
  metadata: {
    csp: {
      connectDomains: ["https://api.weather.com"],
      resourceDomains: ["https://cdn.weather.com"],
      scriptDirectives: ["'unsafe-eval'"], // Required for React runtime
    },
    prefersBorder: true,
    autoResize: true,
  },
};

type WeatherProps = z.infer<typeof propSchema>;

// Widget component
function WeatherContent() {
  const { props, isPending, theme, locale, timeZone, maxWidth, maxHeight, userAgent, safeArea } =
    useWidget<WeatherProps>();

  const isDark = theme === "dark";

  if (isPending) {
    return (
      <div className={`rounded-3xl p-8 ${isDark ? "bg-gray-900" : "bg-gray-50"}`}>
        <div className="flex items-center justify-center">
          <div className={`animate-spin rounded-full h-12 w-12 border-b-2 ${isDark ? "border-purple-400" : "border-purple-600"}`} />
        </div>
      </div>
    );
  }

  return (
    <div className={`rounded-3xl p-8 ${isDark ? "bg-gray-900 text-white" : "bg-white text-gray-900"}`}>
      <h2 className="text-3xl font-bold">{props.city}</h2>
      <p className="text-5xl font-bold">{props.temperature}°C</p>
      <p className="capitalize">{props.conditions}</p>
      <div className="grid grid-cols-2 gap-4 mt-4">
        <div>Humidity: {props.humidity}%</div>
        <div>Wind: {props.windSpeed} km/h</div>
      </div>
    </div>
  );
}

// Default export wrapped in McpUseProvider
export default function Widget() {
  return (
    <McpUseProvider autoSize debugger viewControls>
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
        invoking: "Fetching weather data...",
        invoked: "Weather data loaded",
      },
    },
    async ({ city }) => {
      const data = await fetchWeather(city);
      return widget({
        props: { city, temperature: data.temp, conditions: data.conditions },
        message: `Current weather in ${city}: ${data.conditions}, ${data.temp}°C`,
      });
    }
  );
}
```

### 2. The `widget()` Response Helper

The `widget()` function creates a `CallToolResult` with three visibility channels:

| Field | LLM sees? | Widget sees? | Populated by |
|-------|-----------|-------------|-------------|
| `content` | **Yes** | Yes | `output`, `message`, or `text()` |
| `structuredContent` | **Host-dependent; yes in ChatGPT/OpenAI Apps** | Yes (as `props`) | `props` |
| `_meta` | **No** | Yes (as `metadata`) | `metadata` |

```typescript
import { widget, text } from "mcp-use/server";

return widget({
  props: { city: "Paris", temperature: 22 },       // → useWidget().props; model-safe
  output: text("Weather in Paris: 22°C, Sunny"),    // → LLM sees this
  metadata: { lastUpdated: Date.now() },            // → useWidget().metadata; private/client-only
});

// Shorthand — message is equivalent to text()
return widget({
  props: { city: "Paris", temperature: 22 },
  message: "Weather in Paris: 22°C, Sunny",
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
    return widget({ props: await loadDashboard(), message: "Dashboard loaded" });
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
  props,                // Partial<TProps> — server-computed data (structuredContent); {} while isPending
  toolInput,            // TProps | null — complete tool args the LLM sent (available after tool completes)
  isPending,            // true while tool executes
  isStreaming,          // true while LLM streams tool arguments (false in ChatGPT Apps SDK)
  partialToolInput,     // Partial<TProps> | null — incremental args during streaming
  output,               // TOutput | null — tool output (LLM-visible content)
  metadata,             // TMetadata | null — response metadata (_meta)
  theme,                // "light" | "dark" (default: "light")
  displayMode,          // "inline" | "pip" | "fullscreen" (default: "inline")
  locale,               // string — BCP 47 locale (default: "en")
  timeZone,             // string — IANA timezone (e.g. "America/New_York")
  safeArea,             // { insets: { top, right, bottom, left } } — mobile insets
  maxHeight,            // number — max widget height in pixels (default: 600)
  maxWidth,             // number | undefined — max widget width (MCP Apps only)
  mcp_url,              // string — MCP server base URL
  userAgent,            // { device: { type }, capabilities: { hover, touch } }
  hostInfo,             // { name: string, version: string } | undefined — MCP Apps only
  hostCapabilities,     // Record<string, unknown> | undefined — MCP Apps only
  isAvailable,          // true when provider is connected and ready
  state, setState,      // Persistent state (survives page reload)
  callTool,             // Call another MCP tool
  sendFollowUpMessage,  // Send message to chat (string or MessageContentBlock[])
  openExternal,         // Open URL in browser
  requestDisplayMode,   // Request fullscreen/pip/inline
  notifyIntrinsicHeight, // Tell host about content height
} = useWidget();
```

### `useCallTool()` — Tool Calling

```tsx
const { callTool, callToolAsync, data, isPending, isError, error } = useCallTool("search");

// Fire-and-forget
callTool({ query: "shoes" }, {
  onSuccess: (result, input) => console.log(result.structuredContent),
  onError: (err, input) => console.error(err),
  onSettled: (result, err, input) => {/* runs after success or error */},
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

// Message shorthand (equivalent to text)
return widget({ props: data, message: `Found ${data.length} items` });

// Structured JSON output: use only when the model/client needs typed fields
return widget({ props: data, output: object({ count: data.length, summary }) });
```

---

## Programmatic UI Resources

For simple HTML widgets without a React build step, use `server.uiResource()`:

```typescript
server.uiResource({
  type: "mcpApps",
  name: "greeting-card",
  title: "Greeting Card",
  description: "Shows a personalized greeting message",
  props: {
    name: { type: "string", required: true, description: "Name to greet" },
    greeting: { type: "string", required: true, description: "Greeting message" },
  },
  htmlTemplate: `
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body>
      <div id="greeting">Hello</div>
      <div id="name">World</div>
      <script>
        const params = new URLSearchParams(window.location.search);
        const propsJson = params.get('props');
        if (propsJson) {
          const props = JSON.parse(propsJson);
          document.getElementById('greeting').textContent = props.greeting || 'Hello';
          document.getElementById('name').textContent = props.name || 'World';
        }
      </script>
    </body>
    </html>
  `,
  metadata: {
    prefersBorder: true,
    widgetDescription: "A colorful greeting card with personalized message",
  },
  exposeAsTool: true,  // Auto-expose as a callable tool
});
```

---

## OpenAI Apps SDK Integration

For ChatGPT-compatible clients, mcp-use automatically adapts the protocol:

```typescript
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
