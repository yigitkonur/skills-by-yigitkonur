# Server Manager

Server manager mode lets MCPAgent dynamically connect to multiple MCP servers and route tools intelligently.

---

## Why use server manager

Use server manager when you need:

- Multiple MCP servers (filesystem, db, search, etc.)
- Dynamic server addition at runtime
- Lazy loading (connect only when needed)
- Tool filtering across servers

---

## Key imports

```typescript
import { MCPAgent, MCPClient } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";
```

---

## Enabling server manager

Set `useServerManager: true` in MCPAgent.

```typescript
const client = new MCPClient({
  mcpServers: {
    playwright: {
      command: "npx",
      args: ["@playwright/mcp@latest"],
    },
    filesystem: {
      command: "uvx",
      args: ["mcp-server-filesystem", "/tmp"],
    },
  },
});

const agent = new MCPAgent({
  llm: new ChatOpenAI({ model: "gpt-4o" }),
  client,
  useServerManager: true,
});
```

---

## MCPAgent configuration

| Parameter | Type | Default | Description |
|---|---|---|---|
| `llm` | LangChain LLM instance | – | The language model used for generation (e.g., `ChatOpenAI`) |
| `client` | `MCPClient` | – | Instance that manages MCP server connections |
| `useServerManager` | `boolean` | `false` | When `true`, enables dynamic multi-server orchestration |
| `verbose` | `boolean` | `false` | When `true`, enables detailed logging of Server Manager actions |
| `maxSteps` | `number` | `5` | Upper bound on tool-calling steps before the agent stops |
| `memoryEnabled` | `boolean` | `true` | When `false`, each `run()` is stateless; when `true`, the agent retains conversation history |

---

## MCPClient multi-server configuration

### Configuration table

| Field | Type | Description |
|---|---|---|
| `command` | `string` | Executable to start the MCP server |
| `args` | `string[]` | Arguments passed to the command |

### MCPClient type

```typescript
mcpServers: Record<string, { command: string; args: string[] }>
```

### Example: multiple STDIO servers

```typescript
const client = new MCPClient({
  mcpServers: {
    web: {
      command: "npx",
      args: ["@playwright/mcp@latest"],
    },
    files: {
      command: "uvx",
      args: ["mcp-server-filesystem", "/tmp"],
    },
    database: {
      command: "uvx",
      args: ["mcp-server-sqlite"],
    },
  },
});
```

---

## MCPAgent API methods

| Method | Signature | Description |
|---|---|---|
| `run` | `(opts: { prompt: string; schema?: ZodSchema<any>; maxSteps?: number }): Promise<any>` | Executes a single agent cycle. Returns the final LLM response (typed if `schema` supplied). |
| `stream` | `(opts: { prompt: string }): AsyncIterable<{ action: { tool: string; args: any } }>` | Yields each step as the agent selects and runs a tool. |
| `prettyStreamEvents` | `(opts: { prompt: string; maxSteps?: number }): AsyncIterable<void>` | Same as `stream` but prints formatted, syntax-highlighted output (CLI-friendly). |
| `streamEvents` | `(opts: { prompt: string }): AsyncIterable<{ event: string; data?: any }>` | Low-level event stream (e.g., `event === 'on_chat_model_stream'` gives raw LLM chunks). |
| `close` | `(): Promise<void>` | Gracefully shuts down any open server processes and releases resources. |
| `clearConversationHistory` | `(): void` | Empties the internal memory buffer when `memoryEnabled` is true. |

### run() examples

```typescript
// Basic usage
const response = await agent.run({ prompt: "What is in the current folder?" });
console.log(response);
await agent.close();
```

```typescript
// Structured output with Zod
import { z } from "zod";

const result = await agent.run({
  prompt: "Analyze the file structure",
  schema: z.object({
    totalFiles: z.number(),
    fileTypes: z.array(z.string()),
    largestFile: z.string(),
  }),
});

console.log(result.totalFiles); // fully typed
```

### Streaming examples

