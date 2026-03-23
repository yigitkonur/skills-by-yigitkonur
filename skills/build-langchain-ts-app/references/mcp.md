# MCP Integration with LangChain.js

> Package: `@langchain/mcp-adapters` v1.1.3 · Spec: MCP 2025-06-18 · SDK: `@modelcontextprotocol/sdk`

---

## Overview

Model Context Protocol (MCP) is an open standard (JSON-RPC 2.0) that decouples tool provision from LLM orchestration. MCP servers expose tools, resources, and prompts over a transport wire; any compatible client discovers and invokes them dynamically.

Key benefits for LangChain.js: access to hundreds of pre-built tool servers (Composio 250+, Smithery 100+), language-agnostic servers (Python server from TS client), dynamic tool discovery at runtime, and LangGraph agents can expose themselves as MCP servers for Claude Desktop and other clients.

**Three MCP primitives:**

| Primitive | Purpose | Side effects |
|-----------|---------|-------------|
| Tools | Executable functions (DB queries, API calls) | Yes |
| Resources | Read-only data (files, records, API responses) | No |
| Prompts | Reusable message templates/workflows | No |

```bash
npm install @langchain/mcp-adapters          # client
npm install @modelcontextprotocol/sdk        # for building servers
```

Note: Old repo `langchain-ai/langchainjs-mcp-adapters` is archived (May 2025); moved into main `langchainjs` monorepo.

---

## MultiServerMCPClient — Full API

Primary class. Manages connections to N MCP servers, aggregates tools, and returns `StructuredTool[]`.

```typescript
import { MultiServerMCPClient } from "@langchain/mcp-adapters";

const client = new MultiServerMCPClient({
  // Global options
  throwOnLoadError: true,              // abort if a tool fails to load
  prefixToolNameWithServerName: false, // name tools as "server__toolname"
  additionalToolNamePrefix: "",        // extra prefix on all tool names
  useStandardContentBlocks: true,      // recommended: normalize outputs
  outputHandling: { image: "content", resource: "artifact" },
  defaultToolTimeout: 30000,           // ms; 0 = no timeout
  onConnectionError: "ignore",         // "throw" | "ignore" | (err) => void

  // Lifecycle callbacks
  onMessage: (log, source) => console.log(`[${source.server}] ${log.data}`),
  onProgress: (prog, source) => { /* progress events */ },
  onToolsListChanged: (evt, source) => { /* server updated its tool list dynamically */ },
  onInitialized: (source) => { /* handshake complete */ },
  onCancelled: (source) => { /* server cancelled an in-flight request */ },
  onPromptsListChanged: (evt, source) => { /* server's prompt list changed */ },
  onResourcesListChanged: (evt, source) => { /* server's resource list changed */ },
  onResourcesUpdated: (evt, source) => { /* resource content changed */ },

  // Tool interceptor hooks
  beforeToolCall: async ({ serverName, name, args }) => {
    // optionally return { args: modifiedArgs, headers: { "X-Trace-ID": id } }
  },
  afterToolCall: async (result) => {
    // return modified result, [content, artifact] tuple, ToolMessage, or LangGraph Command
    return result;
  },

  mcpServers: {
    math: {
      transport: "stdio",
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-math"],
      restart: { enabled: true, maxAttempts: 3, delayMs: 1000 },
    },
    weather: {
      url: "https://example.com/weather/mcp",
      headers: { Authorization: `Bearer ${process.env.WEATHER_API_KEY}` },
      automaticSSEFallback: true,
      reconnect: { enabled: true, maxAttempts: 5, delayMs: 2000 },
    },
  },
});

const tools: StructuredTool[] = await client.getTools();
await client.close();  // kills subprocesses, closes HTTP/SSE connections
```

**outputHandling** maps MCP block types to `ToolMessage.content` (LLM sees it) vs `ToolMessage.artifact` (out of context). Default: `resource → "artifact"`, everything else `"content"`.

---

## Transport Types

