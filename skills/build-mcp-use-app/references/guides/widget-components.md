# Widget Components and Hooks

Complete reference for all React components and hooks used in MCP Apps widget development. Import everything from `mcp-use/react`.

---

## `useWidget` Hook

The primary hook for widget components. Abstracts over three runtime providers (ChatGPT Apps SDK, MCP Apps SEP-1865 bridge, URL params fallback).

```typescript
import { useWidget } from "mcp-use/react";

const {
  // --- Core data ---
  props,                // Partial<TProps> — widget props from tool result (structuredContent)
  isPending,            // boolean — true while the tool executes on the server
  output,               // TOutput | null — tool output (content field)
  metadata,             // TMetadata | null — response metadata (_meta field)

  // --- Persistent state ---
  state,                // TState | null — persisted widget state (survives page reload)
  setState,             // (state: TState | ((prev) => TState)) => Promise<void>

  // --- Display ---
  theme,                // "light" | "dark"
  displayMode,          // "inline" | "pip" | "fullscreen"
  requestDisplayMode,   // (mode: "inline" | "pip" | "fullscreen") => Promise<{ mode }>
  safeArea,             // { insets: { top: number, bottom: number, left: number, right: number } }
  maxHeight,            // number (default 600)

  // --- Streaming ---
  isStreaming,           // boolean — true while LLM is streaming tool arguments
  partialToolInput,     // Partial<TProps> | null — incrementally received props during streaming

  // --- Actions ---
  callTool,             // (name: string, args: Record<string, unknown>) => Promise<CallToolResponse>
  sendFollowUpMessage,  // (content: string) => Promise<void>
  openExternal,         // (href: string) => void — open link in host browser
  notifyIntrinsicHeight, // (height: number) => Promise<void> — tell host about content height

  // --- Environment ---
  locale,               // string (default "en")
  mcp_url,              // string — MCP server base URL
  userAgent,            // { device: { type: string }, capabilities: { hover: boolean, touch: boolean } }
  hostInfo,             // { name: string, version: string } | undefined
  hostCapabilities,     // Record<string, unknown> | undefined
  isAvailable,          // boolean — true when the provider is connected and ready
} = useWidget<TProps, TOutput, TMetadata, TState>();
```

### Generic Type Parameters

```typescript
useWidget<
  TProps,     // Shape of structuredContent (what the widget renders)
  TOutput,    // Shape of the output field
  TMetadata,  // Shape of _meta
  TState      // Shape of persisted state
>()
```

### Example Usage

```tsx
import { useWidget } from "mcp-use/react";

interface WeatherProps {
  city: string;
  temperature: number;
  conditions: string;
}

interface WeatherState {
  unit: "celsius" | "fahrenheit";
}

const WeatherWidget: React.FC = () => {
  const {
    props,
    isPending,
    theme,
    state,
    setState,
    callTool,
  } = useWidget<WeatherProps, unknown, unknown, WeatherState>();

  if (isPending) return <p>Loading weather data...</p>;

  const toggleUnit = async () => {
    const newUnit = state?.unit === "fahrenheit" ? "celsius" : "fahrenheit";
    await setState({ unit: newUnit });
    await callTool("get-weather", { city: props.city, units: newUnit });
  };

  return (
    <div className={theme === "dark" ? "bg-gray-900 text-white" : "bg-white text-gray-900"}>
      <h1>{props.city}</h1>
      <p>{props.temperature}° — {props.conditions}</p>
      <button onClick={toggleUnit}>
        Switch to {state?.unit === "fahrenheit" ? "°C" : "°F"}
      </button>
    </div>
  );
};
```

---

## `useCallTool` Hook

TanStack Query-style hook for calling MCP tools from within widgets. Manages loading, success, and error states automatically.

