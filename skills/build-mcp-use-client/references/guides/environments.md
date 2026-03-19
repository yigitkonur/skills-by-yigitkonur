# Environments

Complete reference for mcp-use client environments — Node.js, Browser, React, and CLI entry points.

---

## Entry Points Overview

The mcp-use library ships four distinct entry points. Each targets a specific runtime with
optimized imports, connection types, and feature sets. Choose the entry point that matches
your deployment target.

| Environment | Import Path | Connections | Primary Use Cases |
|---|---|---|---|
| Node.js | `mcp-use` | STDIO, HTTP | Servers, automation scripts, programmatic access |
| Browser | `mcp-use/browser` | HTTP only | Web applications, browser extensions |
| React | `mcp-use/react` | HTTP only | React applications with hooks |
| CLI | `npx mcp-use client` | STDIO, HTTP | Terminal usage, testing, debugging, scripting |

> **Import rule:** Always import from `mcp-use`, `mcp-use/browser`, or `mcp-use/react`.
> Never import directly from `@modelcontextprotocol/sdk` — the mcp-use library wraps and
> re-exports the necessary primitives with its own session management, error handling, and
> lifecycle hooks.

---

## Node.js

The Node.js entry point provides the full feature set. Use it for backend services,
automation scripts, CLI tools, and any environment with access to the file system and
child process spawning.

**Node.js 18.0.0 or higher required.** The library supports both ESM (`import`) and
CommonJS (`require`) syntax.

### Import

```typescript
import { MCPClient } from "mcp-use";
```

### Capabilities

- **STDIO Connections** — Spawn MCP servers as child processes and communicate over stdin/stdout.
- **HTTP Connections** — Connect to remote MCP servers over HTTP with Streamable HTTP transport.
- **File System Operations** — Read and write config files, load server definitions from disk.
- **Code Mode** — Execute sandboxed code through MCP tool calls.
- **OAuth Authentication** — Full OAuth 2.0 flow support for authenticated servers.
- **Elicitation Handling** — Respond to server-initiated prompts programmatically.
- **Notification Callbacks** — React to server notifications in real time.

### Complete Example

```typescript
import { acceptWithDefaults, MCPClient } from "mcp-use";

const client = new MCPClient(
  { mcpServers: { myServer: { url: "http://localhost:3000/mcp" } } },
  {
    onElicitation: async (params) => acceptWithDefaults(params),
    onNotification: (n) => console.log(n.method),
  }
);

await client.createAllSessions();

const session = client.requireSession("myServer");
const tools = await session.listTools();
console.log("Available tools:", tools.map((t) => t.name));

const result = await session.callTool("tool_name", { param: "value" });
console.log("Result:", result);

await client.closeAllSessions();
```

### STDIO Connection

Use STDIO when the MCP server runs as a local child process. The client spawns the
process and communicates over stdin/stdout pipes.

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
    },
  },
});

await client.createAllSessions();
const session = client.requireSession("filesystem");

const result = await session.callTool("read_file", { path: "/tmp/example.txt" });
for (const item of result.content) {
  if (item.type === "text") console.log(item.text);
}

await client.closeAllSessions();
```

### HTTP Connection

Use HTTP when the MCP server is a remote service accessible over the network.

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    remote: {
      url: "https://api.example.com/mcp",
      headers: {
        Authorization: `Bearer ${process.env.API_TOKEN}`,
      },
    },
  },
});

await client.createAllSessions();
const session = client.requireSession("remote");
const tools = await session.listTools();
await client.closeAllSessions();
```

### Loading from Config File

Node.js supports loading configuration from JSON files. The simplest approach is passing the file path directly to the constructor. Alternatively, use the `loadConfigFile` named export (synchronous):

```typescript
// Option 1: pass file path directly to constructor (recommended)
import { MCPClient } from "mcp-use";

const client = new MCPClient("mcp-config.json");
await client.createAllSessions();

// Option 2: use loadConfigFile helper
import { MCPClient, loadConfigFile } from "mcp-use";

const config = loadConfigFile("mcp-config.json");
const client2 = new MCPClient(config);
await client2.createAllSessions();
```

