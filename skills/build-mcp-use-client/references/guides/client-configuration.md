# Client Configuration

Complete reference for MCPClient configuration — connection types, options, callbacks, and factory methods.

---

## Overview

`MCPClient` is the primary entry point for connecting to one or more MCP servers from your application. It manages transport selection, connection lifecycle, session persistence, capability negotiation, and callback routing. Every interaction with an MCP server begins by constructing an `MCPClient` instance with a configuration object that declares which servers to connect to and how.

This guide covers every aspect of client configuration: constructor signatures, config shape, connection types, callback wiring, factory methods, environment variable interpolation, session management, and automatic recovery. Follow the patterns here to build robust, production-grade MCP client applications.

---

## Constructor

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient(config?: string | Record<string, any>, options?: MCPClientOptions);
```

The constructor accepts two arguments:

| Argument | Type | Required | Description |
|---|---|---|---|
| `config` | `string \| Record<string, any>` | No | Path to a JSON config file (string), or an inline config object declaring servers and per-server overrides. Omit to start with an empty configuration and add servers later via `addServer()`. |
| `options` | `MCPClientOptions` | No | Global options that apply across all servers — default callbacks and root-level clientInfo. |

The constructor does **not** establish connections. Connections are created explicitly via `client.createAllSessions()` or `client.createSession(serverName)`.

---

## MCPClientConfig

`MCPClientConfig` is a dictionary keyed by server name. Each key maps to a server entry that describes how to reach that server.

```typescript
import { MCPClient } from "mcp-use";

const config: MCPClientConfig = {
  mcpServers: {
    "server_name": {
      // --- STDIO transport ---
      command: "command_to_run",
      args: ["arg1", "arg2"],
      env: { "ENV_VAR": "value" },
      clientInfo: { name: "my-app", version: "1.0.0" },

      // --- HTTP transport ---
      url: "http://localhost:3000",
      headers: { "Authorization": "Bearer ${AUTH_TOKEN}" },
      clientInfo: { name: "my-app", version: "1.0.0" },

      // --- Per-server callbacks ---
      onSampling: mySamplingHandler,
      onElicitation: myElicitationHandler,
      onNotification: myNotificationHandler,
    },
  },
};

const client = new MCPClient(config);
```

### Key rules

- Server names must be unique within the `mcpServers` object. They are used as identifiers when routing tool calls and accessing individual connections.
- A server entry must declare **either** STDIO fields (`command`) **or** HTTP fields (`url`), never both.
- Per-server callbacks are optional and override any global callbacks set in `MCPClientOptions`.

---

## Connection Types

MCP supports two transport mechanisms. Choose based on your deployment scenario.

| Connection Type | Best For | Use Cases |
|---|---|---|
| STDIO | Local development | Testing locally, file system access, CLI tools, language servers |
| HTTP/SSE | Production | Remote servers, load balancing, auth, cloud deployments, multi-tenant |

### STDIO Transport

STDIO spawns a child process and communicates over standard input/output streams. Use it when the MCP server runs as a local executable.

#### STDIO Config Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `command` | `string` | Yes | – | Executable command to run (e.g., `"npx"`, `"python"`, `"node"`). |
| `args` | `string[]` | No | `[]` | Command-line arguments passed to the executable. |
| `env` | `Record<string, string>` | No | `{}` | Environment variables injected into the child process. |
| `clientInfo` | `ClientInfo` | No | – | Client identity sent during the MCP `initialize` handshake. |
| `onSampling` | `OnSamplingCallback` | No | – | Per-server sampling callback override. |
| `onElicitation` | `OnElicitationCallback` | No | – | Per-server elicitation callback override. |
| `onNotification` | `OnNotificationCallback` | No | – | Per-server notification handler override. |

#### STDIO Example

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/documents"],
      env: {
        NODE_ENV: "development",
      },
    },
  },
});
```

#### When to use STDIO

- The MCP server is a CLI tool installed locally.
- You need direct file system access without network overhead.
- You are prototyping or running integration tests.
- The server does not need to be shared across multiple clients.

### HTTP/SSE Transport

HTTP transport connects to a remote MCP server over HTTP with Server-Sent Events (SSE) for server-to-client streaming. Use it for production deployments where the server runs as a standalone service.

