# MCP Apps Production Patterns

Battle-tested patterns for building production-quality MCP Apps (interactive widgets). Every pattern includes the problem it solves and complete implementation code.

> **Note:** `mcp-use` v1.15.0+ supports dual-protocol MCP Apps — the same widget works in ChatGPT (Apps SDK) and MCP Apps-compatible clients (Claude, Goose, etc.) via `type: "mcpApps"`.

---

## Dual-Protocol Architecture

MCP Apps widgets work across both MCP Apps clients and ChatGPT — the same widget code runs in both environments. The `useWidget` hook abstracts the underlying protocol.

### Protocol Differences

| Aspect | MCP Apps (SEP-1865) | ChatGPT (Apps SDK) |
|--------|--------------------|--------------------|
| Communication | JSON-RPC 2.0 over `postMessage` | `window.openai` bridge API |
| MIME type | `text/html;profile=mcp-app` | `text/html+skybridge` |
| CSP format | camelCase (`connectDomains`) | snake_case (`connect_domains`) |
| Metadata prefix | Standard `_meta.ui.*` namespace | `openai/*` prefixed keys |
| Theme | Sent via `postMessage` | `window.openai.theme` |
| Architecture | Double-iframe sandbox | Single iframe |

### How It Works

```
┌─────────────────────────────────────────────┐
│  Your Widget Code (React + useWidget)       │
├─────────────────────────────────────────────┤
│  useWidget() Hook (protocol abstraction)    │
├──────────────────┬──────────────────────────┤
│  MCP Apps Bridge │  ChatGPT Apps SDK Bridge │
│  (postMessage)   │  (window.openai)         │
├──────────────────┼──────────────────────────┤
│  MCP Client      │  ChatGPT                 │
└──────────────────┴──────────────────────────┘
```

Your widget code never needs to know which protocol is active — the hooks handle detection and adaptation automatically.

### Registering a Dual-Protocol Widget

Use `type: "mcpApps"` on `server.uiResource()`. The server auto-generates metadata for both protocols.

```typescript
import { MCPServer } from "mcp-use/server";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  baseUrl: process.env.MCP_URL || "http://localhost:3000",
});

server.uiResource({
  type: "mcpApps",               // enables dual-protocol: works with ChatGPT AND MCP Apps clients
  name: "weather-display",
  htmlTemplate: `
    <!DOCTYPE html>
    <html>
      <head><meta charset="UTF-8"><title>Weather</title></head>
      <body><div id="root"></div>
        <script type="module" src="/resources/weather-display.js"></script>
      </body>
    </html>
  `,
  metadata: {
    csp: {
      connectDomains: ["https://api.weather.com"],
      resourceDomains: ["https://cdn.weather.com"],
      scriptDirectives: ["'unsafe-eval'"],  // required for React runtime (eval in bundles)
    },
    prefersBorder: true,
    autoResize: true,                        // MCP Apps clients use this
    widgetDescription: "Shows current weather conditions",  // ChatGPT uses this
    invoking: "Fetching weather data...",
    invoked: "Weather data loaded",
  },
});
```

Widgets defined in `resources/<name>/widget.tsx` are discovered and registered automatically — no manual `server.uiResource()` call is needed.

### Auto-Discovered Widget with Metadata

```typescript
// resources/weather-display/widget.tsx
import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

const propSchema = z.object({
  city: z.string().describe("The city name"),
  temperature: z.number().describe("Temperature in Celsius"),
  conditions: z.string().describe("Weather conditions"),
  humidity: z.number().describe("Humidity percentage"),
  windSpeed: z.number().describe("Wind speed in km/h"),
});

export const widgetMetadata: WidgetMetadata = {
  description: "Display weather information with dual-protocol support",
  props: propSchema,
  exposeAsTool: false,  // only used through custom tools
  metadata: {
    csp: {
      connectDomains: ["https://api.weather.com"],
      resourceDomains: ["https://cdn.weather.com"],
      scriptDirectives: ["'unsafe-eval'"],
    },
    prefersBorder: true,
    autoResize: true,
    widgetDescription: "Interactive weather card showing temperature and conditions",
  },
};

const WeatherDisplay: React.FC = () => {
  const { props, isPending, theme } = useWidget<z.infer<typeof propSchema>>();
  const isDark = theme === "dark";

  if (isPending) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600" />
      </div>
    );
  }

  return (
    <McpUseProvider autoSize>
      <div className={`rounded-3xl p-8 ${isDark ? "bg-gray-900 text-white" : "bg-purple-50 text-gray-900"}`}>
        <h2 className="text-3xl font-bold">{props.city}</h2>
        <p>{props.conditions}</p>
        <div className="text-5xl font-bold">{props.temperature}°C</div>
        <div className="grid grid-cols-2 gap-4 mt-4">
          <div><span className="text-sm">Humidity</span><div className="font-semibold">{props.humidity}%</div></div>
          <div><span className="text-sm">Wind</span><div className="font-semibold">{props.windSpeed} km/h</div></div>
        </div>
      </div>
    </McpUseProvider>
  );
};

export default WeatherDisplay;
```

