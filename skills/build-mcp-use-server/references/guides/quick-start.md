# Quick-Start Guide: Build an MCP Server with mcp-use

Build a working MCP server in under 10 minutes using the `mcp-use` TypeScript library.

---

## 1. Project Setup

### Initialize the project

```bash
mkdir my-mcp-server && cd my-mcp-server
npm init -y
npm install mcp-use zod
npm install -D typescript @types/node tsx
npx tsc --init
```

### Configure TypeScript

Replace the generated `tsconfig.json`:

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

> `"module": "NodeNext"` / `"moduleResolution": "NodeNext"` are also valid alternatives to `"Node16"`.

### Configure package.json

Add the following fields to `package.json`:

```json
{
  "name": "my-mcp-server",
  "version": "1.0.0",
  "type": "module",
  "main": "dist/server.js",
  "bin": {
    "my-mcp-server": "dist/server.js"
  },
  "scripts": {
    "dev": "tsx watch src/server.ts",
    "build": "tsc",
    "start": "node dist/server.js"
  }
}
```

- **`"type": "module"`** — Required. Without this, imports from `mcp-use/server` fail.
- **`"bin"`** — Enables `npx my-mcp-server` after publishing. Add `#!/usr/bin/env node` as line 1 for CLI distribution.
- **`"dev"`** — Uses `tsx watch` for hot-reload during development.

Create the source directory and proceed:

```bash
mkdir src
```

---

## 2. Minimal Server — Three Patterns

### Pattern A: Stdio Server (simplest, for CLI tools)

Create `src/server.ts`:

```typescript
import { MCPServer, text } from "mcp-use/server";
import z from "zod";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  description: "My first MCP server",
});

server.tool(
  {
    name: "greet",
    description: "Greet someone by name",
    schema: z.object({
      name: z.string().describe("Name to greet"),
    }),
  },
  async ({ name }) => text(`Hello, ${name}!`)
);

await server.listen();
```

Run it:

```bash
npm run dev
```

The server communicates over stdin/stdout (MCP stdio transport). This is the default when no transport options are passed to `listen()`. Use this pattern when the server runs as a local subprocess launched by Claude Desktop.

### Pattern B: HTTP Server (for remote/web access)

Replace the `listen()` call with:

```typescript
await server.listen({ transportType: "httpStream", port: 3000 });
```

This starts an HTTP server on port 3000 using the MCP Streamable HTTP transport. Use this for network-accessible servers — deployed services, shared team servers, or web-based clients.

Test it:

```bash
curl http://localhost:3000/mcp -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

### Pattern C: With Resources and Prompts

Extend your server with resources and prompts alongside tools:

```typescript
import { MCPServer, text, markdown } from "mcp-use/server";
import z from "zod";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  description: "Server with tools, resources, and prompts",
});

// Tool — an action the LLM can invoke
server.tool(
  {
    name: "greet",
    description: "Greet someone by name",
    schema: z.object({
      name: z.string().describe("Name to greet"),
    }),
  },
  async ({ name }) => text(`Hello, ${name}!`)
);

// Resource — static or dynamic data the LLM can read
server.resource(
  {
    name: "readme",
    uri: "docs://readme",
    title: "README",
  },
  async () => markdown("# My Server\nDocumentation here...")
);

// Prompt — a reusable prompt template
server.prompt(
  {
    name: "summarize",
    description: "Summarize content",
    schema: z.object({
      content: z.string().describe("Content to summarize"),
    }),
  },
  async ({ content }) => text(`Please summarize the following:\n\n${content}`)
);

await server.listen();
```

**Response helpers** — all imported from `"mcp-use/server"`:

| Helper       | Use case                         | Example                                      |
|-------------|----------------------------------|----------------------------------------------|
| `text()`    | Plain text responses             | `text("Done.")`                              |
| `markdown()`| Markdown-formatted content       | `markdown("# Title\nBody")`                  |
| `object()`  | Structured JSON data             | `object({ count: 42, items: ["a", "b"] })`   |

---

## 3. Testing Your Server

### Option A: MCP Inspector (recommended)

```bash
npx @modelcontextprotocol/inspector
```

In the Inspector UI:
1. Set transport to **Stdio**, command to `tsx src/server.ts` (or `node dist/server.js` if built).
2. Click **Connect**.
3. Browse and invoke your tools, resources, and prompts interactively.

For HTTP servers, set transport to **Streamable HTTP** and enter `http://localhost:3000/mcp`.

### Option B: Claude Desktop

See [Section 4](#4-claude-desktop-integration) for configuration. After restarting, look for the hammer icon (🔨) indicating available tools.

### Option C: curl (HTTP servers)

List tools:

```bash
curl http://localhost:3000/mcp -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

Call a tool:

```bash
curl http://localhost:3000/mcp -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "greet",
      "arguments": { "name": "World" }
    }
  }'
```

---

## 4. Claude Desktop Integration

Build first: `npm run build`

Edit Claude Desktop's config file:
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

Add your server entry:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["/absolute/path/to/my-mcp-server/dist/server.js"]
    }
  }
}
```

Restart Claude Desktop. Verify the hammer icon (🔨) appears showing your server's tools.

For HTTP servers, use URL-based config instead:

```json
{
  "mcpServers": {
    "my-server": {
      "url": "http://localhost:3000/mcp"
    }
  }
}
```

> Always use absolute paths in the `"args"` array. Relative paths fail silently because Claude Desktop does not share your shell's working directory.

---

## 5. Common First-Time Issues

### "Cannot find module 'mcp-use/server'"

**Cause:** Missing `"type": "module"` in `package.json`, or wrong `moduleResolution`.

**Fix:** Ensure `package.json` has `"type": "module"` and `tsconfig.json` has `"module": "Node16"` (or `"NodeNext"`) with matching `"moduleResolution"`. Run `npm install` again.

### Server starts but no tools appear in Claude Desktop

**Cause:** Empty or missing `name`/`description` on a tool. MCP requires both to be non-empty strings.

**Fix:** Check every `server.tool()` call has both fields set:

```typescript
// ❌ Wrong — missing description
server.tool(
  { name: "greet", schema: z.object({ name: z.string() }) },
  async ({ name }) => text(`Hello, ${name}!`)
);

// ✅ Correct
server.tool(
  {
    name: "greet",
    description: "Greet someone by name",
    schema: z.object({ name: z.string().describe("Name to greet") }),
  },
  async ({ name }) => text(`Hello, ${name}!`)
);
```

### TypeScript errors with Zod schemas

**Cause:** Older Zod versions have type inference issues under `"strict": true`.

**Fix:** Use Zod v3.23 or later:

```bash
npm install zod@latest
```

### "Top-level await is not allowed"

**Cause:** `tsconfig.json` target below ES2022 or `"module"` not set to `"Node16"`/`"NodeNext"`.

**Fix:** Ensure `"target": "ES2022"` and `"module": "Node16"` in `tsconfig.json`. Top-level `await` requires both settings.

### Server crashes on startup with no error message

**Cause:** Unhandled promise rejection in a tool handler or error thrown before `listen()`.

**Fix:** Wrap startup in a try-catch:

```typescript
try {
  await server.listen();
} catch (error) {
  console.error("Server failed to start:", error);
  process.exit(1);
}
```

---

## 6. Next Steps

- Add structured output with `object()` and Zod output schemas.
- Add dynamic resources using resource templates with URI patterns.
- Add middleware (Express, Hono) for authentication and routing.
- Add session management for stateful multi-turn interactions.
- Deploy to cloud (Supabase Edge Functions, Docker, etc.).
