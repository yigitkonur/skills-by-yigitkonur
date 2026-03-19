# Server Manager

Manage and connect to multiple MCP servers simultaneously.

The Server Manager enables applications to connect to multiple MCP servers at once, combining capabilities from different sources to build powerful, integrated workflows.

---

## Why Use Multiple Servers?

| Reason | Example |
|---|---|
| **Compose capabilities** | Combine tools from different domains (file operations + database + web) |
| **Specialize** | Use dedicated servers for specific tasks |
| **Scale** | Distribute workload across multiple servers |
| **Integrate** | Connect to both local and remote services |

**Common Patterns:**
- Web scraping with Playwright + File operations with filesystem server
- Database queries with SQLite + API calls with HTTP server
- Code execution + Git operations + Documentation generation

---

## Configuration Reference

### MCPClientConfigShape

The top-level configuration object passed to `new MCPClient(config)`:

| Property | Type | Description |
|---|---|---|
| `mcpServers` | `Record<string, ServerConfig>` | Map of logical server IDs to their connection config. Keys are used by `getSession`. |
| `clientInfo?` | `ClientInfo` | Default client identity applied to all servers unless overridden per-server. |
| `onSampling?` | `OnSamplingCallback` | Global fallback for sampling requests from servers. |
| `onElicitation?` | `OnElicitationCallback` | Global fallback for elicitation requests from servers. |
| `onNotification?` | `OnNotificationCallback` | Global handler for server notifications. |

### ServerConfig

`ServerConfig` is a discriminated union of `StdioServerConfig` and `HttpServerConfig`. Each variant also accepts the callback fields `onSampling`, `onElicitation`, `onNotification`.

**StdioServerConfig** — for servers launched as child processes:

| Property | Type | Description |
|---|---|---|
| `command` | `string` | Executable to launch the server (e.g., `"npx"`). |
| `args` | `string[]` | Arguments passed to the command. |
| `env?` | `Record<string, string>` | Environment variables for the server process. Placeholders like `${VAR_NAME}` are replaced at runtime. |
| `onSampling?` | `OnSamplingCallback` | Per-server sampling callback (overrides global). |
| `onElicitation?` | `OnElicitationCallback` | Per-server elicitation callback (overrides global). |
| `onNotification?` | `OnNotificationCallback` | Per-server notification handler (overrides global). |

**HttpServerConfig** — for HTTP/SSE servers:

| Property | Type | Description |
|---|---|---|
| `url` | `string` | HTTP/SSE endpoint URL (e.g., `"http://localhost:3000/mcp"`). |
| `headers?` | `Record<string, string>` | Custom HTTP headers for all requests. |
| `authToken?` | `string` | Bearer token for Authorization header. |
| `transport?` | `'http' \| 'sse'` | Force a specific transport. Default: `'http'` (with SSE fallback). |
| `preferSse?` | `boolean` | Prefer SSE transport over streamable HTTP. |
| `disableSseFallback?` | `boolean` | Disable automatic SSE fallback. |
| `onSampling?` | `OnSamplingCallback` | Per-server sampling callback (overrides global). |
| `onElicitation?` | `OnElicitationCallback` | Per-server elicitation callback (overrides global). |
| `onNotification?` | `OnNotificationCallback` | Per-server notification handler (overrides global). |

### MCPClientOptions (second constructor argument)

The second argument to `new MCPClient(config, options)` sets global callback defaults:

| Property | Type | Description |
|---|---|---|
| `onSampling?` | `OnSamplingCallback` | Global sampling callback applied when no per-server callback matches. |
| `samplingCallback?` | `OnSamplingCallback` | Deprecated alias for `onSampling`. |
| `onElicitation?` | `OnElicitationCallback` | Global elicitation callback applied when no per-server callback matches. |
| `elicitationCallback?` | `OnElicitationCallback` | Deprecated alias for `onElicitation`. |
| `onNotification?` | `OnNotificationCallback` | Global notification handler. |
| `codeMode?` | `boolean \| CodeModeConfig` | Enable code execution mode. |

### MCPAgentOptions

| Property | Type | Description |
|---|---|---|
| `llm` | `any` | Language model instance (e.g., `ChatOpenAI`). |
| `client` | `MCPClient` | MCP client providing server connections. |
| `useServerManager?` | `boolean` | Lazy-start servers only when their tools are needed. |
| `maxSteps?` | `number` | Upper limit on tool-invocation steps per agent run. |
| `disallowedTools?` | `string[]` | Tool IDs the agent must not invoke. |
| `verbose?` | `boolean` | Enables per-step detailed logging from the agent. |

---

## MCPClient API

### Session Lifecycle

| Method | Parameters | Return | Description |
|---|---|---|---|
| `constructor` | `config: MCPClientConfigShape, options?: MCPClientOptions` | `MCPClient` | Instantiates the client with the supplied configuration and optional global callbacks. |
| `createAllSessions()` | – | `Promise<void>` | Starts a session on every configured server. |
| `createSession(serverName)` | `serverName: string` | `Promise<MCPSession>` | Creates and initializes a session for a single named server. |
| `getSession(serverName)` | `serverName: string` | `MCPSession` | Returns the already-created session object for the given server. |
| `closeAllSessions()` | – | `Promise<void>` | Gracefully closes every active session and shuts down managed servers. |

