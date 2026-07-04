# Workflow: Add MCP to an Existing Next.js App

**Goal:** drop an MCP server into a working Next.js project, share its `lib/`, types, aliases, and Tailwind config, and deploy the MCP either as a separate Node service or as a Vercel route. Use the `--mcp-dir` flag of `@mcp-use/cli`.

## Prerequisites

- An existing Next.js 14+ project with `tsconfig.json` aliases (`@/*`).
- mcp-use ≥ 1.21.5, `@mcp-use/cli` (latest) as a devDependency.

## Layout (added to your existing project)

```
my-next-app/
├── package.json
├── tsconfig.json                     # add resources/**/* to "include" (see below)
├── next.config.ts
├── src/
│   ├── app/                          # untouched
│   ├── components/                   # untouched
│   ├── lib/products.ts               # shared between web + MCP
│   ├── types/product.ts
│   └── mcp/                          # NEW — MCP entry + widgets live here
│       ├── index.ts
│       └── resources/
│           └── product-card/
│               └── widget.tsx
```

## Add to `package.json`

```json
{
  "scripts": {
    "dev:web": "next dev -p 3000",
    "dev:mcp": "mcp-use dev --mcp-dir src/mcp -p 3001",
    "dev": "concurrently \"npm:dev:web\" \"npm:dev:mcp\"",
    "build:web": "next build",
    "build:mcp": "mcp-use build --mcp-dir src/mcp",
    "build": "npm run build:web && npm run build:mcp",
    "start:web": "next start -p 3000",
    "start:mcp": "mcp-use start --mcp-dir src/mcp -p 3001"
  },
  "dependencies": {
    "mcp-use": "^1.21.5",
    "zod": "^4.0.0",
    "next": "^15",
    "react": "^19",
    "react-dom": "^19"
  },
  "devDependencies": {
    "@mcp-use/cli": "latest",
    "concurrently": "^9.0.0"
  }
}
```

## Update `tsconfig.json`

Add `resources/**/*` and the MCP dir to `include`. Aliases already work because the CLI honours `tsconfig.json` paths.

```json
{
  "compilerOptions": {
    "paths": { "@/*": ["./src/*"] }
  },
  "include": ["next-env.d.ts", "src/**/*", ".next/types/**/*", ".mcp-use/**/*"]
}
```

## `src/mcp/index.ts`

The MCP entry can import freely from `@/lib`, `@/types`, anything the rest of the Next app uses.

```typescript
import { MCPServer, widget, text } from "mcp-use/server";
import { z } from "zod";

import { getProduct, listProducts } from "@/lib/products";
import type { Product } from "@/types/product";

const server = new MCPServer({
  name: "next-mcp",
  version: "1.0.0",
  description: "MCP server living inside the Next.js app",
});

server.tool(
  {
    name: "show-product",
    description: "Show a product card for the given id",
    schema: z.object({ id: z.string() }),
    widget: { name: "product-card", invoking: "Loading...", invoked: "Loaded" },
  },
  async ({ id }) => {
    const product: Product = await getProduct(id);
    return widget({
      props: { product },
      message: `Showing ${product.title}`,
    });
  }
);

server.tool(
  {
    name: "list-products",
    description: "List products by category",
    schema: z.object({
      category: z.string().optional(),
      limit: z.number().int().min(1).max(50).default(10),
    }),
  },
  async ({ category, limit }) => {
    const items = await listProducts({ category, limit });
    return text(items.map((p) => `${p.id} ${p.title}`).join("\n"));
  }
);

await server.listen();
```

## `src/mcp/resources/product-card/widget.tsx`

Tailwind classes from the host project work. The CLI re-uses your `tailwind.config.ts`.

```tsx
import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";
import type { Product } from "@/types/product";

export const widgetMetadata: WidgetMetadata = {
  description: "A product card",
  props: z.object({
    product: z.object({
      id: z.string(),
      title: z.string(),
      price: z.number(),
      image: z.string().url(),
    }),
  }),
  metadata: { prefersBorder: true },
};

export default function ProductCard() {
  return (
    <McpUseProvider autoSize>
      <Inner />
    </McpUseProvider>
  );
}

function Inner() {
  const { props, isPending } = useWidget<{ product: Product }>();
  if (isPending) return <div className="p-4 animate-pulse h-32 bg-gray-100" />;
  const p = props.product;
  return (
    <div className="p-4 rounded-lg border border-gray-200 bg-white">
      <img src={p.image} alt={p.title} className="w-full h-40 object-cover rounded mb-3" />
      <h3 className="font-semibold">{p.title}</h3>
      <span className="text-blue-600 font-bold">${p.price}</span>
    </div>
  );
}
```

## Run locally (both services)

```bash
npm install
npm run dev
# Web: http://localhost:3000
# MCP: http://localhost:3001/mcp
# Inspector: http://localhost:3001/inspector
```

## Deploy: Option A — separate Node service (recommended)

The standard production shape. Web on Vercel; MCP on Railway / Fly / Docker.

```bash
# Build both
npm run build

# Run MCP as its own process
npm run start:mcp     # mcp-use start --mcp-dir src/mcp -p 3001
```

Two services, same repo, same env. Wire ChatGPT / Claude to `mcp.example.com`.

## Deploy: Option B — Vercel route (stateless only)

Mount the MCP handler as a catch-all route in the same Next deploy.

```typescript
// app/api/mcp/[...mcp]/route.ts
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";
import { getProduct } from "@/lib/products";

const server = new MCPServer({ name: "next-mcp-route", version: "1.0.0" });

server.tool(
  { name: "get-product", schema: z.object({ id: z.string() }) },
  async ({ id }) => text(JSON.stringify(await getProduct(id)))
);

const handler = await server.getHandler();
export const GET = handler;
export const POST = handler;
export const DELETE = handler;
```

The endpoint becomes `https://<your-app>.vercel.app/api/mcp`.

Stateless constraints apply: no `ctx.sample`, no `ctx.elicit`, no per-session subscriptions, no long-running progress. Use Option A if you need any of those.

## Deploy: Option C — Vercel Edge

Same as Option B with `export const runtime = "edge"`. Stricter still — no `pg`, `fs`, `child_process`. Use Neon / Turso / Upstash for data.

## Notes

- `--mcp-dir` is the load-bearing flag. Use the same value across `dev`, `build`, `start`.
- `mcp-use build --mcp-dir` does **not** transpile your full Next project; Next owns its build. The MCP build records source paths and runs them via `tsx` at start time.
- Aliases: nothing extra to configure. The CLI reads `tsconfig.json` `paths`.
- Tailwind: nothing extra. The CLI reads your existing config so widget classes look right.

## See also

- Drop-in details: `../19-nextjs-drop-in/`
- Stateless vs stateful runtime: `../09-transports/`
- Vercel Edge tool server: `01-stateless-vercel-tool-server.md`