| Transport | Config | Use case | Stateful | Headers |
|-----------|--------|---------|---------|---------|
| `stdio` | `transport: "stdio"` | Local subprocess, dev | Yes (subprocess lives) | No |
| Streamable HTTP | `url:` (default) | Remote services, production | Stateless per-request | Yes |
| `sse` | `transport: "sse"` | Legacy SSE-only servers | Persistent stream | Yes |
| `http` | `transport: "http"` | Alias for streamable HTTP | Stateless | Yes |

**stdio** — spawns a child process, communicates over stdin/stdout JSON-RPC:

```typescript
{
  transport: "stdio",
  command: "npx",
  args: ["-y", "@modelcontextprotocol/server-filesystem", "."],
  env: { BRAVE_API_KEY: process.env.BRAVE_API_KEY },
  cwd: "/path/to/dir",
  stderr: process.stderr.fd,
  restart: { enabled: true, maxAttempts: 3, delayMs: 1000 },
}
```

Windows gotcha: `npx` with stdio can fail with `spawn ENOENT`. Fix: use `cmd /c npx` as the command. Also, the stateless default spawns a new subprocess per tool call — expensive on Windows. Use a stateful session or HTTP transport instead.

**Streamable HTTP** — MCP spec 2025-03-26+, recommended for production. Single endpoint, POST for requests, GET for SSE streams:

```typescript
{
  url: "https://api.example.com/mcp",
  headers: { Authorization: "Bearer my-api-key" },
  automaticSSEFallback: true,   // fall back to SSE on 4xx
  reconnect: { enabled: true, maxAttempts: 5, delayMs: 2000 },
}
```

Protocol: `MCP-Protocol-Version: 2025-03-26` header required (wrong version → `400`). Optional `Mcp-Session-Id` for stateful operation. SSE events carry `id` for resumability via `Last-Event-ID`.

**SSE** — deprecated in spec, use only when server doesn't support Streamable HTTP.

---

## loadMcpTools — Manual Client Management

Use when you need direct lifecycle control over the MCP client:

```typescript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import { loadMcpTools } from "@langchain/mcp-adapters";

// stdio
const client = new Client({ name: "my-app", version: "1.0.0" });
await client.connect(new StdioClientTransport({ command: "npx", args: ["-y", "@modelcontextprotocol/server-math"] }));
const tools = await loadMcpTools("math", client, { throwOnLoadError: true, useStandardContentBlocks: true });
await client.close();

// Streamable HTTP
const httpClient = new Client({ name: "my-app", version: "1.0.0" });
await httpClient.connect(new StreamableHTTPClientTransport(new URL("http://localhost:8080/mcp")));
const httpTools = await loadMcpTools("k8s", httpClient);
```

```typescript
// Signature
function loadMcpTools(
  serverName: string,
  client: Client,
  options?: {
    throwOnLoadError?: boolean;         // default: true
    useStandardContentBlocks?: boolean; // default: false
    outputHandling?: OutputHandling;
  }
): Promise<StructuredTool[]>
```

---

## Authentication

### Static Headers

Simple token auth. No automatic refresh — recreate the client when token expires.

```typescript
mcpServers: {
  "my-api": {
    url: "https://api.example.com/mcp",
    headers: { Authorization: `Bearer ${process.env.API_TOKEN}` },
  },
}
```

### OAuth 2.0 (Production)

```typescript
import { OAuthProvider } from "@langchain/mcp-adapters";

class MyOAuthProvider implements OAuthProvider {
  async getToken(): Promise<string> {
    return fetchAccessToken({ clientId: process.env.CLIENT_ID!, clientSecret: process.env.CLIENT_SECRET!, tokenUrl: "https://auth.example.com/token" });
  }
}

mcpServers: {
  "protected": { url: "https://protected.example.com/mcp", authProvider: new MyOAuthProvider() },
}
```

