# MCP Server Project Templates

Starter project structures for building MCP servers with mcp-use.

## Quick Start — `create-mcp-use-app`

```bash
# Fastest way to start — scaffolds a complete project with mcp-use build/dev/start scripts:
npx create-mcp-use-app my-server
cd my-server && npm install && npm run dev
```

The scaffolded project uses the `@mcp-use/cli` scripts (`mcp-use dev`, `mcp-use build`, `mcp-use start`, `mcp-use deploy`) — not raw `tsc`. The entry point is `index.ts` at the project root (not `src/server.ts`).

**Scaffolded project layout:**
```
my-mcp-server/
├── resources/                    # React widgets (MCP-UI / Apps SDK)
│   └── product-search-result/
│       └── widget.tsx
├── public/                       # Static assets (icons, favicon)
├── index.ts                      # MCP server entry point
├── package.json
├── tsconfig.json
└── README.md
```

---

## Template 1: Minimal Server (CLI-scaffolded style)
```
my-mcp-server/
├── package.json
├── tsconfig.json
└── index.ts
```

### `package.json`
```json
{
  "name": "my-mcp-server",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "mcp-use dev",
    "build": "mcp-use build",
    "start": "mcp-use start",
    "deploy": "mcp-use deploy"
  },
  "dependencies": { "mcp-use": "^1.21.5", "zod": "^4.0.0" },
  "devDependencies": { "@mcp-use/cli": "latest", "typescript": "^5.5.0" }
}
```

> **Note (v1.21.5+):** `zod` must be declared in your own `dependencies` — it is a `peerDependency` of `mcp-use` and will not be automatically installed.

### `tsconfig.json`
```json
{
  "compilerOptions": {
    "target": "ES2022", "module": "ESNext", "moduleResolution": "bundler",
    "strict": true, "esModuleInterop": true, "skipLibCheck": true
  },
  "include": ["index.ts", "resources/**/*", ".mcp-use/**/*"]
}
```

### `index.ts`
```typescript
import { MCPServer, text, markdown } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "my-mcp-server", version: "1.0.0", description: "A minimal MCP server",
});

server.tool(
  { name: "greet", description: "Generate a greeting",
    schema: z.object({ name: z.string().describe("Name to greet") }) },
  async ({ name }) => text(`Hello, ${name}! Welcome to MCP.`)
);

server.resource(
  { name: "greeting", uri: "app://greeting", title: "Greeting Message" },
  async () => markdown("# Hello from mcp-use!")
);

// MCP endpoints auto-mounted at /mcp
await server.listen();
```

**Run:** `npm install && npm run dev` (or `npm run build && npm run start` for production)

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
## Template 4: Serverless (Supabase Edge)
```
serverless-mcp-server/
├── deno.json             ← import map (npm: specifiers for Zod conflict resolution)
└── supabase/functions/mcp-server/index.ts
```
### `deno.json`
```json
{
  "imports": {
    "mcp-use/": "npm:mcp-use@latest/",
    "zod": "npm:zod@^4.2.0"
  }
}
```
### `supabase/functions/mcp-server/index.ts`
```typescript
// Uses npm: specifier — resolves via deno.json import map
import { MCPServer, text } from "npm:mcp-use/server";

const server = new MCPServer({
  name: "serverless-mcp",
  version: "1.0.0",
  description: "MCP server deployed on Supabase Edge Functions",
});

server.tool(
  { name: "hello", description: "Greet user" },
  async () => text("Hello from Supabase Edge!")
);

// server.listen() auto-detects the Deno runtime and runs in stateless mode
server.listen().catch(console.error);
```
**Deploy:**
```bash
supabase functions new mcp-server
# copy index.ts and deno.json into supabase/functions/mcp-server/
docker info  # Docker must be running
supabase functions deploy mcp-server --use-docker
```
> **Deno Deploy (standalone):** Use `Deno.serve(server.getHandler())` instead of `server.listen()` for explicit handler export.
---
## Template 5: Widget-Enabled Server (MCP Apps)
```
widget-mcp-server/
├── package.json          ← scripts: "dev": "mcp-use dev", "build": "mcp-use build"
├── tsconfig.json         ← include: ["index.ts", "resources/**/*", ".mcp-use/**/*"]
├── resources/animal-card/widget.tsx
└── index.ts
```
**`package.json` deps:** `"mcp-use": "^1.21.5"`, `"zod": "^4.0.0"`, `"react": "^19"`, `"react-dom": "^19"`, devDeps: `"@mcp-use/cli": "latest"`

> **v1.20.1:** Widget metadata now supports `invoking` and `invoked` status messages. Default widget type changed to `mcpApps` (dual-protocol) in v1.17.0.