---

## Connecting a Tool to a Widget

Use the `widget` field on `server.tool()` to link a tool to a widget. Return `widget()` from the handler.

```typescript
import { MCPServer, widget, text } from "mcp-use/server";
import { z } from "zod";

server.tool(
  {
    name: "get-weather",
    description: "Get current weather for a city",
    schema: z.object({
      city: z.string().describe("City name"),
    }),
    widget: {
      name: "weather-display",
      invoking: "Fetching weather data...",
      invoked: "Weather data loaded",
    },
  },
  async ({ city }) => {
    const weather = await fetchWeather(city);

    return widget({
      // LLM-visible text summary (goes into conversation context)
      output: text(`Current weather in ${city}: ${weather.conditions}, ${weather.temperature}°C`),
      // Model-safe widget data (goes into structuredContent)
      props: { city, ...weather },
    });
  }
);
```

### Data Flow

| Field | LLM sees? | Widget sees? | Purpose |
|-------|-----------|--------------|---------|
| `output` (via `content`) | Yes | Yes (`props` fallback) | Text summary for model context |
| `props` (via `structuredContent`) | Host-dependent; yes in ChatGPT/OpenAI Apps | Yes (as `props`) | Model-safe data for widget rendering |
| `_meta` | No | Yes (as `metadata`) | Private/client-only protocol metadata |

---

## Widget Lifecycle Pattern

Understanding the widget lifecycle is critical for building responsive UIs.

### Lifecycle Stages

```
Mount → Pending → Streaming (optional) → Ready → Interaction → Unmount
```

1. **Mount** — Component renders, `isPending=true`, `props={}` (empty partial)
2. **Streaming** (if LLM streams tool args) — `isStreaming=true`, `partialToolInput` updates incrementally
3. **Ready** — `isPending=false`, full `props` available from `structuredContent`
4. **Interaction** — User interacts: `callTool`, `setState`, `sendFollowUpMessage`, `openExternal`
5. **Unmount** — React cleanup; no special handling needed

### Lifecycle-Aware Component

```tsx
import { useWidget } from "mcp-use/react";

interface ProductProps {
  name: string;
  price: number;
  description: string;
  imageUrl: string;
}

const ProductCard: React.FC = () => {
  const { props, isPending, isStreaming, partialToolInput } = useWidget<ProductProps>();

  // Stage 1: Mount / Pending — show skeleton (no data yet)
  if (isPending && !partialToolInput) {
    return (
      <div className="animate-pulse space-y-3 p-4">
        <div className="h-48 bg-gray-200 rounded" />
        <div className="h-4 bg-gray-200 rounded w-3/4" />
        <div className="h-4 bg-gray-200 rounded w-1/2" />
      </div>
    );
  }

  // Stage 2: Streaming — show partial data as it arrives
  if (isStreaming && partialToolInput) {
    return (
      <div className="p-4 opacity-80">
        <h2>{partialToolInput.name ?? "Loading..."}</h2>
        {partialToolInput.price && <p>${partialToolInput.price}</p>}
        <div className="text-sm text-gray-400">Streaming...</div>
      </div>
    );
  }

  // Stage 3+: Ready — full rendering
  return (
    <div className="p-4">
      <img src={props.imageUrl} alt={props.name} />
      <h2>{props.name}</h2>
      <p className="text-lg font-bold">${props.price}</p>
      <p>{props.description}</p>
    </div>
  );
};
```

---

## State Management Patterns

### Persistent State vs Local State

| State Type | Mechanism | Survives Reload | Use Case |
|------------|-----------|-----------------|----------|
| Persistent | `useWidget().state / setState` | Yes | User preferences, saved selections, favorites |
| Local | React `useState` | No | UI toggles, form input, hover states |