| Aspect | OAuth Provider | Static Headers |
|--------|----------------|----------------|
| Token refresh | Automatic | Manual (recreate client) |
| 401 handling | Automatic retry | Manual |
| PKCE / RFC 6750 | Supported | Not applicable |
| Use case | Production | Dev / simple tokens |

### Runtime Headers per Call

```typescript
const client = new MultiServerMCPClient({
  beforeToolCall: async ({ args }) => {
    return { args, headers: { Authorization: `Bearer ${await getUserToken(userId)}` } };
  },
  mcpServers: { ... },
});
```

Note: Runtime headers only work on `http`/`sse`/`streamable-http`. Not on `stdio`.

---

## Stateless vs. Stateful Sessions

**Stateless (default):** Each tool invocation creates a fresh `ClientSession`. Safe for concurrent agents but expensive for `stdio` (spawns a new subprocess every call).

**Stateful:** Reuse a persistent `Client` instance for servers that maintain context (e.g., DB transactions):

```typescript
const transport = new StdioClientTransport({ command: "node", args: ["my-server.js"] });
const client = new Client({ name: "stateful-client" });
await client.connect(transport);

const tools = await loadMcpTools("my-server", client);
const agent = createReactAgent({ llm: model, tools });

await agent.invoke({ messages: [{ role: "user", content: "Start transaction" }] });
await agent.invoke({ messages: [{ role: "user", content: "Commit transaction" }] });
await client.close(); // session ends here
```

---

## MCP Resources and Prompts

```typescript
// Resources — read-only data blobs
const resources = await client.getResources();
// Returns: Array<{ uri: string; mimeType?: string; contents?: unknown[] }>
const imageResource = resources.find(r => r.mimeType === "image/png");

// Pass resource URI to a tool
await tools.find(t => t.name === "read_file")?.invoke({ uri: "file:///path/to/doc.pdf" });

// Prompts — reusable message templates
const prompt = await client.getPrompt("math", "explain_calculation", { operation: "multiplication" });
// Returns LangChain Message[]
const response = await agent.invoke({ messages: [...prompt, { role: "user", content: "Calculate 15 × 8" }] });
```

For full access, use `loadMcpTools` with a persistent client and call `client.listPrompts()`, `client.getPrompt()`, `client.listResources()` directly via `@modelcontextprotocol/sdk`.

Resource blocks land in `ToolMessage.artifact` by default (`outputHandling.resource = "artifact"`), keeping large data out of the LLM context window.

---

## Tool Discovery and Filtering

### Inspect Available Tools

```typescript
const tools = await client.getTools();
console.log(`Loaded ${tools.length} tools:`);
tools.forEach(t => console.log(`  ${t.name}: ${t.description}`));
```

### Filter by Name or Category

```typescript
const tools = await client.getTools();

// Only file-related tools
const fileTools = tools.filter(t => t.name.includes("file") || t.name.includes("directory"));

// Only tools from a specific server (requires prefixToolNameWithServerName: true)
const githubTools = tools.filter(t => t.name.startsWith("github__"));

// Exclude specific tools
const safeTools = tools.filter(t => !["delete_file", "drop_table"].includes(t.name));
```

### Verify Connection Before Loading Tools

```typescript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const debugClient = new Client({ name: "debug" });
await debugClient.connect(new StdioClientTransport({ command: "npx", args: ["-y", "my-server"] }));

console.log("tools:", (await debugClient.listTools()).tools.map(t => t.name));
console.log("resources:", (await debugClient.listResources()).resources);
console.log("prompts:", (await debugClient.listPrompts()).prompts);
await debugClient.close();
```

---

## Error Handling

| Error type | Origin | Description |
|-----------|--------|-------------|
| `MCPClientError` | Connection/init | Transport or handshake failure |
| `ToolException` | Tool execution | Tool returned an error result |
| `ZodError` | Config validation | Invalid config shape |

