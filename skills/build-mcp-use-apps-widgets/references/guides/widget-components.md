# Widget Components and Hooks

Complete reference for all React components and hooks used in MCP Apps widget development. Import everything from `mcp-use/react`.

---

## `useWidget` Hook

The primary hook for widget components. Abstracts over runtime providers (ChatGPT Apps SDK, MCP Apps SEP-1865 bridge, URL params fallback).

```typescript
import { useWidget } from "mcp-use/react";

const {
  // --- Core data ---
  props,                // Partial<TProps> — server-computed widget data (from structuredContent), empty {} while isPending
  toolInput,            // TProps | null — the full tool call arguments the LLM sent (available after tool completes)
  isPending,            // boolean — true while the tool executes on the server
  output,               // TOutput | null — tool output (content field, visible to LLM)
  metadata,             // TMetadata | null — response metadata (_meta field)

  // --- Persistent state ---
  state,                // TState | null — persisted widget state (survives page reload)
  setState,             // (state: TState | ((prev: TState | null) => TState)) => Promise<void>

  // --- Display ---
  theme,                // "light" | "dark" (default: "light")
  displayMode,          // "inline" | "pip" | "fullscreen" (default: "inline")
  requestDisplayMode,   // (mode: "inline" | "pip" | "fullscreen") => Promise<{ mode }>
  safeArea,             // { insets: { top: number, bottom: number, left: number, right: number } }
  maxHeight,            // number — maximum height available in pixels (default: 600)
  maxWidth,             // number | undefined — maximum width available (MCP Apps only)

  // --- Streaming ---
  isStreaming,          // boolean — true while LLM is streaming tool arguments (false in ChatGPT Apps SDK)
  partialToolInput,     // Partial<TProps> | null — incremental args during streaming; null in ChatGPT Apps SDK

  // --- Actions ---
  callTool,             // (name: string, args: Record<string, unknown>) => Promise<CallToolResponse>
  sendFollowUpMessage,  // (content: string | MessageContentBlock[]) => Promise<void>
  openExternal,         // (href: string) => void — open link in host browser
  notifyIntrinsicHeight, // (height: number) => Promise<void> — tell host about content height

  // --- Environment ---
  locale,               // string — BCP 47 locale (default "en")
  timeZone,             // string — IANA timezone (e.g. "America/New_York")
  mcp_url,              // string — MCP server base URL
  userAgent,            // { device: { type: string }, capabilities: { hover: boolean, touch: boolean } }
  hostInfo,             // { name: string, version: string } | undefined — MCP Apps only
  hostCapabilities,     // Record<string, unknown> | undefined — MCP Apps only; undefined in ChatGPT Apps SDK
  isAvailable,          // boolean — true when the provider is connected and ready
} = useWidget<TProps, TOutput, TMetadata, TState>();
```

### Hook Signature

```typescript
useWidget<
  TProps = {},      // Shape of the tool input args (LLM-visible); also the shape of props (server-computed structuredContent)
  TOutput = any,    // Shape of the output field (LLM-visible content)
  TMetadata = any,  // Shape of _meta
  TState = any      // Shape of persisted widget state
>(): UseWidgetResult<TProps, TOutput, TMetadata, TState>
```

### Default Values

| Property | Default |
|----------|---------|
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

### Widget Lifecycle

1. **First render** — `isPending = true`, `props = {}`, `output`/`metadata` = `null`. Show loading UI.
2. **(Optional) Streaming phase** — `isStreaming = true`, `partialToolInput` updates in real time as LLM streams args.
3. **After tool completes** — `isPending = false`, `props`/`output`/`metadata` populated; component re-renders.

### Basic Usage

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

### Streaming Tool Arguments Example

```tsx
import { useWidget } from "mcp-use/react";

const CodePreviewWidget: React.FC = () => {
  const {
    props,
    isPending,
    isStreaming,
    partialToolInput,
  } = useWidget<{ code: string; language: string }>();

  if (isPending && !partialToolInput) return <div className="animate-spin" />;

  const displayCode = isStreaming && partialToolInput?.code != null
    ? partialToolInput.code
    : props.code ?? "";
  const displayLang = (isStreaming ? partialToolInput?.language : props.language) ?? "text";

  return (
    <pre data-language={displayLang}>
      {displayCode || "Waiting for input…"}
    </pre>
  );
};
```