### MCPSession API

Once you have a session via `getSession()` or `createSession()`, you can interact with that server:

| Method | Parameters | Return | Description |
|---|---|---|---|
| `listTools(options?)` | `options?: RequestOptions` | `Promise<Tool[]>` | Retrieves available tools from the server. |
| `callTool(name, args?, options?)` | `name: string, args?: Record<string, any>, options?: RequestOptions` | `Promise<CallToolResult>` | Invokes a tool with the given arguments and returns its result. |
| `listResources(cursor?, options?)` | `cursor?: string, options?: RequestOptions` | `Promise<...>` | Lists available resources, with optional pagination cursor. |
| `readResource(uri, options?)` | `uri: string, options?: RequestOptions` | `Promise<...>` | Reads the content of a resource by URI. |
| `listPrompts()` | – | `Promise<Prompt[]>` | Lists all prompts exposed by the server. |
| `getPrompt(name, args)` | `name: string, args: Record<string, any>` | `Promise<PromptResult>` | Retrieves a prompt by name with the given arguments. |
| `complete(params)` | `params: CompleteRequestParams` | `Promise<CompleteResult>` | Requests argument completion suggestions. |
| `on("notification", handler)` | `handler: NotificationHandler` | `void` | Registers a listener for server notifications. |
| `serverCapabilities` | – | `Record<string, unknown>` | The capabilities reported by the server during initialization. |
| `serverInfo` | – | `{ name: string; version?: string } \| null` | The server's identity as reported at initialization. |
| `close()` / `disconnect()` | – | `Promise<void>` | Closes the underlying connection for this session only. |

```typescript
import { MCPClient } from 'mcp-use'

const client = new MCPClient({
  mcpServers: {
    'my-local-server': {
      command: 'npx',
      args: ['-y', '@modelcontextprotocol/server-everything'],
    },
    'cloud-server': {
      url: 'https://api.example.com/mcp',
    },
  },
})

// Start all server sessions at once
await client.createAllSessions()

// Work with a specific server session
const session = client.getSession('my-local-server')

// List tools
const tools = await session.listTools()
console.log('Available tools:', tools.map(t => t.name))

// Invoke a tool
const result = await session.callTool('summarize_text', {
  text: 'Lorem ipsum dolor sit amet...',
  maxLength: 150,
})
console.log('Result:', result)

// Close all sessions when done
await client.closeAllSessions()
```

---

## Basic Multi-Server Configuration