#### HTTP Config Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `url` | `string` | Yes | – | Full URL to the MCP server endpoint (e.g., `"https://api.example.com/mcp"`). |
| `headers` | `Record<string, string>` | No | `{}` | Custom HTTP headers sent with every request (e.g., auth tokens). |
| `transport` | `'http' \| 'sse'` | No | `'http'` | Transport variant. `'http'` uses Streamable HTTP (recommended). `'sse'` uses the legacy SSE transport (deprecated). |
| `preferSse` | `boolean` | No | `false` | When `true`, forces SSE fallback even if the server supports Streamable HTTP. |
| `disableSseFallback` | `boolean` | No | `false` | When `true`, disables automatic SSE fallback on servers that do not support Streamable HTTP. |
| `authToken` | `string` | No | – | Bearer token sent as the `Authorization` header. Convenience alternative to setting `headers.Authorization`. |
| `authProvider` | `unknown` | No | – | OAuth provider instance (e.g., `BrowserOAuthClientProvider`) for servers requiring OAuth 2.0 authorization. |
| `fetch` | `typeof fetch` | No | – | Custom `fetch` implementation. Use for environments with non-standard fetch or for testing. |
| `clientInfo` | `ClientInfo` | No | – | Client identity sent during the MCP `initialize` handshake. |
| `onSampling` | `OnSamplingCallback` | No | – | Per-server sampling callback override. |
| `onElicitation` | `OnElicitationCallback` | No | – | Per-server elicitation callback override. |
| `onNotification` | `OnNotificationCallback` | No | – | Per-server notification handler override. |

#### HTTP Example

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    production: {
      url: "https://mcp.example.com/v1",
      headers: {
        "Authorization": "Bearer ${API_TOKEN}",
        "X-Request-ID": "client-abc-123",
      },
      clientInfo: {
        name: "my-production-app",
        version: "2.1.0",
      },
    },
  },
});
```

#### When to use HTTP/SSE

- The MCP server is deployed as a remote service.
- You need authentication, load balancing, or TLS.
- Multiple clients connect to the same server.
- The server runs in a container, serverless function, or cloud VM.

### Transport Migration

> **Transport Migration (MCP Spec 2025-11-25):** The old SSE transport (separate POST and GET endpoints) is deprecated in favor of Streamable HTTP (unified `/mcp` endpoint). Existing `transportType: 'sse'` code continues to work for backward compatibility. For new code, use `transportType: 'http'` or `'auto'`.

```typescript
// Old (deprecated, still works)
const mcp = useMcp({
  url: "http://localhost:3000/sse",
  transportType: "sse",
});

// New (recommended)
const mcp = useMcp({
  url: "http://localhost:3000/mcp",
  transportType: "http", // or 'auto'
});
```

---

## MCPClientOptions

Global options passed as the second argument to the constructor. They apply as defaults across all server connections. Per-server values in the server entry take precedence over these defaults.

```typescript
import { acceptWithDefaults, MCPClient } from "mcp-use";
import type { CreateMessageRequest, CreateMessageResult, ElicitRequestFormParams, ElicitRequestURLParams, ElicitResult, Notification } from "@modelcontextprotocol/sdk/types.js";

interface MCPClientOptions {
  clientInfo?: ClientInfo;
  codeMode?: boolean | CodeModeConfig;
  onSampling?: (params: CreateMessageRequest["params"]) => Promise<CreateMessageResult>;
  onElicitation?: (params: ElicitRequestFormParams | ElicitRequestURLParams) => Promise<ElicitResult>;
  onNotification?: (notification: Notification) => void | Promise<void>;
  /** @deprecated Use onSampling instead */
  samplingCallback?: (params: CreateMessageRequest["params"]) => Promise<CreateMessageResult>;
  /** @deprecated Use onElicitation instead */
  elicitationCallback?: (params: ElicitRequestFormParams | ElicitRequestURLParams) => Promise<ElicitResult>;
}