```typescript
import { useCallTool } from "mcp-use/react";

const {
  callTool,       // (input: TInput, callbacks?) => void — fire-and-forget
  callToolAsync,  // (input: TInput) => Promise<CallToolResult> — promise-based
  data,           // CallToolResult | undefined — result when success
  isPending,      // boolean — call in flight
  isSuccess,      // boolean — call succeeded
  isError,        // boolean — call failed
  error,          // Error | undefined — error when failed
  status,         // "idle" | "pending" | "success" | "error"
  isIdle,         // boolean — no call made yet
} = useCallTool("tool-name");
```

### Return Values Reference

| Property | Type | Description |
|----------|------|-------------|
| `status` | `"idle" \| "pending" \| "success" \| "error"` | Current state machine position |
| `isIdle` | `boolean` | No call has been made yet |
| `isPending` | `boolean` | A call is in flight |
| `isSuccess` | `boolean` | Last call succeeded |
| `isError` | `boolean` | Last call failed |
| `data` | `CallToolResult \| undefined` | Result data when `isSuccess` is true |
| `error` | `Error \| undefined` | Error object when `isError` is true |
| `callTool` | `(input, callbacks?) => void` | Fire-and-forget with optional callbacks |
| `callToolAsync` | `(input) => Promise<CallToolResult>` | Promise-based for async/await usage |

### Fire-and-Forget Pattern

```tsx
import { useCallTool } from "mcp-use/react";

function SearchPanel() {
  const { callTool, data, isPending, isError, error } = useCallTool("search-products");

  const handleSearch = (query: string) => {
    callTool({ query, limit: 20 }, {
      onSuccess: (result) => console.log("Found:", result.structuredContent),
      onError: (err) => console.error("Search failed:", err),
      onSettled: (result, err) => console.log("Search completed"),
    });
  };

  return (
    <div>
      <button onClick={() => handleSearch("shoes")} disabled={isPending}>
        {isPending ? "Searching..." : "Search"}
      </button>
      {isError && <p className="text-red-500">{error?.message}</p>}
      {data && <pre>{JSON.stringify(data.structuredContent, null, 2)}</pre>}
    </div>
  );
}
```

### Async/Await Pattern

```tsx
const { callToolAsync, isPending } = useCallTool("add-to-cart");

const handleAddToCart = async (productId: string) => {
  try {
    const result = await callToolAsync({ productId, quantity: 1 });
    console.log("Added:", result.structuredContent);
    showToast("Item added to cart!");
  } catch (err) {
    showToast("Failed to add item", "error");
  }
};
```

### Multiple Tools in One Widget

```tsx
const { callTool: search, data: results, isPending: searching } = useCallTool("search-products");
const { callTool: addFav, isPending: saving } = useCallTool("add-favorite");
const { callToolAsync: getDetails } = useCallTool("get-product-details");

// Each hook manages its own state independently
```

---

## Helper Hooks

Convenience hooks that extract single values from `useWidget()`.

### `useWidgetProps<T>()`

Returns only the `props` value from `useWidget()`:

```typescript
import { useWidgetProps } from "mcp-use/react";

interface DashboardProps {
  metrics: { cpu: number; memory: number };
  serverName: string;
}

const props = useWidgetProps<DashboardProps>();
// props.metrics.cpu, props.serverName, etc.
```

### `useWidgetTheme()`

Returns the current theme (`"light"` or `"dark"`):

```typescript
import { useWidgetTheme } from "mcp-use/react";

const theme = useWidgetTheme();
// theme === "light" | "dark"
```

### `useWidgetState<T>(initialState?)`

Returns a tuple of `[state, setState]` for persistent widget state:

```typescript
import { useWidgetState } from "mcp-use/react";

interface Preferences {
  sortBy: "name" | "date" | "price";
  ascending: boolean;
}

const [prefs, setPrefs] = useWidgetState<Preferences>({
  sortBy: "name",
  ascending: true,
});

// Update with new value
await setPrefs({ sortBy: "price", ascending: false });

// Update with callback
await setPrefs((prev) => ({ ...prev, ascending: !prev.ascending }));
```

