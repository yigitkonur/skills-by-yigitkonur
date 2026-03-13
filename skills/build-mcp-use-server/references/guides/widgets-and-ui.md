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

When an LLM streams tool call arguments, the widget receives partial input in real time via `partialToolInput` and `isStreaming` from `useWidget()`:

```tsx
import { useWidget } from "mcp-use/react";

const CodePreview: React.FC = () => {
  const { props, partialToolInput, isStreaming } = useWidget<{ code: string; language: string }>();
  const displayCode = isStreaming ? partialToolInput?.code ?? "" : props.code;

  return (
    <pre>
      <code className={`language-${props.language ?? "text"}`}>
        {displayCode}
        {isStreaming && <span className="cursor">▌</span>}
      </code>
    </pre>
  );
};
```

### OpenAI Apps SDK Integration — `AppsSdkAdapter`

For ChatGPT-compatible clients, mcp-use uses protocol adapters automatically:

```typescript
import { AppsSdkAdapter } from "mcp-use/server";

// Created automatically — transforms unified widget metadata to Apps SDK format:
//   MIME type → "text/html+skybridge"
//   Metadata → _meta["openai/*"] prefixed keys
//   CSP      → snake_case (connect_domains, resource_domains)
```

Manual Apps SDK metadata on a tool (advanced):

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
}, async ({ data }) => ({
  _meta: { "openai/outputTemplate": "ui://widgets/chart" },
  content: [{ type: "text", text: "Chart displayed" }],
  structuredContent: { data },
}));
```

---

## Client-Side: React Hooks and Components

Import all client-side APIs from `mcp-use/react`.

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

### `useCallTool(name)` — Tool Calling

TanStack Query-like hook with discriminated union state (`idle` → `pending` → `success` | `error`):

```tsx
import { useCallTool } from "mcp-use/react";

function SearchFlights() {
  const { callTool, callToolAsync, data, isPending, isError, error } =
    useCallTool("search-flights");

  // Fire-and-forget with callbacks
  const handleSearch = () => {
    callTool({ destination: "NYC" }, {
      onSuccess: (res) => console.log(res.structuredContent.flights),
      onError: (err) => console.error(err),
    });
  };

  // Or async/await
  const handleAsync = async () => {
    const result = await callToolAsync({ destination: "NYC" });
  };

  return (
    <div>
      <button onClick={handleSearch} disabled={isPending}>Search</button>
      {data && <pre>{JSON.stringify(data.structuredContent, null, 2)}</pre>}
    </div>
  );
}
```

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

### `useMcpServer(name)` — Get Specific Server

Retrieve a single server by ID. Returns `undefined` if not found. Throws if called outside `McpClientProvider`:

```tsx
import { useMcpServer } from "mcp-use/react";

const linear = useMcpServer("linear");
if (linear?.state === "ready") console.log(linear.tools.length);
```

### `useWidget()` — Widget State in React

Primary hook for widget components. Abstracts over three runtime providers (ChatGPT Apps SDK, MCP Apps SEP-1865 bridge, URL params fallback):

```tsx
import { useWidget } from "mcp-use/react";

interface WeatherProps { city: string; temperature: number; conditions: string }

const WeatherWidget: React.FC = () => {
  const { props, isPending, toolInput, theme, isStreaming } = useWidget<
    WeatherProps,  // Props (from structuredContent)
    {},            // State
    WeatherProps,  // Output type
    {},            // Metadata
    { city: string }  // ToolInput (tool call args)
  >();

  if (isPending) return <p>Loading...</p>;

  return (
    <div data-theme={theme}>
      <h1>{props.city}</h1>
      <p>{props.temperature}°C — {props.conditions}</p>
    </div>
  );
};
```

Key fields: `props`, `isPending`, `toolInput`, `partialToolInput`, `isStreaming`, `theme`, `displayMode`, `locale`, `timeZone`, `safeArea`, `maxHeight`, `callTool`, `sendFollowUpMessage`, `openExternal`, `requestDisplayMode`, `state`/`setState`, `metadata`.

Convenience hooks: `useWidgetProps<T>()`, `useWidgetState<T>()`, `useWidgetTheme()`.

### `generateHelpers()` — Type-Safe Helper Generation

Alternative to auto-generated types from `mcp-use dev`. Produces typed hooks from a tool map:

```typescript
import { generateHelpers } from "mcp-use/react";

type MyToolMap = {
  "search-flights": {
    input: { destination: string; date?: string };
    output: { flights: Array<{ id: string; price: number }> };
  };
};

const { useCallTool, useToolInfo } = generateHelpers<MyToolMap>();
const { callTool, data } = useCallTool("search-flights"); // fully typed
```

> **Preferred:** Use `mcp-use dev` which auto-generates types in `.mcp-use/tool-registry.d.ts`.

---

## React Components

### `McpUseProvider`

Unified provider combining StrictMode, ThemeProvider, ErrorBoundary, optional WidgetControls, and auto-sizing:

```tsx
import { McpUseProvider } from "mcp-use/react";

<McpUseProvider debugger viewControls autoSize>
  <MyWidgetContent />
</McpUseProvider>
```

### `WidgetControls`

Adds debug and view-control buttons to a widget:

```tsx
import { WidgetControls } from "mcp-use/react";

<WidgetControls debugger viewControls position="top-right">
  <div>Widget content</div>
</WidgetControls>
```

### `ErrorBoundary`

Catches React errors in the child tree and displays a fallback UI:

```tsx
import { ErrorBoundary } from "mcp-use/react";

<ErrorBoundary>
  <RiskyComponent />
</ErrorBoundary>
```

### `ThemeProvider`

Manages dark mode class on `document.documentElement`. Priority: 1) `useWidget()` theme, 2) system preference.

```tsx
import { ThemeProvider } from "mcp-use/react";

<ThemeProvider><App /></ThemeProvider>
```

### `Image`

Automatically resolves `/`-prefixed paths to the MCP public URL. Absolute URLs and `data:` URIs pass through unchanged:

```tsx
import { Image } from "mcp-use/react";

<Image src="/icons/logo.png" alt="Logo" />
// → http://localhost:3000/mcp-use/public/icons/logo.png
```

---

## Quick Reference

| Import | Package | Purpose |
|---|---|---|
| `widget`, `text`, `object` | `mcp-use/server` | Response helpers for tool handlers |
| `AppsSdkAdapter` | `mcp-use/server` | OpenAI Apps SDK protocol adapter |
| `useMcp` | `mcp-use/react` | Single-server connection hook |
| `useCallTool` | `mcp-use/react` | Tool calling with state machine |
| `McpClientProvider` | `mcp-use/react` | Multi-server provider |
| `useMcpClient` | `mcp-use/react` | Access servers map + management |
| `useMcpServer` | `mcp-use/react` | Get specific server by ID |
| `useWidget` | `mcp-use/react` | Widget state in components |
| `generateHelpers` | `mcp-use/react` | Type-safe hook factory |
| `McpUseProvider` | `mcp-use/react` | All-in-one widget provider |
| `WidgetControls` | `mcp-use/react` | Debug / view control buttons |
| `ErrorBoundary` | `mcp-use/react` | React error boundary |
| `ThemeProvider` | `mcp-use/react` | Dark mode management |
| `Image` | `mcp-use/react` | Path-resolving image component |