const client = new MCPClient(
  {
    mcpServers: {
      myServer: { url: "http://localhost:3000/mcp" },
    },
  },
  {
    clientInfo: { name: "my-app", version: "1.0.0" },
    onElicitation: async (params) => acceptWithDefaults(params),
    onNotification: (n) => console.log(n.method, n.params),
    // onSampling: optional; see Sampling docs
  }
);
```

### Options Reference

| Option | Type | Default | Description |
|---|---|---|---|
| `clientInfo` | `ClientInfo` | `undefined` | Fallback client identity used for any server entry that does not specify its own `clientInfo`. |
| `codeMode` | `boolean \| CodeModeConfig` | `false` | Enable code execution mode (Node.js only). `true` uses the VM executor. Pass a `CodeModeConfig` object to choose `"vm"` or `"e2b"` executor with options. |
| `onSampling` | `(params) => Promise<CreateMessageResult>` | `undefined` | Default sampling callback. Invoked when a server requests an LLM completion. |
| `onElicitation` | `(params) => Promise<ElicitResult>` | `undefined` | Default elicitation callback. Invoked when a server requests user input. |
| `onNotification` | `(notification) => void \| Promise<void>` | `undefined` | Default notification handler. Receives server-initiated notifications. |
| `samplingCallback` | `(params) => Promise<CreateMessageResult>` | `undefined` | **Deprecated.** Use `onSampling` instead. |
| `elicitationCallback` | `(params) => Promise<ElicitResult>` | `undefined` | **Deprecated.** Use `onElicitation` instead. |

---

## ClientInfo Interface (per-server)

`ClientInfo` identifies your application to the MCP server during the `initialize` handshake. Set it on a server entry so operators can identify your application.

```typescript
interface ClientInfo {
  name: string;
  title?: string;
  version: string;
  description?: string;
  icons?: Array<{
    src: string;
    mimeType?: string;
    sizes?: string[];
  }>;
  websiteUrl?: string;
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | Machine-readable identifier (e.g., `"my-agent"`). |
| `title` | `string` | No | Human-readable display name. |
| `version` | `string` | Yes | Semantic version string (e.g., `"1.0.0"`). |
| `description` | `string` | No | Short description of the client application. |
| `icons` | `Array<Icon>` | No | Application icons for display in server UIs. |
| `websiteUrl` | `string` | No | URL to the client application's website or docs. |

### Default ClientInfo

When `clientInfo` is not specified on a server entry and no root-level `clientInfo` is set in `MCPClientOptions`, mcp-use automatically uses:

| Field | Default value |
|---|---|
| `name` | `"mcp-use"` |
| `title` | `"mcp-use"` |
| `version` | Current mcp-use package version |
| `description` | `"mcp-use is a complete TypeScript framework for building and using MCP"` |
| `icons` | `[{ "src": "https://mcp-use.com/logo.png" }]` |
| `websiteUrl` | `"https://mcp-use.com"` |

---

## Callback Configuration

MCP defines three callback types that servers can invoke on the client. Configure them globally via `MCPClientOptions` or per-server inside the server entry.

### Callback Precedence

Callback precedence follows a simple rule: **per-server overrides global**.

1. If the server entry declares a callback → that callback is used for that server.
2. If the server entry does not declare a callback → the global callback from `MCPClientOptions` is used.
3. If neither is set → the capability is not advertised to the server.

```typescript
import { MCPClient } from "mcp-use";

const claudeSampling = async (request) => {
  // Use Claude for code-related sampling
  return { model: "claude-sonnet-4-20250514", content: { type: "text", text: "..." } };
};

const fallbackSampling = async (request) => {
  // Use a cheaper model for utility sampling
  return { model: "gpt-4o-mini", content: { type: "text", text: "..." } };
};

const client = new MCPClient(
  {
    mcpServers: {
      codeServer: {
        url: "https://code.example.com/mcp",
        onSampling: claudeSampling, // ← Per-server: uses Claude
      },
      utilityServer: {
        url: "https://util.example.com/mcp",
        // No onSampling → falls back to global
      },
    },
  },
  {
    onSampling: fallbackSampling, // ← Global fallback
  }
);
// codeServer → claudeSampling
// utilityServer → fallbackSampling
```

### Callback Types

| Callback | Type | Signature | Purpose |
|---|---|---|---|
| `onSampling` | `SamplingCallback` | `(params: SamplingParams) => Promise<SamplingResult>` | Server requests an LLM completion from the client. |
| `onElicitation` | `ElicitationCallback` | `(params: ElicitationParams) => Promise<ElicitationResult>` | Server requests interactive user input. |
| `onNotification` | `NotificationCallback` | `(notification: NotificationMessage) => void` | Server sends a one-way notification (no response expected). |

---

## Factory Methods

`MCPClient` provides multiple ways to instantiate a client.

### Constructor (standard)

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    myServer: { url: "https://mcp.example.com" },
  },
});
```

### Config File via Constructor (simplest)

Pass the file path string directly to the constructor. The client reads and parses the file synchronously during construction:

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient("path/to/config.json");
await client.createAllSessions();
```

### loadConfigFile