#### Config File Structure

```json
{
  "mcpServers": {
    "python-server": {
      "command": "python",
      "args": ["-m", "my_mcp_server"],
      "env": {
        "DEBUG": "1"
      }
    },
    "uvx-server": {
      "command": "uvx",
      "args": ["blender-mcp"]
    },
    "npx-server": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest"],
      "env": {
        "DISPLAY": ":1"
      }
    },
    "remote-server": {
      "url": "https://api.example.com/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN"
      }
    }
  }
}
```

### Multiple Servers

Connect to several MCP servers simultaneously. Each server gets its own independent
session with isolated state.

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
    },
    database: {
      url: "http://localhost:4000/mcp",
    },
    analytics: {
      url: "https://analytics.example.com/mcp",
      headers: { Authorization: `Bearer ${process.env.ANALYTICS_TOKEN}` },
    },
  },
});

await client.createAllSessions();

// requireSession throws if the session does not exist (use getSession if you want null)
const fsSession = client.requireSession("filesystem");
const dbSession = client.requireSession("database");
const analyticsSession = client.requireSession("analytics");

// Use each session independently
const files = await fsSession.callTool("list_directory", { path: "/tmp" });
const query = await dbSession.callTool("run_query", { sql: "SELECT 1" });

await client.closeAllSessions();
```

### Elicitation Handling

Servers can request additional input from the client during tool execution. Handle
these requests with the `onElicitation` callback.

```typescript
import { acceptWithDefaults, MCPClient } from "mcp-use";

// Accept all elicitations with their schema defaults
const client = new MCPClient(
  { mcpServers: { myServer: { url: "http://localhost:3000/mcp" } } },
  {
    onElicitation: async (params) => acceptWithDefaults(params),
  }
);
```

---

## Browser

The browser entry point targets web applications running in the browser sandbox.
It excludes STDIO, file system, and code mode features that require Node.js APIs.

### Import

```typescript
import { MCPClient } from "mcp-use/browser";
```

### Capabilities and Limitations

| Feature | Status | Notes |
|---|---|---|
| HTTP Connections | ✅ Supported | Full Streamable HTTP transport |
| OAuth Authentication | ✅ Supported | Complete OAuth 2.0 flow with redirect handling |
| STDIO Connections | ❌ Not available | Cannot spawn child processes in browsers |
| File System Operations | ❌ Not available | Cannot read/write local files |
| Code Mode | ❌ Not available | Sandboxed code execution not supported |
| Config File Loading | ❌ Not available | No file system access |

### Basic Example

```typescript
import { MCPClient } from "mcp-use/browser";

const client = new MCPClient({
  mcpServers: {
    myServer: {
      url: "https://api.example.com/mcp",
      headers: { Authorization: "Bearer YOUR_TOKEN" },
    },
  },
});

await client.createAllSessions();
const session = client.requireSession("myServer");

const result = await session.callTool("tool_name", { param: "value" });
for (const item of result.content) {
  if (item.type === "text") console.log(item.text);
}

await client.closeAllSessions();
```

### HTTP with SSE Control

```typescript
import { MCPClient } from "mcp-use/browser";

// HTTP with automatic SSE fallback
const client = new MCPClient({
  mcpServers: {
    myServer: {
      url: "https://api.example.com/mcp",
      preferSse: false, // Set to true to force SSE
    },
  },
});
```

### Browser OAuth

Use `BrowserOAuthClientProvider` for servers that require OAuth 2.0 authentication.
The provider handles the full redirect-based authorization flow within the browser.

```typescript
import { MCPClient, BrowserOAuthClientProvider } from "mcp-use/browser";

const authProvider = new BrowserOAuthClientProvider({
  clientId: "your-client-id",
  authorizationUrl: "https://api.example.com/oauth/authorize",
  tokenUrl: "https://api.example.com/oauth/token",
  callbackUrl: window.location.origin + "/oauth/callback",
});