**ChatGPT:** `setState` calls `window.openai.setWidgetState()`.
**MCP Apps:** `setState` updates local React state and sends `ui/update-model-context` to the host.

### Persistent State Pattern

```tsx
import { useWidget } from "mcp-use/react";

interface AppState {
  favorites: string[];
  sortOrder: "asc" | "desc";
  lastViewedId: string | null;
}

const MyWidget: React.FC = () => {
  const { state, setState } = useWidget<unknown, unknown, unknown, AppState>();

  const addFavorite = async (id: string) => {
    await setState((prev) => ({
      ...prev,
      favorites: [...(prev?.favorites ?? []), id],
    }));
  };

  const toggleSort = async () => {
    await setState((prev) => ({
      ...prev,
      sortOrder: prev?.sortOrder === "asc" ? "desc" : "asc",
    }));
  };

  return (
    <div>
      <button onClick={toggleSort}>Sort: {state?.sortOrder ?? "asc"}</button>
      <p>Favorites: {state?.favorites?.length ?? 0}</p>
    </div>
  );
};
```

### Combined State Pattern (persistent + local)

```tsx
import { useState } from "react";
import { useWidget } from "mcp-use/react";

const SearchWidget: React.FC = () => {
  const { state, setState } = useWidget<unknown, unknown, unknown, { history: string[] }>();
  const { callTool } = useWidget();

  // Local state: transient UI
  const [query, setQuery] = useState("");
  const [isExpanded, setIsExpanded] = useState(false);

  const handleSearch = async () => {
    await callTool("search", { query });
    // Persist to widget state for reload survival
    await setState((prev) => ({
      history: [...(prev?.history ?? []), query].slice(-10),
    }));
    setQuery("");
  };

  return (
    <div>
      <input value={query} onChange={(e) => setQuery(e.target.value)} />
      <button onClick={handleSearch}>Search</button>
      <button onClick={() => setIsExpanded(!isExpanded)}>
        {isExpanded ? "Hide" : "Show"} History
      </button>
      {isExpanded && (
        <ul>{state?.history?.map((q, i) => <li key={i}>{q}</li>)}</ul>
      )}
    </div>
  );
};
```

---

## Theme-Aware Component Pattern

Always use `theme` from `useWidget()` to match the host app's appearance. `McpUseProvider` sets the Tailwind `dark` class automatically.

```tsx
import { useWidget } from "mcp-use/react";

const ThemedCard: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => {
  const { theme } = useWidget();

  const isDark = theme === "dark";
  const styles = {
    container: {
      backgroundColor: isDark ? "#1a1a2e" : "#ffffff",
      color: isDark ? "#e0e0e0" : "#333333",
      border: `1px solid ${isDark ? "#333" : "#e0e0e0"}`,
      borderRadius: "8px",
      padding: "16px",
    },
  };

  return (
    <div style={styles.container}>
      <h3>{title}</h3>
      {children}
    </div>
  );
};
```

### Tailwind CSS + Dark Mode (preferred)

```tsx
// ThemeProvider (inside McpUseProvider) sets the `dark` class on <html>
const Card: React.FC = () => (
  <div className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
    <h3 className="text-lg font-semibold">Dashboard</h3>
    <p className="text-gray-600 dark:text-gray-400">System metrics</p>
  </div>
);
```

---

## Loading State Pattern (Skeleton UI)

Show meaningful loading states that match the final content layout.

```tsx
import { useWidget } from "mcp-use/react";

interface DataProps {
  title: string;
  items: Array<{ id: string; name: string; value: number }>;
  summary: string;
}

const DataWidget: React.FC = () => {
  const { isPending, isStreaming, partialToolInput, props } = useWidget<DataProps>();

  // Pure skeleton — no data yet
  if (isPending && !partialToolInput) {
    return (
      <div className="animate-pulse space-y-4 p-4">
        <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/3" />
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex justify-between">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4" />
          </div>
        ))}
      </div>
    );
  }

  // Use streaming data while streaming, full props when ready
  const displayData = isStreaming ? partialToolInput : props;

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold">{displayData?.title ?? "Loading..."}</h2>
      <ul className="space-y-2 my-4">
        {(displayData?.items ?? []).map((item) => (
          <li key={item.id} className="flex justify-between">
            <span>{item.name}</span>
            <span className="font-mono">{item.value}</span>
          </li>
        ))}
      </ul>
      {displayData?.summary && <p className="text-gray-600">{displayData.summary}</p>}
      {isStreaming && <div className="text-sm text-blue-500 animate-pulse">Loading more data...</div>}
    </div>
  );
};
```

