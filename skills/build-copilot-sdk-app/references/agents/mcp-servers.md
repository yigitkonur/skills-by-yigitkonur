# MCP Servers — Reference

MCP (Model Context Protocol) servers extend the Copilot runtime with external tools. The SDK supports two transports: **local stdio** (subprocess) and **remote HTTP/SSE** (network). MCP servers are registered per-session and their tools appear alongside built-in tools for the duration of that session.

---

## `MCPServerConfig` Type

The union type covers both local and remote variants:

```typescript
// Local / stdio subprocess
interface MCPLocalServerConfig {
    type?: "local" | "stdio";    // defaults to "local" when omitted
    command: string;             // executable to spawn
    args: string[];              // command-line arguments
    env?: Record<string, string>; // additional environment variables
    cwd?: string;                // working directory for the subprocess
    tools: string[];             // "*" = all, [] = none, or explicit list
    timeout?: number;            // ms; per-call timeout
}

// Remote HTTP or SSE endpoint
interface MCPRemoteServerConfig {
    type: "http" | "sse";        // required for remote
    url: string;                 // full URL to the MCP server
    headers?: Record<string, string>; // HTTP headers (auth, etc.)
    tools: string[];
    timeout?: number;
}

type MCPServerConfig = MCPLocalServerConfig | MCPRemoteServerConfig;
```

---

## MCP Server Registration in SessionConfig

Register servers in the `mcpServers` field — a `Record<string, MCPServerConfig>` where each key is the server's logical name.

```typescript
import { CopilotClient } from "@github/copilot-sdk";

const client = new CopilotClient();
await client.start();

const session = await client.createSession({
    onPermissionRequest: async () => ({ kind: "approved" }),
    mcpServers: {
        "filesystem": {
            type: "local",
            command: "npx",
            args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            tools: ["*"],
        },
        "github": {
            type: "http",
            url: "https://api.githubcopilot.com/mcp/",
            headers: { "Authorization": `Bearer ${process.env.GITHUB_TOKEN}` },
            tools: ["*"],
        },
    },
});
```

The server name (e.g., `"filesystem"`) becomes the namespace prefix for tool disambiguation. See Tool Namespace Handling below.

---

## Local MCP Server Config (stdio)

Spawns a subprocess and communicates via stdin/stdout using the MCP stdio transport.

```typescript
mcpServers: {
    "my-server": {
        type: "local",      // or "stdio" — identical behavior
        command: "node",
        args: ["./servers/my-mcp-server.js"],
        env: {
            DATABASE_URL: process.env.DATABASE_URL!,
            DEBUG: "mcp:*",
        },
        cwd: "./servers",
        tools: ["*"],       // expose all tools this server offers
        timeout: 30_000,    // 30s per tool call
    },
}
```

Use `npx -y <package>` as the command to run published MCP servers without installing them:

```typescript
{
    command: "npx",
    args: ["-y", "@modelcontextprotocol/server-postgres", "postgresql://localhost/mydb"],
    tools: ["*"],
}
```

Pass secrets via `env`, not via `args` — args are visible in process listings.

---

## Remote MCP Server Config (HTTP/SSE)

Connects to a server over HTTP. Use `type: "http"` for standard HTTP and `type: "sse"` for Server-Sent Events streaming.

```typescript
mcpServers: {
    "remote-api": {
        type: "http",
        url: "https://mcp.example.com/v1",
        headers: {
            "Authorization": `Bearer ${process.env.API_KEY}`,
            "X-Tenant-ID": "acme",
        },
        tools: ["search", "fetch"],   // only expose a subset of tools
        timeout: 60_000,
    },
    "streaming-server": {
        type: "sse",
        url: "https://mcp.example.com/sse",
        headers: { "Authorization": `Bearer ${process.env.API_KEY}` },
        tools: ["*"],
    },
}
```

`type` is required for remote servers — omitting it causes the SDK to treat the config as a local server and fail to parse `url`.

---

## Multiple MCP Servers

Register any number of servers. Each runs independently; tool namespace prefixes prevent collisions.

```typescript
const session = await client.createSession({
    onPermissionRequest: async () => ({ kind: "approved" }),
    mcpServers: {
        "postgres": {
            command: "npx",
            args: ["-y", "@modelcontextprotocol/server-postgres", process.env.PG_URL!],
            tools: ["*"],
        },
        "github": {
            type: "http",
            url: "https://api.githubcopilot.com/mcp/",
            headers: { "Authorization": `Bearer ${process.env.GITHUB_TOKEN}` },
            tools: ["create_pull_request", "list_issues", "search_code"],
        },
        "filesystem": {
            command: "npx",
            args: ["-y", "@modelcontextprotocol/server-filesystem", process.cwd()],
            tools: ["read_file", "write_file", "list_directory"],
        },
    },
});
```