const client = new MCPClient({
  mcpServers: {
    myServer: { url: "https://api.example.com/mcp", authProvider },
  },
});

await client.createAllSessions();
const session = client.requireSession("myServer");
const tools = await session.listTools();
```

### CORS Considerations

Browser clients are subject to CORS restrictions. The MCP server must return appropriate
headers for cross-origin requests.

```typescript
// ❌ BAD: Connecting to a server without CORS headers — the browser blocks the request
const client = new MCPClient({
  mcpServers: {
    internal: { url: "http://internal-service:3000/mcp" },
  },
});

// ✅ GOOD: Connect to a server that returns proper CORS headers, or use a proxy
const client = new MCPClient({
  mcpServers: {
    api: { url: "https://api.example.com/mcp" }, // Server returns Access-Control-Allow-Origin
  },
});
```

### Browser Bundle Size

The `mcp-use/browser` entry point tree-shakes Node.js-specific code. Only HTTP transport
and OAuth utilities are included. This keeps the bundle small for web applications.

---

## React

The React entry point provides hooks-based integration with automatic connection state
management, tool discovery, and session lifecycle handling.

### Installation

```bash
yarn add mcp-use react
```

### Import

```typescript
import { useMcp } from "mcp-use/react";
```

### Single Server with `useMcp`

The `useMcp` hook manages a single MCP server connection. It handles connecting,
tool discovery, and cleanup automatically.

```typescript
import { useMcp } from "mcp-use/react";

function MyComponent() {
  const mcp = useMcp({
    url: "https://api.example.com/mcp",
    headers: { Authorization: "Bearer YOUR_API_KEY" },
  });

  if (mcp.state !== "ready") return <div>Connecting to MCP server...</div>;

  return (
    <div>
      <h2>Available Tools</h2>
      <ul>
        {mcp.tools.map((tool) => (
          <li key={tool.name}>
            <strong>{tool.name}</strong>: {tool.description}
          </li>
        ))}
      </ul>
    </div>
  );
}
```

### Connection States

The `mcp.state` property reflects the current stage of the connection lifecycle.
Handle each state to provide appropriate UI feedback.

| State | Description | Typical UI |
|---|---|---|
| `discovering` | Initial handshake with the server | Loading spinner |
| `authenticating` | OAuth flow in progress | "Authenticating…" message |
| `pending_auth` | Waiting for user to complete OAuth redirect | "Complete login in popup" |
| `ready` | Connected and tools are available | Render tools and allow calls |
| `failed` | Connection or authentication failed | Error message with retry |

```typescript
import { useMcp } from "mcp-use/react";

function ConnectionStatus() {
  const mcp = useMcp({ url: "https://api.example.com/mcp" });

  return (
    <div>
      {mcp.state === "discovering" && <p>Discovering server...</p>}
      {mcp.state === "authenticating" && <p>Authenticating...</p>}
      {mcp.state === "pending_auth" && <p>Waiting for authorization...</p>}
      {mcp.state === "ready" && <p>Connected and ready!</p>}
      {mcp.state === "failed" && (
        <div>
          <p>Connection failed</p>
          <p>{mcp.error}</p>
          <button onClick={mcp.retry}>Retry</button>
        </div>
      )}
    </div>
  );
}
```

### Calling Tools

Call tools directly through the `mcp` hook object using `mcp.callTool`:

```typescript
function ToolExecutor() {
  const mcp = useMcp({ url: "https://api.example.com/mcp" });
  const [result, setResult] = React.useState(null);

  const handleCallTool = async () => {
    try {
      const result = await mcp.callTool("send-email", {
        to: "[email protected]",
        subject: "Hello",
        body: "Test message",
      });
      setResult(result);
    } catch (error) {
      console.error("Tool call failed:", error);
    }
  };

  return (
    <div>
      <button onClick={handleCallTool} disabled={mcp.state !== "ready"}>
        Send Email
      </button>
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </div>
  );
}
```

### OAuth Authentication

The hook provides complete OAuth flow management. OAuth is auto-detected from server
metadata. Use `mcp.authUrl` to present the authorization link when state is `pending_auth`.

```typescript
function OAuthApp() {
  const mcp = useMcp({
    url: "https://api.example.com/mcp",
    // OAuth is auto-detected from server metadata
  });

  if (mcp.state === "pending_auth") {
    return (
      <div>
        <h2>Authorization Required</h2>
        <p>Please authorize the application to continue.</p>
        <a href={mcp.authUrl} target="_blank">
          Authorize Now
        </a>
      </div>
    );
  }

  return <div>Ready to use!</div>;
}
```

### React Hook Features

The `useMcp` hook accepts the following options and returns a reactive object:

```typescript
const mcp = useMcp({
  url: string,
  headers?: Record<string, string>,
  authProvider?: OAuthProvider,  // optional — auto-detected from server metadata if omitted
  // other MCPClient options…
});