---

## `McpUseProvider`

Universal wrapper that composes all required providers and utilities for widget rendering.

```tsx
import { McpUseProvider } from "mcp-use/react";

<McpUseProvider autoSize debugger viewControls="fullscreen">
  <MyWidget />
</McpUseProvider>
```

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | `ReactNode` | *required* | Widget content to render |
| `debugger` | `boolean` | `false` | Show debug panel with props/state inspector |
| `viewControls` | `boolean \| "pip" \| "fullscreen"` | `false` | Show display mode controls |
| `autoSize` | `boolean` | `false` | Auto-report content height to host via `notifyIntrinsicHeight` |

### Internal Composition

`McpUseProvider` internally composes the following in order:

1. `StrictMode` — React strict mode for development checks
2. `ThemeProvider` — Theme synchronization with host
3. `WidgetControls` — Optional debug/view controls
4. `ErrorBoundary` — Catches render errors
5. Auto-size wrapper — Reports intrinsic height when `autoSize` is true

### Usage in widget.tsx Entry Point

```tsx
// resources/my-widget/widget.tsx
import { McpUseProvider } from "mcp-use/react";
import { MyWidgetContent } from "./components/MyWidgetContent";

export default function Widget() {
  return (
    <McpUseProvider autoSize>
      <MyWidgetContent />
    </McpUseProvider>
  );
}
```

---

## `WidgetControls`

Renders debug and view-control buttons over the widget content.

```tsx
import { WidgetControls } from "mcp-use/react";

<WidgetControls debugger viewControls position="top-right" showLabels className="custom-controls">
  <MyWidget />
</WidgetControls>
```

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | `ReactNode` | *required* | Widget content |
| `debugger` | `boolean` | `false` | Show props/state debug panel |
| `viewControls` | `boolean \| "pip" \| "fullscreen"` | `false` | Show display mode controls |
| `position` | `string` | `"top-right"` | Button position (8 options below) |
| `attachTo` | `HTMLElement` | — | Portal target for controls |
| `showLabels` | `boolean` | `false` | Show text labels on buttons |
| `className` | `string` | — | Custom CSS class for controls container |

### Position Options

`"top-left"` | `"top-center"` | `"top-right"` | `"middle-left"` | `"middle-right"` | `"bottom-left"` | `"bottom-center"` | `"bottom-right"`

---

## `ErrorBoundary`

React error boundary that catches render errors in the widget tree and displays a fallback UI.

```tsx
import { ErrorBoundary } from "mcp-use/react";

<ErrorBoundary>
  <MyWidget />
</ErrorBoundary>
```

### Behavior

- Auto-included by `McpUseProvider` — you only need this for manual provider composition
- Displays a red-bordered error message with the error description
- Logs the full error and component stack to `console.error`
- Prevents the entire widget from crashing on render errors

---

## `Image`

CSP-aware image component that resolves relative paths to the MCP server's public assets URL.

```tsx
import { Image } from "mcp-use/react";

// Relative path — resolved via window.__mcpPublicAssetsUrl or window.__mcpPublicUrl
<Image src="/fruits/apple.png" alt="Apple" />

// Absolute URL — passed through unchanged
<Image src="https://cdn.example.com/img.jpg" alt="External image" />

// Data URI — passed through unchanged
<Image src="data:image/png;base64,iVBOR..." alt="Inline image" />
```

### URL Resolution

For `/`-prefixed paths, `Image` resolves the URL using:
1. `window.__mcpPublicAssetsUrl` (set by mcp-use runtime)
2. Falls back to `window.__mcpPublicUrl`
3. Final result: `http://localhost:3000/mcp-use/public/fruits/apple.png`

Absolute URLs (`https://...`) and data URIs (`data:...`) pass through without modification.

---

## `ThemeProvider`