```typescript
async function robustAgent() {
  let client: MultiServerMCPClient | null = null;
  try {
    client = new MultiServerMCPClient({
      throwOnLoadError: false,
      onConnectionError: "ignore",
      mcpServers: { math: { transport: "stdio", command: "npx", args: ["-y", "@modelcontextprotocol/server-math"] } },
    });
    const tools = await client.getTools();
    const agent = createReactAgent({ llm: new ChatOpenAI({ model: "gpt-4o-mini" }), tools });
    return await agent.invoke({ messages: [{ role: "user", content: "What is 3 + 5?" }] });
  } catch (e: unknown) {
    if (e instanceof Error) {
      if (e.name === "MCPClientError") console.error("Connection failure:", e.message);
      else if (e.name === "ToolException") console.error("Tool error:", e.message);
      else if (e.name === "ZodError") (e as any).issues.forEach((i: any) => console.error(`${i.path.join(".")}: ${i.message}`));
      else throw e;
    }
  } finally {
    await client?.close();
  }
}
```

---

## LangGraph Integration

### ReAct Agent with MCP Tools

```typescript
import { createReactAgent } from "@langchain/langgraph/prebuilt";
import { ChatAnthropic } from "@langchain/anthropic";
import { MultiServerMCPClient } from "@langchain/mcp-adapters";

const client = new MultiServerMCPClient({
  useStandardContentBlocks: true,
  mcpServers: {
    filesystem: { transport: "stdio", command: "npx", args: ["-y", "@modelcontextprotocol/server-filesystem", "."] },
    github: { transport: "stdio", command: "npx", args: ["-y", "@modelcontextprotocol/server-github"], env: { GITHUB_PERSONAL_ACCESS_TOKEN: process.env.GITHUB_TOKEN! } },
  },
});

const tools = await client.getTools();
const agent = createReactAgent({ llm: new ChatAnthropic({ model: "claude-sonnet-4-6" }), tools });

try {
  const result = await agent.invoke({ messages: [{ role: "user", content: "List TS files and create a GitHub issue" }] });
  return result;
} finally {
  await client.close();
}
```

### Exposing a LangGraph Agent as an MCP Server

Any deployed LangGraph agent automatically exposes `/mcp` (Streamable HTTP):

```json
// langgraph.json
{
  "graphs": {
    "my_agent": { "path": "./my_agent/agent.ts:graph", "description": "Finance analysis agent" }
  }
}
```

Disable: `{ "http": { "disable_mcp": true } }`

Connect another agent to it:

```typescript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";

const client = new Client({ name: "orchestrator", version: "1.0.0" });
await client.connect(new StreamableHTTPClientTransport(new URL("http://localhost:2024/mcp")));
console.log(await client.listTools());
```

---

## Building MCP Servers in TypeScript

### stdio Server

```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";

const server = new Server({ name: "math-server", version: "1.0.0" }, { capabilities: { tools: {} } });

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    { name: "add", description: "Add two numbers", inputSchema: { type: "object", properties: { a: { type: "number" }, b: { type: "number" } }, required: ["a", "b"] } },
    { name: "multiply", description: "Multiply two numbers", inputSchema: { type: "object", properties: { a: { type: "number" }, b: { type: "number" } }, required: ["a", "b"] } },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async ({ params: { name, arguments: args } }) => {
  const a = (args as any).a, b = (args as any).b;
  const result = name === "add" ? a + b : name === "multiply" ? a * b : (() => { throw new Error(`Unknown tool: ${name}`); })();
  return { content: [{ type: "text", text: String(result) }] };
});

await server.connect(new StdioServerTransport());
```

### HTTP Server (Express + SSE)

```typescript
import express from "express";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";

const app = express();
const server = new Server({ name: "weather-server", version: "1.0.0" }, { capabilities: { tools: {} } });

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [{ name: "get_weather", description: "Get weather", inputSchema: { type: "object", properties: { city: { type: "string" } }, required: ["city"] } }],
}));
server.setRequestHandler(CallToolRequestSchema, async ({ params }) => ({
  content: [{ type: "text", text: `Weather in ${(params.arguments as any).city}: Sunny, 72°F` }],
}));

app.get("/mcp", async (req, res) => {
  await server.connect(new SSEServerTransport("/mcp", res));
});
app.listen(8000);
```