// Returned fields
mcp.state: "discovering" | "authenticating" | "pending_auth" | "ready" | "failed";
mcp.error?: string;                         // set when state is "failed"
mcp.tools: Array<{ name: string; description: string }>;
mcp.callTool(name: string, params: object): Promise<any>;
mcp.retry(): void;                          // retry after failure
mcp.authUrl?: string;                       // set when state is "pending_auth"
```

The hook provides:

- **Automatic Connection** — Manages connect, disconnect, and reconnect.
- **State Management** — Reactive state updates for UI synchronization.
- **OAuth Support** — Complete OAuth flow with token management. When `state === "pending_auth"`, use `mcp.authUrl` to present the authorization link.
- **Tool Execution** — Call tools with automatic error handling via `mcp.callTool`.
- **Type Safety** — Full TypeScript support with type inference.
- **Resource Access** — Read resources and prompts from servers.

### React Cleanup

`useMcp` handles session cleanup automatically when components unmount. Do not call
`closeAllSessions` manually inside React components — the hook manages the full lifecycle.

```typescript
// ❌ BAD: Manual cleanup in React — the hook already handles this
useEffect(() => {
  return () => {
    client.closeAllSessions(); // Don't do this
  };
}, []);

// ✅ GOOD: Let the hook manage lifecycle
const mcp = useMcp({ url: "https://api.example.com/mcp" });
// Cleanup happens automatically on unmount
```

---

## CLI

The CLI entry point provides terminal-based access to MCP servers. Use it for
testing, debugging, scripting, and interactive exploration. No installation is required —
run commands directly with `npx mcp-use client`, or install globally with
`npm install -g mcp-use`.

### Quick Start

```bash
# Connect to an HTTP server
npx mcp-use client connect http://localhost:3000/mcp --name my-server

# Connect to a STDIO server
npx mcp-use client connect --stdio "npx -y @modelcontextprotocol/server-filesystem /tmp" --name fs

# List available tools
npx mcp-use client tools list

# Call a specific tool with JSON arguments
npx mcp-use client tools call read_file '{"path": "/tmp/test.txt"}'

# Start interactive mode
npx mcp-use client interactive
```

### Command Structure

The CLI uses scoped commands organized by resource type:

```bash
# Tools
npx mcp-use client tools list
npx mcp-use client tools call <name> [args]
npx mcp-use client tools describe <name>

# Resources
npx mcp-use client resources list
npx mcp-use client resources read <uri>

# Prompts
npx mcp-use client prompts list
npx mcp-use client prompts get <name> [args]

# Sessions
npx mcp-use client sessions list
npx mcp-use client sessions switch <name>

# Interactive mode
npx mcp-use client interactive
```

### Session Management

Sessions are automatically saved to `~/.mcp-use/cli-sessions.json` and persist
across terminal sessions:

```bash
# Connect to multiple servers
npx mcp-use client connect http://localhost:3000/mcp --name server1
npx mcp-use client connect http://localhost:4000/mcp --name server2

