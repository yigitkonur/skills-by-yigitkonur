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
npx create-mcp-use-app@latest my-server
cd my-server
npm run dev
```

This creates a fully configured TypeScript project with mcp-use, Zod, example tools, resources, prompts, and optional UI widgets. The dev server launches with HMR and an Inspector UI at `http://localhost:3000/inspector`.

### Template Options

Pass `--template` to choose a starting point:

```bash
# Default — tools, resources, prompts, and UI widgets
npx create-mcp-use-app my-server --template starter

# OpenAI Apps SDK widgets for ChatGPT
npx create-mcp-use-app my-server --template mcp-apps

# MCP-UI widgets (iframe, raw HTML, Remote DOM)
npx create-mcp-use-app my-server --template mcp-ui
```

| Template | Includes | Best for |
|----------|----------|----------|
| `starter` (default) | Tools, resources, prompts, UI widgets | Full-featured servers, learning all MCP features |
| `mcp-apps` | OpenAI Apps SDK widgets, React Query, product examples | ChatGPT-compatible widget apps |
| `mcp-ui` | All three UIResource types (iframe, raw HTML, Remote DOM) | Complex UI requirements, MCP-UI spec compliance |

Run `npx create-mcp-use-app --help` to see all available options.

If you used the scaffolder, skip to [Section 6](#6-development-workflow).

---

## 3. Manual Setup

For existing projects or custom configurations, set up from scratch.

### Initialize the project

```bash
mkdir my-mcp-server && cd my-mcp-server
npm init -y
npm install mcp-use zod@^4.0.0
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
    "start": "mcp-use start"
  },
  "dependencies": {
    "mcp-use": "^1.21.4",
    "zod": "^4.0.0"
  }
}
```

- **`"type": "module"`** — required; without this, imports from `mcp-use/server` fail.
- **`"dev"`** — uses `mcp-use dev` for hot-reload with auto-embedded Inspector.

### Configure tsconfig.json

Create `tsconfig.json`:

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
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src/**/*"]
}
```

> `"module": "NodeNext"` / `"moduleResolution": "NodeNext"` are also valid alternatives.

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
│   └── product-search-result/
│       ├── widget.tsx             # Widget entry point
│       ├── components/            # Sub-components
│       └── types.ts
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

The simplest possible mcp-use server in ~15 lines:

```typescript
// src/server.ts
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
});

server.tool(
  {
    name: "hello",
    description: "Say hello",
    schema: z.object({ name: z.string() }),
  },
  async ({ name }) => text(`Hello, ${name}!`)
);

await server.listen();
```

`listen()` starts an HTTP server using MCP Streamable HTTP transport on port 3000 by default. Override via `PORT` env variable or `--port` CLI flag.

### HTTP Server with Explicit Port

Pass a port number to `listen()`:

```typescript
await server.listen(4000);
// MCP endpoint:  http://localhost:4000/mcp
// Inspector:     http://localhost:4000/inspector
```

Test it:

```bash
curl http://localhost:4000/mcp -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

---

## 6. Development Workflow

```bash
npm run dev
# or directly: npx mcp-use dev src/server.ts
```

This starts the server with:

- **Hot Module Reloading (HMR)** — edit tools, resources, or prompts and changes apply instantly without restarting the server or dropping client connections
- **Built-in Inspector** — automatically served at `http://localhost:3000/inspector`
- **MCP endpoint** — available at `http://localhost:3000/mcp`

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

A tool is an action the LLM can invoke. Define it with a Zod schema for typed parameters:

```typescript
import { MCPServer, text, object } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "weather-server",
  version: "1.0.0",
});

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
    return object({ city, temperature: temp, units, condition: "sunny" });
  }
);

await server.listen();
```

**Response helpers** — all imported from `"mcp-use/server"`:

| Helper | Use case | Example |
|--------|----------|---------|
| `text()` | Plain text | `text("Done.")` |
| `markdown()` | Markdown content | `markdown("# Title\nBody")` |
| `object()` | Structured JSON | `object({ count: 42 })` |
| `error()` | Error responses | `error("Failed")` |
| `image()` | Base64 images | `image(b64, "image/png")` |
| `html()` | HTML content | `html("<p>Hi</p>")` |
| `mix()` | Combine types | `mix(text("Result:"), object({ n: 1 }))` |

---

## 8. Adding a Resource

A resource exposes data the LLM can read, similar to a GET endpoint:

```typescript
server.resource(
  {
    name: "server-config",
    uri: "config://settings",
    title: "Server Configuration",
  },
  async () => object({
    version: "1.0.0",
    environment: process.env.NODE_ENV ?? "development",
    features: ["weather", "geocoding"],
  })
);
```

Clients call `resources/read` with the URI to retrieve the content.

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
    text(`Review the following ${language} code for bugs and improvements:\n\n\`\`\`${language}\n${code}\n\`\`\``)
);
```

---

## 10. Testing Your Server

### Built-in Inspector (recommended)

In dev mode (`mcp-use dev`), the Inspector is auto-served at `http://localhost:3000/inspector`. Open it to:

1. Browse all registered tools, resources, and prompts.
2. Invoke tools with test parameters.
3. Read resource contents.
4. See real-time `list_changed` notifications when HMR applies updates.

### Standalone Inspector

Outside dev mode, use the official MCP Inspector:

```bash
npx @modelcontextprotocol/inspector
```

Set transport to **Streamable HTTP**, enter `http://localhost:3000/mcp`, and click **Connect**.

### curl

```bash
# List tools
curl http://localhost:3000/mcp -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

# Call a tool
curl http://localhost:3000/mcp -X POST \
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

Restart Claude Desktop. The hammer icon (🔨) confirms your tools are available.

> `mcp-use` servers use HTTP transport (Streamable HTTP). Always use the `"url"` config format — the `"command"/"args"` format is for stdio servers and is not compatible with `mcp-use`.

---

## 12. Building for Production

```bash
npm run build    # or: npx mcp-use build
npm run start    # or: npx mcp-use start
```

The production server serves the same MCP endpoint and Inspector without HMR overhead.

---

## 13. Next Steps

- **[Tools Guide](./tools.md)** — advanced patterns, streaming responses, output schemas
- **[Resources Guide](./resources.md)** — dynamic resources, resource templates with URI patterns
- **[Prompts Guide](./prompts.md)** — multi-message prompts, embedded resources
- **[Authentication](./authentication.md)** — OAuth providers, token validation
- **[Sessions](./sessions.md)** — stateful multi-turn interactions
- **[Middleware](./middleware.md)** — custom Hono routes, CORS, middleware chains
- **[Deployment](./deployment.md)** — Docker, edge runtimes, cloud platforms