Alternatively, use the `loadConfigFile` named export to load and parse a JSON config file synchronously, then pass the result to the constructor. This is useful when you need to inspect or modify the config before constructing the client.

```typescript
import { MCPClient, loadConfigFile } from "mcp-use";

const config = loadConfigFile("path/to/config.json");
const client = new MCPClient(config);
```

### MCPClient.fromConfigFile

Use the convenience factory when you want to construct directly from a config path without manually holding the parsed object:

```typescript
import { MCPClient } from "mcp-use";

const client = MCPClient.fromConfigFile("path/to/config.json");
await client.createAllSessions();
```

The JSON file must follow the `MCPClientConfig` schema:

```json
{
  "mcpServers": {
    "github": {
      "command": "mcp-server-github",
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "slack": {
      "url": "https://slack-mcp.example.com",
      "headers": {
        "Authorization": "Bearer ${SLACK_TOKEN}"
      }
    }
  }
}
```

### useMcp (React hook)

A React hook that manages a single MCP server connection with automatic lifecycle handling. Import from `mcp-use/react`. Note: `useMcp` takes a flat options object (`url`, `headers`, `transportType`, etc.), not a nested `mcpServers` config.

```typescript
import { useMcp } from "mcp-use/react";

function MyComponent() {
  const mcp = useMcp({
    url: "https://mcp.example.com",
    headers: { Authorization: "Bearer YOUR_TOKEN" },
  });

  if (mcp.state !== "ready") return <div>Connecting...</div>;
  return <div>{mcp.tools.length} tools available</div>;
}
```

Use `useMcp` instead of `new MCPClient(...)` in React components. The hook manages connect, disconnect, and reconnection automatically on mount/unmount.

---

## Session Management

After constructing the client, use the session methods to establish and tear down connections.

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    "my-server": {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-everything"],
    },
  },
});

// Create sessions for all configured servers
await client.createAllSessions();

// Get a session for a specific server by name
const session = client.getSession("my-server");

// List available tools
const tools = await session.listTools();

// Call a tool
const result = await session.callTool("tool_name", { param: "value" });

// Cleanup — close all sessions
await client.closeAllSessions();
```

### Session Methods

| Method | Returns | Description |
|---|---|---|
| `createSession(serverName, autoInitialize?)` | `Promise<MCPSession>` | Creates and initializes a session for a single named server. |
| `createAllSessions(autoInitialize?)` | `Promise<Record<string, MCPSession>>` | Establishes connections to all configured servers. |
| `getSession(serverName)` | `MCPSession \| null` | Returns the active session for the named server, or `null` if not found. |
| `requireSession(serverName)` | `MCPSession` | Returns the active session for the named server. Throws if not found. |
| `getAllActiveSessions()` | `Record<string, MCPSession>` | Returns all active sessions as a name-to-session map. |
| `closeSession(serverName)` | `Promise<void>` | Closes a single named session. |
| `closeAllSessions()` | `Promise<void>` | Gracefully closes all open connections. |
| `addServer(name, config)` | `void` | Adds or updates a server configuration dynamically. |
| `removeServer(name)` | `void` | Removes a server configuration and its active session. |
| `getServerNames()` | `string[]` | Returns all server names defined in the configuration. |
| `getServerConfig(name)` | `Record<string, any>` | Returns the configuration object for a specific server. |
| `activeSessions` | `string[]` | Public property listing names of servers with active sessions. |

---

## Multiple Server Configuration

A single `MCPClient` can manage connections to many servers simultaneously. Declare each server under a unique key in `mcpServers`.

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    airbnb: {
      command: "npx",
      args: ["-y", "@openbnb/mcp-server-airbnb"],
    },
    playwright: {
      command: "npx",
      args: ["@playwright/mcp@latest"],
      env: { DISPLAY: ":1" },
    },
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/"],
    },
    github: {
      command: "mcp-server-github",
      env: { GITHUB_TOKEN: "${GITHUB_TOKEN}" },
    },
    remoteApi: {
      url: "https://api.example.com/mcp",
      headers: { "Authorization": "Bearer ${API_KEY}" },
    },
  },
});
```

Mix STDIO and HTTP servers freely. The client selects the correct transport based on whether the server entry contains `command` (STDIO) or `url` (HTTP).

---

## Environment Variable Support

Both JSON config files and inline config objects support `${VAR_NAME}` syntax for environment variable interpolation. This prevents secrets from being hardcoded in source or config files.

### In JSON config files

