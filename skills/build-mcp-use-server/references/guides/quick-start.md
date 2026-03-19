# Quick Start

Build a working MCP server in under 10 minutes using the `mcp-use` TypeScript framework.

---

## 1. Prerequisites

- **Node.js 18** (or higher) — [download](https://nodejs.org/)
- **Package manager** — npm (bundled with Node), pnpm, or yarn

Verify your setup:

```bash
node --version   # v18.x.x or higher
npm --version    # 9.x.x or higher
```

---

## 2. Project Scaffolding (Recommended)

The fastest way to start is `create-mcp-use-app`:

```bash
npx create-mcp-use-app my-mcp-server
cd my-mcp-server
npm run dev
```

This command will create a new MCP server with:

- A complete TypeScript MCP server project structure.
- Example MCP Tools and Resources to get you started.
- Example UI Widgets React components in `resources/` folder exposed as tools and resources in MCP Apps and ChatGPT Apps SDK format.
- Pre-configured server metadata (title, icons, websiteUrl) with your project name.
- Hot Module Reloading (HMR) — modify tools/prompts/resources without restarting or dropping connections.
- Automatically launches an MCP Inspector in your browser to test your server.

### Generated File Walkthrough

After creation, your project will have this structure:

```
my-mcp-server/
├── resources/                     # React widgets (MCP Apps + ChatGPT)
│   └── product-search-result/
│       ├── widget.tsx             # Widget entry point
│       ├── components/            # Sub-components
│       └── types.ts
├── public/                        # Static assets (icons, favicon)
│   ├── icon.svg
│   └── favicon.ico
├── index.ts                       # MCP server entry point
├── package.json
├── tsconfig.json
└── README.md
```

The scaffolded project uses `index.ts` at the project root as its entry point.

If you used the scaffolder, skip to [Section 6](#6-development-workflow).

---

## 3. Manual Setup

For existing projects or custom configurations, set up from scratch.

### Install the package

```bash
npm install mcp-use
```

Or, to initialize a brand-new project first:

```bash
mkdir my-mcp-server && cd my-mcp-server
npm init -y
npm install mcp-use
npm install -D typescript @types/node tsx
```

### Configure package.json

Update `package.json` with these fields:

```json
{
  "name": "my-mcp-server",
  "version": "1.0.0",
  "type": "module",
  "main": "dist/server.js",
  "scripts": {
    "dev": "mcp-use dev src/server.ts",
    "build": "mcp-use build",
    "start": "mcp-use start",
    "deploy": "mcp-use deploy",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "mcp-use": "latest"
  }
}
```

- **`"type": "module"`** — required; without this, imports from `mcp-use/server` fail.
- **`"dev"`** — uses `mcp-use dev` for hot-reload with auto-embedded Inspector.
- **`"build"`** — compiles TypeScript to `dist/`.
- **`"start"`** — runs the compiled code in production mode.
- **`"deploy"`** — deploys the server to Manufact Cloud.

### Configure tsconfig.json

Create `tsconfig.json` with strict settings:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "strict": true,
    "outDir": "./dist",
    "rootDir": "./src",
    "declaration": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true
  },
  "include": ["src/**/*"]
}
```

> `"module": "NodeNext"` / `"moduleResolution": "NodeNext"` are also valid and recommended for modern Node.js environments.

Key settings for MCP servers:

- **`"target": "ES2022"`**: Ensures top-level await and class fields work natively.
- **`"module": "Node16"`**: Uses `.mjs` output for ESM compatibility.
- **`"moduleResolution": "Node16"`**: Proper package exports support (essential for `mcp-use`).
- **`"strict": true`**: Prevents `any` leaks in tool arguments.
- **`"skipLibCheck": true`**: Speeds up compilation by ignoring `node_modules`.

If you see `Cannot find module`, check `moduleResolution`. If you see `SyntaxError: unexpected token export`, check `type: module` in `package.json`.

### Create the source directory

```bash
mkdir src
```

---

## 4. Project Structure

A standard mcp-use project looks like this:

```
my-mcp-server/
├── resources/                     # React widgets (MCP Apps + ChatGPT)
│   ├── product-search-result/   # Example widget (folder name = widget name)
│   │   ├── widget.tsx             # Main widget component
│   │   ├── types.ts               # Props and types
│   │   ├── components/            # Optional subcomponents
│   │   └── hooks/                 # Optional hooks
│   └── styles.css                # Shared styles
├── public/                        # Static assets (icons, favicon)
│   ├── icon.svg
│   └── favicon.ico
├── index.ts                       # MCP server entry point (scaffolded)
├── src/
│   └── server.ts                  # Entry point (manual setup)
├── package.json
├── tsconfig.json
└── README.md
```

The `resources/` and `public/` directories are optional. Scaffolded projects use `index.ts` at the root; manual projects typically use `src/server.ts`.

---

## 5. Minimal Server

The simplest possible mcp-use server:

```typescript
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "my-server",
  title: "My Server",        // display name shown in clients
  version: "1.0.0",
  description: "My custom MCP server",
  websiteUrl: "https://mcp-use.com",
  favicon: "favicon.ico",
  icons: [
    {
      src: "icon.svg",
      mimeType: "image/svg+xml",
      sizes: ["512x512"],
      theme: "light"          // optional: "light" | "dark"
    }
  ]
});