---

## Multi-Tool Widget Pattern

Widgets that orchestrate multiple tool calls for complex interactions.

```tsx
import { useWidget, useCallTool } from "mcp-use/react";

interface ProductListProps {
  products: Array<{ id: string; name: string; price: number; thumbnail: string }>;
  category: string;
}

const ProductBrowser: React.FC = () => {
  const { props, isPending, theme } = useWidget<ProductListProps>();
  const { callToolAsync: getDetails, data: details, isPending: loadingDetails } = useCallTool("get-product-details");
  const { callTool: addFavorite, isPending: savingFav } = useCallTool("add-favorite");
  const { callTool: addToCart, isPending: addingToCart } = useCallTool("add-to-cart");

  if (isPending) return <div className="animate-pulse p-4">Loading products...</div>;

  return (
    <div className={theme === "dark" ? "bg-gray-900" : "bg-white"}>
      <h2>{props.category} Products</h2>
      <div className="grid grid-cols-2 gap-4">
        {props.products?.map((product) => (
          <div key={product.id} className="border rounded p-3">
            <img src={product.thumbnail} alt={product.name} />
            <h3>{product.name}</h3>
            <p>${product.price}</p>
            <div className="flex gap-2 mt-2">
              <button onClick={() => getDetails({ productId: product.id })} disabled={loadingDetails}>Details</button>
              <button onClick={() => addFavorite({ productId: product.id })} disabled={savingFav}>♥</button>
              <button onClick={() => addToCart({ productId: product.id, quantity: 1 })} disabled={addingToCart}>Add to Cart</button>
            </div>
          </div>
        ))}
      </div>
      {details && (
        <div className="mt-4 p-4 border rounded">
          <h3>Product Details</h3>
          <pre>{JSON.stringify(details.structuredContent, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};
```

---

## Display Mode Management

Widgets can request different display modes from the host.

```tsx
import { useWidget } from "mcp-use/react";

const ExpandableChart: React.FC = () => {
  const { displayMode, requestDisplayMode, props } = useWidget();

  const isFullscreen = displayMode === "fullscreen";
  const isPip = displayMode === "pip";

  return (
    <div className={isFullscreen ? "h-screen w-full p-6" : "h-64 p-4"}>
      <div className="flex justify-between items-center mb-4">
        <h2>Analytics Dashboard</h2>
        <div className="flex gap-2">
          {!isFullscreen && !isPip && (
            <>
              <button onClick={() => requestDisplayMode("pip")} className="px-3 py-1 bg-gray-300 rounded text-sm">⧉ PiP</button>
              <button onClick={() => requestDisplayMode("fullscreen")} className="px-3 py-1 bg-blue-500 text-white rounded text-sm">⛶ Expand</button>
            </>
          )}
          {(isFullscreen || isPip) && (
            <button onClick={() => requestDisplayMode("inline")} className="px-3 py-1 bg-gray-500 text-white rounded text-sm">✕ Exit</button>
          )}
        </div>
      </div>
      <div className={isFullscreen ? "h-[calc(100%-60px)]" : "h-full"}>
        <div className="w-full h-full bg-gray-100 dark:bg-gray-800 rounded flex items-center justify-center">
          Chart ({displayMode} mode)
        </div>
      </div>
    </div>
  );
};
```

---

## CSP Configuration for Common Scenarios

Content Security Policy domains must be declared in `widgetMetadata` for external requests to work. Setting `baseUrl` (or `MCP_URL` env var) automatically injects the server origin into `connectDomains`, `resourceDomains`, and `baseUriDomains`.

### CSP Field Reference

| Field | Description |
|-------|-------------|
| `connectDomains` | Domains allowed for fetch, XHR, WebSocket |
| `resourceDomains` | Domains for scripts, styles, images |
| `baseUriDomains` | Base-URI domains (MCP Apps only) |
| `frameDomains` | Domains permitted for iframe embeds |
| `redirectDomains` | Domains for redirects (ChatGPT-specific) |
| `scriptDirectives` | Custom script CSP directives (e.g. `'unsafe-eval'` for React) |
| `styleDirectives` | Custom style CSP directives |

### External REST API