```json
{
  "mcpServers": {
    "github": {
      "command": "mcp-server-github",
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "production": {
      "url": "https://mcp.example.com",
      "headers": {
        "Authorization": "Bearer ${AUTH_TOKEN}"
      }
    }
  }
}
```

### In TypeScript config objects

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    github: {
      command: "mcp-server-github",
      env: {
        GITHUB_TOKEN: "${GITHUB_TOKEN}",
      },
    },
  },
});
```

### How interpolation works

1. The client scans all string values in the config for the `${VAR_NAME}` pattern.
2. Each match is replaced with the value of the corresponding environment variable from `process.env`.
3. If an environment variable is not set, the placeholder remains as-is — no error is thrown at config time. The missing value surfaces as a connection or auth error at runtime.

---

## Automatic 404 Recovery (HTTP/SSE)

HTTP connections include built-in session recovery. When a server restarts or a session expires, the client recovers transparently without application code changes.

### Recovery flow

1. Client makes a request with its current session ID.
2. Server returns HTTP `404` (session not found — server restarted or session expired).
3. Client detects the `404` response.
4. Client clears the stale session ID from its internal state.
5. Client sends a new `initialize` request to establish a fresh session.
6. Client retries the original request using the new session ID.
7. The entire flow is transparent to application code — no errors propagate.

You can observe recovery in logs:

```
[StreamableHttp] Session not found (404), re-initializing per MCP spec...
[StreamableHttp] Re-initialization successful, retrying request
```

### What triggers recovery

| Trigger | Action |
|---|---|
| Server restart | Session IDs are invalidated. Next request gets 404. Client re-initializes. |
| Session timeout | Long-idle sessions expire server-side. Client re-initializes on next use. |
| Load balancer failover | Request hits a different server instance. Client re-initializes. |

This behavior is automatic and requires no configuration.

---

## Session Persistence (HTTP/SSE)

HTTP connections maintain persistent session state between requests.

| Aspect | Behavior |
|---|---|
| Session ID | Automatically managed. Sent as a header on every request. |
| Client capabilities | Preserved across requests within the same session. |
| Server capabilities | Cached locally after the `initialize` handshake. |
| Subscriptions | Maintained for resource update notifications. |
| Tool list | Cached after initial `listTools` call. Refreshed on `tools/list_changed` notification. |

STDIO connections are **stateless** — they do not use sessions. Each STDIO connection is a long-lived child process; state is maintained implicitly by the process lifetime.

---

## Browser and React Imports

When running in a browser or React environment, import from the appropriate subpath.

### Browser

```typescript
import { MCPClient } from "mcp-use/browser";

const client = new MCPClient({
  mcpServers: {
    api: {
      url: "https://mcp.example.com",
      headers: { "Authorization": "Bearer token" },
    },
  },
});
```

> **Note:** STDIO transport is not available in the browser. Use HTTP/SSE exclusively.

### React

```typescript
import { MCPClient } from "mcp-use/react";

const client = new MCPClient({
  mcpServers: {
    api: {
      url: "https://mcp.example.com",
    },
  },
});
```

---

## Best Practices

| # | Practice | Why |
|---|---|---|
| 1 | Use environment variables for secrets | Prevents accidental credential leaks in version control. |
| 2 | Set descriptive `clientInfo` on every client | Helps server operators identify your application in logs and dashboards. |
| 3 | Use per-server callbacks when servers need different behavior | Avoids complex conditional logic inside a single global callback. |
| 4 | Prefer HTTP/SSE for production deployments | Enables auth, load balancing, TLS, and session recovery. |
| 5 | Use `loadConfigFile` for shared team configs | Keeps server definitions in one place, editable without code changes. |
| 6 | Limit the number of STDIO servers in production | Each STDIO connection spawns a child process. Too many increase memory and CPU usage. |
| 7 | Handle `onNotification` to react to server-side changes | Resource updates and tool list changes arrive as notifications. Ignoring them means stale state. |
| 8 | Test with STDIO locally, deploy with HTTP | Get fast local iteration with STDIO, then switch to HTTP for staging and production. |

---

## Common Mistakes

### ❌ BAD: Hardcoding secrets in config

```typescript
import { MCPClient } from "mcp-use";

// NEVER do this — secrets end up in source control
const client = new MCPClient({
  mcpServers: {
    github: {
      command: "mcp-server-github",
      env: {
        GITHUB_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
      },
    },
  },
});
```

### ✅ GOOD: Using environment variables for secrets

```typescript
import { MCPClient } from "mcp-use";

