# Quick Start (v2)

Scaffold a new MCP server using the v2 split-package SDK. Source-verified against `main` branch.

## Prerequisites

- Node.js 20+
- npm or pnpm

## Project setup

```bash
mkdir my-mcp-server && cd my-mcp-server
npm init -y
npm install @modelcontextprotocol/server zod
npm install -D typescript @types/node
npx tsc --init
```

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

`"type": "module"` is **required** — v2 is ESM-only.

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

## Project structure

```
my-mcp-server/
├── package.json
├── tsconfig.json
├── src/
│   ├── index.ts          # Entry point — transport + connection
│   ├── server.ts         # McpServer factory — registers all capabilities
│   ├── tools/
│   │   ├── index.ts      # Registers all tools
│   │   └── example.ts    # Individual tool handler
│   ├── resources/
│   │   └── index.ts
│   └── prompts/
│       └── index.ts
```

## Minimal stdio server

```typescript
#!/usr/bin/env node
import { McpServer, StdioServerTransport } from "@modelcontextprotocol/server";
import * as z from "zod/v4";

const server = new McpServer(
  { name: "calculator", version: "1.0.0" },
  { instructions: "A simple calculator server" }
);

server.registerTool("add", {
  title: "Add Numbers",
  description: "Add two numbers together",
  inputSchema: z.object({
    a: z.number().describe("First number"),
    b: z.number().describe("Second number"),
  }),
  annotations: {
    readOnlyHint: true,
    destructiveHint: false,
    idempotentHint: true,
    openWorldHint: false,
  },
}, async ({ a, b }, ctx) => {
  await ctx.mcpReq.log("info", `Adding ${a} + ${b}`);
  return {
    content: [{ type: "text" as const, text: String(a + b) }],
  };
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

**Critical:** Always `console.error()`, never `console.log()` — stdout is reserved for JSON-RPC.

Run: `npx tsx src/index.ts`
Test: `npx @anthropic-ai/mcp-inspector npx tsx src/index.ts`

## Minimal HTTP server (Express, stateful)

```bash
npm install @modelcontextprotocol/node @modelcontextprotocol/express express
```

```typescript
#!/usr/bin/env node
import { randomUUID } from "node:crypto";
import { McpServer } from "@modelcontextprotocol/server";
import { NodeStreamableHTTPServerTransport } from "@modelcontextprotocol/node";
import { createMcpExpressApp } from "@modelcontextprotocol/express";
import { isInitializeRequest } from "@modelcontextprotocol/core";
import * as z from "zod/v4";

function createServer(): McpServer {
  const server = new McpServer({ name: "http-server", version: "1.0.0" });

  server.registerTool("echo", {
    description: "Echo back a message",
    inputSchema: z.object({ message: z.string() }),
    annotations: { readOnlyHint: true },
  }, async ({ message }) => ({
    content: [{ type: "text" as const, text: message }],
  }));

  return server;
}

const app = createMcpExpressApp();
const transports: Record<string, NodeStreamableHTTPServerTransport> = {};

app.post("/mcp", async (req, res) => {
  const sessionId = req.headers["mcp-session-id"] as string | undefined;

  if (sessionId && transports[sessionId]) {
    await transports[sessionId].handleRequest(req, res, req.body);
    return;
  }

  if (!sessionId && isInitializeRequest(req.body)) {
    const transport = new NodeStreamableHTTPServerTransport({
      sessionIdGenerator: () => randomUUID(),
      onsessioninitialized: (sid) => { transports[sid] = transport; },
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
    error: { code: -32000, message: "Bad Request" },
    id: null,
  });
});

app.get("/mcp", async (req, res) => {
  const sid = req.headers["mcp-session-id"] as string;
  if (!sid || !transports[sid]) { res.status(400).send("Invalid session"); return; }
  await transports[sid].handleRequest(req, res);
});

app.delete("/mcp", async (req, res) => {
  const sid = req.headers["mcp-session-id"] as string;
  if (sid && transports[sid]) await transports[sid].handleRequest(req, res);
  res.status(200).end();
});

app.listen(3000, () => console.error("MCP server on :3000"));
```

## Key v2 differences from v1

| v1 pattern | v2 pattern |
|---|---|
| `import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js"` | `import { McpServer } from "@modelcontextprotocol/server"` |
| `import { StreamableHTTPServerTransport } from "...sdk/server/streamableHttp.js"` | `import { NodeStreamableHTTPServerTransport } from "@modelcontextprotocol/node"` |
| `inputSchema: { name: z.string() }` (raw shape) | `inputSchema: z.object({ name: z.string() })` (full schema) |
| `async (args, extra) => { extra.signal; }` | `async (args, ctx) => { ctx.mcpReq.signal; }` |
| `McpError` / `ErrorCode` | `ProtocolError` / `ProtocolErrorCode` |

## Next steps

- Add more tools → `references/guides/tools-and-schemas.md`
- Add resources or prompts → `references/guides/resources-and-prompts.md`
- Use Hono instead of Express → `references/guides/framework-adapters.md`
- Deploy → `references/patterns/deployment.md`
