# MCP Apps Production Patterns

Battle-tested patterns for building production-quality MCP Apps (interactive widgets). Every pattern includes the problem it solves and complete implementation code.

---

## Dual-Protocol Architecture

MCP Apps widgets work across both MCP Apps clients and ChatGPT — the same widget code runs in both environments. The `useWidget` hook abstracts the underlying protocol.

### Protocol Differences

| Aspect | MCP Apps (SEP-1865) | ChatGPT (Apps SDK) |
|--------|--------------------|--------------------|
| Communication | JSON-RPC over `postMessage` | `window.openai` bridge API |
| MIME type | `text/html;profile=mcp-app` | `text/html+skybridge` |
| CSP format | camelCase (`connectDomains`) | snake_case (`connect_domains`) |
| Metadata prefix | Standard `_meta` | `openai/*` prefixed keys |
| Theme | Sent via postMessage | `window.openai.theme` |

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
5. **Unmount** — React cleanup, no special handling needed

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

  // Stage 1: Mount / Pending — show skeleton
  if (isPending && !partialToolInput) {
    return (
      <div className="animate-pulse space-y-3 p-4">
        <div className="h-48 bg-gray-200 rounded" />
        <div className="h-4 bg-gray-200 rounded w-3/4" />
        <div className="h-4 bg-gray-200 rounded w-1/2" />
      </div>
    );
  }

  // Stage 2: Streaming — show partial data
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
| Persistent | `useWidget().state / setState` | ✅ Yes | User preferences, saved selections, favorites |
| Local | React `useState` | ❌ No | UI toggles, form input, hover states |

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
      <button onClick={toggleSort}>
        Sort: {state?.sortOrder ?? "asc"}
      </button>
      <p>Favorites: {state?.favorites?.length ?? 0}</p>
    </div>
  );
};
```

### Combined State Pattern

```tsx
import { useState } from "react";
import { useWidget } from "mcp-use/react";

const SearchWidget: React.FC = () => {
  const { state, setState, callTool } = useWidget<unknown, unknown, unknown, { history: string[] }>();

  // Local state: transient UI
  const [query, setQuery] = useState("");
  const [isExpanded, setIsExpanded] = useState(false);

  const handleSearch = async () => {
    await callTool("search", { query });
    // Persist to state for reload survival
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
        <ul>
          {state?.history?.map((q, i) => <li key={i}>{q}</li>)}
        </ul>
      )}
    </div>
  );
};
```

---

## Theme-Aware Component Pattern

Always use theme from `useWidget()` to match the host app's appearance.

```tsx
import { useWidget } from "mcp-use/react";