### `resources/animal-card/widget.tsx` — widget metadata + React component
```tsx
import React from "react";
import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

const propsSchema = z.object({
  name: z.string(),
  species: z.string(),
  age: z.number(),
  enclosure: z.string(),
});

export const widgetMetadata: WidgetMetadata = {
  description: "Displays zoo animal details",
  props: propsSchema,
  invoking: "Loading animal details...",
  invoked: "Animal details loaded",
};

type AnimalCardProps = z.infer<typeof propsSchema>;

const AnimalCard: React.FC = () => {
  const { props } = useWidget<AnimalCardProps>();
  return (
    <McpUseProvider autoSize>
      <div style={{ padding: "20px", border: "1px solid #e0e0e0", borderRadius: "8px" }}>
        <h2>{props.name}</h2>
        <p><strong>Species:</strong> {props.species}</p>
        <p><strong>Age:</strong> {props.age} years</p>
        <p><strong>Enclosure:</strong> {props.enclosure}</p>
      </div>
    </McpUseProvider>
  );
};

export default AnimalCard;
```
### `index.ts` — widgets in `resources/` are auto-discovered by the CLI
```typescript
import { MCPServer, object, text, widget } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({ name: "widget-mcp-server", version: "1.0.0" });

server.tool(
  {
    name: "get-animal",
    description: "Get zoo animal details with interactive widget",
    schema: z.object({ name: z.string().describe("Animal name") }),
    widget: { name: "animal-card", invoking: "Loading animal...", invoked: "Loaded" },
  },
  async ({ name }) => {
    const animal = { name, species: "lion", age: 7, enclosure: "The Big Cat Plains" };
    return widget({
      props: animal,
      output: text(`Found ${animal.name}, a ${animal.age}-year-old ${animal.species}.`),
    });
  }
);

await server.listen();
```
> `mcp-use dev` for hot-reload development; `mcp-use build` for production bundles.
---
## Template 6: Multi-Server Proxy (Gateway)

Requires `mcp-use` ≥ v1.21.0. `MCPServer.proxy()` is async — must be awaited before `listen()`.

```
mcp-gateway/
├── package.json          ← reuse Template 1 package.json structure
└── index.ts
```
### `index.ts`
```typescript
import { MCPServer, object } from "mcp-use/server";

const gateway = new MCPServer({
  name: "mcp-gateway",
  version: "1.0.0",
  description: "Gateway composing multiple MCP servers",
});

// proxy() is async — await it before listen()
await gateway.proxy({
  github:     { command: "npx", args: ["-y", "@modelcontextprotocol/server-github"] },
  filesystem: { command: "npx", args: ["-y", "@modelcontextprotocol/server-filesystem", "./data"] },
  db:         { url: "https://db-mcp.internal:3001/mcp" },
});

// Gateway-level tool (available alongside proxied tools)
gateway.tool(
  { name: "health", description: "Check all upstream servers" },
  async () => object({ servers: ["github", "filesystem", "db"], status: "healthy" })
);

await gateway.listen(3000);
```

---

## Template 7: Monorepo Workspace (Turborepo)

Manage multiple MCP servers and shared libraries in a single repository.

```
mcp-monorepo/
├── package.json
├── turbo.json
├── apps/
│   ├── api-server/       # HTTP Server
│   └── worker/           # Background Worker
└── packages/
    ├── shared-utils/     # Common code
    └── schemas/          # Shared Zod schemas
```

### Root `package.json`

```json
{
  "name": "mcp-monorepo",
  "private": true,
  "workspaces": ["apps/*", "packages/*"],
  "scripts": {
    "build": "turbo run build",
    "dev": "turbo run dev",
    "lint": "turbo run lint"
  },
  "devDependencies": { "turbo": "latest" }
}
```

### `packages/shared-utils/src/index.ts`

```typescript
import { z } from "zod";

export const commonSchemas = {
  pagination: z.object({
    page: z.number().default(1),
    limit: z.number().default(10),
  }),
};

export function logger(name: string) {
  return {
    info: (msg: string) => console.log(`[${name}] ${msg}`),
  };
}
```

### `apps/api-server/src/server.ts`

```typescript
import { MCPServer, text } from "mcp-use/server";
import { commonSchemas, logger } from "@repo/shared-utils";

const log = logger("api");
const server = new MCPServer({ name: "api", version: "1.0.0" });

server.tool(
  { name: "list", schema: commonSchemas.pagination },
  async ({ page, limit }) => {
    log.info(`Listing page ${page}`);
    return text(`Page ${page} of items`);
  }
);

await server.listen(3000);
```

---

## Template 8: Existing App + MCP Side-Car

Run MCP alongside an existing HTTP service on a separate port. Because `MCPServer` is a self-contained Hono application, the idiomatic pattern is to start it on its own port rather than mounting it as Express/Fastify middleware.

```
multi-service-app/
├── src/
│   ├── api.ts       # Existing HTTP service (Express/Fastify/etc.)
│   └── mcp.ts       # MCP server on a separate port
```

### `src/mcp.ts`

```typescript
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";

export async function startMCPServer(port = 3001) {
  const server = new MCPServer({
    name: "sidecar-mcp",
    version: "1.0.0",
  });

  // Add custom REST routes alongside MCP — MCPServer IS a Hono app
  server.get("/api/status", (c) => c.json({ status: "ok" }));

  server.tool(
    { name: "ping", schema: z.object({}) },
    async () => text("pong")
  );

  await server.listen(port);
  console.log(`MCP server running on http://localhost:${port}/mcp`);
}
```

### `src/api.ts`

```typescript
import express from "express";
import { startMCPServer } from "./mcp.js";