// Define a tool
server.tool(
  {
    name: "get_weather",
    description: "Get weather for a city",
    schema: z.object({
      city: z.string().describe("City name"),
    }),
  },
  async ({ city }) => {
    return text(`Temperature: 72°F, Condition: sunny, City: ${city}`);
  }
);

// Start the HTTP server (Streamable HTTP)
server.listen(3000);
// Inspector available at http://localhost:3000/inspector
```

`listen()` starts an HTTP server using MCP Streamable HTTP transport on port 3000 by default. Override via the `PORT` env variable.

### MCPServer Constructor Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `name` | `string` | Yes | – | Server identifier (shown in inspector and discovery). |
| `version` | `string` | Yes | – | Semantic version string. |
| `title` | `string` | No | `name` | Human-readable display name shown in clients and Inspector. |
| `description` | `string` | No | – | Short description shown during discovery. |
| `websiteUrl` | `string` | No | – | Your website or docs URL. |
| `favicon` | `string` | No | – | Path to favicon file relative to `public/`. |
| `icons` | `Array<{ src: string; mimeType?: string; sizes?: string[]; theme?: "light" \| "dark" }>` | No | – | Icon definitions for PWA/manifest. `theme` can be `"light"` or `"dark"`. |
| `host` | `string` | No | `'localhost'` | Hostname the HTTP server binds to. |
| `baseUrl` | `string` | No | – | Public base URL for widget/asset URLs behind reverse proxies or CDNs. Also read from `MCP_URL` env var. |
| `cors` | `{ origin: string[]; allowMethods: string[]; allowHeaders?: string[]; exposeHeaders?: string[] }` | No | Permissive (see below) | CORS configuration; replaces the built-in permissive default. |
| `allowedOrigins` | `string[]` | No | – | Host header whitelist for DNS-rebinding protection. |
| `stateless` | `boolean` | No | Auto-detect | Force stateless (`true`) or stateful (`false`) mode. |
| `sessionIdleTimeoutMs` | `number` | No | `86400000` (1 day) | Idle session TTL in milliseconds. |
| `sessionStore` | `SessionStore` | No | `InMemorySessionStore` | Pluggable store for session metadata. |
| `streamManager` | `StreamManager` | No | `InMemoryStreamManager` | Controls SSE stream handling. |
| `oauth` | `OAuthProvider` | No | – | Authentication provider (use `oauthAuth0Provider`, `oauthSupabaseProvider`, `oauthKeycloakProvider`, or `oauthCustomProvider`). |
| `autoCreateSessionOnInvalidId` | `boolean` | No | – | **Deprecated.** Server now returns 404 for invalid sessions per MCP spec. Use `sessionStore` for persistence instead. |

> **Note:** Icon paths (like `icon.svg`) are automatically converted to absolute URLs (e.g., `http://localhost:3000/mcp-use/public/icon.svg`) when `baseUrl` is configured.