const ThemedCard: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => {
  const { theme } = useWidget();

  const styles = {
    container: {
      backgroundColor: theme === "dark" ? "#1a1a2e" : "#ffffff",
      color: theme === "dark" ? "#e0e0e0" : "#333333",
      border: `1px solid ${theme === "dark" ? "#333" : "#e0e0e0"}`,
      borderRadius: "8px",
      padding: "16px",
    },
    title: {
      color: theme === "dark" ? "#ffffff" : "#111827",
      fontSize: "1.25rem",
      fontWeight: 600,
      marginBottom: "8px",
    },
  };

  return (
    <div style={styles.container}>
      <h3 style={styles.title}>{title}</h3>
      {children}
    </div>
  );
};
```

### Tailwind CSS + Dark Mode

With Tailwind's `darkMode: "class"` (set automatically by `ThemeProvider`):

```tsx
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
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-2/3" />
      </div>
    );
  }

  // Use streaming data if available, otherwise full props
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

  if (isPending) return <div className="animate-pulse">Loading products...</div>;

  const handleViewDetails = async (productId: string) => {
    const result = await getDetails({ productId });
    // details state auto-updates
  };

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
              <button onClick={() => handleViewDetails(product.id)} disabled={loadingDetails}>
                Details
              </button>
              <button onClick={() => addFavorite({ productId: product.id })} disabled={savingFav}>
                ♥
              </button>
              <button onClick={() => addToCart({ productId: product.id, quantity: 1 })} disabled={addingToCart}>
                Add to Cart
              </button>
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

  return (
    <div className={isFullscreen ? "h-screen w-full p-6" : "h-64 p-4"}>
      <div className="flex justify-between items-center mb-4">
        <h2>Analytics Dashboard</h2>
        <div className="flex gap-2">
          {displayMode !== "fullscreen" && (
            <button
              onClick={() => requestDisplayMode("fullscreen")}
              className="px-3 py-1 bg-blue-500 text-white rounded text-sm"
            >
              ⛶ Expand
            </button>
          )}
          {displayMode === "fullscreen" && (
            <button
              onClick={() => requestDisplayMode("inline")}
              className="px-3 py-1 bg-gray-500 text-white rounded text-sm"
            >
              ✕ Close
            </button>
          )}
          {displayMode !== "pip" && (
            <button
              onClick={() => requestDisplayMode("pip")}
              className="px-3 py-1 bg-gray-300 rounded text-sm"
            >
              ⧉ PiP
            </button>
          )}
        </div>
      </div>
      <div className={isFullscreen ? "h-[calc(100%-60px)]" : "h-full"}>
        {/* Chart content adapts to available space */}
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

Content Security Policy domains must be declared in `widgetMetadata` for external requests to work.

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

### Multiple External Services

```typescript
export const widgetMetadata: WidgetMetadata = {
  description: "Widget with maps, analytics, and external data",
  props: z.object({ location: z.string() }),
  metadata: {
    csp: {
      connectDomains: [
        "https://api.mapbox.com",
        "https://api.analytics.example.com",
      ],
      resourceDomains: [
        "https://api.mapbox.com",
        "https://tiles.mapbox.com",
      ],
    },
    prefersBorder: false,
  },
};
```

---

## Widget-to-Widget Communication

Widgets communicate indirectly through shared MCP tools and persistent state.

```tsx
// Widget A: Settings panel
const SettingsWidget: React.FC = () => {
  const { callTool } = useWidget();

  const updateTheme = async (theme: string) => {
    // Save setting via a shared tool
    await callTool("save-setting", { key: "dashboardTheme", value: theme });
  };

  return (
    <div>
      <button onClick={() => updateTheme("compact")}>Compact</button>
      <button onClick={() => updateTheme("detailed")}>Detailed</button>
    </div>
  );
};

// Widget B: Dashboard reads settings via its own tool call
const DashboardWidget: React.FC = () => {
  const { props } = useWidget<{ theme: string; data: unknown[] }>();
  // Server resolved the theme setting when generating props
  return <div className={props.theme === "compact" ? "text-sm" : "text-base"}>...</div>;
};
```

---

## Error Handling Pattern

Combine `ErrorBoundary` for render errors with try/catch for tool call errors.

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
      // Handle success
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred");
    }
  };

  if (error) {
    return (
      <div className="p-4 border border-red-300 bg-red-50 dark:bg-red-900/20 rounded">
        <p className="text-red-600 dark:text-red-400">{error}</p>
        <button onClick={() => setError(null)} className="mt-2 text-sm underline">
          Dismiss
        </button>
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

Let users ask follow-up questions via the chat from within a widget.

```tsx
import { useWidget } from "mcp-use/react";

const DataExplorer: React.FC = () => {
  const { props, sendFollowUpMessage } = useWidget<{ data: Record<string, number> }>();

  const askAbout = (metric: string) => {
    sendFollowUpMessage(`Tell me more about the ${metric} metric and what factors influence it.`);
  };

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
                <button
                  onClick={() => askAbout(key)}
                  className="text-blue-500 hover:underline text-sm"
                >
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

## Performance Patterns

### Memoize Expensive Computations

```tsx
import { useMemo, useCallback } from "react";
import { useWidget } from "mcp-use/react";

const DataTable: React.FC = () => {
  const { props } = useWidget<{ rows: Array<Record<string, unknown>> }>();

  // Memoize sorted/filtered data
  const sortedRows = useMemo(
    () => [...(props.rows ?? [])].sort((a, b) => String(a.name).localeCompare(String(b.name))),
    [props.rows]
  );

  // Memoize callbacks passed to children
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

### Avoid Unnecessary Re-Renders

```tsx
import { memo } from "react";

// Memoize child components that receive stable props
const MetricCard = memo<{ label: string; value: number }>(({ label, value }) => (
  <div className="p-3 border rounded">
    <div className="text-sm text-gray-500">{label}</div>
    <div className="text-2xl font-bold">{value}</div>
  </div>
));

MetricCard.displayName = "MetricCard";
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
      <button
        onClick={() => openExternal(props.url)}
        className="text-blue-500 hover:underline"
      >
        Open in browser →
      </button>
    </div>
  );
};
```