---

## convertMcpToLangchainTools vs. MultiServerMCPClient

```typescript
import { convertMcpToLangchainTools } from "@h1deya/langchain-mcp-tools";

const { tools, cleanup } = await convertMcpToLangchainTools({
  filesystem: { command: "npx", args: ["-y", "@modelcontextprotocol/server-filesystem", "."] },
  github: { type: "http", url: "https://api.githubcopilot.com/mcp/", headers: { Authorization: `Bearer ${process.env.GITHUB_TOKEN}` } },
}, { llmProvider: "google_gemini", logLevel: "debug" });

try { /* use tools */ } finally { await cleanup(); }
```

| Feature | `MultiServerMCPClient` | `convertMcpToLangchainTools` |
|---------|----------------------|------------------------------|
| MCP Resources/Prompts | Yes | No (tools only) |
| Hooks/interceptors | Yes | No |
| OAuth support | Yes | Yes |
| WebSocket transport | No | Yes |
| LLM schema adaptation | No | Yes (`llmProvider`) |
| Maintenance | Official | Community |
| Use case | Production, full feature set | Lightweight prototyping, WebSocket |

---

## Ecosystem

### Composio (250+ servers)

```typescript
const client = new MultiServerMCPClient({
  mcpServers: {
    github: { transport: "sse", url: `https://mcp.composio.dev/${process.env.COMPOSIO_API_KEY}/github/sse` },
    slack: { transport: "sse", url: `https://mcp.composio.dev/${process.env.COMPOSIO_API_KEY}/slack/sse` },
  },
});
```

### Popular Official Packages

| Server | Package | Key tools |
|--------|---------|-----------|
| Filesystem | `@modelcontextprotocol/server-filesystem` | `read_file`, `write_file`, `list_directory` |
| Brave Search | `@modelcontextprotocol/server-brave-search` | `brave_web_search` |
| GitHub | `@modelcontextprotocol/server-github` | `create_issue`, `search_code` |
| Postgres | `@modelcontextprotocol/server-postgres` | `query` |
| Puppeteer | `@modelcontextprotocol/server-puppeteer` | `navigate`, `screenshot` |
| Kubernetes | `kubernetes-mcp-server` | `list_pods`, `get_logs` |

---

## Production Patterns

### Token Optimization — On-Demand Loading

Loading all MCP tools adds 45,000–50,000 tokens per run (filesystem + linear + GitHub + Figma combined). Load only what the current task needs:

```typescript
const serverConfigs = {
  fs: { transport: "stdio", command: "npx", args: ["-y", "@modelcontextprotocol/server-filesystem", "."] },
  github: { transport: "stdio", command: "npx", args: ["-y", "@modelcontextprotocol/server-github"], env: { GITHUB_PERSONAL_ACCESS_TOKEN: process.env.GITHUB_TOKEN! } },
} as const;

const taskServers = { filesystem: ["fs"], code: ["github", "fs"] } as const;