**Default CORS configuration** (used when `cors` is not overridden):

```ts
{
  origin: '*',
  allowMethods: ['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowHeaders: [
    'Content-Type', 'Accept', 'Authorization',
    'mcp-protocol-version', 'mcp-session-id',
    'X-Proxy-Token', 'X-Target-URL',
  ],
  exposeHeaders: ['mcp-session-id'],
}
```

### Environment Variables

| Variable | Effect | Default |
|----------|--------|---------|
| `PORT` | HTTP server port | `3000` |
| `HOST` | Bind hostname | `localhost` |
| `MCP_URL` | Full public base URL (overrides `baseUrl`) | `http://{HOST}:{PORT}` |
| `NODE_ENV` | Set to `'production'` to disable dev features (inspector, type generation) | – |
| `DEBUG` | Enable verbose debug logging | – |
| `CSP_URLS` | Extra URLs added to widget CSP `resource_domains` | – |

### Transport Modes

| Mode | Sessions | SSE support | Typical use-case |
|------|----------|-------------|-----------------|
| **Stateful** (default in Node.js) | Yes | Yes | Long-lived clients, notifications, sampling. |
| **Stateless** | No | No | Edge functions, serverless, simple request/response. |
| **Auto-detect** | – | – | Deno/edge → always stateless; Node.js → decides per request from `Accept` header. |

Set `stateless: true` in the constructor to force stateless mode.

### Session Store & Stream Manager

For multi-instance (horizontally scaled) deployments, swap the default in-memory implementations:

```typescript
import {
  MCPServer,
  RedisSessionStore,
  RedisStreamManager,
} from "mcp-use/server";
import { createClient } from "redis";

const redis = createClient({ url: process.env.REDIS_URL });
const redisPubSub = createClient({ url: process.env.REDIS_URL });
await redis.connect();
await redisPubSub.connect();

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  sessionStore: new RedisSessionStore({
    client: redis,
    prefix: "mcp:session:",   // optional, default shown
    defaultTTL: 3600,          // seconds; optional
  }),
  streamManager: new RedisStreamManager({
    client: redis,
    pubSubClient: redisPubSub, // dedicated Pub/Sub connection required
    prefix: "mcp:stream:",     // optional, default shown
    heartbeatInterval: 10,     // seconds; optional
  }),
});
```

Available implementations:

| Class | Import | Notes |
|-------|--------|-------|
| `InMemorySessionStore` | `mcp-use/server` | Default; sessions lost on restart. |
| `FileSystemSessionStore` | `mcp-use/server` | Persists across HMR reloads; not for production. |
| `RedisSessionStore` | `mcp-use/server` | Production-ready, shared across instances. |
| `InMemoryStreamManager` | `mcp-use/server` | Default; single-instance only. |
| `RedisStreamManager` | `mcp-use/server` | Fan-out SSE notifications across multiple instances. |

### Middleware

The server instance is also a Hono app. Add middleware before calling `listen()`:

```typescript
// Hono-style middleware (2-arg)
server.use(async (c, next) => {
  console.log(`${c.req.method} ${c.req.url}`);
  await next();
});

// Route-scoped middleware
server.use("/api/admin/*", async (c, next) => {
  // auth check
  await next();
});
```

---

## 6. Development Workflow

```bash
npm run dev
# or directly: npx mcp-use dev src/server.ts
```

This starts the server with:

- **Hot Module Reloading (HMR)** — edit tools, resources, or prompts and changes apply instantly without restarting the server or dropping client connections