# List all sessions (shows active session)
npx mcp-use client sessions list

# Switch between sessions
npx mcp-use client sessions switch server2

# Use a specific session without switching
npx mcp-use client tools list --session server1

# Disconnect a named session
npx mcp-use client disconnect automation
```

### Interactive Mode

Start an interactive REPL session for exploratory use:

```bash
npx mcp-use client interactive

# In interactive mode:
# mcp> tools list
# mcp> tools call read_file
# Arguments (JSON): {"path": "/tmp/test.txt"}
# ✓ Success
# ...
# mcp> exit
```

Inside the REPL, type tool names and arguments to execute calls. The session persists
across commands, so server state is maintained between calls.

### Scripting with CLI

Use the `--json` flag for machine-readable output in automation scripts:

```bash
#!/bin/bash

# Connect to server
npx mcp-use client connect http://localhost:3000/mcp --name automation

# Get data as JSON and process with jq
RESULT=$(npx mcp-use client tools call get_data '{}' --json 2>/dev/null)
VALUE=$(echo "$RESULT" | jq -r '.content[0].text')

echo "Retrieved value: $VALUE"

# Cleanup
npx mcp-use client disconnect automation
```

### CLI Features

- **No Code Required** — Interact with MCP servers from the terminal.
- **Both Transports** — Supports HTTP and STDIO connections.
- **Session Persistence** — Sessions saved to `~/.mcp-use/cli-sessions.json` and restored automatically.
- **Interactive Mode** — REPL-style interface for exploration.
- **Scripting Support** — `--json` flag for machine-readable output in automation.
- **Multi-Session** — Manage multiple server connections simultaneously.
- **Testing and Debugging** — Immediate feedback, perfect for server development.

---

## Feature Support Matrix

Complete comparison of features across all four environments.

| Feature | Node.js | Browser | React | CLI |
|---|---|---|---|---|
| STDIO Connections | ✅ | ❌ | ❌ | ✅ |
| HTTP Connections | ✅ | ✅ | ✅ | ✅ |
| OAuth Authentication | ✅ | ✅ | ✅ | ✅ |
| File System Operations | ✅ | ❌ | ❌ | ✅ |
| Code Mode | ✅ | ❌ | ❌ | ❌ |
| Config File Loading | ✅ | ❌ | ❌ | ✅ |
| Automatic State Management | ❌ | ❌ | ✅ | ❌ |
| React Hooks | ❌ | ❌ | ✅ | ❌ |
| Interactive REPL | ❌ | ❌ | ❌ | ✅ |
| Session Persistence | ❌ | ❌ | ❌ | ✅ |

---

## Import Reference

| Environment | ESM (`import`) | CommonJS (`require`) |
|---|---|---|
| Node.js | `import { MCPClient } from "mcp-use"` | `const { MCPClient } = require("mcp-use")` |
| Browser | `import { MCPClient } from "mcp-use/browser"` | Not supported — ESM only |
| React | `import { useMcp } from "mcp-use/react"` | Not supported — ESM only |
| CLI | `npx mcp-use client` | — |

```typescript
// Node.js — full feature set (ESM)
import { MCPClient } from "mcp-use";

// Node.js — full feature set (CommonJS)
const { MCPClient } = require("mcp-use");

// Node.js — config file loading
import { MCPClient, loadConfigFile } from "mcp-use";

// Browser — no STDIO, no file system
import { MCPClient } from "mcp-use/browser";

// Browser — OAuth helpers
import { MCPClient, BrowserOAuthClientProvider, onMcpAuthorization } from "mcp-use/browser";

// React — hook-based API
import { useMcp } from "mcp-use/react";