---

## MCP Tool Namespace Handling

When listing tools, the runtime exposes each MCP tool with a namespaced name in the format `<serverName>/<toolName>`. Use namespaced names when restricting tool access in `CustomAgentConfig.tools` or session-level `availableTools`.

```typescript
// Given: mcpServers: { "postgres": { ... } }
// The postgres MCP server exposes tools: query, list_tables, describe_table
// Namespaced names: "postgres/query", "postgres/list_tables", "postgres/describe_table"

// Restrict an agent to only postgres query tool
customAgents: [
    {
        name: "db-reader",
        tools: ["postgres/query", "postgres/list_tables"],
        prompt: "Read-only database analyst.",
    },
]
```

The `namespacedName` field is returned by `session.rpc.tools.list()` (server-scoped RPC) when a model-specific tool listing is requested.

---

## MCP Server Lifecycle

MCP servers start when the session is created and stop when the session is disconnected. There is no manual start/stop API — lifecycle is tied entirely to session lifecycle.

```typescript
// Servers start here
const session = await client.createSession({ mcpServers: { ... } });

// Servers are running — tools available throughout
await session.sendAndWait({ prompt: "Query the database for recent orders." });

// Servers stop here
await session.disconnect();
```

On `client.resumeSession()`, pass `mcpServers` again in `ResumeSessionConfig` — servers are re-launched fresh on each resume.

---

## Debugging MCP Server Connections

When MCP tools are not appearing or are not being called:

1. Check the command path resolves: run the command manually in a terminal before adding it to the SDK.
2. Verify `tools` is not `[]` — an empty array means no tools are exposed.
3. Confirm the server starts without crashing. Local stdio servers that exit immediately on startup cause silent failures.
4. Enable debug logging on the client to see MCP lifecycle messages:

```typescript
const client = new CopilotClient({ logLevel: "debug" });
```

5. For remote servers, verify headers contain valid credentials. A 401 from the remote server will prevent tool registration.
6. Use `env` to pass `DEBUG` variables into local server processes:

```typescript
{
    command: "node",
    args: ["./my-server.js"],
    env: { DEBUG: "*", NODE_ENV: "development" },
    tools: ["*"],
}
```

Common error patterns:

| Symptom | Cause | Fix |
|---|---|---|
| Tools never appear | `tools: []` | Set `tools: ["*"]` |
| "command not found" | Binary not on PATH | Use absolute path or `npx` |
| Timeout on first call | Server slow to start | Increase `timeout` or pre-warm |
| 401 from remote server | Bad/expired token | Refresh token in `headers` |
| Server exits immediately | Startup crash | Check stderr output with `logLevel: "debug"` |

---

## Common MCP Server Patterns

### Database access

```typescript
// Postgres
"postgres": {
    command: "npx",
    args: ["-y", "@modelcontextprotocol/server-postgres", process.env.DATABASE_URL!],
    tools: ["*"],
}

// SQLite
"sqlite": {
    command: "npx",
    args: ["-y", "@modelcontextprotocol/server-sqlite", "./data/app.db"],
    tools: ["*"],
}
```

### External API access

```typescript
// GitHub
"github": {
    type: "http",
    url: "https://api.githubcopilot.com/mcp/",
    headers: { "Authorization": `Bearer ${process.env.GITHUB_TOKEN}` },
    tools: ["*"],
}

// Slack (hypothetical custom MCP server)
"slack": {
    command: "node",
    args: ["./mcp/slack-server.mjs"],
    env: { SLACK_BOT_TOKEN: process.env.SLACK_BOT_TOKEN! },
    tools: ["post_message", "list_channels", "get_thread"],
}
```

### File system access

```typescript
"filesystem": {
    command: "npx",
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
    tools: ["*"],
    cwd: "/workspace",
}
```

### Browser automation

```typescript
"puppeteer": {
    command: "npx",
    args: ["-y", "@modelcontextprotocol/server-puppeteer"],
    tools: ["*"],
    timeout: 120_000,  // browser operations can be slow
}
```

---

## Selective Tool Exposure

Use an explicit `tools` array to expose only a subset of what the server offers. This reduces the tool surface area visible to the model and can improve response quality.

```typescript
"github": {
    type: "http",
    url: "https://api.githubcopilot.com/mcp/",
    headers: { "Authorization": `Bearer ${token}` },
    // only expose read operations — no write tools
    tools: ["search_code", "get_file_contents", "list_issues", "get_pull_request"],
}
```

`"*"` exposes everything. `[]` exposes nothing (the server is still launched but contributes no tools). An explicit list exposes only the named tools.