### What HMR Does

| Action | Effect |
|--------|--------|
| Add a new tool/resource/prompt | Appears immediately in connected clients |
| Update an existing one | Description, schema, or handler changes apply in-place |
| Remove a registration | Removed from the server instantly |
| Any change | Connected clients receive `list_changed` notifications and auto-refresh |

Keep the Inspector open while editing — your changes appear without losing your session.

---

## 7. Adding Your First Tool

A tool is an action the LLM can invoke. Define it with a Zod schema for typed parameters.

### Basic Tool

```typescript
import { MCPServer } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({ name: "weather-server", version: "1.0.0" });

server.tool(
  {
    name: "get_weather",
    description: "Get current weather for a city",
    schema: z.object({
      city: z.string().describe("City name"),
      units: z.enum(["celsius", "fahrenheit"]).default("celsius").describe("Temperature units"),
    }),
  },
  async ({ city, units }) => {
    const temp = units === "celsius" ? 22 : 72;
    return text(`City: ${city}, Temperature: ${temp}°${units === "celsius" ? "C" : "F"}, Condition: sunny`);
  }
);
```

### Tool with Optional Fields

```typescript
server.tool(
  {
    name: "search-products",
    description: "Search the product catalog",
    schema: z.object({
      query: z.string().min(3).describe("Search term"),
      category: z.enum(["electronics", "clothing", "home"]).optional().describe("Filter by category"),
      maxPrice: z.number().positive().optional().describe("Maximum price filter"),
      inStock: z.boolean().default(true).describe("Only show in-stock items"),
    }),
  },
  async ({ query, category, maxPrice, inStock }) => {
    // Handler logic...
    return object({ results: [] });
  }
);
```

---

## 8. Adding a Resource

A resource exposes data the LLM can read.

### Static Resource

```typescript
import { object } from "mcp-use/server";

server.resource(
  {
    name: "server-config",
    uri: "config://settings",
    title: "Server Configuration",
  },
  async () => object({
    version: "1.0.0",
    environment: process.env.NODE_ENV ?? "development",
  })
);
```

### Resource Template

Use templates for dynamic data:

```typescript
server.resourceTemplate(
  {
    name: "user-profile",
    resourceTemplate: {
      uriTemplate: "users://{userId}/profile",
      name: "user-profile",
      description: "User profile data",
    },
    title: "User Profile",
  },
  async (uri, { userId }) => {
    const user = await db.getUser(userId);
    return object(user);
  }
);
```

Clients call `resources/read` with `users://123/profile`.

---

## 9. Adding a Prompt

A prompt is a reusable template for LLM interactions:

```typescript
server.prompt(
  {
    name: "review-code",
    description: "Review code for bugs and improvements",
    schema: z.object({
      code: z.string().describe("Code to review"),
      language: z.string().default("typescript").describe("Programming language"),
    }),
  },
  async ({ code, language }) =>
    `Review the following ${language} code for bugs and improvements:\n\n\`\`\`${language}\n${code}\n\`\`\``
);
```

---

## 10. Testing Your Server

### Built-in Inspector (recommended)

When running `npm run dev`, the MCP Inspector is automatically available at:

```
http://localhost:3000/inspector
```

Use it to:

1. Browse all registered tools, resources, and prompts.
2. Invoke tools with test parameters.
3. Read resource contents.
4. See real-time `list_changed` notifications when HMR applies updates.

You can also use the online inspector at [inspector.mcp-use.com](https://inspector.mcp-use.com).

### Standalone Inspector

Outside dev mode, use the official MCP Inspector:

```bash
npx @modelcontextprotocol/inspector
```

### curl

```bash
# List tools
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

# Call a tool
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0", "id": 2,
    "method": "tools/call",
    "params": { "name": "get_weather", "arguments": { "city": "London" } }
  }'
