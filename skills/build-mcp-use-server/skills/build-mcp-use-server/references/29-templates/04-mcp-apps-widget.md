# Template: MCP Apps Widget Server

Canonical scaffold from `npx create-mcp-use-app my-app --template mcp-apps`. Tools return `widget({ props, message })` and reference React components in `resources/`. Compatible with ChatGPT, Claude, and any MCP-Apps-aware client.

## Scaffold

```bash
npx create-mcp-use-app my-widget-app --template mcp-apps --no-skills
cd my-widget-app && npm install && npm run dev
```

## Layout

```
my-widget-app/
├── package.json
├── tsconfig.json
├── index.ts                       # MCP server entry point
├── resources/                     # Widget components (auto-discovered)
│   └── product-search-result/
│       ├── widget.tsx             # Default export + widgetMetadata
│       ├── components/
│       │   ├── ProductCard.tsx
│       │   └── SearchFilters.tsx
│       └── types.ts
├── public/                        # Static assets at /mcp-use/public/
│   ├── icon.svg
│   └── favicon.ico
└── .mcp-use/
    └── tool-registry.d.ts         # Auto-generated useCallTool types
```

## `package.json`

```json
{
  "name": "my-widget-app",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "mcp-use dev",
    "build": "mcp-use build",
    "start": "mcp-use start"
  },
  "dependencies": {
    "mcp-use": "^1.21.5",
    "zod": "^4.0.0",
    "react": "^19",
    "react-dom": "^19"
  },
  "devDependencies": {
    "@mcp-use/cli": "latest",
    "typescript": "^5.5.0",
    "@types/node": "^22.0.0",
    "@types/react": "^19.0.0"
  }
}
```

## `tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "jsx": "react-jsx",
    "strict": true,
    "outDir": "dist",
    "declaration": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["index.ts", "resources/**/*", ".mcp-use/**/*"]
}
```

## `index.ts`

```typescript
import { MCPServer, widget } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "my-widget-app",
  version: "1.0.0",
  description: "MCP App with interactive widgets",
  baseUrl: process.env.MCP_URL,
});

server.tool(
  {
    name: "search-products",
    description: "Search products and display them as an interactive widget",
    schema: z.object({
      query: z.string().describe("Search query"),
      category: z.string().optional().describe("Product category filter"),
    }),
    widget: {
      name: "product-search-result", // matches resources/product-search-result/
      invoking: "Searching products...",
      invoked: "Products found",
    },
  },
  async ({ query, category }) => {
    const products = [
      { id: "1", name: `${query} Widget`, price: 29.99, rating: 4.5 },
      { id: "2", name: `${query} Pro`, price: 49.99, rating: 4.8 },
    ];

    return widget({
      props: { products, query, category: category ?? "all" },
      message: `Found ${products.length} products for "${query}"`,
    });
  }
);

await server.listen();
```

## `resources/product-search-result/types.ts`

```typescript
export interface Product {
  id: string;
  name: string;
  price: number;
  rating: number;
}

export interface ProductSearchProps {
  products: Product[];
  query: string;
  category: string;
}
```

## `resources/product-search-result/widget.tsx`

```tsx
import { McpUseProvider, useWidget, useCallTool, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";
import type { ProductSearchProps } from "./types.js";

export const widgetMetadata: WidgetMetadata = {
  description: "Displays product search results with filtering and sorting",
  props: z.object({
    products: z.array(z.object({
      id: z.string(),
      name: z.string(),
      price: z.number(),
      rating: z.number(),
    })),
    query: z.string(),
    category: z.string(),
  }),
  metadata: { prefersBorder: true },
};

function ProductSearchContent() {
  const { props, isPending, theme } = useWidget<ProductSearchProps>();
  const { callTool: refine, isPending: searching } = useCallTool("search-products");

  if (isPending) {
    return (
      <div className="animate-pulse p-4 space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-16 bg-gray-200 dark:bg-gray-700 rounded" />
        ))}
      </div>
    );
  }

  const isDark = theme === "dark";

  return (
    <div className={`p-4 ${isDark ? "bg-gray-900 text-white" : "bg-white text-gray-900"}`}>
      <h2 className="text-lg font-bold mb-3">
        Results for "{props.query}" ({props.products?.length ?? 0})
      </h2>
      <div className="space-y-3">
        {props.products?.map((product) => (
          <div
            key={product.id}
            className={`p-3 rounded border ${isDark ? "border-gray-700 bg-gray-800" : "border-gray-200 bg-gray-50"}`}
          >
            <div className="flex justify-between items-center">
              <h3 className="font-medium">{product.name}</h3>
              <span className="font-bold">${product.price}</span>
            </div>
            <div className="text-yellow-500 text-sm mt-1">
              {"★".repeat(Math.floor(product.rating))} {product.rating}
            </div>
          </div>
        ))}
      </div>
      <button
        onClick={() => refine({ query: props.query, category: "electronics" })}
        disabled={searching}
        className="mt-3 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 text-sm"
      >
        {searching ? "Searching..." : "Refine Search"}
      </button>
    </div>
  );
}

export default function Widget() {
  return (
    <McpUseProvider autoSize>
      <ProductSearchContent />
    </McpUseProvider>
  );
}
```

## File-by-file role

| File | Purpose |
|---|---|
| `index.ts` | MCP server entry — registers tools, starts HTTP server |
| `resources/*/widget.tsx` | Default-exported React component + named `widgetMetadata` |
| `resources/*/components/` | Sub-components used by the widget |
| `public/` | Static assets served at `/mcp-use/public/` |
| `.mcp-use/tool-registry.d.ts` | Auto-generated types for type-safe `useCallTool` |
| `tsconfig.json` | Must include `jsx: "react-jsx"` and `resources/**/*` |

## Develop

```bash
npm run dev     # HMR + Inspector at localhost:3000/inspector
npm run build   # Production bundle
npm run start   # Production server
```

> **v1.20.1+:** widget metadata supports `invoking` and `invoked` status messages. Default widget type is `mcpApps` (dual-protocol with MCP-UI) since v1.17.0.

## See also

- Full widget patterns: `../18-mcp-apps/`
- Streaming widget props: `../30-workflows/11-streaming-chart-widget.md`
- CSP for external APIs in widgets: `../18-mcp-apps/` and `../31-canonical-examples/01-mcp-widget-gallery.md`