```typescript
// Step-by-step streaming
for await (const step of agent.stream({ prompt: "Write a report" })) {
  console.log(`Tool: ${step.action.tool}`);
}

// Pretty formatted streaming (CLI friendly)
for await (const _ of agent.prettyStreamEvents({
  prompt: "Analyze the codebase",
  maxSteps: 20,
})) {
  // automatic syntax highlighting
}

// Low-level event streaming
for await (const event of agent.streamEvents({ prompt: "Generate content" })) {
  if (event.event === "on_chat_model_stream") {
    process.stdout.write(event.data?.chunk?.content ?? "");
  }
}
```

---

## Lazy loading (connect on first tool call)

The Server Manager intercepts tool calls. If the required tool's server is not active, it automatically runs `connect_to_mcp_server` behind the scenes, loads only that tool, executes it, then may keep the server active based on usage patterns. Servers defined in `mcpServers` are **not** connected at startup.

**Benefits:**

- Faster startup
- Lower resource usage
- Only connect to required servers

**Tradeoff:**

- First tool call to a server incurs connection latency

---

## Management tools

When `useServerManager: true`, the agent gains access to these built-in management tools:

| Tool | Parameters | Purpose | Example prompt |
|---|---|---|---|
| `list_mcp_servers` | none | Discover available servers and their exposed tools | "What servers do I have access to?" |
| `connect_to_mcp_server` | `serverName: string` | Activate a server and load its tools into the agent context | "Connect to the filesystem server." |
| `get_active_mcp_server` | none | Retrieve the currently connected server, or report none | "Which server am I currently using?" |
| `disconnect_from_mcp_server` | none | Deactivate the current server and unload its tools | "Disconnect from current server." |
| `add_mcp_server_from_config` | `serverName: string`, `serverConfig: object` | Dynamically add and connect to a new server | "Add a new server with this configuration." |

---

## Dynamic server addition

Use the `add_mcp_server_from_config` management tool to add servers at runtime. The `config` parameter follows the same shape as entries in `MCPClient`'s `mcpServers`.

### Config shape

The `add_mcp_server_from_config` tool takes these parameters (as seen by the LLM via its Zod schema):

| Parameter | Type | Required | Description |
|---|---|---|---|
| `serverName` | `string` | Yes | Unique identifier for the server (the key in `mcpServers`) |
| `serverConfig` | object | Yes | Configuration object for the server — same shape as a `mcpServers` entry (`command`, `args`, `env`, `url`, etc.) |

### Example

```typescript
// Let the agent discover it needs a new server and add it
const result = await agent.run(
  "I need to query the SQLite database. Add the sqlite server and show me the available tables."
  // Agent reasoning:
  // 1. No sqlite tools available.
  // 2. Call add_mcp_server_from_config with { command: "uvx", args: ["mcp-server-sqlite"] }.
  // 3. Connect to the new server and proceed.
);
```

---

## Transport types

The official MCPClient `ServerConfig` uses `command` + `args` (STDIO) as its documented interface. The underlying MCP protocol supports multiple transports:

| Transport | Description |
|---|---|
| STDIO | Communication over standard input/output streams |
| HTTP | REST-style HTTP requests |
| SSE | Server-Sent Events for streaming responses |

---

## Server health and cleanup

Use `agent.close()` or `client.closeAllSessions()` to clean up processes on shutdown.

**Reconnection strategies:**

1. **Agent-driven reconnect:** If a tool call fails, the agent can call `disconnect_from_mcp_server` then `connect_to_mcp_server` to re-establish the connection.
2. **Graceful shutdown:** Always call `agent.close()` or `client.closeAllSessions()` when done to clean up STDIO processes and connections.
3. **Health verification:** Use `get_active_mcp_server` to check the current connection state.

### Health monitoring checklist

- [ ] Error handling around `agent.run()` calls
- [ ] Graceful cleanup via `agent.close()` or `client.closeAllSessions()` on shutdown

---

## BAD / GOOD patterns

### 1) Using a plain string for run() instead of the options object

Passing a plain string still works but is **deprecated**. The options object form is required to use `schema`, `maxSteps`, or `signal`.

BAD
```typescript
// Deprecated — works but cannot pass schema/maxSteps/signal
await agent.run("What is in the current folder?");
```