### Complete Example (with state, actions, layout)

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
  } = useWidget<ProductProps, ProductOutput, {}, ProductState>();

  const handleAddToFavorites = async () => {
    const newFavs = [...(state?.favorites ?? []), props.productId];
    await setState({ favorites: newFavs });
  };

  const handleGetReviews = async () => {
    await callTool("get-product-reviews", { productId: props.productId });
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

### Hook Signature

```typescript
function useCallTool<ToolName extends string = string>(
  toolName: ToolName
): {
  status: "idle" | "pending" | "success" | "error";
  isIdle: boolean;
  isPending: boolean;
  isSuccess: boolean;
  isError: boolean;
  data?: CallToolResult;
  error?: Error;
  callTool: (input: ToolInput<ToolName>, callbacks?: CallToolCallbacks<ToolName>) => void;
  callToolAsync: (input: ToolInput<ToolName>) => Promise<CallToolResult>;
}
```

### Supporting Types

```typescript
interface CallToolResult {
  content: Array<TextContent | ImageContent | EmbeddedResource>;
  isError?: boolean;
  structuredContent?: any;   // Strongly typed when tool types are generated
  metadata?: Record<string, unknown>;
}

interface CallToolCallbacks<T> {
  onSuccess?: (data: CallToolResult, input: ToolInput<T>) => void;
  onError?:   (error: Error, input: ToolInput<T>) => void;
  onSettled?: (data?: CallToolResult, error?: Error, input: ToolInput<T>) => void;
}
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
      onSuccess: (result, input) => console.log("Found:", result.structuredContent),
      onError: (err, input) => console.error("Search failed:", err),
      onSettled: (result, err, input) => console.log("Search completed"),
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

Universal wrapper that composes all required providers and utilities for widget rendering. Protocol-agnostic: works unchanged in MCP Apps and ChatGPT Apps SDK environments.

```tsx
import { McpUseProvider } from "mcp-use/react";

<McpUseProvider autoSize debugger viewControls="fullscreen">
  <MyWidget />
</McpUseProvider>
```

### Props

| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `children` | `ReactNode` | — | **yes** | Widget content to render |
| `debugger` | `boolean` | `false` | no | Show debug panel with props/state inspector |
| `viewControls` | `boolean \| "pip" \| "fullscreen"` | `false` | no | `true` shows both fullscreen & PiP; `"pip"` shows only PiP; `"fullscreen"` shows only fullscreen |
| `autoSize` | `boolean` | `false` | no | Automatically notify the host about container height changes using ResizeObserver |

### Internal Composition

`McpUseProvider` internally composes the following in order:

1. `StrictMode` — React strict mode for development checks
2. `ThemeProvider` — Theme synchronization with host
3. `WidgetControls` — Optional debug/view controls (when `debugger` or `viewControls` are truthy)
4. `ErrorBoundary` — Catches render errors (innermost)
5. Auto-size wrapper — Reports intrinsic height when `autoSize` is true

### Breaking Change (v1.20.1)

`McpUseProvider` no longer includes `BrowserRouter`. If your widget uses `react-router` for navigation, add it explicitly:

```tsx
import { BrowserRouter } from "react-router";

<McpUseProvider>
  <BrowserRouter>
    <MyWidget />
  </BrowserRouter>
</McpUseProvider>
```

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

| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `children` | `ReactNode` | — | **yes** | Widget content |
| `debugger` | `boolean` | `false` | no | Show props/state debug panel |
| `viewControls` | `boolean \| "pip" \| "fullscreen"` | `false` | no | Show display mode controls |
| `position` | `"top-left" \| "top-center" \| "top-right" \| "center-left" \| "center-right" \| "bottom-left" \| "bottom-center" \| "bottom-right"` | `"top-right"` | no | Position of the control buttons |
| `attachTo` | `HTMLElement \| null` | `undefined` | no | Element to attach controls to (for custom positioning) |
| `showLabels` | `boolean` | `true` | no | Show text labels on buttons |
| `className` | `string` | `""` | no | Custom CSS class for controls container |

### Debug Button Overlay

The debug button opens an overlay showing:
- Props, tool output, response metadata, widget state
- Theme, display mode, safe area insets, user agent, locale
- All keys on `window.openai`
- Interactive testing: call tool, send follow-up, open external URL, set state

### Position Examples

```tsx
// Top right (default)
<WidgetControls position="top-right" debugger>
  <MyWidget />
</WidgetControls>

// Bottom left
<WidgetControls position="bottom-left" viewControls>
  <MyWidget />
</WidgetControls>

// Center right, only PiP control
<WidgetControls position="center-right" viewControls="pip">
  <MyWidget />
</WidgetControls>
```

---

## `ErrorBoundary`

React error boundary that catches render errors in the widget tree and displays a fallback UI.

```tsx
import { ErrorBoundary } from "mcp-use/react";

<ErrorBoundary>
  <MyWidget />
</ErrorBoundary>
```

### Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `children` | `ReactNode` | **yes** | The widget content to wrap |

### Behavior

- Auto-included by `McpUseProvider` — you only need this for manual provider composition
- Displays a red-bordered error message with the error description (dark-mode-aware styling)
- Logs the full error object and component stack to `console.error`
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

### Props

| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `src` | `string` | — | **yes** | Image source URL or path |
| `alt` | `string` | `""` | no | Alternate text for the image |
| *(all standard `img` attributes)* | various | — | no | Any valid `<img>` attribute (e.g., `width`, `height`, `loading`, `className`) |

### URL Resolution

For `/`-prefixed paths, `Image` resolves the URL using (in priority order):
1. `window.__mcpPublicAssetsUrl` (set by mcp-use runtime for static deployments)
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

### Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `children` | `ReactNode` | **yes** | The widget content to wrap |

### Theme Resolution Priority

1. Widget theme from `window.openai.theme` (when Apps SDK is available — ChatGPT)
2. System preference (`prefers-color-scheme: dark`) — fallback when widget API is not available

### Behavior

- Sets the `dark` class on `document.documentElement` when dark mode is active
- Removes the `dark` class for light mode
- Uses `useLayoutEffect` to apply theme synchronously before browser paint, preventing flash
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
  exposeAsTool: false,  // Set to true to auto-expose widget as a callable tool
  metadata: {
    csp: {
      connectDomains: ["https://api.weather.com"],
      resourceDomains: ["https://cdn.weather-icons.com"],
      scriptDirectives: ["'unsafe-eval'"],  // Required for React runtime
    },
    prefersBorder: true,
    autoResize: true,
  },
};
```

### `WidgetMetadata` Fields

| Field | Type | Description |
|-------|------|-------------|
| `description` | `string` | Description shown to the LLM for tool invocation context |
| `props` | `ZodObject` | Zod schema defining the expected props shape |
| `exposeAsTool` | `boolean` | Whether to auto-expose widget as a callable tool |
| `metadata.csp.connectDomains` | `string[]` | Domains the widget can make fetch/XHR/WebSocket requests to |
| `metadata.csp.resourceDomains` | `string[]` | Domains the widget can load images/scripts/styles from |
| `metadata.csp.baseUriDomains` | `string[]` | Domains for base URI (MCP Apps) |
| `metadata.csp.frameDomains` | `string[]` | Domains the widget can embed in iframes |
| `metadata.csp.redirectDomains` | `string[]` | Domains for redirects (ChatGPT-specific) |
| `metadata.csp.scriptDirectives` | `string[]` | Custom script CSP directives |
| `metadata.csp.styleDirectives` | `string[]` | Custom style CSP directives |
| `metadata.prefersBorder` | `boolean` | Whether the host should render a border around the widget |
| `metadata.autoResize` | `boolean` | MCP Apps clients use this for auto-resizing |
| `metadata.invoking` | `string` | Status text shown while the tool is running |
| `metadata.invoked` | `string` | Status text shown after the tool completes |

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
