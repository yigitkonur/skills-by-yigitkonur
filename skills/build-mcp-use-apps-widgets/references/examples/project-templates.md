# MCP Project Templates

Starter project structures for building MCP servers and MCP Apps with mcp-use.

## Quick Start — `create-mcp-use-app`

```bash
# Fastest way to start — scaffolds a complete project:
npx create-mcp-use-app my-app
cd my-app && npm install && npm run dev
```

### Template Options

```bash
# Default starter — tools, resources, prompts, and widgets
npx create-mcp-use-app my-app --template starter

# MCP Apps — widget-focused for ChatGPT and MCP clients
npx create-mcp-use-app my-app --template mcp-apps

# MCP-UI — iframe, raw HTML, Remote DOM widget types
npx create-mcp-use-app my-app --template mcp-ui
```

| Template | Includes | Best for |
|----------|----------|----------|
| `starter` (default) | Tools, resources, prompts, UI widgets | Full-featured servers, learning all MCP features |
| `mcp-apps` | React widgets, useCallTool, ChatGPT compatibility | Interactive widget apps for chat clients |
| `mcp-ui` | All three UIResource types (iframe, raw HTML, Remote DOM) | Complex UI requirements, MCP-UI spec compliance |

---

## Template: MCP Apps (Widget-Focused)

The `mcp-apps` template creates a project optimized for building interactive widgets that work in ChatGPT, Claude, and other MCP clients.

```bash
npx create-mcp-use-app my-widget-app --template mcp-apps
```

### Project Structure

```
my-widget-app/
├── package.json
├── tsconfig.json
├── index.ts                       # MCP server entry point
├── resources/                     # Widget components
│   └── product-search-result/
│       ├── widget.tsx             # Widget entry (default export + widgetMetadata)
│       ├── components/
│       │   ├── ProductCard.tsx
│       │   └── SearchFilters.tsx
│       └── types.ts
├── public/                        # Static assets
│   ├── icon.svg
│   └── favicon.ico
└── .mcp-use/                      # Auto-generated
    └── tool-registry.d.ts         # Type-safe useCallTool types
```

> **Note on entry point location:** This template uses `index.ts` at the project root, matching the `create-mcp-use-app` scaffolding. For manual setup, you can also organize your entry point as `src/server.ts` — both conventions work with `mcp-use dev`. See Template 5 below and the quick-start guide for the `src/` layout.

### `package.json`

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
    "mcp-use": "^1.21.0",
    "zod": "^4.0.0"
  },
  "devDependencies": {
    "@mcp-use/cli": "latest",
    "typescript": "^5.5.0",
    "@types/node": "^22.0.0",
    "@types/react": "^19.0.0"
  }
}
```

### `tsconfig.json`

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
  "include": ["src", "index.ts", "resources/**/*", ".mcp-use/**/*"]
}
```

### `index.ts` — Server with Widget-Enabled Tool

