# Widget Recipes

Complete, production-ready widget examples. Each recipe includes server-side tool definition, widget component code, and file structure.

---

## Recipe 1: Weather Dashboard Widget

A weather display widget with temperature, humidity, wind data, refresh functionality, and dark/light theme support.

### File Structure

```
resources/weather-dashboard/
├── widget.tsx          # Entry point + metadata
└── components/
    └── WeatherCard.tsx
src/
└── tools/weather.ts    # Server-side tool
```

### Server-Side Tool — `src/tools/weather.ts`

```typescript
import { widget, text } from "mcp-use/server";
import type { MCPServer } from "mcp-use/server";
import { z } from "zod";

export function registerWeatherTools(server: MCPServer) {
  server.tool(
    {
      name: "get-weather",
      description: "Get current weather conditions for a city",
      schema: z.object({
        city: z.string().describe("City name (e.g., 'San Francisco')"),
        units: z.enum(["metric", "imperial"]).default("metric").describe("Temperature units"),
      }),
      widget: {
        name: "weather-dashboard",
        invoking: "Fetching weather data...",
        invoked: "Weather loaded",
      },
    },
    async ({ city, units }) => {
      const apiKey = process.env.OPENWEATHER_API_KEY;
      const res = await fetch(
        `https://api.openweathermap.org/data/2.5/weather?q=${encodeURIComponent(city)}&units=${units}&appid=${apiKey}`
      );
      const data = await res.json();

      return widget({
        props: {
          city: data.name,
          country: data.sys.country,
          temperature: Math.round(data.main.temp),
          feelsLike: Math.round(data.main.feels_like),
          humidity: data.main.humidity,
          windSpeed: data.wind.speed,
          conditions: data.weather[0].main,
          description: data.weather[0].description,
          icon: data.weather[0].icon,
          units,
        },
        output: text(`Weather in ${data.name}: ${Math.round(data.main.temp)}°${units === "metric" ? "C" : "F"}, ${data.weather[0].description}`),
      });
    }
  );
}
```

### Widget Component — `resources/weather-dashboard/widget.tsx`

```tsx
import { McpUseProvider, useWidget, useCallTool, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

export const widgetMetadata: WidgetMetadata = {
  description: "Displays current weather conditions with temperature, humidity, and wind data",
  props: z.object({
    city: z.string(),
    country: z.string(),
    temperature: z.number(),
    feelsLike: z.number(),
    humidity: z.number(),
    windSpeed: z.number(),
    conditions: z.string(),
    description: z.string(),
    icon: z.string(),
    units: z.enum(["metric", "imperial"]),
  }),
  metadata: {
    csp: {
      connectDomains: ["https://api.openweathermap.org"],
      resourceDomains: ["https://openweathermap.org"],
    },
    prefersBorder: true,
  },
};

interface WeatherProps {
  city: string;
  country: string;
  temperature: number;
  feelsLike: number;
  humidity: number;
  windSpeed: number;
  conditions: string;
  description: string;
  icon: string;
  units: "metric" | "imperial";
}

function WeatherContent() {
  const { props, isPending, theme } = useWidget<WeatherProps>();
  const { callTool: refresh, isPending: refreshing } = useCallTool("get-weather");

  if (isPending) {
    return (
      <div className="animate-pulse p-6 space-y-4">
        <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
        <div className="h-16 bg-gray-200 dark:bg-gray-700 rounded w-1/3" />
        <div className="grid grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-12 bg-gray-200 dark:bg-gray-700 rounded" />
          ))}
        </div>
      </div>
    );
  }

  const unitSymbol = props.units === "metric" ? "°C" : "°F";
  const windUnit = props.units === "metric" ? "m/s" : "mph";
  const isDark = theme === "dark";

  return (
    <div className={`p-6 rounded-lg ${isDark ? "bg-gray-900 text-white" : "bg-white text-gray-900"}`}>
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold">{props.city}, {props.country}</h2>
          <p className={`text-sm ${isDark ? "text-gray-400" : "text-gray-500"}`}>
            {props.description}
          </p>
        </div>
        <button
          onClick={() => refresh({ city: props.city, units: props.units })}
          disabled={refreshing}
          className={`p-2 rounded-full ${refreshing ? "animate-spin" : ""} ${isDark ? "hover:bg-gray-800" : "hover:bg-gray-100"}`}
        >
          ↻
        </button>
      </div>

      <div className="flex items-center gap-4 my-4">
        <img
          src={`https://openweathermap.org/img/wn/${props.icon}@2x.png`}
          alt={props.conditions}
          className="w-16 h-16"
        />
        <span className="text-5xl font-light">{props.temperature}{unitSymbol}</span>
      </div>

      <div className="grid grid-cols-3 gap-4 mt-4">
        <div className={`p-3 rounded ${isDark ? "bg-gray-800" : "bg-gray-50"}`}>
          <div className={`text-xs ${isDark ? "text-gray-400" : "text-gray-500"}`}>Feels Like</div>
          <div className="text-lg font-semibold">{props.feelsLike}{unitSymbol}</div>
        </div>
        <div className={`p-3 rounded ${isDark ? "bg-gray-800" : "bg-gray-50"}`}>
          <div className={`text-xs ${isDark ? "text-gray-400" : "text-gray-500"}`}>Humidity</div>
          <div className="text-lg font-semibold">{props.humidity}%</div>
        </div>
        <div className={`p-3 rounded ${isDark ? "bg-gray-800" : "bg-gray-50"}`}>
          <div className={`text-xs ${isDark ? "text-gray-400" : "text-gray-500"}`}>Wind</div>
          <div className="text-lg font-semibold">{props.windSpeed} {windUnit}</div>
        </div>
      </div>
    </div>
  );
}