// Secrets are read from the environment at runtime
const client = new MCPClient({
  mcpServers: {
    github: {
      command: "mcp-server-github",
      env: {
        GITHUB_TOKEN: "${GITHUB_TOKEN}",
      },
    },
  },
});
```

---

### ❌ BAD: Not setting clientInfo

```typescript
import { MCPClient } from "mcp-use";

// Server operators see "mcp-use" in their logs — no way to identify your app
const client = new MCPClient({
  mcpServers: {
    api: { url: "https://mcp.example.com" },
  },
});
```

### ✅ GOOD: Setting descriptive clientInfo

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    api: {
      url: "https://mcp.example.com",
      clientInfo: {
        name: "order-processing-agent",
        version: "3.2.1",
        description: "Handles order fulfillment via MCP tools",
        websiteUrl: "https://internal.example.com/docs/order-agent",
      },
    },
  },
});
```

---

### ❌ BAD: Using the same callback for all servers when they need different behavior

```typescript
import { MCPClient } from "mcp-use";

// One callback tries to handle every server — fragile and hard to maintain
const genericSampling = async (request) => {
  if (request.context?.serverName === "codeServer") {
    return { model: "claude-sonnet-4-20250514", content: { type: "text", text: "..." } };
  }
  return { model: "gpt-4o-mini", content: { type: "text", text: "..." } };
};

const client = new MCPClient(
  {
    mcpServers: {
      codeServer: { url: "https://code.example.com/mcp" },
      utilityServer: { url: "https://util.example.com/mcp" },
    },
  },
  { onSampling: genericSampling }
);
```

### ✅ GOOD: Per-server callback overrides

```typescript
import { MCPClient } from "mcp-use";

const codeSampling = async (request) => {
  return { model: "claude-sonnet-4-20250514", content: { type: "text", text: "..." } };
};

const utilitySampling = async (request) => {
  return { model: "gpt-4o-mini", content: { type: "text", text: "..." } };
};

const client = new MCPClient({
  mcpServers: {
    codeServer: {
      url: "https://code.example.com/mcp",
      onSampling: codeSampling,
    },
    utilityServer: {
      url: "https://util.example.com/mcp",
      onSampling: utilitySampling,
    },
  },
});
```

---

### ❌ BAD: Mixing STDIO and HTTP fields in a single server entry

```typescript
import { MCPClient } from "mcp-use";

// Do NOT combine command and url — the client cannot determine which transport to use
const client = new MCPClient({
  mcpServers: {
    confused: {
      command: "npx",
      args: ["-y", "my-server"],
      url: "https://mcp.example.com",
    },
  },
});
```

### ✅ GOOD: One transport per server entry

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: {
    localDev: {
      command: "npx",
      args: ["-y", "my-server"],
    },
    remoteProduction: {
      url: "https://mcp.example.com",
    },
  },
});
```

---

## Quick Reference

```typescript
import { MCPClient, loadConfigFile, acceptWithDefaults } from "mcp-use";

// Minimal STDIO
const stdio = new MCPClient({
  mcpServers: { myTool: { command: "my-mcp-server" } },
});

// Minimal HTTP
const http = new MCPClient({
  mcpServers: { myApi: { url: "https://mcp.example.com" } },
});

// From file path string (simplest)
const fromPath = new MCPClient("./mcp-config.json");

// From file via loadConfigFile (synchronous)
const config = loadConfigFile("./mcp-config.json");
const fromFile = new MCPClient(config);

// Full-featured
const full = new MCPClient(
  {
    mcpServers: {
      code: {
        url: "https://code.example.com/mcp",
        headers: { "Authorization": "Bearer ${CODE_TOKEN}" },
        onSampling: codeSamplingHandler,
        clientInfo: { name: "code-agent", version: "1.0.0" },
      },
      fs: {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", "/data"],
        env: { HOME: "/data" },
      },
    },
  },
  {
    clientInfo: { name: "my-app", version: "1.0.0" },
    onSampling: defaultSamplingHandler,
    onElicitation: async (params) => acceptWithDefaults(params),
    onNotification: (n) => console.log("Notification:", n),
  }
);

// Session lifecycle
await full.createAllSessions();
const session = full.requireSession("code"); // throws if not found
// or: const session = full.getSession("code"); // returns null if not found
const tools = await session.listTools();
await full.closeAllSessions();
```