```typescript
import { MCPServer, widget } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "my-widget-app",
  version: "1.0.0",
  description: "MCP App with interactive widgets",
});

server.tool(
  {
    name: "search-products",
    description: "Search for products by query and display results as an interactive widget",
    schema: z.object({
      query: z.string().describe("Search query"),
      category: z.string().optional().describe("Product category filter"),
    }),
    widget: {
      name: "product-search-result",  // Matches resources/product-search-result/
      invoking: "Searching products...",
      invoked: "Products found",
    },
  },
  async ({ query, category }) => {
    // Replace with real product API
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

### `resources/product-search-result/widget.tsx` — Widget Component

```tsx
import { McpUseProvider, useWidget, useCallTool, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

export const widgetMetadata: WidgetMetadata = {
  description: "Displays product search results with filtering and sorting",
  props: z.object({
    products: z.array(z.object({
      id: z.string(), name: z.string(), price: z.number(), rating: z.number(),
    })),
    query: z.string(),
    category: z.string(),
  }),
  metadata: { prefersBorder: true },
};

interface Product {
  id: string;
  name: string;
  price: number;
  rating: number;
}

function ProductSearchContent() {
  const { props, isPending, theme } = useWidget<{
    products: Product[];
    query: string;
    category: string;
  }>();
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

### What Each File Does

| File | Purpose |
|------|---------|
| `index.ts` | MCP server entry — registers tools, starts HTTP server |
| `resources/*/widget.tsx` | Widget entry — default export (React) + widgetMetadata |
| `resources/*/components/` | Sub-components used by the widget |
| `public/` | Static assets served at `/mcp-use/public/` |
| `.mcp-use/tool-registry.d.ts` | Auto-generated types for type-safe `useCallTool` |
| `tsconfig.json` | Must include `jsx: "react-jsx"` and `resources/**/*` |

### Development

```bash
npm run dev     # HMR + Inspector at localhost:3000/inspector
npm run build   # Production build
npm run start   # Production server
```

---

## Template 1: Minimal CLI Server
```
my-mcp-server/
├── package.json
├── tsconfig.json
└── src/server.ts
```

### `package.json`
```json
{
  "name": "my-mcp-server",
  "version": "1.0.0",
  "type": "module",
  "bin": { "my-mcp-server": "./dist/server.js" },
  "scripts": { "build": "tsc", "start": "node dist/server.js", "dev": "tsx src/server.ts" },
  "dependencies": { "mcp-use": "^1.21.0", "zod": "^4.0.0" },
  "devDependencies": { "tsx": "^4.0.0", "typescript": "^5.5.0" }
}
```

### `tsconfig.json`
```json
{
  "compilerOptions": {
    "target": "ES2022", "module": "ESNext", "moduleResolution": "bundler",
    "outDir": "dist", "rootDir": "src", "strict": true,
    "esModuleInterop": true, "skipLibCheck": true, "declaration": true
  },
  "include": ["src"]
}
```

### `src/server.ts`
```typescript
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "my-mcp-server", version: "1.0.0", description: "A minimal MCP server",
});

server.tool(
  { name: "greet", description: "Generate a greeting",
    schema: z.object({ name: z.string().describe("Name to greet") }) },
  async ({ name }) => text(`Hello, ${name}! Welcome to MCP.`)
);

await server.listen();
```

**Run:** `npm install && npm run build && echo '{}' | npx my-mcp-server`

---

## Template 2: Production HTTP Server

```
production-mcp-server/
├── package.json
├── tsconfig.json
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── src/
    ├── server.ts
    ├── config.ts
    └── tools/
        ├── index.ts
        └── search.ts
```

### `src/config.ts`
```typescript
import "dotenv/config";
export const config = {
  name: "production-server",
  version: process.env.npm_package_version || "1.0.0",
  port: parseInt(process.env.PORT || "3000", 10),
  redisUrl: process.env.REDIS_URL || "redis://localhost:6379",
};
```

### `src/tools/search.ts` — modular tool registration pattern
```typescript
import { object } from "mcp-use/server";
import type { MCPServer } from "mcp-use/server";
import { z } from "zod";

export function registerSearchTools(server: MCPServer) {
  server.tool(
    { name: "search", description: "Search indexed documents",
      schema: z.object({ query: z.string().min(1), limit: z.number().default(10) }) },
    async ({ query, limit }) => object({ query, results: [], count: 0 }) // replace with real search
  );
}
```

### `src/tools/index.ts` — barrel file registers all tool modules
```typescript
import type { MCPServer } from "mcp-use/server";
import { registerSearchTools } from "./search.js";
export function registerAllTools(server: MCPServer) { registerSearchTools(server); }
```

### `src/server.ts`
```typescript
import { MCPServer } from "mcp-use/server";
import { config } from "./config.js";
import { registerAllTools } from "./tools/index.js";

const server = new MCPServer({ name: config.name, version: config.version, description: "Production MCP server" });
registerAllTools(server);
await server.listen(config.port);
```

### `.env.example`
```env
PORT=3000
REDIS_URL=redis://localhost:6379
API_KEY=your-api-key-here
```

### `Dockerfile` (also reuse for Template 3)
```dockerfile
FROM node:22-slim AS build
WORKDIR /app
COPY package*.json tsconfig.json ./
COPY src ./src
RUN npm ci && npm run build

FROM node:22-slim
WORKDIR /app
COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules ./node_modules
COPY package*.json ./
ENV NODE_ENV=production
EXPOSE 3000
CMD ["node", "dist/server.js"]
```

### `docker-compose.yml`
```yaml
services:
  mcp-server:
    build: .
    ports: ["3000:3000"]
    environment: [PORT=3000, "REDIS_URL=redis://redis:6379", "API_KEY=${API_KEY}"]
    depends_on: [redis]
    restart: unless-stopped
  redis:
    image: redis:7-alpine
    volumes: [redis-data:/data]
volumes:
  redis-data:
```

---

## Template 3: OAuth-Protected Server
```
oauth-mcp-server/
├── package.json          ← add dotenv
├── tsconfig.json
├── .env.example
├── Dockerfile            ← reuse from Template 2
└── src/
    ├── server.ts, config.ts
    └── tools/protected.ts
```

### `src/config.ts`
```typescript
import "dotenv/config";
export const config = {
  name: "oauth-mcp-server", version: "1.0.0",
  port: parseInt(process.env.PORT || "3000", 10),
};
```

### `src/tools/protected.ts`
```typescript
import { object, error } from "mcp-use/server";
import type { MCPServer } from "mcp-use/server";
import { z } from "zod";

export function registerProtectedTools(server: MCPServer) {
  server.tool(
    { name: "list-users", description: "List org users (requires read:users)",
      schema: z.object({ page: z.number().default(1), limit: z.number().default(20) }) },
    async ({ page, limit }, ctx) => {
      if (!ctx.auth?.permissions?.includes("read:users")) return error("Forbidden: requires read:users");
      return object({ users: [], total: 0 }); // replace with real user store
    }
  );

  server.tool(
    { name: "get-tenant-config", description: "Get config for authenticated tenant", schema: z.object({}) },
    async (_params, ctx) => {
      if (!ctx.auth) return error("Authentication required");
      return object({ tenant: ctx.auth.userId, features: ["search", "analytics"], plan: "pro" });
    }
  );
}
```

### `src/server.ts`
```typescript
import { MCPServer, oauthAuth0Provider } from "mcp-use/server";
import { config } from "./config.js";
import { registerProtectedTools } from "./tools/protected.js";

const server = new MCPServer({
  name: config.name,
  version: config.version,
  description: "OAuth-protected MCP server",
  oauth: oauthAuth0Provider({
    domain: process.env.MCP_USE_OAUTH_AUTH0_DOMAIN!,
    audience: process.env.MCP_USE_OAUTH_AUTH0_AUDIENCE!,
  }),
});

registerProtectedTools(server);
await server.listen(config.port);
```

### `.env.example`
```env
PORT=3000
MCP_USE_OAUTH_AUTH0_DOMAIN=your-tenant.auth0.com
MCP_USE_OAUTH_AUTH0_AUDIENCE=https://api.your-app.com
```
---
## Template 4: Serverless (Supabase Edge / Deno Deploy)
```
serverless-mcp-server/
├── package.json          ← deps: mcp-use, zod (no build scripts needed)
└── supabase/functions/mcp-server/index.ts
```
### `supabase/functions/mcp-server/index.ts`
```typescript
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";
const server = new MCPServer({ name: "serverless-mcp", version: "1.0.0", description: "Serverless MCP server" });
server.tool(
  { name: "hello", description: "Greet user", schema: z.object({ name: z.string() }) },
  async ({ name }) => text(`Hello, ${name}!`)
);
await server.listen(); // Edge runtimes (Deno/Supabase) are auto-detected as stateless
```
> **Deno Deploy:** `server.listen()` auto-detects edge runtimes and runs in stateless mode — no special export needed.
---
## Template 5: Widget-Enabled Server (MCP Apps)

> **Tip:** For a fully scaffolded version, use `npx create-mcp-use-app my-app --template mcp-apps` (see MCP Apps template above).

```
widget-mcp-server/
├── package.json          ← scripts: "dev": "mcp-use dev", "build": "mcp-use build"
├── tsconfig.json         ← include: ["src", "resources/**/*", ".mcp-use/**/*"], jsx: "react-jsx"
├── resources/dashboard/widget.tsx
└── src/server.ts
```
**`package.json` deps:** `"mcp-use": "^1.21.0"`, `"zod": "^4.0.0"`, devDeps: `"@mcp-use/cli": "latest"`
### `resources/dashboard/widget.tsx` — widget metadata + React component
```tsx
import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

export const widgetMetadata: WidgetMetadata = {
  description: "Displays server health metrics",
  props: z.object({ refreshInterval: z.number().default(30).describe("Refresh interval in seconds") }),
  metadata: { prefersBorder: true },
};

interface DashboardProps {
  refreshInterval: number;
}

function DashboardContent() {
  const { props, isPending } = useWidget<DashboardProps>();
  if (isPending) return <div className="animate-pulse p-4 h-24" />;
  return (
    <div>
      <h2>System Dashboard</h2>
      <p>Auto-refresh every {props.refreshInterval}s</p>
    </div>
  );
}

export default function Dashboard() {
  return (
    <McpUseProvider autoSize>
      <DashboardContent />
    </McpUseProvider>
  );
}
```
### `src/server.ts` — widgets in `resources/` are auto-discovered by the CLI
```typescript
import { MCPServer, object } from "mcp-use/server";
import { z } from "zod";
const server = new MCPServer({ name: "widget-mcp-server", version: "1.0.0", description: "MCP server with widget support" });
server.tool(
  { name: "get-metrics", description: "Fetch server metrics",
    schema: z.object({ range: z.enum(["1h", "24h", "7d"]).default("1h") }) },
  async ({ range }) => object({ cpu: 42, memory: 68, range, uptime: "3d 12h" })
);
await server.listen();
```
> `mcp-use dev` for hot-reload development; `mcp-use build` for production bundles.
---
## Template 6: Multi-Server Proxy (Gateway)
```
mcp-gateway/
├── package.json          ← reuse Template 1 package.json structure
└── src/server.ts
```
### `src/server.ts`
```typescript
import { MCPServer, object } from "mcp-use/server";
const gateway = new MCPServer({ name: "mcp-gateway", version: "1.0.0", description: "Gateway composing multiple MCP servers" });
await gateway.proxy({
  github:     { command: "npx", args: ["-y", "@modelcontextprotocol/server-github"] },
  filesystem: { command: "npx", args: ["-y", "@modelcontextprotocol/server-filesystem", "./data"] },
  db:         { url: "https://db-mcp.internal:3001/mcp" } });
gateway.tool(
  { name: "health", description: "Check all upstream servers" },
  async () => object({ servers: ["github", "filesystem", "db"], status: "healthy" })
);
await gateway.listen(3000);
```