export default function Widget() {
  return (
    <McpUseProvider autoSize>
      <WeatherContent />
    </McpUseProvider>
  );
}
```

---

## Recipe 2: Product Carousel Widget

A product search results carousel with animation, click-to-detail, and persistent favorites.

### File Structure

```
resources/product-carousel/
├── widget.tsx
└── components/
    ├── Carousel.tsx
    └── ProductCard.tsx
src/
└── tools/products.ts
```

### Server-Side Tools — `src/tools/products.ts`

```typescript
import { widget, text, object } from "mcp-use/server";
import type { MCPServer } from "mcp-use/server";
import { z } from "zod";

export function registerProductTools(server: MCPServer) {
  server.tool(
    {
      name: "search-products",
      description: "Search for products by query",
      schema: z.object({
        query: z.string().describe("Search query"),
        category: z.string().optional().describe("Product category filter"),
        limit: z.number().int().min(1).max(20).default(8).describe("Max results"),
      }),
      widget: {
        name: "product-carousel",
        invoking: "Searching products...",
        invoked: "Products found",
      },
    },
    async ({ query, category, limit }) => {
      // Replace with real product API
      const products = Array.from({ length: limit }, (_, i) => ({
        id: `prod-${i + 1}`,
        name: `${query} Product ${i + 1}`,
        price: Math.round(Math.random() * 200 + 10),
        image: `/products/placeholder-${(i % 4) + 1}.png`,
        rating: Math.round(Math.random() * 20 + 30) / 10,
        category: category ?? "general",
      }));

      return widget({
        props: { products, query, totalResults: products.length },
        output: text(`Found ${products.length} products for "${query}"`),
      });
    }
  );

  server.tool(
    {
      name: "get-product-details",
      description: "Get detailed info about a specific product",
      schema: z.object({ productId: z.string().describe("Product ID") }),
    },
    async ({ productId }) => {
      return object({
        id: productId,
        name: `Product ${productId}`,
        description: "A high-quality product with great reviews.",
        price: 49.99,
        specs: { weight: "200g", dimensions: "10x5x3cm" },
        reviews: 128,
      });
    }
  );

  server.tool(
    {
      name: "toggle-favorite",
      description: "Add or remove a product from favorites",
      schema: z.object({
        productId: z.string().describe("Product ID"),
        action: z.enum(["add", "remove"]).describe("Add or remove from favorites"),
      }),
    },
    async ({ productId, action }) => {
      return object({ productId, favorited: action === "add", message: `Product ${action === "add" ? "added to" : "removed from"} favorites` });
    }
  );
}
```

### Widget Component — `resources/product-carousel/widget.tsx`

```tsx
import { useState, useRef } from "react";
import { McpUseProvider, useWidget, useCallTool, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

export const widgetMetadata: WidgetMetadata = {
  description: "Displays product search results in a scrollable carousel with details and favorites",
  props: z.object({
    products: z.array(z.object({
      id: z.string(), name: z.string(), price: z.number(),
      image: z.string(), rating: z.number(), category: z.string(),
    })),
    query: z.string(),
    totalResults: z.number(),
  }),
  metadata: { prefersBorder: true },
};

interface Product {
  id: string;
  name: string;
  price: number;
  image: string;
  rating: number;
  category: string;
}

interface CarouselProps {
  products: Product[];
  query: string;
  totalResults: number;
}

interface WidgetState {
  favorites: string[];
}

function CarouselContent() {
  const { props, isPending, theme, state, setState } = useWidget<CarouselProps, unknown, unknown, WidgetState>();
  const { callToolAsync: getDetails, isPending: loadingDetails } = useCallTool("get-product-details");
  const { callTool: toggleFav } = useCallTool("toggle-favorite");

  const [selectedProduct, setSelectedProduct] = useState<Record<string, unknown> | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const isDark = theme === "dark";
  const favorites = state?.favorites ?? [];

  if (isPending) {
    return (
      <div className="flex gap-4 p-4 overflow-hidden">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="animate-pulse flex-shrink-0 w-48">
            <div className="h-48 bg-gray-200 dark:bg-gray-700 rounded-t" />
            <div className="p-3 space-y-2">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  const scroll = (direction: "left" | "right") => {
    scrollRef.current?.scrollBy({ left: direction === "left" ? -220 : 220, behavior: "smooth" });
  };

  const handleViewDetails = async (productId: string) => {
    const result = await getDetails({ productId });
    setSelectedProduct(result.structuredContent as Record<string, unknown>);
  };

  const handleToggleFavorite = async (productId: string) => {
    const isFav = favorites.includes(productId);
    toggleFav({ productId, action: isFav ? "remove" : "add" });
    await setState((prev) => ({
      favorites: isFav
        ? (prev?.favorites ?? []).filter((id) => id !== productId)
        : [...(prev?.favorites ?? []), productId],
    }));
  };

  return (
    <div className={`p-4 ${isDark ? "bg-gray-900 text-white" : "bg-white text-gray-900"}`}>
      <div className="flex justify-between items-center mb-3">
        <h2 className="text-lg font-bold">Results for "{props.query}" ({props.totalResults})</h2>
        <div className="flex gap-1">
          <button onClick={() => scroll("left")} className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700">←</button>
          <button onClick={() => scroll("right")} className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700">→</button>
        </div>
      </div>

      <div ref={scrollRef} className="flex gap-4 overflow-x-auto scroll-smooth pb-2" style={{ scrollbarWidth: "none" }}>
        {props.products?.map((product) => (
          <div
            key={product.id}
            className={`flex-shrink-0 w-48 rounded-lg overflow-hidden border transition-transform hover:scale-105 ${isDark ? "border-gray-700 bg-gray-800" : "border-gray-200 bg-white"}`}
          >
            <div className="h-48 bg-gray-100 dark:bg-gray-700 flex items-center justify-center text-4xl">
              🛍️
            </div>
            <div className="p-3">
              <h3 className="font-medium text-sm truncate">{product.name}</h3>
              <div className="flex justify-between items-center mt-1">
                <span className="font-bold">${product.price}</span>
                <span className="text-yellow-500 text-sm">★ {product.rating}</span>
              </div>
              <div className="flex gap-1 mt-2">
                <button
                  onClick={() => handleViewDetails(product.id)}
                  disabled={loadingDetails}
                  className="flex-1 text-xs py-1 px-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                >
                  Details
                </button>
                <button
                  onClick={() => handleToggleFavorite(product.id)}
                  className={`text-xs py-1 px-2 rounded ${favorites.includes(product.id) ? "bg-red-500 text-white" : "bg-gray-200 dark:bg-gray-600"}`}
                >
                  {favorites.includes(product.id) ? "♥" : "♡"}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {selectedProduct && (
        <div className={`mt-4 p-4 rounded-lg border ${isDark ? "border-gray-700 bg-gray-800" : "border-gray-200 bg-gray-50"}`}>
          <div className="flex justify-between items-start">
            <h3 className="font-bold">{String(selectedProduct.name)}</h3>
            <button onClick={() => setSelectedProduct(null)} className="text-gray-400 hover:text-gray-600">✕</button>
          </div>
          <p className="text-sm mt-1">{String(selectedProduct.description)}</p>
          <p className="font-bold mt-2">${String(selectedProduct.price)}</p>
        </div>
      )}
    </div>
  );
}

export default function Widget() {
  return (
    <McpUseProvider autoSize>
      <CarouselContent />
    </McpUseProvider>
  );
}
```

---

## Recipe 3: Live Code Preview Widget

A widget that shows code being streamed from the LLM with syntax highlighting and copy-to-clipboard.

### File Structure

```
resources/code-preview/
├── widget.tsx
src/
└── tools/code.ts
```

### Server-Side Tool — `src/tools/code.ts`

```typescript
import { widget, text } from "mcp-use/server";
import type { MCPServer } from "mcp-use/server";
import { z } from "zod";

export function registerCodeTools(server: MCPServer) {
  server.tool(
    {
      name: "generate-code",
      description: "Generate code for a given task",
      schema: z.object({
        task: z.string().describe("What the code should do"),
        language: z.string().default("typescript").describe("Programming language"),
      }),
      widget: {
        name: "code-preview",
        invoking: "Generating code...",
        invoked: "Code ready",
      },
    },
    async ({ task, language }) => {
      const code = `// Generated code for: ${task}\nfunction example() {\n  console.log("Hello from ${language}");\n  return { success: true };\n}\n\nexport default example;`;

      return widget({
        props: { code, language, task, lineCount: code.split("\n").length },
        output: text(`Generated ${language} code for: ${task}`),
      });
    }
  );
}
```

### Widget Component — `resources/code-preview/widget.tsx`

```tsx
import { useState } from "react";
import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

export const widgetMetadata: WidgetMetadata = {
  description: "Displays generated code with syntax highlighting, streaming preview, and copy to clipboard",
  props: z.object({
    code: z.string(),
    language: z.string(),
    task: z.string(),
    lineCount: z.number(),
  }),
  metadata: { prefersBorder: true },
};

interface CodeProps {
  code: string;
  language: string;
  task: string;
  lineCount: number;
}

function CodePreviewContent() {
  const { props, isPending, isStreaming, partialToolInput, theme } = useWidget<CodeProps>();
  const [copied, setCopied] = useState(false);
  const isDark = theme === "dark";

  // Determine what code to display based on lifecycle stage
  const displayCode = isStreaming ? (partialToolInput?.code ?? "") : (props.code ?? "");
  const displayLanguage = (isStreaming ? partialToolInput?.language : props.language) ?? "text";
  const lines = displayCode.split("\n");

  const handleCopy = async () => {
    await navigator.clipboard.writeText(displayCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (isPending && !partialToolInput) {
    return (
      <div className={`p-4 rounded-lg font-mono ${isDark ? "bg-gray-900" : "bg-gray-50"}`}>
        <div className="animate-pulse space-y-2">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className={`h-4 rounded ${isDark ? "bg-gray-800" : "bg-gray-200"}`} style={{ width: `${30 + Math.random() * 60}%` }} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={`rounded-lg overflow-hidden ${isDark ? "bg-gray-900" : "bg-gray-50"}`}>
      {/* Header bar */}
      <div className={`flex justify-between items-center px-4 py-2 ${isDark ? "bg-gray-800" : "bg-gray-200"}`}>
        <div className="flex items-center gap-2">
          <span className={`text-xs font-mono px-2 py-0.5 rounded ${isDark ? "bg-gray-700 text-gray-300" : "bg-gray-300 text-gray-700"}`}>
            {displayLanguage}
          </span>
          {isStreaming && (
            <span className="text-xs text-blue-400 animate-pulse">● Streaming...</span>
          )}
          {!isStreaming && props.lineCount && (
            <span className={`text-xs ${isDark ? "text-gray-500" : "text-gray-400"}`}>
              {props.lineCount} lines
            </span>
          )}
        </div>
        <button
          onClick={handleCopy}
          disabled={isStreaming}
          className={`text-xs px-3 py-1 rounded transition-colors ${
            copied
              ? "bg-green-500 text-white"
              : isDark
              ? "bg-gray-700 text-gray-300 hover:bg-gray-600"
              : "bg-gray-300 text-gray-700 hover:bg-gray-400"
          }`}
        >
          {copied ? "✓ Copied" : "Copy"}
        </button>
      </div>

      {/* Code area */}
      <div className="overflow-x-auto p-4">
        <pre className="text-sm">
          <code>
            {lines.map((line, i) => (
              <div key={i} className="flex">
                <span className={`select-none w-8 text-right mr-4 ${isDark ? "text-gray-600" : "text-gray-400"}`}>
                  {i + 1}
                </span>
                <span className={isDark ? "text-gray-200" : "text-gray-800"}>
                  {line}
                </span>
              </div>
            ))}
            {isStreaming && (
              <span className="text-blue-400 animate-pulse">▌</span>
            )}
          </code>
        </pre>
      </div>
    </div>
  );
}

export default function Widget() {
  return (
    <McpUseProvider autoSize>
      <CodePreviewContent />
    </McpUseProvider>
  );
}
```

---

## Recipe 4: Data Dashboard Widget

A multi-section data dashboard with summary cards, data table, and fullscreen mode.

### File Structure

```
resources/data-dashboard/
├── widget.tsx
src/
└── tools/analytics.ts
```

### Server-Side Tool — `src/tools/analytics.ts`

```typescript
import { widget, text } from "mcp-use/server";
import type { MCPServer } from "mcp-use/server";
import { z } from "zod";

export function registerAnalyticsTools(server: MCPServer) {
  server.tool(
    {
      name: "get-analytics",
      description: "Get analytics dashboard data for a date range",
      schema: z.object({
        range: z.enum(["7d", "30d", "90d"]).default("7d").describe("Date range"),
        metric: z.string().optional().describe("Focus on specific metric"),
      }),
      widget: {
        name: "data-dashboard",
        invoking: "Loading analytics...",
        invoked: "Dashboard ready",
      },
    },
    async ({ range }) => {
      const data = {
        summary: {
          totalVisitors: 12453,
          pageViews: 45231,
          bounceRate: 34.5,
          avgSessionDuration: 185,
        },
        topPages: [
          { path: "/home", views: 8921, change: 12.3 },
          { path: "/products", views: 6543, change: -2.1 },
          { path: "/about", views: 3210, change: 5.7 },
          { path: "/contact", views: 1987, change: 0.8 },
          { path: "/blog", views: 1432, change: 15.2 },
        ],
        range,
      };

      return widget({
        props: data,
        output: text(`Analytics for ${range}: ${data.summary.totalVisitors} visitors, ${data.summary.pageViews} page views`),
      });
    }
  );
}
```

### Widget Component — `resources/data-dashboard/widget.tsx`

```tsx
import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

export const widgetMetadata: WidgetMetadata = {
  description: "Analytics dashboard with visitor stats, top pages, and fullscreen mode",
  props: z.object({
    summary: z.object({
      totalVisitors: z.number(),
      pageViews: z.number(),
      bounceRate: z.number(),
      avgSessionDuration: z.number(),
    }),
    topPages: z.array(z.object({
      path: z.string(),
      views: z.number(),
      change: z.number(),
    })),
    range: z.string(),
  }),
  metadata: { prefersBorder: true },
};

interface DashboardProps {
  summary: {
    totalVisitors: number;
    pageViews: number;
    bounceRate: number;
    avgSessionDuration: number;
  };
  topPages: Array<{ path: string; views: number; change: number }>;
  range: string;
}

function DashboardContent() {
  const { props, isPending, theme, displayMode, requestDisplayMode, sendFollowUpMessage } =
    useWidget<DashboardProps>();

  const isDark = theme === "dark";
  const isFullscreen = displayMode === "fullscreen";

  if (isPending) {
    return (
      <div className="p-6 animate-pulse space-y-6">
        <div className="grid grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className={`h-20 rounded-lg ${isDark ? "bg-gray-800" : "bg-gray-200"}`} />
          ))}
        </div>
        <div className={`h-48 rounded-lg ${isDark ? "bg-gray-800" : "bg-gray-200"}`} />
      </div>
    );
  }

  const formatDuration = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}m ${s}s`;
  };

  const cards = [
    { label: "Visitors", value: props.summary.totalVisitors.toLocaleString(), icon: "👥" },
    { label: "Page Views", value: props.summary.pageViews.toLocaleString(), icon: "📄" },
    { label: "Bounce Rate", value: `${props.summary.bounceRate}%`, icon: "📊" },
    { label: "Avg Session", value: formatDuration(props.summary.avgSessionDuration), icon: "⏱" },
  ];

  return (
    <div className={`${isFullscreen ? "h-screen" : ""} p-6 ${isDark ? "bg-gray-900 text-white" : "bg-white text-gray-900"}`}>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-xl font-bold">Analytics Dashboard</h2>
          <p className={`text-sm ${isDark ? "text-gray-400" : "text-gray-500"}`}>Last {props.range}</p>
        </div>
        <div className="flex gap-2">
          {!isFullscreen && (
            <button
              onClick={() => requestDisplayMode("fullscreen")}
              className="px-3 py-1.5 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              ⛶ Expand
            </button>
          )}
          {isFullscreen && (
            <button
              onClick={() => requestDisplayMode("inline")}
              className="px-3 py-1.5 text-sm bg-gray-500 text-white rounded hover:bg-gray-600"
            >
              ✕ Close
            </button>
          )}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {cards.map((card) => (
          <div
            key={card.label}
            className={`p-4 rounded-lg border ${isDark ? "border-gray-700 bg-gray-800" : "border-gray-200 bg-gray-50"}`}
          >
            <div className="flex items-center gap-2 mb-1">
              <span>{card.icon}</span>
              <span className={`text-xs ${isDark ? "text-gray-400" : "text-gray-500"}`}>{card.label}</span>
            </div>
            <div className="text-2xl font-bold">{card.value}</div>
          </div>
        ))}
      </div>

      {/* Top Pages Table */}
      <div className={`rounded-lg border ${isDark ? "border-gray-700" : "border-gray-200"}`}>
        <div className={`px-4 py-3 border-b font-medium ${isDark ? "border-gray-700 bg-gray-800" : "border-gray-200 bg-gray-50"}`}>
          Top Pages
        </div>
        <table className="w-full">
          <thead>
            <tr className={`text-xs ${isDark ? "text-gray-400" : "text-gray-500"}`}>
              <th className="text-left px-4 py-2">Page</th>
              <th className="text-right px-4 py-2">Views</th>
              <th className="text-right px-4 py-2">Change</th>
            </tr>
          </thead>
          <tbody>
            {props.topPages?.map((page) => (
              <tr key={page.path} className={`border-t ${isDark ? "border-gray-800" : "border-gray-100"}`}>
                <td className="px-4 py-2 font-mono text-sm">{page.path}</td>
                <td className="px-4 py-2 text-right">{page.views.toLocaleString()}</td>
                <td className={`px-4 py-2 text-right ${page.change >= 0 ? "text-green-500" : "text-red-500"}`}>
                  {page.change >= 0 ? "+" : ""}{page.change}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Follow-up action */}
      <div className="mt-4 flex gap-2">
        <button
          onClick={() => sendFollowUpMessage("What are the key trends in this analytics data? What should I focus on improving?")}
          className={`text-sm px-3 py-1.5 rounded ${isDark ? "bg-gray-800 hover:bg-gray-700 text-gray-300" : "bg-gray-100 hover:bg-gray-200 text-gray-700"}`}
        >
          Ask about trends →
        </button>
        <button
          onClick={() => sendFollowUpMessage("Compare this data with the previous period and highlight significant changes.")}
          className={`text-sm px-3 py-1.5 rounded ${isDark ? "bg-gray-800 hover:bg-gray-700 text-gray-300" : "bg-gray-100 hover:bg-gray-200 text-gray-700"}`}
        >
          Compare periods →
        </button>
      </div>
    </div>
  );
}

export default function Widget() {
  return (
    <McpUseProvider autoSize>
      <DashboardContent />
    </McpUseProvider>
  );
}
```

---

## Recipe 5: Interactive Form Widget

A multi-step form with validation, submission via `callTool`, and success/error states.

### File Structure

```
resources/contact-form/
├── widget.tsx
src/
└── tools/forms.ts
```

### Server-Side Tool — `src/tools/forms.ts`

```typescript
import { widget, text, object } from "mcp-use/server";
import type { MCPServer } from "mcp-use/server";
import { z } from "zod";

export function registerFormTools(server: MCPServer) {
  server.tool(
    {
      name: "show-contact-form",
      description: "Show a contact form for user input",
      schema: z.object({
        topic: z.string().optional().describe("Pre-filled topic"),
      }),
      widget: {
        name: "contact-form",
        invoking: "Loading form...",
        invoked: "Form ready",
      },
    },
    async ({ topic }) => {
      return widget({
        props: { topic: topic ?? "", departments: ["Sales", "Support", "Engineering", "Billing"] },
        output: text("Contact form is ready for input."),
      });
    }
  );

  server.tool(
    {
      name: "submit-contact-form",
      description: "Submit a contact form",
      schema: z.object({
        name: z.string().min(1).describe("Contact name"),
        email: z.string().email().describe("Contact email"),
        department: z.string().describe("Target department"),
        message: z.string().min(10).describe("Message body"),
        priority: z.enum(["low", "medium", "high"]).default("medium").describe("Priority level"),
      }),
    },
    async ({ name, email, department, message, priority }) => {
      const ticketId = `TICKET-${Date.now().toString(36).toUpperCase()}`;
      return object({
        ticketId,
        status: "submitted",
        message: `Thank you, ${name}. Your ${priority}-priority ticket ${ticketId} has been sent to ${department}.`,
      });
    }
  );
}
```

### Widget Component — `resources/contact-form/widget.tsx`

```tsx
import { useState } from "react";
import { McpUseProvider, useWidget, useCallTool, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

export const widgetMetadata: WidgetMetadata = {
  description: "Multi-step contact form with validation and submission",
  props: z.object({
    topic: z.string(),
    departments: z.array(z.string()),
  }),
  metadata: { prefersBorder: true },
};

interface FormProps {
  topic: string;
  departments: string[];
}

interface FormData {
  name: string;
  email: string;
  department: string;
  message: string;
  priority: "low" | "medium" | "high";
}

type FormStep = "info" | "message" | "review";

function FormContent() {
  const { props, isPending, theme } = useWidget<FormProps>();
  const { callToolAsync: submit, isPending: submitting } = useCallTool("submit-contact-form");

  const [step, setStep] = useState<FormStep>("info");
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [errors, setErrors] = useState<Partial<Record<keyof FormData, string>>>({});
  const [formData, setFormData] = useState<FormData>({
    name: "",
    email: "",
    department: props.departments?.[0] ?? "Support",
    message: props.topic ? `Regarding: ${props.topic}\n\n` : "",
    priority: "medium",
  });

  const isDark = theme === "dark";

  if (isPending) return <div className="animate-pulse p-6 h-48" />;

  const inputClass = `w-full px-3 py-2 rounded border ${isDark ? "bg-gray-800 border-gray-600 text-white" : "bg-white border-gray-300 text-gray-900"} focus:outline-none focus:ring-2 focus:ring-blue-500`;

  const validateStep = (s: FormStep): boolean => {
    const newErrors: Partial<Record<keyof FormData, string>> = {};
    if (s === "info") {
      if (!formData.name.trim()) newErrors.name = "Name is required";
      if (!formData.email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) newErrors.email = "Valid email required";
    }
    if (s === "message") {
      if (formData.message.trim().length < 10) newErrors.message = "Message must be at least 10 characters";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    setSubmitError(null);
    try {
      const res = await submit(formData);
      setResult(res.structuredContent as Record<string, unknown>);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Submission failed");
    }
  };

  if (result) {
    return (
      <div className={`p-6 text-center ${isDark ? "bg-gray-900 text-white" : "bg-white"}`}>
        <div className="text-4xl mb-3">✅</div>
        <h3 className="text-lg font-bold mb-2">Submitted Successfully</h3>
        <p className="mb-1">Ticket: <code className="font-mono">{String(result.ticketId)}</code></p>
        <p className={`text-sm ${isDark ? "text-gray-400" : "text-gray-500"}`}>{String(result.message)}</p>
      </div>
    );
  }

  return (
    <div className={`p-6 ${isDark ? "bg-gray-900 text-white" : "bg-white text-gray-900"}`}>
      {/* Step indicator */}
      <div className="flex gap-2 mb-6">
        {(["info", "message", "review"] as FormStep[]).map((s, i) => (
          <div key={s} className="flex items-center gap-2">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              step === s ? "bg-blue-500 text-white" : i < ["info", "message", "review"].indexOf(step)
                ? "bg-green-500 text-white" : isDark ? "bg-gray-700 text-gray-400" : "bg-gray-200 text-gray-500"
            }`}>{i + 1}</div>
            {i < 2 && <div className={`w-8 h-0.5 ${isDark ? "bg-gray-700" : "bg-gray-300"}`} />}
          </div>
        ))}
      </div>

      {step === "info" && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Name</label>
            <input className={inputClass} value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} placeholder="Your name" />
            {errors.name && <p className="text-red-500 text-xs mt-1">{errors.name}</p>}
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <input className={inputClass} type="email" value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} placeholder="you@example.com" />
            {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email}</p>}
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Department</label>
            <select className={inputClass} value={formData.department} onChange={(e) => setFormData({ ...formData, department: e.target.value })}>
              {props.departments?.map((d) => <option key={d} value={d}>{d}</option>)}
            </select>
          </div>
          <button onClick={() => validateStep("info") && setStep("message")} className="w-full py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
            Next →
          </button>
        </div>
      )}

      {step === "message" && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Message</label>
            <textarea className={`${inputClass} h-32`} value={formData.message} onChange={(e) => setFormData({ ...formData, message: e.target.value })} placeholder="Describe your issue..." />
            {errors.message && <p className="text-red-500 text-xs mt-1">{errors.message}</p>}
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Priority</label>
            <div className="flex gap-2">
              {(["low", "medium", "high"] as const).map((p) => (
                <button key={p} onClick={() => setFormData({ ...formData, priority: p })} className={`flex-1 py-2 rounded capitalize ${formData.priority === p ? "bg-blue-500 text-white" : isDark ? "bg-gray-700" : "bg-gray-200"}`}>{p}</button>
              ))}
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={() => setStep("info")} className={`flex-1 py-2 rounded ${isDark ? "bg-gray-700" : "bg-gray-200"}`}>← Back</button>
            <button onClick={() => validateStep("message") && setStep("review")} className="flex-1 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">Review →</button>
          </div>
        </div>
      )}

      {step === "review" && (
        <div className="space-y-4">
          <div className={`p-4 rounded ${isDark ? "bg-gray-800" : "bg-gray-50"}`}>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className={isDark ? "text-gray-400" : "text-gray-500"}>Name:</div><div>{formData.name}</div>
              <div className={isDark ? "text-gray-400" : "text-gray-500"}>Email:</div><div>{formData.email}</div>
              <div className={isDark ? "text-gray-400" : "text-gray-500"}>Dept:</div><div>{formData.department}</div>
              <div className={isDark ? "text-gray-400" : "text-gray-500"}>Priority:</div><div className="capitalize">{formData.priority}</div>
            </div>
            <div className="mt-3">
              <div className={`text-sm ${isDark ? "text-gray-400" : "text-gray-500"}`}>Message:</div>
              <p className="text-sm mt-1 whitespace-pre-wrap">{formData.message}</p>
            </div>
          </div>
          {submitError && <p className="text-red-500 text-sm">{submitError}</p>}
          <div className="flex gap-2">
            <button onClick={() => setStep("message")} className={`flex-1 py-2 rounded ${isDark ? "bg-gray-700" : "bg-gray-200"}`}>← Edit</button>
            <button onClick={handleSubmit} disabled={submitting} className="flex-1 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50">
              {submitting ? "Submitting..." : "Submit ✓"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function Widget() {
  return (
    <McpUseProvider autoSize>
      <FormContent />
    </McpUseProvider>
  );
}
```

---

## Recipe 6: Kanban Board Widget

A task management board with columns, drag-and-drop, priority badges, and persistent state.

### File Structure

```
resources/kanban-board/
├── widget.tsx
src/
└── tools/tasks.ts
```

### Server-Side Tools — `src/tools/tasks.ts`

```typescript
import { widget, text, object } from "mcp-use/server";
import type { MCPServer } from "mcp-use/server";
import { z } from "zod";

export function registerTaskTools(server: MCPServer) {
  server.tool(
    {
      name: "show-kanban",
      description: "Display a kanban board with tasks",
      schema: z.object({
        projectName: z.string().describe("Project name"),
      }),
      widget: {
        name: "kanban-board",
        invoking: "Loading board...",
        invoked: "Board ready",
      },
    },
    async ({ projectName }) => {
      const tasks = [
        { id: "1", title: "Design homepage", column: "todo", priority: "high" },
        { id: "2", title: "Set up CI/CD", column: "todo", priority: "medium" },
        { id: "3", title: "API authentication", column: "in-progress", priority: "high" },
        { id: "4", title: "Database schema", column: "in-progress", priority: "low" },
        { id: "5", title: "Project scaffolding", column: "done", priority: "medium" },
      ];

      return widget({
        props: {
          projectName,
          columns: ["todo", "in-progress", "done"],
          tasks,
        },
        output: text(`Kanban board for "${projectName}": ${tasks.length} tasks`),
      });
    }
  );

  server.tool(
    {
      name: "update-task",
      description: "Move a task to a different column or update its priority",
      schema: z.object({
        taskId: z.string().describe("Task ID"),
        column: z.string().optional().describe("New column"),
        priority: z.enum(["low", "medium", "high"]).optional().describe("New priority"),
        title: z.string().optional().describe("Updated title"),
      }),
    },
    async ({ taskId, column, priority, title }) => {
      return object({ taskId, updated: { column, priority, title }, success: true });
    }
  );

  server.tool(
    {
      name: "create-task",
      description: "Create a new task on the board",
      schema: z.object({
        title: z.string().describe("Task title"),
        column: z.string().default("todo").describe("Initial column"),
        priority: z.enum(["low", "medium", "high"]).default("medium").describe("Priority"),
      }),
    },
    async ({ title, column, priority }) => {
      const id = Date.now().toString(36);
      return object({ id, title, column, priority, success: true });
    }
  );
}
```

### Widget Component — `resources/kanban-board/widget.tsx`

```tsx
import { useState } from "react";
import { McpUseProvider, useWidget, useCallTool, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

export const widgetMetadata: WidgetMetadata = {
  description: "Kanban board with draggable tasks, priority badges, and persistent state",
  props: z.object({
    projectName: z.string(),
    columns: z.array(z.string()),
    tasks: z.array(z.object({
      id: z.string(), title: z.string(), column: z.string(),
      priority: z.enum(["low", "medium", "high"]),
    })),
  }),
  metadata: { prefersBorder: true },
};

interface Task {
  id: string;
  title: string;
  column: string;
  priority: "low" | "medium" | "high";
}

interface BoardProps {
  projectName: string;
  columns: string[];
  tasks: Task[];
}

interface BoardState {
  tasks: Task[];
}

const priorityColors: Record<string, string> = {
  high: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
  medium: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
  low: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
};

const columnLabels: Record<string, string> = {
  "todo": "📋 To Do",
  "in-progress": "🔨 In Progress",
  "done": "✅ Done",
};

function KanbanContent() {
  const { props, isPending, theme, state, setState } = useWidget<BoardProps, unknown, unknown, BoardState>();
  const { callTool: updateTask } = useCallTool("update-task");
  const { callToolAsync: createTask } = useCallTool("create-task");

  const [draggedTask, setDraggedTask] = useState<string | null>(null);
  const [newTaskTitle, setNewTaskTitle] = useState("");
  const [showAddForm, setShowAddForm] = useState(false);

  const isDark = theme === "dark";
  const tasks = state?.tasks ?? props.tasks ?? [];

  if (isPending) {
    return (
      <div className="p-6 animate-pulse">
        <div className={`h-8 rounded w-1/3 mb-6 ${isDark ? "bg-gray-800" : "bg-gray-200"}`} />
        <div className="grid grid-cols-3 gap-4">
          {[1, 2, 3].map((c) => (
            <div key={c} className="space-y-3">
              <div className={`h-6 rounded w-2/3 ${isDark ? "bg-gray-800" : "bg-gray-200"}`} />
              {[1, 2].map((t) => (
                <div key={t} className={`h-16 rounded ${isDark ? "bg-gray-800" : "bg-gray-200"}`} />
              ))}
            </div>
          ))}
        </div>
      </div>
    );
  }

  const moveTask = async (taskId: string, newColumn: string) => {
    const updated = tasks.map((t) => t.id === taskId ? { ...t, column: newColumn } : t);
    await setState({ tasks: updated });
    updateTask({ taskId, column: newColumn });
  };

  const handleAddTask = async () => {
    if (!newTaskTitle.trim()) return;
    try {
      const result = await createTask({ title: newTaskTitle, column: "todo", priority: "medium" });
      const newTask = result.structuredContent as Task;
      await setState({ tasks: [...tasks, newTask] });
      setNewTaskTitle("");
      setShowAddForm(false);
    } catch {
      // Handle error silently
    }
  };

  const handleDragStart = (taskId: string) => setDraggedTask(taskId);

  const handleDrop = (column: string) => {
    if (draggedTask) {
      moveTask(draggedTask, column);
      setDraggedTask(null);
    }
  };

  return (
    <div className={`p-6 ${isDark ? "bg-gray-900 text-white" : "bg-white text-gray-900"}`}>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold">{props.projectName}</h2>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="px-3 py-1.5 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          + Add Task
        </button>
      </div>

      {showAddForm && (
        <div className={`mb-4 p-3 rounded border ${isDark ? "border-gray-700 bg-gray-800" : "border-gray-200 bg-gray-50"}`}>
          <div className="flex gap-2">
            <input
              className={`flex-1 px-3 py-1.5 rounded border text-sm ${isDark ? "bg-gray-700 border-gray-600 text-white" : "bg-white border-gray-300"}`}
              value={newTaskTitle}
              onChange={(e) => setNewTaskTitle(e.target.value)}
              placeholder="Task title..."
              onKeyDown={(e) => e.key === "Enter" && handleAddTask()}
            />
            <button onClick={handleAddTask} className="px-3 py-1.5 text-sm bg-green-500 text-white rounded">Add</button>
            <button onClick={() => setShowAddForm(false)} className={`px-3 py-1.5 text-sm rounded ${isDark ? "bg-gray-700" : "bg-gray-200"}`}>Cancel</button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-3 gap-4">
        {props.columns?.map((column) => {
          const columnTasks = tasks.filter((t) => t.column === column);
          return (
            <div
              key={column}
              className={`rounded-lg p-3 min-h-[200px] ${isDark ? "bg-gray-800" : "bg-gray-50"}`}
              onDragOver={(e) => e.preventDefault()}
              onDrop={() => handleDrop(column)}
            >
              <div className="flex justify-between items-center mb-3">
                <h3 className="font-medium text-sm">{columnLabels[column] ?? column}</h3>
                <span className={`text-xs px-2 py-0.5 rounded-full ${isDark ? "bg-gray-700" : "bg-gray-200"}`}>
                  {columnTasks.length}
                </span>
              </div>

              <div className="space-y-2">
                {columnTasks.map((task) => (
                  <div
                    key={task.id}
                    draggable
                    onDragStart={() => handleDragStart(task.id)}
                    className={`p-3 rounded border cursor-grab active:cursor-grabbing transition-shadow hover:shadow-md ${
                      isDark ? "border-gray-700 bg-gray-900" : "border-gray-200 bg-white"
                    } ${draggedTask === task.id ? "opacity-50" : ""}`}
                  >
                    <p className="text-sm font-medium">{task.title}</p>
                    <div className="flex justify-between items-center mt-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full capitalize ${priorityColors[task.priority]}`}>
                        {task.priority}
                      </span>
                      {column !== "done" && (
                        <button
                          onClick={() => moveTask(task.id, column === "todo" ? "in-progress" : "done")}
                          className={`text-xs ${isDark ? "text-gray-500 hover:text-gray-300" : "text-gray-400 hover:text-gray-600"}`}
                        >
                          {column === "todo" ? "Start →" : "Done ✓"}
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function Widget() {
  return (
    <McpUseProvider autoSize>
      <KanbanContent />
    </McpUseProvider>
  );
}
```