const app = express();
const PORT = 3000;

// Existing Express routes
app.get("/", (req, res) => res.send("Hello from Express"));

app.listen(PORT, () => {
  console.log(`Express API on http://localhost:${PORT}`);
});

// Start MCP server on its own port
startMCPServer(3001).catch(console.error);
```

> **Note:** `MCPServer` is built on Hono and starts its own HTTP server via `server.listen()`. Use `server.get()`, `server.post()`, `server.use()` to add custom routes/middleware to the same MCP server instead of mounting it into Express or Fastify.

---

## Template 9: Custom Routes and Middleware (Hono)

Add REST endpoints, authentication middleware, and sub-apps directly on the `MCPServer` instance (which is a Hono app).

```
hono-extended-server/
└── src/server.ts
```

```typescript
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";
import { cors } from "hono/cors";
import { logger } from "hono/logger";

const server = new MCPServer({ name: "extended-server", version: "1.0.0" });

// Hono middleware
server.use(logger());
server.use("/api/*", cors());

// Auth middleware for specific paths
server.use("/secure/*", async (c, next) => {
  const token = c.req.header("Authorization");
  if (token !== "Bearer secret") return c.text("Unauthorized", 401);
  await next();
});

// Custom REST endpoints
server.get("/api/status", (c) => c.json({ status: "ok", mcp: true }));
server.post("/secure/trigger", async (c) => {
  const body = await c.req.json();
  return c.json({ triggered: true, data: body });
});

// MCP tool
server.tool(
  { name: "echo", schema: z.object({ msg: z.string() }) },
  async ({ msg }) => text(msg)
);

// Mount a sub-app
const adminApp = new MCPServer({ name: "admin", version: "1.0.0" });
adminApp.get("/", (c) => c.text("Admin Area"));
server.route("/admin", adminApp);

await server.listen(3000);
```

---

## Template 10: NestJS Module

Integrate MCP into a NestJS application using a dynamic module.

```
src/
├── app.module.ts
├── mcp/
│   ├── mcp.module.ts
│   └── mcp.service.ts
```

### `mcp.service.ts`

```typescript
import { Injectable, OnModuleInit, OnModuleDestroy } from "@nestjs/common";
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";

@Injectable()
export class McpService implements OnModuleInit, OnModuleDestroy {
  private server: MCPServer;

  constructor() {
    this.server = new MCPServer({ name: "nest-mcp", version: "1.0.0" });
    this.registerTools();
  }

  private registerTools() {
    this.server.tool(
      { name: "info", schema: z.object({}) },
      async () => text("NestJS MCP Server")
    );
  }

  async onModuleInit() {
    // Start MCP server on a separate port or integrate via middleware
    await this.server.listen(3001);
    console.log("MCP Server listening on 3001");
  }

  async onModuleDestroy() {
    // Cleanup if needed
  }
}
```

### `mcp.module.ts`

```typescript
import { Module } from "@nestjs/common";
import { McpService } from "./mcp.service";

@Module({
  providers: [McpService],
  exports: [McpService],
})
export class McpModule {}
```

---

## Template 11: Electron Desktop App

Embed an MCP server inside an Electron application to expose local desktop capabilities.

```
electron-app/
├── src/
│   ├── main.ts
│   ├── preload.ts
│   └── mcp-server.ts
```

### `src/mcp-server.ts`

```typescript
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";
import { shell } from "electron";

export async function startMCPServer() {
  const server = new MCPServer({ name: "electron-mcp", version: "1.0.0" });

  server.tool(
    { name: "open-url", schema: z.object({ url: z.string().url() }) },
    async ({ url }) => {
      await shell.openExternal(url);
      return text(`Opened ${url}`);
    }
  );

  // Listen on localhost only
  await server.listen(3000);
}
```

### `src/main.ts`

```typescript
import { app, BrowserWindow } from "electron";
import { startMCPServer } from "./mcp-server";

app.whenReady().then(() => {
  createWindow();
  startMCPServer().catch(console.error);
});
```

---

## Template 12: Background Worker (BullMQ)

Decouple tool execution from HTTP response for long-running tasks.

```
worker-server/
├── src/
│   ├── server.ts
│   ├── worker.ts
│   └── queue.ts
```

### `src/queue.ts`

```typescript
import { Queue } from "bullmq";
export const taskQueue = new Queue("tasks", { connection: { host: "localhost" } });
```

### `src/server.ts`

```typescript
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";
import { taskQueue } from "./queue.js";

const server = new MCPServer({ name: "producer", version: "1.0.0" });

server.tool(
  { name: "start-job", schema: z.object({ name: z.string() }) },
  async ({ name }) => {
    const job = await taskQueue.add("process", { name });
    return text(`Job ${job.id} queued`);
  }
);

await server.listen(3000);
```

### `src/worker.ts`

```typescript
import { Worker } from "bullmq";

const worker = new Worker("tasks", async (job) => {
  console.log(`Processing ${job.data.name}...`);
  await new Promise(r => setTimeout(r, 5000));
  console.log("Done");
}, { connection: { host: "localhost" } });
```