```typescript
export const widgetMetadata: WidgetMetadata = {
  description: "Widget that fetches data from an API",
  props: z.object({ query: z.string() }),
  metadata: {
    csp: {
      connectDomains: ["https://api.example.com", "https://api.backup.example.com"],
    },
  },
};
```

### CDN Images and Scripts

```typescript
export const widgetMetadata: WidgetMetadata = {
  description: "Widget with external images",
  props: z.object({ items: z.array(z.any()) }),
  metadata: {
    csp: {
      resourceDomains: [
        "https://cdn.example.com",
        "https://images.unsplash.com",
        "https://cdn.jsdelivr.net",
      ],
    },
  },
};
```

### Multiple External Services + React Runtime

```typescript
export const widgetMetadata: WidgetMetadata = {
  description: "Widget with maps and external data",
  props: z.object({ location: z.string() }),
  metadata: {
    csp: {
      connectDomains: ["https://api.mapbox.com", "https://api.analytics.example.com"],
      resourceDomains: ["https://api.mapbox.com", "https://tiles.mapbox.com"],
      scriptDirectives: ["'unsafe-eval'"],  // required for bundled React runtime
    },
    prefersBorder: false,
  },
};
```

---

## Migration from `appsSdk` to `mcpApps`

To gain dual-protocol support (MCP Apps + ChatGPT), migrate from `type: "appsSdk"` to `type: "mcpApps"`.

```typescript
// Before (ChatGPT-only, deprecated)
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

// After (dual-protocol: ChatGPT + MCP Apps clients)
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

**Migration checklist:**
1. Change `type` from `"appsSdk"` to `"mcpApps"`
2. Rename `appsSdkMetadata` to `metadata`
3. Convert CSP fields to camelCase (`connect_domains` → `connectDomains`, `resource_domains` → `resourceDomains`)
4. Remove `"openai/"` prefix from all keys (`"openai/widgetPrefersBorder"` → `prefersBorder`)
5. Test in both environments (ChatGPT + MCP Inspector)

---

## Widget-to-Widget Communication

Widgets communicate indirectly through shared MCP tools and persistent state.

```tsx
// Widget A: Settings panel saves preference via tool
const SettingsWidget: React.FC = () => {
  const { callTool } = useWidget();

  const updateLayout = async (layout: string) => {
    await callTool("save-setting", { key: "dashboardLayout", value: layout });
  };

  return (
    <div>
      <button onClick={() => updateLayout("compact")}>Compact</button>
      <button onClick={() => updateLayout("detailed")}>Detailed</button>
    </div>
  );
};

// Widget B: Dashboard reads settings (server resolves them into props)
const DashboardWidget: React.FC = () => {
  const { props } = useWidget<{ layout: string; data: unknown[] }>();
  return <div className={props.layout === "compact" ? "text-sm" : "text-base"}>...</div>;
};
```

---

## Error Handling Pattern

Combine `ErrorBoundary` for render errors with `try/catch` for tool call errors.

```tsx
import { useWidget, useCallTool } from "mcp-use/react";
import { useState } from "react";

const RobustWidget: React.FC = () => {
  const { props, isPending } = useWidget();
  const { callToolAsync } = useCallTool("process-data");
  const [error, setError] = useState<string | null>(null);

  const handleProcess = async () => {
    setError(null);
    try {
      const result = await callToolAsync({ data: props });
      if (result.isError) {
        setError("Server returned an error. Please try again.");
        return;
      }
      // handle success
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred");
    }
  };

  if (error) {
    return (
      <div className="p-4 border border-red-300 bg-red-50 dark:bg-red-900/20 rounded">
        <p className="text-red-600 dark:text-red-400">{error}</p>
        <button onClick={() => setError(null)} className="mt-2 text-sm underline">Dismiss</button>
      </div>
    );
  }

  return (
    <div>
      <button onClick={handleProcess} disabled={isPending}>Process</button>
    </div>
  );
};
```

---

## Follow-Up Message Pattern

Let users trigger chat follow-ups from inside a widget.

```tsx
import { useWidget } from "mcp-use/react";