Manages dark/light mode synchronization between the host app and the widget.

```tsx
import { ThemeProvider } from "mcp-use/react";

<ThemeProvider>
  <MyWidget />
</ThemeProvider>
```

### Theme Resolution Priority

1. `useWidget()` theme value (from host via postMessage or Apps SDK)
2. System preference (`prefers-color-scheme: dark`)

### Behavior

- Sets the `dark` class on `document.documentElement` when dark mode is active
- Removes the `dark` class for light mode
- Compatible with Tailwind CSS `darkMode: "class"` configuration
- Auto-included by `McpUseProvider`

---

## Widget Metadata

Every widget exports metadata that tells the host and LLM about the widget's capabilities. Export `widgetMetadata` from your `widget.tsx`:

```typescript
import { type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

export const widgetMetadata: WidgetMetadata = {
  description: "Displays weather information for a city with temperature and conditions",
  props: z.object({
    city: z.string().describe("City name"),
    temperature: z.number().describe("Temperature value"),
    conditions: z.string().describe("Weather conditions description"),
  }),
  metadata: {
    csp: {
      connectDomains: ["https://api.weather.com"],
      resourceDomains: ["https://cdn.weather-icons.com"],
    },
    prefersBorder: true,
  },
};
```

### `WidgetMetadata` Fields

| Field | Type | Description |
|-------|------|-------------|
| `description` | `string` | Description shown to the LLM for tool invocation context |
| `props` | `ZodObject` | Zod schema defining the expected props shape |
| `metadata.csp.connectDomains` | `string[]` | Domains the widget can make fetch/XHR requests to |
| `metadata.csp.resourceDomains` | `string[]` | Domains the widget can load images/scripts/styles from |
| `metadata.prefersBorder` | `boolean` | Whether the host should render a border around the widget |

---

## Type Generation

### Automatic (Recommended)

When running `mcp-use dev`, types are automatically generated in `.mcp-use/tool-registry.d.ts`:

```typescript
// Auto-generated — do not edit
declare module "mcp-use/react" {
  interface ToolRegistry {
    "search-products": {
      input: { query: string; limit?: number };
      output: { results: Array<{ id: string; name: string; price: number }> };
    };
    "get-weather": {
      input: { city: string };
      output: { temperature: number; conditions: string };
    };
  }
}
```

This provides full type safety for `useCallTool`:

```typescript
const { callTool } = useCallTool("search-products");
// callTool input is typed as { query: string; limit?: number }
// data.structuredContent is typed as { results: Array<...> }
```

### Manual Type Generation

For projects not using `mcp-use dev`, use `generateHelpers`:

```typescript
import { generateHelpers } from "mcp-use/react";

type MyTools = {
  "search-products": {
    input: { query: string; limit?: number };
    output: { results: Array<{ id: string; name: string; price: number }> };
  };
  "add-to-cart": {
    input: { productId: string; quantity: number };
    output: { cartId: string; total: number };
  };
};

const { useCallTool, useToolInfo } = generateHelpers<MyTools>();

// Now fully typed:
const { callTool } = useCallTool("search-products");
// TypeScript knows the input/output shapes
```

---

## Import Summary

| Import | Purpose |
|--------|---------|
| `useWidget` | Primary widget hook — props, state, actions, theme |
| `useCallTool` | Tool calling with state machine |
| `useWidgetProps` | Convenience — just props |
| `useWidgetTheme` | Convenience — just theme |
| `useWidgetState` | Convenience — just state/setState |
| `McpUseProvider` | All-in-one provider wrapper |
| `WidgetControls` | Debug/view control overlay |
| `ErrorBoundary` | React error boundary |
| `ThemeProvider` | Dark/light mode sync |
| `Image` | CSP-aware image component |
| `generateHelpers` | Manual type-safe hook factory |
| `WidgetMetadata` | Type for widget metadata export |

All imports come from `"mcp-use/react"`.