Create a configuration file that defines multiple servers:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"],
      "env": {
        "DISPLAY": ":1",
        "PLAYWRIGHT_HEADLESS": "true"
      }
    },
    "filesystem": {
      "command": "mcp-server-filesystem",
      "args": ["/safe/workspace/directory"],
      "env": {
        "FILESYSTEM_READONLY": "false"
      }
    },
    "sqlite": {
      "command": "mcp-server-sqlite",
      "args": ["--db", "/path/to/database.db"],
      "env": {
        "SQLITE_READONLY": "false"
      }
    },
    "github": {
      "command": "mcp-server-github",
      "args": ["--token", "${GITHUB_TOKEN}"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

---

## Using Multiple Servers

### Basic Approach (Manual Server Selection)

All servers connect when the agent is created:

```typescript
import { ChatOpenAI } from '@langchain/openai'
import { MCPAgent, MCPClient, loadConfigFile } from 'mcp-use'

async function main() {
    // Load multi-server configuration
    const config = await loadConfigFile('multi_server_config.json')
    const client = new MCPClient(config)

    // Create agent (all servers will be connected)
    const llm = new ChatOpenAI({ model: 'gpt-4' })
    const agent = new MCPAgent({ llm, client })

    // Agent has access to tools from all servers
    const result = await agent.run(
        'Search for Python tutorials online, save the best ones to a file, ' +
        'then create a database table to track my learning progress'
    )
    console.log(result)

    await client.closeAllSessions()
}

main().catch(console.error)
```

### Advanced Approach (Server Manager)

Enable the server manager for more efficient resource usage — servers connect only when needed:

```typescript
import { ChatOpenAI } from '@langchain/openai'
import { MCPAgent, MCPClient, loadConfigFile } from 'mcp-use'

async function main() {
    const config = await loadConfigFile('multi_server_config.json')
    const client = new MCPClient(config)
    const llm = new ChatOpenAI({ model: 'gpt-4' })

    // Enable server manager for dynamic server selection
    const agent = new MCPAgent({
        llm,
        client,
        useServerManager: true,  // Only connects to servers as needed
        maxSteps: 30
    })

    // The agent will automatically choose appropriate servers
    const result = await agent.run(
        'Research the latest AI papers, summarize them in a markdown file, ' +
        'and commit the file to my research repository on GitHub'
    )
    console.log(result)

    await client.closeAllSessions()
}

main().catch(console.error)
```

---

## Managing Server Dependencies

### Environment Variables

Store sensitive information in environment variables and reference them in config:

**.env**
```
GITHUB_TOKEN=ghp_...
DATABASE_URL=postgresql://user:pass@localhost/db
API_KEY=sk-...
WORKSPACE_PATH=/safe/workspace
```

**config.json**
```json
{
  "mcpServers": {
    "github": {
      "command": "mcp-server-github",
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "filesystem": {
      "command": "mcp-server-filesystem",
      "args": ["${WORKSPACE_PATH}"]
    }
  }
}
```

### Conditional Server Loading

Conditionally include servers based on availability:

```typescript
import { ChatOpenAI } from '@langchain/openai'
import { MCPClient, MCPAgent } from 'mcp-use'

async function createAgentWithAvailableServers() {
    const config: any = { mcpServers: {} }

    // Always include filesystem
    config.mcpServers.filesystem = {
        command: 'mcp-server-filesystem',
        args: ['/workspace']
    }

    // Include GitHub server if token is available
    if (process.env.GITHUB_TOKEN) {
        config.mcpServers.github = {
            command: 'mcp-server-github',
            env: { GITHUB_TOKEN: process.env.GITHUB_TOKEN }
        }
    }

    // Include database server if URL is available
    if (process.env.DATABASE_URL) {
        config.mcpServers.postgres = {
            command: 'mcp-server-postgres',
            env: { DATABASE_URL: process.env.DATABASE_URL }
        }
    }

    const client = new MCPClient(config)
    return new MCPAgent({
        llm: new ChatOpenAI({ model: 'gpt-4' }),
        client
    })
}
```

---

## Advanced Client Features

### Authentication for HTTP Servers

Pass an `authToken` in the server config to add a `Bearer` token to every HTTP request:

```typescript
const client = new MCPClient({
    mcpServers: {
        'secure-server': {
            url: 'https://api.example.com/mcp',
            authToken: process.env.API_KEY,
        },
    },
})
```

Custom headers can also be set per-server:

```typescript
const client = new MCPClient({
    mcpServers: {
        'custom-auth-server': {
            url: 'https://api.example.com/mcp',
            headers: {
                'X-Custom-Auth': 'my-token',
                'X-API-Version': '2',
            },
        },
    },
})
```

### Code Mode

Enable code execution mode for tools that return executable code:

```typescript
const client = new MCPClient(
    { mcpServers: { /* ... */ } },
    { codeMode: true }
)
```

For advanced configuration, use the `CodeModeConfig` shape:

```typescript
const client = new MCPClient(
    { mcpServers: { /* ... */ } },
    {
        codeMode: {
            enabled: true,
            executor: 'vm',          // 'vm' (default) or 'e2b'
            executorOptions: {
                timeoutMs: 30000,
            },
        },
    }
)
```

---

## Performance Optimization

### Server Manager Benefits

| Benefit | Description |
|---|---|
| **Lazy loading** | Servers connect only when their tools are needed |
| **Dynamic selection** | Agent automatically chooses which server to use |
| **Resource efficiency** | Only active servers consume resources |

```typescript
// Without server manager — all servers start immediately
const agent = new MCPAgent({ llm, client, useServerManager: false })
// Result: All 5 servers start, consuming resources

// With server manager — servers start only when needed
const agentOptimized = new MCPAgent({ llm, client, useServerManager: true })
// Result: Only the required servers start for each task
```

### Tool Filtering

Block specific tools from an agent using the deny-list approach:

```typescript
// Block specific tools by ID
const agent = new MCPAgent({
    llm,
    client,
    disallowedTools: ['system_exec', 'network_request']
})
```

---

## Troubleshooting Multi-Server Setups

### Common Issues

**Server startup failures** — check logs and ensure all dependencies are installed:

```typescript
import { logger } from 'mcp-use'

// Enable detailed logging
logger.level = 'debug'
const config = await loadConfigFile('config.json')
const client = new MCPClient(config)
```

### Debug Configuration

Enable comprehensive debugging:

```typescript
import { logger, MCPAgent, MCPClient, loadConfigFile } from 'mcp-use'
import { ChatOpenAI } from '@langchain/openai'

// Enable debug logging
logger.level = 'debug'

const config = await loadConfigFile('multi_server_config.json')
const client = new MCPClient(config)

const llm = new ChatOpenAI({ model: 'gpt-4' })

// Create agent with verbose output
const agent = new MCPAgent({
    llm,
    client,
    useServerManager: true,
    verbose: true
})
```

---

## Best Practices

- **Start simple** — Begin with 2–3 servers and add more as needed. Too many servers can overwhelm the LLM.
- **Use Server Manager** — Enable `useServerManager: true` for better performance and resource management.
- **Environment variables** — Store sensitive configuration like API keys in environment variables, not config files.
- **Error handling** — Implement graceful degradation when servers are unavailable or fail.
- **Enable debug logging** — Set `logger.level = 'debug'` and `verbose: true` on the agent to trace tool calls across servers.
- **Use `disallowedTools` for security** — Block dangerous tools explicitly rather than relying solely on the LLM's judgment.
- **Close sessions explicitly** — Always call `client.closeAllSessions()` (or `session.close()`) when done to free resources and terminate managed server processes.