async function getTaskTools(task: keyof typeof taskServers) {
  const client = new MultiServerMCPClient({
    mcpServers: Object.fromEntries(taskServers[task].map(n => [n, serverConfigs[n]])),
  });
  return { tools: await client.getTools(), client };
}
```

### Connection Pooling

```typescript
class MCPClientPool {
  private static instance: MultiServerMCPClient | null = null;
  static async get() {
    if (!this.instance) {
      this.instance = new MultiServerMCPClient({ throwOnLoadError: false, onConnectionError: "ignore", mcpServers: { /* ... */ } });
    }
    return this.instance;
  }
  static async close() { await this.instance?.close(); this.instance = null; }
}
process.on("SIGINT", () => MCPClientPool.close().then(() => process.exit(0)));
process.on("SIGTERM", () => MCPClientPool.close().then(() => process.exit(0)));
```

### Namespacing

```typescript
// Prevents "search" collision when multiple servers expose the same tool name
const client = new MultiServerMCPClient({
  prefixToolNameWithServerName: true,  // "github__search", "linear__search"
  mcpServers: { github: { ... }, linear: { ... } },
});
```

### Health Monitoring

```typescript
const client = new MultiServerMCPClient({
  onMessage: (log, source) => {
    metrics.increment("mcp.log_message", { server: source.server, level: log.level });
  },
  onProgress: (prog, source) => {
    if (prog.percentage !== undefined) {
      metrics.gauge("mcp.tool_progress", prog.percentage, { server: source.server });
    }
  },
  onToolsListChanged: (evt, source) => {
    console.log(`Tools updated on ${source.server}:`, evt);
    metrics.increment("mcp.tools_list_changed", { server: source.server });
  },
  mcpServers: { ... },
});
```

### Audit Logging

```typescript
const client = new MultiServerMCPClient({
  beforeToolCall: async ({ serverName, name, args }) => {
    auditLog.write({ event: "tool_call_start", server: serverName, tool: name, timestamp: Date.now() });
    return { args };
  },
  afterToolCall: async (result) => {
    auditLog.write({ event: "tool_call_end", timestamp: Date.now() });
    return result;
  },
  mcpServers: { ... },
});
```

---

## Security

- **Credentials:** Always use env vars. Never hardcode tokens. Use `authProvider` (OAuth 2.0) in production over static headers.
- **Prompt injection:** Sanitize user inputs before they reach MCP tools. Check for patterns like `"ignore previous instructions"`, enforce length limits.
- **Least privilege:** Scope filesystem servers to specific directories, not `/`. Use `env: {}` to clear inherited env vars from subprocess servers.
- **Audit logging:** Use `beforeToolCall`/`afterToolCall` hooks to log every tool invocation with server, tool name, and timestamp.
- **Validation:** Set `throwOnLoadError: true` in production to reject malformed tool definitions.

---

## MCP vs. Native LangChain Tools

| Criterion | MCP Tools | Native Tools |
|-----------|-----------|--------------|
| Definition | External server, dynamic discovery | Local TS function |
| Token overhead | 45–50k for large server sets | Zero |
| Cross-language | Yes | No |
| Vendor ecosystem | Yes (Composio, Smithery) | No |
| Latency | Network/subprocess overhead | Zero (local call) |
| Multi-server | Built-in | Manual namespacing |

Use MCP for: third-party ecosystems, language-agnostic servers, 20+ tools from multiple domains, Claude Desktop access.

Use native tools for: fewer than 10 simple local tools, latency-sensitive operations, pure TS/JS with no cross-language needs.

Hybrid: native tools for high-frequency ops (caching, formatting); MCP for external service integrations (GitHub, databases, search).

---

## Session Lifecycle

```
1. new MultiServerMCPClient({ mcpServers: {...} })     → Zod config validation
2. await client.getTools()
   ├─ stdio: spawn subprocess, MCP handshake
   ├─ HTTP: POST InitializeRequest, receive session ID
   └─ SSE: GET /mcp, open event stream
   └─ Fetch tool manifest → LangChain StructuredTool[]
3. agent.invoke(...)
   └─ LLM selects tool(s)
   └─ Per tool call:
      ├─ beforeToolCall hook
      ├─ New session (stateless) or existing (stateful)
      ├─ MCP CallToolRequest over transport
      ├─ afterToolCall hook
      └─ Result → ToolMessage
4. await client.close()
   ├─ stdio: SIGTERM to subprocess
   ├─ HTTP: close connections
   └─ SSE: close event stream