// React — OAuth helper
import { onMcpAuthorization } from "mcp-use/react";
```

**CommonJS Support:** All Node.js features of `mcp-use` work with CommonJS (`require`).
Browser and React modules require ESM (`import`) — `require()` is not supported for those entry points.

> **Transport Migration (MCP Spec 2025-11-25):** The old SSE transport (separate POST and GET endpoints) is deprecated in favor of Streamable HTTP (unified `/mcp` endpoint). Existing `transportType: 'sse'` code continues to work for backward compatibility. For new code, use `transportType: 'http'` or `'auto'`.
>
> ```typescript
> // Old (deprecated, still works)
> const mcp = useMcp({ url: 'http://localhost:3000/sse', transportType: 'sse' });
>
> // New (recommended)
> const mcp = useMcp({ url: 'http://localhost:3000/mcp', transportType: 'http' });
> ```

---

## Security Considerations

### Credential Management

Never hardcode secrets in browser-facing code. Use OAuth providers or environment
variables on the server side.

```typescript
// ❌ BAD: Hardcoded credentials in browser code — exposed to end users
import { MCPClient } from "mcp-use/browser";

const client = new MCPClient({
  mcpServers: {
    api: {
      url: "https://api.example.com/mcp",
      headers: { Authorization: "Bearer SECRET_TOKEN" }, // Don't do this!
    },
  },
});
```

```typescript
// ✅ GOOD: Use OAuth for browser authentication — tokens managed securely
import { MCPClient, BrowserOAuthClientProvider } from "mcp-use/browser";

const authProvider = new BrowserOAuthClientProvider({
  clientId: "your-client-id",
  authorizationUrl: "https://api.example.com/oauth/authorize",
  tokenUrl: "https://api.example.com/oauth/token",
  callbackUrl: window.location.origin + "/oauth/callback",
});

const client = new MCPClient({
  mcpServers: {
    api: { url: "https://api.example.com/mcp", authProvider },
  },
});
```

```typescript
// ✅ GOOD: Use environment variables in Node.js
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    api: {
      url: "https://api.example.com/mcp",
      headers: { Authorization: `Bearer ${process.env.API_TOKEN}` },
    },
  },
});
```

### Transport Security

Always use HTTPS for production HTTP connections. Plain HTTP is acceptable only for
local development servers.

```typescript
// ❌ BAD: Plain HTTP in production — traffic is unencrypted
const client = new MCPClient({
  mcpServers: { api: { url: "http://api.example.com/mcp" } },
});

// ✅ GOOD: HTTPS in production
const client = new MCPClient({
  mcpServers: { api: { url: "https://api.example.com/mcp" } },
});

// ✅ GOOD: HTTP is fine for local development
const client = new MCPClient({
  mcpServers: { local: { url: "http://localhost:3000/mcp" } },
});
```

---

## Running Examples

Client examples live in the package under `examples/client/`. Run them from the
**package root** (`libraries/typescript/packages/mcp-use`):

- **Node**: `examples/client/node/` — full-features (tool calls, sampling, elicitation, notifications) and communication examples.
- **Browser**: `examples/client/browser/` — full-features and CommonJS (`browser/commonjs/`).

```bash
# From package root (libraries/typescript/packages/mcp-use)

# Node.js — full-featured example with STDIO and HTTP servers
pnpm run example:node:full

# Browser — web application connecting to an HTTP MCP server
pnpm run example:browser:full

# Client notifications — handling server-sent notifications
pnpm run example:client:notification

# Client sampling — LLM sampling through MCP
pnpm run example:client:sampling

# CommonJS — browser CommonJS build
pnpm run example:commonjs

