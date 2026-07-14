# Anti-Patterns

Common mistakes when building MCP servers with the official TypeScript SDK, and how to fix them.

## Using deprecated APIs

### Deprecated: `tool()` positional arguments

```typescript
// BAD — deprecated, will be removed in v2
server.tool("greet", "Greet a user", { name: z.string() }, async ({ name }) => ({
  content: [{ type: "text", text: `Hello ${name}` }],
}));

// GOOD — use registerTool with config object
server.registerTool("greet", {
  description: "Greet a user",
  inputSchema: { name: z.string() },
}, async ({ name }) => ({
  content: [{ type: "text", text: `Hello ${name}` }],
}));
```

Same applies to `resource()` → `registerResource()` and `prompt()` → `registerPrompt()`.

### Deprecated: `Server` class directly

```typescript
// BAD — Server is deprecated for direct use
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
const server = new Server({ name: "my-server", version: "1.0.0" }, {
  capabilities: { tools: {} },
});
server.setRequestHandler(ListToolsRequestSchema, ...);
server.setRequestHandler(CallToolRequestSchema, ...);

// GOOD — use McpServer
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
const server = new McpServer({ name: "my-server", version: "1.0.0" });
server.registerTool("my-tool", config, handler);
```

### Deprecated: SSEServerTransport

```typescript
// BAD — SSE transport is deprecated
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";

// GOOD — use StreamableHTTPServerTransport
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
```

## Missing Zod schemas

```typescript
// BAD — raw JSON Schema, no runtime validation
server.registerTool("search", {
  description: "Search items",
  inputSchema: {
    type: "object",
    properties: {
      query: { type: "string" },
    },
  } as any,
}, async (args: any) => { /* ... */ });

// GOOD — Zod schemas provide runtime validation AND type safety
server.registerTool("search", {
  description: "Search items",
  inputSchema: {
    query: z.string().min(1).max(200).describe("Search query"),
  },
}, async ({ query }) => { /* ... */ });
```

## Missing tool annotations

```typescript
// BAD — no annotations, LLM can't assess risk
server.registerTool("delete-user", {
  description: "Delete a user account",
  inputSchema: { userId: z.string() },
}, handler);

// GOOD — explicit annotations communicate risk
server.registerTool("delete-user", {
  description: "Delete a user account permanently",
  inputSchema: { userId: z.string() },
  annotations: {
    readOnlyHint: false,
    destructiveHint: true,
    idempotentHint: true,
    openWorldHint: true,
  },
}, handler);
```

## Logging to stdout

```typescript
// BAD — stdout is reserved for JSON-RPC in stdio transport
console.log("Server started");
console.log("Processing request", data);

// GOOD — use stderr for all logging
console.error("Server started");
console.error("Processing request", JSON.stringify(data));
```

## Swallowing errors

```typescript
// BAD — silent failure, LLM gets empty response
server.registerTool("fetch", config, async ({ url }) => {
  try {
    const data = await fetch(url).then(r => r.json());
    return { content: [{ type: "text", text: JSON.stringify(data) }] };
  } catch {
    return { content: [{ type: "text", text: "" }] };
  }
});

// GOOD — return actionable error messages
server.registerTool("fetch", config, async ({ url }) => {
  try {
    const data = await fetch(url).then(r => r.json());
    return { content: [{ type: "text", text: JSON.stringify(data) }] };
  } catch (error) {
    return {
      content: [{
        type: "text",
        text: `Failed to fetch ${url}: ${(error as Error).message}. Check the URL and try again.`,
      }],
      isError: true,
    };
  }
});
```

## Hardcoded secrets

```typescript
// BAD — secrets in source code
const API_KEY = "sk-abc123def456";
const DB_URL = "postgres://admin:password@db.example.com/prod";

// GOOD — environment variables with validation
const API_KEY = process.env.API_KEY;
if (!API_KEY) {
  console.error("API_KEY environment variable is required");
  process.exit(1);
}
```

## No DNS rebinding protection

```typescript
// BAD — HTTP server vulnerable to DNS rebinding
const app = express();
app.use(express.json());
app.post("/mcp", ...);
app.listen(3000);

// GOOD — use createMcpExpressApp() which includes protection
import { createMcpExpressApp } from "@modelcontextprotocol/sdk/server/express.js";
const app = createMcpExpressApp();
app.post("/mcp", ...);
app.listen(3000);
```

## Leaking internal errors

```typescript
// BAD — stack traces and internal details exposed
server.registerTool("query", config, async ({ sql }) => {
  try {
    return { content: [{ type: "text", text: JSON.stringify(await db.query(sql)) }] };
  } catch (error) {
    // Leaks table names, column names, query structure
    throw error;
  }
});

// GOOD — sanitize error messages
server.registerTool("query", config, async ({ sql }) => {
  try {
    return { content: [{ type: "text", text: JSON.stringify(await db.query(sql)) }] };
  } catch (error) {
    console.error("Query failed:", error); // Full error to stderr only
    return {
      content: [{ type: "text", text: "Query failed. Check the SQL syntax and try again." }],
      isError: true,
    };
  }
});
```

## Missing graceful shutdown

```typescript
// BAD — no cleanup on shutdown, connections leak
app.listen(3000);

// GOOD — clean shutdown with transport cleanup
const httpServer = app.listen(3000);

process.on("SIGINT", async () => {
  for (const transport of Object.values(transports)) {
    await transport.close().catch(() => {});
  }
  httpServer.close();
  process.exit(0);
});
process.on("SIGTERM", async () => { /* same */ });
```

## Mixing v1 and v2 packages

```typescript
// BAD — v2 alpha packages are not production-ready
import { McpServer } from "@modelcontextprotocol/server"; // v2 alpha

// GOOD — use the stable v1 SDK
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js"; // v1 stable
```

## Missing `.describe()` on Zod fields

```typescript
// BAD — LLM doesn't understand what the parameter means
inputSchema: {
  q: z.string(),
  n: z.number(),
}

// GOOD — descriptive fields help LLMs choose correct values
inputSchema: {
  query: z.string().describe("Search query to match against item names and descriptions"),
  maxResults: z.number().min(1).max(100).describe("Maximum number of results to return"),
}
```