GOOD
```typescript
// Preferred — enables all options
await agent.run({ prompt: "What is in the current folder?" });
```

### 2) Eagerly connecting all servers

BAD
```typescript
await client.createAllSessions();
```

GOOD
```typescript
const agent = new MCPAgent({ llm, client, useServerManager: true });
// The Server Manager will auto-connect servers as tools are needed
```

### 3) Silently ignoring tool failures

BAD
```typescript
try {
  await agent.run({ prompt: "Read the database schema" });
} catch (e) {} // Silent failure, server may be disconnected
```

GOOD
```typescript
try {
  await agent.run({ prompt: "Read the database schema" });
} catch (e) {
  console.error("Agent run failed:", e);
  // The agent can reconnect on the next run via its management tools
  await agent.run({ prompt: "Check which server is active and reconnect to database if needed" });
}
```

---

## Complete multi-server example

```typescript
import { MCPClient, MCPAgent } from "mcp-use";
import { ChatOpenAI } from "@langchain/openai";

async function demoServerManager() {
  const client = new MCPClient({
    mcpServers: {
      web: { command: "npx", args: ["@playwright/mcp@latest"] },
      files: { command: "uvx", args: ["mcp-server-filesystem", "/tmp"] },
      database: { command: "uvx", args: ["mcp-server-sqlite"] },
    },
  });

  const agent = new MCPAgent({
    llm: new ChatOpenAI({ model: "gpt-4o" }),
    client,
    useServerManager: true,
    verbose: true,
  });

  const result = await agent.run({
    prompt: `
      I need to build a complete data collection system:

      1. Show available servers and tools.
      2. Scrape product info from https://example-store.com.
      3. Clean and structure the data.
      4. Save as JSON and CSV.
      5. Load into a SQLite database.
      6. Generate a summary report.
    `,
  });

  console.log("Task completed!");
  console.log(result);

  await client.closeAllSessions();
}

demoServerManager().catch(console.error);
```

---

## Tool discovery flow

When `useServerManager: true`, the agent uses built-in management tools to discover and connect to servers:

1. **List available servers:** The agent calls `list_mcp_servers` to see what servers are configured and what tools each exposes.
2. **Connect to a server:** The agent calls `connect_to_mcp_server` with `serverName` to activate a server and load its tools into context.
3. **Use server tools:** Once connected, the server's tools become available for the agent to call.
4. **Check active server:** The agent calls `get_active_mcp_server` to verify the current connection status.
5. **Switch servers:** The agent calls `connect_to_mcp_server` with a different server name.
6. **Disconnect:** The agent calls `disconnect_from_mcp_server` to deactivate the current server.
7. **Add new server:** The agent calls `add_mcp_server_from_config` with `serverName` and `serverConfig` to register and immediately connect to a new server.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Tool not found | Server not connected | Use `connect_to_mcp_server` or add the server first with `add_mcp_server_from_config` |
| First call slow | Lazy loading | Expected behavior; Server Manager connects on first use |
| Cannot pass `schema` or `maxSteps` to `run()` | Using deprecated plain-string form | Switch to `agent.run({ prompt: "...", maxSteps: 20 })` |
| Server addition fails | Wrong parameter names | `add_mcp_server_from_config` expects `serverName` (string) and `serverConfig` (object), not `serverId` and `config` |

---

## Summary

- Enable with `useServerManager: true` on `MCPAgent`.
- Configure multi-server `mcpServers` in `MCPClient` using `{ command, args, env?, url?, headers? }` per server.
- Lazy loading is automatic — the Server Manager connects servers on first tool use; do not call `client.createAllSessions()` when using Server Manager.
- Add servers dynamically at runtime via the `add_mcp_server_from_config` tool with `{ serverName, serverConfig }` parameters.
- `memoryEnabled` defaults to `true`; set it explicitly to avoid accidental cross-request contamination.
- `maxSteps` defaults to `5`; raise it substantially for multi-server workflows.
- Use `agent.close()` or `client.closeAllSessions()` for graceful shutdown.
- Use `verbose: true` on `MCPAgent` for detailed Server Manager logging.