const DataExplorer: React.FC = () => {
  const { props, sendFollowUpMessage } = useWidget<{ data: Record<string, number> }>();

  const askAbout = (metric: string) => {
    sendFollowUpMessage(`Tell me more about the ${metric} metric and what factors influence it.`);
  };

  // Also supports full content arrays (images, resources per SEP-1865):
  // sendFollowUpMessage([{ type: "text", text: "Tell me more..." }])

  return (
    <div className="p-4">
      <h2>Data Explorer</h2>
      <table className="w-full">
        <tbody>
          {Object.entries(props.data ?? {}).map(([key, value]) => (
            <tr key={key} className="border-b">
              <td className="py-2">{key}</td>
              <td className="py-2 font-mono">{value}</td>
              <td className="py-2">
                <button onClick={() => askAbout(key)} className="text-blue-500 hover:underline text-sm">
                  Ask about this →
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

---

## Host Context Fields

All fields are exposed by `useWidget()`:

| Field | Type | Description |
|-------|------|-------------|
| `theme` | `"light" \| "dark"` | Current host theme |
| `locale` | `string` | BCP 47 locale (e.g. `"en-US"`) |
| `timeZone` | `string` | IANA timezone (e.g. `"America/New_York"`) |
| `safeArea` | `{ insets: { top, right, bottom, left } }` | Safe-area insets |
| `userAgent` | `{ device: { type }, capabilities: { hover, touch } }` | Device info |
| `maxHeight` | `number` | Max available height (px) |
| `maxWidth` | `number \| undefined` | Max width (MCP Apps only) |
| `displayMode` | `"inline" \| "fullscreen" \| "pip"` | Current display mode |

---

## Performance Patterns

### Memoize Expensive Computations

```tsx
import { useMemo, useCallback, memo } from "react";
import { useWidget } from "mcp-use/react";

const DataTable: React.FC = () => {
  const { props } = useWidget<{ rows: Array<Record<string, unknown>> }>();

  const sortedRows = useMemo(
    () => [...(props.rows ?? [])].sort((a, b) => String(a.name).localeCompare(String(b.name))),
    [props.rows]
  );

  const handleRowClick = useCallback((id: string) => {
    console.log("Row clicked:", id);
  }, []);

  return (
    <div>
      {sortedRows.map((row, i) => (
        <div key={i} onClick={() => handleRowClick(String(row.id))}>
          {String(row.name)}
        </div>
      ))}
    </div>
  );
};

// Memoize child components that receive stable props
const MetricCard = memo<{ label: string; value: number }>(({ label, value }) => (
  <div className="p-3 border rounded">
    <div className="text-sm text-gray-500">{label}</div>
    <div className="text-2xl font-bold">{value}</div>
  </div>
));
MetricCard.displayName = "MetricCard";
```

### Lazy Load Heavy Components

```tsx
import { lazy, Suspense } from "react";
import { useWidget } from "mcp-use/react";

const HeavyChart = lazy(() => import("./components/HeavyChart"));

const DashboardWidget: React.FC = () => {
  const { props, displayMode } = useWidget();

  return (
    <div>
      <h2>Dashboard</h2>
      {displayMode === "fullscreen" && (
        <Suspense fallback={<div className="animate-pulse h-64 bg-gray-200 rounded" />}>
          <HeavyChart data={props} />
        </Suspense>
      )}
    </div>
  );
};
```

---

## Open External Links Pattern

Use `openExternal` to open URLs in the host's browser rather than inside the widget iframe.

```tsx
import { useWidget } from "mcp-use/react";

const LinkWidget: React.FC = () => {
  const { props, openExternal } = useWidget<{ url: string; title: string }>();

  return (
    <div className="p-4">
      <h3>{props.title}</h3>
      <button onClick={() => openExternal(props.url)} className="text-blue-500 hover:underline">
        Open in browser →
      </button>
    </div>
  );
};
```

---

## Testing Widgets

### MCP Inspector (development)

```bash
npm run dev
# Open http://localhost:3000/inspector
# Toggle CSP Mode: Permissive (dev) ↔ Widget-Declared (production behavior)
# Use device/locale/theme controls; test display modes
```

The Inspector's **CSP Mode Toggle** enforces declared CSP in Widget-Declared mode, exposing violations before they hit production.

### Manual curl testing (server tools)

```bash
# List tools (including widget-exposed tools)
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

# Call a widget tool
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get-weather","arguments":{"city":"Tokyo"}}}'
```

### Production clients

- **ChatGPT**: Enable Developer Mode → Connectors → Advanced → add your MCP server URL
- **Claude Desktop**: Add server in MCP configuration; widgets render on tool response
- **Goose**: Configure server URL; invoke tools that return widgets