```

---

## 11. Connecting to Claude Desktop

Start your server first (`npm run dev` or `npm start`), then edit Claude Desktop's config:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "my-server": {
      "url": "http://localhost:3000/mcp"
    }
  }
}
```

Restart Claude Desktop. The hammer icon confirms your tools are available.

> `mcp-use` servers use HTTP transport (Streamable HTTP). Always use the `"url"` config format — the `"command"/"args"` format is for stdio servers and is not compatible with `mcp-use`.

---

## 12. Runtime Endpoints

When your server is running (dev or prod), it exposes these endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/mcp` | POST | **Primary Endpoint.** Streamable HTTP transport for MCP clients. |
| `/mcp-use/widgets/*` | GET | Widget asset serving (React widget bundles and static files). |
| `/inspector` | GET | Interactive web debugger (dev mode only). |
| `/sse` | GET | **Deprecated.** Legacy Server-Sent Events endpoint. |
| `/messages` | POST | **Deprecated.** Legacy message posting endpoint. |

**Note:** Always direct clients to `/mcp`.

---

## 13. Building for Production

### Build Command

```bash
npm run build
# runs: mcp-use build
```

This compiles your TypeScript to `dist/`, optimized for production.

### Start Production Server

```bash
npm run start
# runs: mcp-use start
```

### Deploy to Manufact Cloud

```bash
npm run deploy
# runs: mcp-use deploy
```

### Dockerfile

Deploying with Docker is recommended for consistent environments.

```dockerfile
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/dist ./dist
RUN npm ci --omit=dev
ENV PORT=3000
ENV NODE_ENV=production
EXPOSE 3000
CMD ["node", "dist/server.js"]
```

### Deployment Checklist

- [ ] Set `NODE_ENV=production`
- [ ] Set `PORT` environment variable
- [ ] Set `HOST` environment variable (if not binding to `localhost`)
- [ ] Set `MCP_URL` to the public base URL (behind reverse proxy or CDN)
- [ ] Configure `allowedOrigins` (DNS rebinding protection)
- [ ] Configure `sessionStore` (use `RedisSessionStore` for multi-instance deployments)
- [ ] Configure `streamManager` (use `RedisStreamManager` for multi-instance deployments)

---

## 14. MCPServer API Reference

The `MCPServer` class provides a clean, chainable API:

```typescript
class MCPServer {
  // MCP Protocol Methods
  tool(definition: ToolDefinition, handler: ToolHandler): this
  resource(definition: ResourceDefinition, handler: ResourceHandler): this
  resourceTemplate(definition: ResourceTemplateDefinition, handler: ResourceHandler): this
  prompt(definition: PromptDefinition, handler: PromptHandler): this
  uiResource(definition: UIResourceDefinition): this

  listen(port?: number): Promise<void>
  getHandler(): RequestHandler   // Returns raw handler for embedding in other frameworks

  // Server composition (v1.21.0+)
  proxy(target: MCPServer): this  // Aggregate tools/resources/prompts from another server

  // Notification helpers
  sendToolsListChanged(): Promise<void>
  sendResourcesListChanged(): Promise<void>
  sendPromptsListChanged(): Promise<void>
  notifyResourceUpdated(uri: string): Promise<void>

  // Hono proxy — all HTTP methods available
  // Examples: get(), post(), use(), route()
  get(path: string, handler: Handler): this
  post(path: string, handler: Handler): this
  use(middleware: Middleware): this
}
```

### Response Helpers

Import from `mcp-use/server`:

| Helper | Signature | Returns |
|--------|-----------|---------|
| `text` | `(content: string) => Response` | Plain-text MCP response. |
| `object` | `(payload: any) => Response` | JSON-serializable object response. |
| `binary` | `(base64: string, mimeType: string) => Response` | Binary data (base64-encoded). |
| `error` | `(msg: string) => Response` | Error response. |

```typescript
import { text, object, binary, error } from "mcp-use/server";
```

### Custom Endpoints

The server instance is also a Hono app, so you can add custom HTTP routes:

```typescript
// Add custom routes
server.get('/api/status', (c) => {
  return c.json({ status: 'ok' })
})
```

---

## 15. Next Steps

- **[Tools Guide](https://manufact.com/docs/typescript/server/tools)** — create MCP tools, prompts and resources
- **[UI Widgets](https://manufact.com/docs/typescript/server/ui-widgets)** — interactive React components with auto-registration (MCP Apps + ChatGPT)
- **[Configuration](https://manufact.com/docs/typescript/server/configuration)** — advanced configuration and deployment options
- **[CLI Reference](https://manufact.com/docs/typescript/server/cli-reference)** — all `mcp-use` CLI commands
- **[Authentication](https://manufact.com/docs/typescript/server/authentication)** — OAuth providers, token validation
- **[Deploy Your Server](https://manufact.com/docs/typescript/server/deployment/mcp-use)** — deploy to production with one command
- **[Inspector](https://manufact.com/docs/inspector)** — debug and test MCP servers interactively

---

## 16. Common Errors

### `EADDRINUSE: address already in use`

Another process is using the port (default 3000).

- **Fix:** `PORT=3001 npm run dev` or find and kill the process (`lsof -i :3000`).

### `Module not found: mcp-use/server`

You are likely missing `"type": "module"` in `package.json` or using an old Node version.

- **Fix:** Add `"type": "module"` and ensure Node.js >= 18.

### `Connection refused` (Inspector)

The server isn't running or the Inspector is trying the wrong port.

- **Fix:** Check console logs for "Server listening on port X" and update the Inspector URL.

### `ZodError: Required`

You called a tool without required arguments.

- **Fix:** Check the schema definition. All fields are required by default unless `.optional()` or `.default()` is used.

### `Request failed with status code 404`

Client is hitting a wrong endpoint.

- **Fix:** Ensure client uses `/mcp` (Streamable HTTP) not `/sse` or `/messages` (Legacy).

---

## 17. Why `mcp-use`?

The official `@modelcontextprotocol/sdk` is low-level. `mcp-use` adds a production-ready framework layer:

| Feature | Raw SDK | `mcp-use` |
|---|---|---|
| **Schemas** | JSON Schema (manual) | Zod (type-safe, inferred) |
| **Transport** | Manual setup | Auto-detected (HTTP/stdio) |
| **HMR** | No | Yes (`mcp-use dev`) |
| **Inspector** | No | Built-in (auto-launched) |
| **UI Widgets** | No | MCP Apps + ChatGPT Apps SDK |
| **Edge Runtime** | No | Built-in support |
| **Auth** | Manual | Built-in OAuth providers |
| **Conformance** | N/A | 100/100 official MCP tests |

Use `mcp-use` to focus on your tools and resources, not protocol details.

---

## 18. Community & Support

- **GitHub**: [github.com/mcp-use/mcp-use](https://github.com/mcp-use/mcp-use)
- **Discord**: [discord.gg/XkNkSkMz3V](https://discord.gg/XkNkSkMz3V)
- **Documentation**: Full docs at [mcp-use.com/docs](https://mcp-use.com/docs)

Happy building!

---

## Best Practices: Scaffolding

### Directory Structure

```typescript
// BAD: Everything in index.ts
import { MCPServer } from "mcp-use/server";
const server = new MCPServer({ name: "my-server", version: "1.0.0" });
// ... 500 lines of tools and resources ...

// GOOD: Modular file structure
// src/index.ts -> imports from tools/*
import { userTool } from "./tools/user";
import { configResource } from "./resources/config";

server.tool(userTool, userHandler).resource(configResource, configHandler);
```

### Async Handlers

```typescript
// BAD: Blocking I/O
import { readFileSync } from "fs";
const data = readFileSync("large-file.txt");

// GOOD: Non-blocking async
import { readFile } from "fs/promises";
const data = await readFile("large-file.txt");
```
