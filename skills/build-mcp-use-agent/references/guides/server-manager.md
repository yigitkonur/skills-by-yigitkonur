# Server Manager

The Server Manager enables dynamic multi-server orchestration — the agent automatically discovers, connects to, and switches between MCP servers based on the task.

## Enable server manager

```typescript
const agent = new MCPAgent({
  llm, client,
  useServerManager: true,
  verbose: true,  // recommended for debugging
});
```

## How it works

When `useServerManager: true`, the agent gets 5 built-in management tools:

| Tool | Description |
|------|-------------|
| `list_mcp_servers` | Returns all configured server identifiers |
| `connect_to_mcp_server` | Activates a server and loads its tools |
| `get_active_mcp_server` | Returns the currently active server (or null) |
| `disconnect_from_mcp_server` | Deactivates the current server |
| `add_mcp_server_from_config` | Adds a new server at runtime |

The agent's system prompt is automatically updated with server management instructions.

## Multi-server setup

```typescript
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

// Agent automatically picks the right server for each sub-task
const result = await agent.run(`
  1. Scrape data from https://example.com
  2. Save it as a JSON file
  3. Load it into a SQLite database
  4. Generate a summary report
`);
```

## Dynamic server addition

Add servers at runtime using `add_mcp_server_from_config`:

```typescript
import { ServerManager, AddMCPServerFromConfigTool } from "mcp-use";
import { LangChainAdapter } from "mcp-use/adapters";

const client = new MCPClient(); // start empty

const serverManager = new ServerManager(client, new LangChainAdapter());
serverManager.setManagementTools([
  new AddMCPServerFromConfigTool(serverManager),
]);

const agent = new MCPAgent({
  llm, client,
  useServerManager: true,
  serverManagerFactory: () => serverManager,
  autoInitialize: true,
  maxSteps: 30,
});

// Agent can now add servers via prompts
await agent.run(`Add a Playwright server with config: ${JSON.stringify({
  command: "npx",
  args: ["@playwright/mcp@latest"],
})}, then browse the web.`);
```

## Server config options

```typescript
interface MCPServerConfig {
  command?: string;              // executable (for stdio servers)
  args?: string[];               // CLI arguments
  env?: Record<string, string>;  // environment variables
  url?: string;                  // HTTP/SSE endpoint (for remote servers)
  headers?: Record<string, string>; // custom headers
  auth_token?: string;           // authentication token
  transport?: "http" | "sse";    // transport type
}
```

## When to use server manager

| Scenario | Use Server Manager? |
|----------|-------------------|
| Single MCP server | No — direct connection is simpler |
| 2-3 servers, known in advance | Optional — useful if tasks span servers |
| Many servers, dynamic selection | Yes — agent auto-routes |
| Runtime server discovery | Yes — `add_mcp_server_from_config` |

## Best practices

1. **Use `verbose: true`** when debugging server manager behavior.
2. **Give servers descriptive names** — the agent uses names to decide which to connect to.
3. **Limit server count** — too many servers overwhelms the LLM's tool selection.
4. **Use `serverManagerFactory` for custom management tools** — beyond the 5 built-in ones.
