# Quick Start

Scaffold a new MCP server from scratch using `@modelcontextprotocol/sdk` v1.x.

## Prerequisites

- Node.js 18+ (required for `globalThis.crypto`)
- npm or pnpm

## Project setup

```bash
mkdir my-mcp-server && cd my-mcp-server
npm init -y
npm install @modelcontextprotocol/sdk zod
npm install -D typescript @types/node
npx tsc --init
```

### tsconfig.json essentials

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "declaration": true
  },
  "include": ["src/**/*"]
}
```

Key requirement: `moduleResolution` must be `Node16` or `NodeNext` — the SDK uses subpath exports (`@modelcontextprotocol/sdk/server/mcp.js`).

### package.json essentials

```json
{
  "type": "module",
  "bin": { "my-mcp-server": "./dist/index.js" },
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js",
    "dev": "npx tsx src/index.ts"
  }
}
```

Add `"type": "module"` — the SDK ships ES modules. Add `bin` if the server will be invoked via `npx`.

## Project structure

```
my-mcp-server/
├── package.json
├── tsconfig.json
├── src/
│   ├── index.ts          # Entry point — transport + server connection
│   ├── server.ts         # McpServer factory — registers all capabilities
│   ├── tools/
│   │   ├── index.ts      # Registers all tools on the server
│   │   └── example.ts    # Individual tool handler
│   ├── resources/
│   │   └── index.ts      # Registers all resources (optional)
│   └── prompts/
│       └── index.ts      # Registers all prompts (optional)
```

## Minimal stdio server

The smallest working MCP server — a single file with one tool:

```typescript
#!/usr/bin/env node
// src/index.ts
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer(
  { name: "calculator", version: "1.0.0" },
  { instructions: "A simple calculator server" }
);

server.registerTool("add", {
  description: "Add two numbers",
  inputSchema: {
    a: z.number().describe("First number"),
    b: z.number().describe("Second number"),
  },
  annotations: {
    readOnlyHint: true,
    destructiveHint: false,
    idempotentHint: true,
    openWorldHint: false,
  },
}, async ({ a, b }) => ({
  content: [{ type: "text", text: String(a + b) }],
}));

server.registerTool("multiply", {
  description: "Multiply two numbers",
  inputSchema: {
    a: z.number().describe("First number"),
    b: z.number().describe("Second number"),
  },
  annotations: {
    readOnlyHint: true,
    destructiveHint: false,
    idempotentHint: true,
    openWorldHint: false,
  },
}, async ({ a, b }) => ({
  content: [{ type: "text", text: String(a * b) }],
}));

const transport = new StdioServerTransport();
await server.connect(transport);
```

Run it:
```bash
npx tsx src/index.ts
```

Test with the MCP Inspector:
```bash
npx @anthropic-ai/mcp-inspector npx tsx src/index.ts
```

## Minimal HTTP server (stateful)

A Streamable HTTP server with session management:

```typescript
#!/usr/bin/env node
// src/index.ts
import express from "express";
import { randomUUID } from "node:crypto";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { createMcpExpressApp } from "@modelcontextprotocol/sdk/server/express.js";
import { isInitializeRequest } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";

function createServer(): McpServer {
  const server = new McpServer({ name: "my-http-server", version: "1.0.0" });

  server.registerTool("echo", {
    description: "Echo back the provided message",
    inputSchema: { message: z.string() },
    annotations: { readOnlyHint: true },
  }, async ({ message }) => ({
    content: [{ type: "text", text: message }],
  }));

  return server;
}

const app = createMcpExpressApp(); // includes DNS rebinding protection
const transports: Record<string, StreamableHTTPServerTransport> = {};

app.post("/mcp", async (req, res) => {
  const sessionId = req.headers["mcp-session-id"] as string | undefined;

  if (sessionId && transports[sessionId]) {
    await transports[sessionId].handleRequest(req, res, req.body);
    return;
  }

  if (!sessionId && isInitializeRequest(req.body)) {
    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: () => randomUUID(),
      onsessioninitialized: (sid) => {
        transports[sid] = transport;
      },
    });

    transport.onclose = () => {
      const sid = transport.sessionId;
      if (sid) delete transports[sid];
    };

    const server = createServer();
    await server.connect(transport);
    await transport.handleRequest(req, res, req.body);
    return;
  }

  res.status(400).json({
    jsonrpc: "2.0",
    error: { code: -32000, message: "Bad Request: missing session" },
    id: null,
  });
});

app.get("/mcp", async (req, res) => {
  const sessionId = req.headers["mcp-session-id"] as string;
  if (!sessionId || !transports[sessionId]) {
    res.status(400).send("Invalid session");
    return;
  }
  await transports[sessionId].handleRequest(req, res);
});

app.delete("/mcp", async (req, res) => {
  const sessionId = req.headers["mcp-session-id"] as string;
  if (sessionId && transports[sessionId]) {
    await transports[sessionId].handleRequest(req, res);
  }
  res.status(200).end();
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.error(`MCP server listening on http://localhost:${PORT}/mcp`);
});
```

Additional dependency:
```bash
npm install express
npm install -D @types/express
```

## Minimal HTTP server (stateless)

For simple request-response servers without session tracking:

```typescript
import express from "express";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { createMcpExpressApp } from "@modelcontextprotocol/sdk/server/express.js";
import { z } from "zod";

const app = createMcpExpressApp();

const server = new McpServer({ name: "stateless-server", version: "1.0.0" });

server.registerTool("lookup", {
  description: "Look up a value",
  inputSchema: { key: z.string() },
  annotations: { readOnlyHint: true },
}, async ({ key }) => ({
  content: [{ type: "text", text: `Value for ${key}` }],
}));

const transport = new StreamableHTTPServerTransport({
  sessionIdGenerator: undefined, // explicit stateless mode
});

await server.connect(transport);

app.post("/mcp", async (req, res) => {
  await transport.handleRequest(req, res, req.body);
});

app.listen(3000);
```

## Next steps

- Add more tools → `references/guides/tools-and-schemas.md`
- Add resources or prompts → `references/guides/resources-and-prompts.md`
- Add authentication → `references/guides/authentication.md`
- Deploy to production → `references/patterns/deployment.md`