```

---

## Known Pitfalls

**`RunnableConfig` timeout does not propagate to MCP tool calls** (GitHub issue #9560, Dec 2025).
Passing `{ timeout: N }` via `RunnableConfig` to a tool invocation does not reliably stop MCP calls. Use `defaultToolTimeout` on the `MultiServerMCPClient` constructor instead.

**`spawn ENOENT` on Windows with stdio transport.**
`npx` is not a native binary on Windows — calling it directly causes a spawn error. Fix: use `cmd /c npx` as the command, or resolve the full path `node ./node_modules/.bin/npx`. Alternatively switch to HTTP/SSE transport.

**Stateless client spawns a new subprocess per tool call on stdio.**
On Windows and slow systems, each tool invocation incurs full subprocess startup time. For repeated calls to the same stdio server, use a persistent `Client` instance via `loadMcpTools` (stateful session pattern).

**Preloading all MCP tools exceeds the context budget.**
50k+ tokens for a full server set (filesystem + linear + GitHub + Figma combined) is not unusual and consumes ~25% of a 200k model's context window. Load only the servers relevant to the current task.

**Old `langchainjs-mcp-adapters` repo is archived.**
The repository `langchain-ai/langchainjs-mcp-adapters` was archived in May 2025. The current package lives inside the main monorepo at `github.com/langchain-ai/langchainjs/tree/main/libs/langchain-mcp-adapters`.

**Static header auth does not auto-refresh tokens.**
If a token expires mid-session, the client will receive 401 errors with no automatic recovery. Use `authProvider` (OAuth 2.0) for production workloads where token expiry is a concern.

**MCP Prompts and Resources API is under-documented for TypeScript.**
As of December 2025, `client.getPrompt()` and `client.getResources()` on `MultiServerMCPClient` are not fully documented for LangGraph TypeScript. Prefer calling `client.listPrompts()`, `client.getPrompt()`, and `client.listResources()` directly on the `@modelcontextprotocol/sdk` `Client` instance for reliability.

**SSE transport is deprecated.**
The MCP spec officially deprecated SSE-only transport in favor of Streamable HTTP. Only use `transport: "sse"` for servers that have not yet migrated. Set `automaticSSEFallback: true` on HTTP configs to handle servers mid-migration.

**`@modelcontextprotocol/sdk` v2 breaking changes expected Q1 2026.**
Pin your SDK version (`~1.x`) in `package.json` until the v2 migration guide is available.

### Error Quick-Reference

| Error | Cause | Fix |
|-------|-------|-----|
| `spawn ENOENT` (Windows) | `npx` not on PATH | Use `cmd /c npx` as command |
| `Connection closed` (Windows) | Stateless spawns new subprocess per call | Use stateful session or HTTP transport |
| `ZodError: invalid config` | Wrong config shape | Check required fields; read full Zod error |
| Tool timeout ignored | `RunnableConfig` timeout bug (#9560, Dec 2025) | Use `defaultToolTimeout` on client instead |
| `400 Bad Request` | Wrong `MCP-Protocol-Version` header | Upgrade `@modelcontextprotocol/sdk` |
| Token budget exceeded | All tools preloaded | Use on-demand loading |
| `ToolException` on every call | Server-side error | Check stdio stderr; set `stderr` logging |

### Debug Logging

```bash
DEBUG='@langchain/mcp-adapters:*' node my-agent.js
DEBUG='@langchain/mcp-adapters:client' node my-agent.js
DEBUG='@langchain/mcp-adapters:tools' node my-agent.js
MODEL_CONTEXT_DEBUG=true node my-agent.js
```

---

## Quick-Start Checklist

- [ ] `npm install @langchain/mcp-adapters`
- [ ] Transport: `stdio` for local dev, Streamable HTTP (`url:`) for production
- [ ] Set `useStandardContentBlocks: true`
- [ ] Set `throwOnLoadError: false` in dev, `true` in production
- [ ] Set `prefixToolNameWithServerName: true` with multiple servers
- [ ] Always `await client.close()` in `finally` or on `SIGTERM`/`SIGINT`
- [ ] Set `defaultToolTimeout` to prevent hanging tool calls
- [ ] On Windows: use stateful sessions to avoid per-call spawn overhead
- [ ] In production: use `authProvider` (OAuth) not static headers
- [ ] Limit preloaded tools to only the servers needed for the current task