# Conformance — starts conformance server, then node + browser full-features
pnpm run example:with-conformance
```

---

## Decision Matrix — When to Use Which Environment

Use this table to select the right environment for your use case.

| Scenario | Recommended | Why |
|---|---|---|
| Backend service calling MCP tools | Node.js | Full feature set, STDIO and HTTP, file system access |
| Automation script or batch job | Node.js | Programmatic control, process spawning, config files |
| Web application with MCP integration | Browser | Lightweight, HTTP-only, tree-shakes Node.js code |
| React SPA with real-time tool access | React | Hooks manage state, cleanup, and reconnection |
| Testing an MCP server during development | CLI | Interactive REPL, quick tool calls, no code needed |
| Debugging server responses | CLI | Immediate feedback, scriptable output, session persistence |
| CI/CD pipeline calling MCP tools | Node.js or CLI | Node.js for complex logic, CLI for simple calls |
| Browser extension | Browser | Runs in browser sandbox, HTTP connections only |
| Electron desktop app (main process) | Node.js | Main process has full Node.js API access |
| Electron desktop app (renderer process) | Browser | Renderer is a browser context |
| Quick one-off tool call from terminal | CLI | No code to write, immediate results |
| Server-side rendering (SSR) | Node.js | Server context, full feature access |

### Decision Flowchart

1. **Running in a browser?**
   - Yes → Is it a React app?
     - Yes → Use **React** (`mcp-use/react`)
     - No → Use **Browser** (`mcp-use/browser`)
   - No → Continue
2. **Running in Node.js?**
   - Yes → Need STDIO or file system?
     - Yes → Use **Node.js** (`mcp-use`)
     - No → Use **Node.js** (`mcp-use`) — still the best default for server-side
   - No → Continue
3. **Running from the terminal?**
   - Yes → Need scripting or interactive testing?
     - Yes → Use **CLI** (`npx mcp-use client`)
     - No → Use **Node.js** (`mcp-use`) for programmatic scripts

---

## Common Patterns Across Environments

### Error Handling

All environments follow the same error handling pattern. Wrap `callTool` in try/catch.

```typescript
// Works in Node.js, Browser, and React
try {
  const result = await session.callTool("tool_name", { param: "value" });
  if (result.isError) {
    const errText = result.content[0]?.type === "text" ? result.content[0].text : JSON.stringify(result.content);
    console.error("Tool error:", errText);
  } else {
    for (const item of result.content) {
      if (item.type === "text") console.log("Success:", item.text);
    }
  }
} catch (error) {
  // Transport-level error (network, timeout, abort)
  console.error("Tool call failed:", error.message);
}
```

### Tool Discovery

List available tools before calling them. The API is identical across Node.js, Browser,
and React (via the session object). Each `Tool` object has `name`, `description`, and `inputSchema` fields.

```typescript
const tools = await session.listTools();
for (const tool of tools) {
  console.log(`${tool.name}: ${tool.description}`);
  console.log("  Input schema:", JSON.stringify(tool.inputSchema));
}
```

> **Caching note:** `session.listTools()` always fetches fresh tool definitions from the server. The `session.tools` getter returns the in-memory cache without a network round-trip. Prefer `listTools()` when you need the most current list; use `session.tools` for read-heavy scenarios where the list rarely changes.

### Notifications

Register notification handlers to receive server-sent events. Supported in Node.js
and Browser via the client options.

```typescript
// Node.js / Browser
const client = new MCPClient(
  { mcpServers: { myServer: { url: "http://localhost:3000/mcp" } } },
  {
    onNotification: (notification) => {
      console.log("Notification:", notification.method, notification.params);
    },
  }
);
```

---

## Migration Between Environments

### Node.js to Browser

1. Change the import from `mcp-use` to `mcp-use/browser`.
2. Remove all STDIO server configurations — use HTTP only.
3. Remove file system operations and config file loading.
4. Replace `process.env` token access with OAuth or a backend token proxy.

### Browser to React

1. Change the import from `mcp-use/browser` to `mcp-use/react`.
2. Replace manual `MCPClient` instantiation with the `useMcp` hook.
3. Remove manual `createAllSessions` and `closeAllSessions` calls — hooks handle lifecycle.
4. Use `mcp.state` for conditional rendering instead of manual state tracking.
5. Call tools directly via `mcp.callTool(...)` instead of `session.callTool(...)`.

### Node.js to CLI

1. No code changes needed — the CLI is a separate entry point.
2. Translate `MCPClient` config into CLI `connect` commands.
3. Replace `callTool` calls with `npx mcp-use client tools call` commands.
