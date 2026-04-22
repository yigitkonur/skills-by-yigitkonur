# Server Recipes (v2)

Complete v2 server examples using the split-package SDK.

## Recipe 1 — API wrapper (stdio)

```typescript
#!/usr/bin/env node
import { McpServer, StdioServerTransport } from "@modelcontextprotocol/server";
import * as z from "zod/v4";

const API_BASE = process.env.API_BASE_URL!;
const API_KEY = process.env.API_KEY!;

if (!API_BASE || !API_KEY) {
  console.error("API_BASE_URL and API_KEY required");
  process.exit(1);
}

const server = new McpServer(
  { name: "api-wrapper", version: "1.0.0" },
  { instructions: "Wraps the Example API" }
);

server.registerTool("search", {
  title: "Search Items",
  description: "Search for items by query",
  inputSchema: z.object({
    query: z.string().min(1).describe("Search query"),
    limit: z.number().min(1).max(100).default(20).describe("Max results"),
  }),
  annotations: { readOnlyHint: true, openWorldHint: true },
}, async ({ query, limit }, ctx) => {
  await ctx.mcpReq.log("info", `Searching: ${query}`);
  try {
    const res = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}&limit=${limit}`, {
      headers: { Authorization: `Bearer ${API_KEY}` },
      signal: ctx.mcpReq.signal,
    });
    if (!res.ok) throw new Error(`API ${res.status}`);
    const data = await res.json();
    return { content: [{ type: "text" as const, text: JSON.stringify(data, null, 2) }] };
  } catch (error) {
    return { content: [{ type: "text" as const, text: `Search failed: ${error}` }], isError: true };
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

## Recipe 2 — HTTP server with Express (stateful)

```typescript
#!/usr/bin/env node
import { randomUUID } from "node:crypto";
import { McpServer } from "@modelcontextprotocol/server";
import { NodeStreamableHTTPServerTransport } from "@modelcontextprotocol/node";
import { createMcpExpressApp } from "@modelcontextprotocol/express";
import { isInitializeRequest } from "@modelcontextprotocol/core";
import * as z from "zod/v4";

function createServer(): McpServer {
  const server = new McpServer(
    { name: "http-server", version: "1.0.0" },
    { capabilities: { logging: {} } }
  );

  server.registerTool("greet", {
    title: "Greet",
    description: "Greet someone",
    inputSchema: z.object({ name: z.string() }),
    annotations: { readOnlyHint: true },
  }, async ({ name }, ctx) => {
    await ctx.mcpReq.log("info", `Greeting ${name}`);
    return { content: [{ type: "text" as const, text: `Hello, ${name}!` }] };
  });

  return server;
}

const app = createMcpExpressApp();
const transports: Record<string, NodeStreamableHTTPServerTransport> = {};

app.post("/mcp", async (req, res) => {
  const sid = req.headers["mcp-session-id"] as string | undefined;
  if (sid && transports[sid]) {
    await transports[sid].handleRequest(req, res, req.body);
    return;
  }
  if (!sid && isInitializeRequest(req.body)) {
    const transport = new NodeStreamableHTTPServerTransport({
      sessionIdGenerator: () => randomUUID(),
      onsessioninitialized: (s) => { transports[s] = transport; },
    });
    transport.onclose = () => { const s = transport.sessionId; if (s) delete transports[s]; };
    const server = createServer();
    await server.connect(transport);
    await transport.handleRequest(req, res, req.body);
    return;
  }
  res.status(400).json({ jsonrpc: "2.0", error: { code: -32000, message: "Bad Request" }, id: null });
});

app.get("/mcp", async (req, res) => {
  const sid = req.headers["mcp-session-id"] as string;
  if (!sid || !transports[sid]) { res.status(400).send("Bad session"); return; }
  await transports[sid].handleRequest(req, res);
});

app.delete("/mcp", async (req, res) => {
  const sid = req.headers["mcp-session-id"] as string;
  if (sid && transports[sid]) await transports[sid].handleRequest(req, res);
  res.status(200).end();
});

const httpServer = app.listen(3000, () => console.error("MCP on :3000"));
process.on("SIGINT", async () => {
  for (const t of Object.values(transports)) await t.close().catch(() => {});
  httpServer.close();
  process.exit(0);
});
```

## Recipe 3 — Structured output with outputSchema

```typescript
import { McpServer, StdioServerTransport } from "@modelcontextprotocol/server";
import * as z from "zod/v4";

const server = new McpServer({ name: "weather", version: "1.0.0" });

server.registerTool("get-weather", {
  description: "Get weather for a city",
  inputSchema: z.object({ city: z.string() }),
  outputSchema: z.object({
    temperature: z.object({ celsius: z.number(), fahrenheit: z.number() }),
    conditions: z.enum(["sunny", "cloudy", "rainy", "stormy"]),
    humidity: z.number().min(0).max(100),
  }),
}, async ({ city }) => {
  const weather = { temperature: { celsius: 22, fahrenheit: 72 }, conditions: "sunny" as const, humidity: 45 };
  return {
    content: [{ type: "text" as const, text: JSON.stringify(weather, null, 2) }],
    structuredContent: weather,
  };
});

await server.connect(new StdioServerTransport());
```

## Recipe 4 — Tool with elicitation and logging

```typescript
import { McpServer, StdioServerTransport } from "@modelcontextprotocol/server";
import * as z from "zod/v4";

const server = new McpServer(
  { name: "interactive", version: "1.0.0" },
  { capabilities: { logging: {} } }
);

server.registerTool("deploy", {
  description: "Deploy to an environment",
  inputSchema: z.object({ service: z.string() }),
  annotations: { destructiveHint: true, openWorldHint: true },
}, async ({ service }, ctx) => {
  // Ask for confirmation via elicitation
  const result = await ctx.mcpReq.elicitInput({
    mode: "form",
    message: `Deploy ${service} to production?`,
    requestedSchema: {
      type: "object",
      properties: {
        confirm: { type: "boolean", title: "Confirm deployment", default: false },
      },
      required: ["confirm"],
    },
  });

  if (result.action !== "accept" || !result.content?.confirm) {
    return { content: [{ type: "text" as const, text: "Deployment cancelled" }] };
  }

  await ctx.mcpReq.log("info", `Deploying ${service}...`);
  // ... deploy logic ...
  await ctx.mcpReq.log("info", `${service} deployed successfully`);

  return { content: [{ type: "text" as const, text: `${service} deployed to production` }] };
});

await server.connect(new StdioServerTransport());
```
