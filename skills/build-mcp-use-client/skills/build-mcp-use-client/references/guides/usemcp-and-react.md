# useMcp and React Integration

Complete guide to building React applications with MCP client hooks and providers.

Source: https://manufact.com/docs/typescript/client/usemcp

---

## Table of Contents

1. [Installation](#installation)
2. [Architecture Overview](#architecture-overview)
3. [Quick Start with Provider](#quick-start-with-provider)
4. [Automatic Proxy Fallback](#automatic-proxy-fallback)
5. [Connection States](#connection-states)
6. [McpClientProvider — Configuration](#mcpclientprovider--configuration)
7. [useMcpClient — Multi-Server Context Hook](#usemcpclient--multi-server-context-hook)
8. [useMcpServer — Per-Server Hook](#usemcpserver--per-server-hook)
9. [Server Methods Reference](#server-methods-reference)
10. [Authentication](#authentication)
11. [Calling Tools](#calling-tools)
12. [Reading Resources](#reading-resources)
13. [Managing Multiple Servers](#managing-multiple-servers)
14. [Persistence with StorageProvider](#persistence-with-storageprovider)
15. [Notification Management](#notification-management)
16. [Sampling and Elicitation](#sampling-and-elicitation)
17. [Error Handling](#error-handling)
18. [Reconnection and Health Checks](#reconnection-and-health-checks)
19. [Standalone useMcp Hook](#standalone-usemcp-hook)
20. [Common Mistakes](#common-mistakes)

---

## Installation

Install the `mcp-use` package. This single package provides Node.js, browser, and React entry points.

```bash
npm install mcp-use
```

Required peer dependencies for React:

```bash
npm install react react-dom
```

### Import Paths

```typescript
// React hooks and providers
import {
  McpClientProvider,
  useMcpClient,
  useMcpServer,
  useMcp,
  LocalStorageProvider,
} from "mcp-use/react";

// OAuth callback helper (also available from mcp-use/react)
import { onMcpAuthorization } from "mcp-use/auth";

// Elicitation helpers
import { acceptWithDefaults } from "mcp-use";
```

---

## Architecture Overview

The `mcp-use/react` package provides two usage patterns:

| Pattern | API | Use Case |
|---|---|---|
| Provider-based (recommended) | `McpClientProvider` + `useMcpClient` + `useMcpServer` | Multi-server apps, production use |
| Standalone hook | `useMcp(options)` | Simple single-server applications |

**Recommended approach:** Use `McpClientProvider` for managing multiple MCP server connections. It provides automatic proxy fallback, notification management, persistence support, and a superior developer experience compared to standalone `useMcp()`.

---

## Quick Start with Provider

```typescript
import { McpClientProvider, useMcpClient, useMcpServer } from "mcp-use/react";
import { useEffect } from "react";

// 1. Wrap your app with the provider
function App() {
  return (
    <McpClientProvider
      defaultAutoProxyFallback={true} // Enable automatic proxy fallback
    >
      <MyComponent />
    </McpClientProvider>
  );
}

// 2. Add servers dynamically
function MyComponent() {
  const { addServer, servers } = useMcpClient();

  useEffect(() => {
    addServer("linear", {
      url: "https://mcp.linear.app/mcp",
      name: "Linear",
    });

    addServer("my-server", {
      url: "http://localhost:3000/mcp",
      name: "My Server",
      headers: { Authorization: "Bearer YOUR_API_KEY" },
    });
  }, [addServer]);

  return (
    <div>
      <h2>Connected Servers ({servers.length})</h2>
      {servers.map((server) => (
        <ServerCard key={server.id} server={server} />
      ))}
    </div>
  );
}

// 3. Use individual servers
function ServerCard({ server }) {
  if (server.state !== "ready") {
    return (
      <div>
        {server.name}: {server.state}...
      </div>
    );
  }

  return (
    <div>
      <h3>{server.serverInfo?.name || server.name}</h3>
      <p>Tools: {server.tools.length}</p>
      <button onClick={() => server.callTool("my-tool", {})}>Call Tool</button>
    </div>
  );
}
```

---

## Automatic Proxy Fallback

The provider includes intelligent automatic proxy fallback for FastMCP and CORS-restricted servers.

### Default behavior

```typescript
<McpClientProvider
  defaultAutoProxyFallback={true} // Enabled by default
  // Uses https://inspector.mcp-use.com/inspector/api/proxy by default
>
  <MyApp />
</McpClientProvider>
```

**How it works:**

1. Tries direct connection first
2. Detects FastMCP or CORS errors automatically
3. Retries with proxy seamlessly
4. Connection established through proxy

### Custom proxy

```typescript
<McpClientProvider
  defaultAutoProxyFallback={{
    enabled: true,
    proxyAddress: "http://localhost:3005/inspector/api/proxy",
  }}
>
  <MyApp />
</McpClientProvider>
```

### Per-server override

```typescript
// Disable automatic fallback for a specific server
addServer("my-server", {
  url: "http://localhost:3000/mcp",
  autoProxyFallback: false, // Override provider default
});

// Use a different proxy for one server
addServer("special-server", {
  url: "https://api.example.com/mcp",
  proxyConfig: {
    proxyAddress: "https://my-custom-proxy.com/api/proxy",
  },
});
```

---

## Connection States

Each server manages its own connection state via `server.state`.

| State | Meaning |
|---|---|
| `"discovering"` | Connecting and resolving server capabilities |
| `"authenticating"` | OAuth flow in progress (popup open) |
| `"pending_auth"` | Server requires authentication; waiting for user to trigger it |
| `"ready"` | Fully connected and capabilities loaded |
| `"failed"` | Connection or authentication failed |

```typescript
function ServerStatus({ serverId }: { serverId: string }) {
  const server = useMcpServer(serverId);

  if (!server) return null;

  switch (server.state) {
    case "discovering":
      return <div>Connecting...</div>;

    case "authenticating":
      return <div>Authenticating... Check for popup window</div>;

    case "pending_auth":
      return (
        <button onClick={server.authenticate}>Click to Authenticate</button>
      );

    case "ready":
      return <div>Connected ({server.tools.length} tools available)</div>;

    case "failed":
      return (
        <div>
          Connection failed: {server.error}
          <button onClick={server.retry}>Retry</button>
        </div>
      );
  }
}
```

---

## McpClientProvider — Configuration

### Props

```typescript
interface McpClientProviderProps {
  // Default proxy configuration for all servers (can be overridden per-server)
  defaultProxyConfig?: {
    proxyAddress?: string;
    headers?: Record<string, string>;
  };

  // Enable automatic proxy fallback (default: true)
  // When a server fails with FastMCP or CORS errors, automatically retries with proxy
  defaultAutoProxyFallback?:
    | boolean
    | {
        enabled?: boolean;
        proxyAddress?: string; // Default: https://inspector.mcp-use.com/inspector/api/proxy
      };

  // Initial servers (auto-connected on mount)
  mcpServers?: Record<string, McpServerOptions>;

  // Persistence
  storageProvider?: StorageProvider;

  // Debugging
  enableRpcLogging?: boolean;

  // Callbacks
  onServerAdded?: (id: string, server: McpServer) => void;
  onServerRemoved?: (id: string) => void;
  onServerStateChange?: (id: string, state: string) => void;
  onSamplingRequest?: (request, serverId, serverName, approve, reject) => void;
  onElicitationRequest?: (request, serverId, serverName, approve, reject) => void;
}
```

### Server Options

```typescript
interface McpServerOptions {
  // Connection
  url?: string;                              // MCP server URL
  name?: string;                             // Display name for the server
  enabled?: boolean;                         // Enable/disable connection (default: true)
  headers?: Record<string, string>;          // Auth headers
  transportType?: "auto" | "http" | "sse";  // Transport preference (default: 'auto')
  timeout?: number;                          // Connection timeout (ms, default: 30000)

  // Proxy (overrides provider defaults)
  proxyConfig?: {
    proxyAddress?: string;
    headers?: Record<string, string>;
  };
  autoProxyFallback?: boolean | { enabled?: boolean; proxyAddress?: string };

  // OAuth
  preventAutoAuth?: boolean;     // Prevent automatic OAuth popup (default: true)
  useRedirectFlow?: boolean;     // Use redirect instead of popup (default: false)
  callbackUrl?: string;          // OAuth callback URL
  authProvider?: OAuthClientProvider; // Optional external OAuth provider
  clientInfo?: {
    name: string;
    version: string;
    description?: string;
    icons?: Array<{ src: string }>;
    websiteUrl?: string;
  };

  // Reconnection & Health Checks
  autoRetry?: boolean | number;   // Auto-retry on initial failure
  autoReconnect?: boolean | number | {       // Auto-reconnect on drop (default: 3000ms)
    enabled?: boolean;                       // Enable/disable (default: true)
    initialDelay?: number;                   // Delay before reconnect in ms (default: 3000)
    healthCheckInterval?: number | false;    // Health check polling in ms, or false to disable (default: 10000)
    healthCheckTimeout?: number;             // Time before connection considered dead in ms (default: 30000)
  };
  reconnectionOptions?: ReconnectionOptions; // SDK-level transport reconnection

  // Advanced
  wrapTransport?: (transport: any, serverId: string) => any;
  onNotification?: (notification: Notification) => void;
  onSampling?: (params) => Promise<CreateMessageResult>;
  onElicitation?: (params) => Promise<ElicitResult>;
}
```

---

## useMcpClient — Multi-Server Context Hook

`useMcpClient()` returns the multi-server client context from the nearest `McpClientProvider`.

### Signature

```typescript
function useMcpClient(): UseMcpClientReturn;
```

### Return Value

```typescript
const {
  servers,       // McpServer[] — array of all registered server objects
  addServer,     // (id: string, options: McpServerOptions) => void
  removeServer,  // (id: string) => void
  updateServer,  // (id: string, options: Partial<McpServerOptions>) => Promise<void>
  getServer,     // (id: string) => McpServer | undefined
  storageLoaded, // boolean — true when persistence has been loaded
} = useMcpClient();
```

### Example

```typescript
import { useMcpClient } from "mcp-use/react";
import { useEffect } from "react";

function ServerManager() {
  const { servers, addServer, removeServer } = useMcpClient();

  useEffect(() => {
    addServer("linear", {
      url: "https://mcp.linear.app/mcp",
      name: "Linear",
    });
  }, [addServer]);

  return (
    <div>
      <h2>Connected Servers ({servers.length})</h2>
      {servers.map((server) => (
        <div key={server.id}>
          <h4>{server.serverInfo?.name || server.name}</h4>
          <p>State: {server.state}</p>
          <p>Tools: {server.tools.length}</p>
          <button onClick={() => removeServer(server.id)}>Remove</button>
        </div>
      ))}
    </div>
  );
}
```

### Updating a server

`updateServer` disconnects and reconnects the server with new options:

```typescript
// Update authorization header (disconnects and reconnects)
await updateServer("my-server", {
  headers: { Authorization: "Bearer new-key" },
});
```

---

## useMcpServer — Per-Server Hook

`useMcpServer(id)` returns the state and methods for a single named server.

### Signature

```typescript
function useMcpServer(id: string): McpServer | undefined;
```

### Server Object Properties

| Property | Type | Description |
|---|---|---|
| `id` | `string` | Server identifier passed to `addServer`. |
| `name` | `string` | Display name. |
| `state` | `"discovering" \| "authenticating" \| "pending_auth" \| "ready" \| "failed"` | Current connection state. |
| `tools` | `Tool[]` | Discovered tools. |
| `resources` | `Resource[]` | Discovered resources. |
| `resourceTemplates` | `ResourceTemplate[]` | Discovered resource templates. |
| `prompts` | `Prompt[]` | Discovered prompts. |
| `serverInfo` | `{ name: string; version: string; ... } \| undefined` | Server metadata (available when ready). |
| `error` | `string \| undefined` | Error message if state is `"failed"`. |
| `notifications` | `McpNotification[]` | All server notifications received. |
| `unreadNotificationCount` | `number` | Number of unread notifications. |
| `pendingSamplingRequests` | `PendingSamplingRequest[]` | Pending sampling requests from the server. |

### Server Object Methods

| Method | Signature | Description |
|---|---|---|
| `callTool` | `(name: string, args: Record<string, unknown>, options?: CallToolOptions) => Promise<CallToolResult>` | Call a tool. |
| `readResource` | `(uri: string) => Promise<ReadResourceResult>` | Read a resource. |
| `listResources` | `() => Promise<ListResourcesResult>` | List resources. |
| `listPrompts` | `() => Promise<ListPromptsResult>` | List prompts. |
| `getPrompt` | `(name: string, args?: Record<string, string>) => Promise<GetPromptResult>` | Get a prompt. |
| `complete` | `(params: CompleteParams) => Promise<CompleteResult>` | Request autocomplete suggestions. |
| `refreshResourceTemplates` | `() => Promise<void>` | Force-refresh resource templates. |
| `retry` | `() => void` | Retry connection after failure. |
| `disconnect` | `() => void` | Disconnect from the server. |
| `authenticate` | `() => void` | Trigger OAuth authentication. |
| `clearStorage` | `() => void` | Clear persisted auth/session data. |
| `approveSampling` | `(requestId: string, result: CreateMessageResult) => void` | Approve a pending sampling request. |
| `rejectSampling` | `(requestId: string) => void` | Reject a pending sampling request. |
| `markNotificationRead` | `(notificationId: string) => void` | Mark a notification as read. |
| `markAllNotificationsRead` | `() => void` | Mark all notifications as read. |
| `clearNotifications` | `() => void` | Clear all notifications. |

### Example: Per-Server Panel

```typescript
import { useMcpServer } from "mcp-use/react";

function ServerPanel({ serverId }: { serverId: string }) {
  const server = useMcpServer(serverId);

  if (!server) return null;

  return (
    <div>
      <h3>{server.serverInfo?.name || server.name}</h3>
      <p>State: {server.state}</p>
      <p>Tools: {server.tools.length}</p>
      <p>Resources: {server.resources.length}</p>
      <p>Notifications: {server.unreadNotificationCount} unread</p>

      {server.state === "failed" && (
        <div>
          <p>Error: {server.error}</p>
          <button onClick={server.retry}>Retry</button>
        </div>
      )}

      {server.state === "pending_auth" && (
        <button onClick={server.authenticate}>Sign In</button>
      )}

      {server.state === "ready" && (
        <div>
          <button onClick={server.disconnect}>Disconnect</button>
          <ul>
            {server.tools.map((tool) => (
              <li key={tool.name}>
                <strong>{tool.name}</strong>: {tool.description}
                <button onClick={() => server.callTool(tool.name, {})}>Run</button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
```

---

## Server Methods Reference

### callTool(name, args, options?)

```typescript
// Basic call
const result = await server.callTool("send-email", {
  to: "[email protected]",
  subject: "Hello",
  body: "Test message",
});

// With timeout options
const result = await server.callTool(
  "long-task",
  { data: "..." },
  {
    timeout: 300000,              // 5 minutes
    resetTimeoutOnProgress: true, // Reset timer on each progress event
  }
);
```

### readResource(uri), listResources(), listPrompts(), getPrompt()

```typescript
// List resources
const { resources } = await server.listResources();

// Read a specific resource
const resource = await server.readResource("file:///path/to/file");
const text = resource.contents[0].text;

// List prompts
const { prompts } = await server.listPrompts();

// Get a prompt with arguments
const prompt = await server.getPrompt("code-review", { language: "typescript" });
```

### complete(params)

Request autocomplete suggestions for prompt arguments or resource template URIs:

```typescript
// Complete a prompt argument
const result = await server.complete({
  ref: { type: "ref/prompt", name: "code-review" },
  argument: { name: "language", value: "py" },
});
console.log("Suggestions:", result.completion.values);
// Output: ['python', 'pytorch', ...]

// Complete a resource template URI variable
const result = await server.complete({
  ref: { type: "ref/resource", uri: "file:///{path}" },
  argument: { name: "path", value: "/home" },
});
```

### refreshResourceTemplates()

Force a refresh of the resource templates list:

```typescript
await server.refreshResourceTemplates();
console.log("Updated templates:", server.resourceTemplates);
```

The `resourceTemplates` state is automatically populated on connection and updated when notifications are received. Use this method to force a refresh.

---

## Authentication

### Bearer Token Authentication

Pass auth headers directly in server options:

```typescript
addServer("authenticated-server", {
  url: "http://localhost:3000/mcp",
  name: "My Server",
  headers: {
    Authorization: "Bearer YOUR_API_KEY",
  },
});
```

### OAuth Authentication

**Manual OAuth Trigger (Default)**

By default, `preventAutoAuth: true` — you must explicitly trigger OAuth when a server reaches `"pending_auth"` state:

```typescript
function ServerCard({ serverId }: { serverId: string }) {
  const server = useMcpServer(serverId);

  if (server?.state === "pending_auth") {
    return (
      <button onClick={server.authenticate}>Sign in to {server.name}</button>
    );
  }

  if (server?.state === "authenticating") {
    return <div>Authenticating...</div>;
  }

  // ... rest of component
}
```

**Automatic OAuth Popup**

To automatically trigger the OAuth popup when authentication is required, set `preventAutoAuth: false`:

```typescript
addServer("linear", {
  url: "https://mcp.linear.app/mcp",
  name: "Linear",
  preventAutoAuth: false, // Auto-trigger OAuth popup
});
```

**Redirect Flow** (for mobile or popup-blocked environments)

```typescript
addServer("linear", {
  url: "https://mcp.linear.app/mcp",
  name: "Linear",
  useRedirectFlow: true, // Use redirect instead of popup
});
```

### OAuth Callback Page

Create an OAuth callback route to handle OAuth redirects. `onMcpAuthorization()` handles all success and error cases internally — for popup flow it posts a message to the opener; for redirect flow it handles navigation automatically.

```typescript
// app/oauth/callback/page.tsx (Next.js App Router)
// or pages/oauth/callback.tsx (Next.js Pages Router)
import { onMcpAuthorization } from "mcp-use/auth";
// Also available from: import { onMcpAuthorization } from 'mcp-use/react'
import { useEffect } from "react";

export default function OAuthCallback() {
  useEffect(() => {
    // Handles everything: success/error UI, posts message to opener (popup),
    // redirects (redirect flow). No custom error handling needed.
    onMcpAuthorization();
  }, []);

  return <div>Processing authentication...</div>;
}
```

---

## Calling Tools

```typescript
function ToolExecutor({ serverId }: { serverId: string }) {
  const server = useMcpServer(serverId);
  const [result, setResult] = useState(null);

  if (!server || server.state !== "ready") {
    return <div>Server not ready...</div>;
  }

  const handleSendEmail = async () => {
    try {
      const result = await server.callTool("send-email", {
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
      <h3>{server.serverInfo?.name} Tools</h3>
      <button onClick={handleSendEmail}>Send Email</button>
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}

      <h4>Available Tools:</h4>
      <ul>
        {server.tools.map((tool) => (
          <li key={tool.name}>
            {tool.name}: {tool.description}
          </li>
        ))}
      </ul>
    </div>
  );
}
```

---

## Reading Resources

```typescript
function ResourceViewer({ serverId, uri }: { serverId: string; uri: string }) {
  const server = useMcpServer(serverId);
  const [content, setContent] = useState("");

  useEffect(() => {
    if (server?.state === "ready") {
      server.readResource(uri).then((resource) => {
        setContent(resource.contents[0].text || "");
      });
    }
  }, [server?.state, uri]);

  if (!server) return null;

  return (
    <div>
      <h3>
        {server.name} - Resource: {uri}
      </h3>
      <pre>{content}</pre>
    </div>
  );
}
```

---

## Managing Multiple Servers

```typescript
function ServerManager() {
  const { servers, addServer, removeServer } = useMcpClient();

  const handleAddLinear = () => {
    addServer("linear", {
      url: "https://mcp.linear.app/mcp",
      name: "Linear",
    });
  };

  const handleAddLocal = () => {
    addServer("local", {
      url: "http://localhost:3000/mcp",
      name: "Local Server",
      headers: { Authorization: "Bearer key" },
    });
  };

  return (
    <div>
      <button onClick={handleAddLinear}>Add Linear</button>
      <button onClick={handleAddLocal}>Add Local Server</button>

      <h3>Connected Servers ({servers.length})</h3>
      {servers.map((server) => (
        <div key={server.id}>
          <h4>{server.serverInfo?.name || server.name}</h4>
          <p>State: {server.state}</p>
          <p>Tools: {server.tools.length}</p>
          <p>Resources: {server.resources.length}</p>
          <p>Notifications: {server.unreadNotificationCount} unread</p>
          <button onClick={() => removeServer(server.id)}>Remove</button>
        </div>
      ))}
    </div>
  );
}
```

---

## Persistence with StorageProvider

Use `LocalStorageProvider` to automatically save and restore server configurations across page reloads. Servers added via `addServer()` are automatically saved and restored.

```typescript
import { McpClientProvider, LocalStorageProvider } from "mcp-use/react";

function App() {
  return (
    <McpClientProvider
      storageProvider={new LocalStorageProvider("my-app-servers")}
      defaultAutoProxyFallback={true}
    >
      <MyApp />
    </McpClientProvider>
  );
}
```

### Custom Storage Provider

Implement the `StorageProvider` interface for custom backends:

```typescript
class CustomStorageProvider implements StorageProvider {
  async getServers(): Promise<Record<string, McpServerOptions>> {
    // Load from your backend, IndexedDB, etc.
    return {};
  }

  async setServers(servers: Record<string, McpServerOptions>): Promise<void> {
    // Save to your backend, IndexedDB, etc.
  }
}

// Use with McpClientProvider
function Root() {
  return (
    <McpClientProvider storageProvider={new CustomStorageProvider()}>
      <App />
    </McpClientProvider>
  );
}
```

---

## Notification Management

Each server maintains its own notification history with read/unread tracking.

```typescript
function NotificationPanel({ serverId }: { serverId: string }) {
  const server = useMcpServer(serverId);

  if (!server) return null;

  return (
    <div>
      <h3>Notifications ({server.unreadNotificationCount} unread)</h3>
      <button onClick={server.markAllNotificationsRead}>Mark All Read</button>
      <button onClick={server.clearNotifications}>Clear All</button>

      <ul>
        {server.notifications.map((notification) => (
          <li
            key={notification.id}
            style={{ fontWeight: notification.read ? "normal" : "bold" }}
            onClick={() => server.markNotificationRead(notification.id)}
          >
            {notification.method}
            <pre>{JSON.stringify(notification.params, null, 2)}</pre>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

Per-server notification callback:

```typescript
addServer("my-server", {
  url: "http://localhost:3000/mcp",
  onNotification: (notification) => {
    console.log("Received notification:", notification.method);
  },
});
```

Provider-level notification handling via `onServerStateChange`:

```typescript
<McpClientProvider
  onServerStateChange={(id, state) => {
    console.log(`Server ${id} state changed to: ${state}`);
  }}
>
  <MyApp />
</McpClientProvider>
```

---

## Sampling and Elicitation

Handle interactive server requests (AI sampling, form elicitation).

### UI-driven sampling (via server object)

Access `pendingSamplingRequests` on the server object and respond with `approveSampling` or `rejectSampling`:

```typescript
function SamplingHandler() {
  const { servers } = useMcpClient();

  return (
    <div>
      {servers.map((server) => (
        <div key={server.id}>
          {server.pendingSamplingRequests.map((request) => (
            <div key={request.id}>
              <h4>{server.name} needs AI assistance</h4>
              <pre>{JSON.stringify(request.request.params, null, 2)}</pre>
              <button
                onClick={() =>
                  server.approveSampling(request.id, {
                    content: [{ type: "text", text: "AI response here" }],
                    model: "gpt-4",
                    role: "assistant",
                  })
                }
              >
                Approve
              </button>
              <button onClick={() => server.rejectSampling(request.id)}>
                Reject
              </button>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
```

### Provider-level callbacks

Handle sampling and elicitation at the provider level with `onSamplingRequest` and `onElicitationRequest`:

```typescript
<McpClientProvider
  onSamplingRequest={(request, serverId, serverName, approve, reject) => {
    // Call approve(result) or reject() based on your logic
    approve({
      content: [{ type: "text", text: "AI response" }],
      model: "gpt-4",
      role: "assistant",
    });
  }}
  onElicitationRequest={(request, serverId, serverName, approve, reject) => {
    // Call approve(data) or reject() based on user input
    approve({ someField: "user input" });
  }}
>
  <MyApp />
</McpClientProvider>
```

### Per-server callbacks

```typescript
addServer("my-server", {
  url: "http://localhost:3000/mcp",
  onSampling: async (params) => {
    // Return a CreateMessageResult
    return {
      role: "assistant",
      content: [{ type: "text", text: "Response" }],
      model: "gpt-4",
    };
  },
  onElicitation: async (params) => {
    // Return an ElicitResult
    return { action: "accept", content: { field: "value" } };
  },
});
```

### Elicitation helpers

Use `acceptWithDefaults` from `mcp-use` to automatically accept elicitation requests using schema defaults:

```typescript
import { acceptWithDefaults } from "mcp-use";

addServer("my-server", {
  url: "http://localhost:3000/mcp",
  onElicitation: async (params) => acceptWithDefaults(params),
});
```

---

## Error Handling

```typescript
function ServerMonitor() {
  const { servers } = useMcpClient();

  return (
    <div>
      {servers.map((server) => (
        <div key={server.id}>
          <h3>{server.name}</h3>

          {server.state === "failed" && (
            <div>
              <p>Error: {server.error}</p>
              <button onClick={server.retry}>Retry Connection</button>

              {/* Common error guidance */}
              {server.error?.includes("401") && (
                <p>Add Authorization header in server configuration</p>
              )}
              {server.error?.includes("CORS") && (
                <p>CORS error - proxy fallback will retry automatically</p>
              )}
              {server.error?.includes("FastMCP") && (
                <p>FastMCP error - proxy fallback will retry automatically</p>
              )}
            </div>
          )}

          {server.state === "ready" && (
            <div>Connected - {server.tools.length} tools available</div>
          )}
        </div>
      ))}
    </div>
  );
}
```

Provider-level lifecycle callbacks:

```typescript
<McpClientProvider
  defaultAutoProxyFallback={true}
  onServerStateChange={(id, state) => {
    console.log(`Server ${id} state changed to: ${state}`);
  }}
  onServerAdded={(id, server) => {
    console.log(`Server ${id} added:`, server);
  }}
  onServerRemoved={(id) => {
    console.log(`Server ${id} removed`);
  }}
>
  <MyApp />
</McpClientProvider>
```

---

## Reconnection and Health Checks

When `autoReconnect` is enabled (the default), the hook monitors connection health by sending periodic HEAD requests to the server URL.

### How it works

1. After a successful connection, a health check timer starts.
2. Every **10 seconds** (default), a HEAD request is sent to the server URL.
3. If no successful response is received for **30 seconds** (default), the connection is considered broken.
4. The server transitions to `"discovering"` state and reconnects after a configurable delay.

### autoReconnect configuration

`autoReconnect` accepts three forms:

```typescript
// Boolean: enable with defaults (3s reconnect delay, 10s health check interval)
addServer("my-server", { url: "...", autoReconnect: true });

// Number: custom reconnect delay in ms
addServer("my-server", { url: "...", autoReconnect: 5000 });

// Object: full control over reconnection and health checks
addServer("my-server", {
  url: "...",
  autoReconnect: {
    enabled: true,
    initialDelay: 5000,          // Wait 5s before reconnecting
    healthCheckInterval: 30000,  // Poll every 30s instead of 10s
    healthCheckTimeout: 60000,   // Wait 60s before declaring dead
  },
});
```

Same options apply to the standalone `useMcp` hook:

```typescript
useMcp({
  url: "...",
  autoReconnect: {
    enabled: true,
    initialDelay: 5000,
    healthCheckInterval: 30000,
    healthCheckTimeout: 60000,
  },
});
```

### Disabling health checks

Disable health check polling while still reconnecting on transport-level failures:

```typescript
useMcp({
  url: "...",
  autoReconnect: {
    healthCheckInterval: false, // No HEAD request polling
  },
});
```

### SDK-level reconnection options

`reconnectionOptions` controls the underlying `StreamableHTTPClientTransport` retry behavior, separate from the health check system:

```typescript
import type { ReconnectionOptions } from "mcp-use/react";

useMcp({
  url: "...",
  reconnectionOptions: {
    initialReconnectionDelay: 2000,    // Start with 2s delay (default: 1000)
    maxReconnectionDelay: 60000,       // Cap at 60s (default: 30000)
    reconnectionDelayGrowFactor: 2,    // Double each retry (default: 1.5)
    maxRetries: 5,                     // Retry up to 5 times (default: 2)
  },
});
```

> `autoReconnect` controls **application-level** health monitoring (HEAD request polling and reconnect triggers). `reconnectionOptions` controls **transport-level** retry behavior within the MCP SDK when the SSE/HTTP stream drops. Both can be used together for robust connection handling.

---

## Standalone useMcp Hook

For simple single-server applications, use `useMcp` directly without the provider.

> **Note:** For most applications, prefer `McpClientProvider` for better multi-server support, automatic proxy fallback, and notification management.

### Basic usage

```typescript
import { useMcp } from "mcp-use/react";

function SimpleApp() {
  const mcp = useMcp({
    url: "http://localhost:3000/mcp",
    headers: { Authorization: "Bearer key" },
    autoProxyFallback: true, // Enable automatic proxy fallback
    enabled: true,           // Default: true. Set false to pause connection
  });

  if (mcp.state !== "ready") return <div>Connecting... ({mcp.state})</div>;

  return (
    <div>
      <h2>Tools ({mcp.tools.length})</h2>
      {mcp.tools.map((tool) => (
        <div key={tool.name}>{tool.name}</div>
      ))}
    </div>
  );
}
```

### With elicitation

```typescript
import { useMcp } from "mcp-use/react";
import { acceptWithDefaults } from "mcp-use";

function ElicitationExample() {
  const mcp = useMcp({
    url: "http://localhost:3000/mcp",
    onElicitation: async (params) => acceptWithDefaults(params),
  });

  if (mcp.state !== "ready") return <div>{mcp.state}</div>;

  return <div>{mcp.tools.length} tools available</div>;
}
```

### useMcp options

The standalone `useMcp` hook accepts the following options:

| Option | Type | Default | Description |
|---|---|---|---|
| `url` | `string` | — | MCP server endpoint URL |
| `enabled` | `boolean` | `true` | Enable/disable the connection. When `false`, no connection is attempted |
| `headers` | `Record<string, string>` | — | HTTP headers (e.g., `Authorization: Bearer …`) |
| `transportType` | `"auto" \| "http" \| "sse"` | `"auto"` | Transport preference. `"sse"` is deprecated; use `"http"` or `"auto"` |
| `autoProxyFallback` | `boolean \| { enabled?: boolean; proxyAddress?: string }` | `false` | Enable automatic proxy fallback on CORS/FastMCP errors |
| `proxyConfig` | `{ proxyAddress?: string; headers?: Record<string, string> }` | — | Custom proxy configuration |
| `autoReconnect` | `boolean \| number \| object` | `3000` | Reconnection config. Default enables health checks at 10s intervals |
| `reconnectionOptions` | `ReconnectionOptions` | — | SDK-level transport retry configuration |
| `preventAutoAuth` | `boolean` | `true` | When `true`, OAuth requires explicit `authenticate()` call |
| `useRedirectFlow` | `boolean` | `false` | Use full-page redirect OAuth instead of popup |
| `callbackUrl` | `string` | `/oauth/callback` on current origin | OAuth redirect URI |
| `authProvider` | `OAuthClientProvider` | — | External OAuth provider for headless/testing environments |
| `onNotification` | `(notification: Notification) => void` | — | Notification callback |
| `onSampling` | `(params) => Promise<CreateMessageResult>` | — | Sampling request callback |
| `onElicitation` | `(params) => Promise<ElicitResult>` | — | Elicitation request callback |
| `timeout` | `number` | `30000` | Connection timeout in ms |
| `sseReadTimeout` | `number` | `300000` | SSE read timeout in ms to prevent idle drops |
| `logLevel` | `"silent" \| "error" \| "warn" \| "info" \| "verbose" \| "debug" \| "silly"` | — | Console log level. `"silent"` suppresses all console output |
| `wrapTransport` | `(transport: any, serverId: string) => any` | — | Wrap the transport (e.g., for custom logging) |
| `clientInfo` | `{ name: string; version: string; ... }` | — | Client metadata sent in the MCP initialize request |
| `fetch` | `typeof globalThis.fetch` | — | Custom fetch function for all MCP HTTP requests |

### useMcp return value

The hook returns a `UseMcpResult` object with the following properties and methods:

| Property / Method | Type | Description |
|---|---|---|
| `state` | `"discovering" \| "pending_auth" \| "authenticating" \| "ready" \| "failed"` | Current connection state |
| `tools` | `Tool[]` | Discovered tools |
| `resources` | `Resource[]` | Discovered resources |
| `resourceTemplates` | `ResourceTemplate[]` | Discovered resource templates |
| `prompts` | `Prompt[]` | Discovered prompts |
| `serverInfo` | `object \| undefined` | Server metadata (name, version, title, icons, websiteUrl) |
| `error` | `string \| undefined` | Error message when state is `"failed"` |
| `authUrl` | `string \| undefined` | Auth URL if popup was blocked — show this link to the user |
| `authTokens` | `object \| undefined` | OAuth tokens when OAuth was used and state is `"ready"` |
| `log` | `Array<{ level, message, timestamp }>` | Internal log messages for debugging |
| `callTool` | `(name, args?, options?) => Promise<any>` | Call a tool |
| `readResource` | `(uri: string) => Promise<...>` | Read a resource |
| `listResources` | `() => Promise<void>` | Refresh resources list |
| `listPrompts` | `() => Promise<void>` | Refresh prompts list |
| `complete` | `(params) => Promise<CompleteResult>` | Request autocomplete suggestions |
| `refreshTools` | `() => Promise<void>` | Force-refresh tools list |
| `refreshResources` | `() => Promise<void>` | Force-refresh resources list |
| `refreshResourceTemplates` | `() => Promise<void>` | Force-refresh resource templates list |
| `refreshPrompts` | `() => Promise<void>` | Force-refresh prompts list |
| `refreshAll` | `() => Promise<void>` | Force-refresh all lists |
| `retry` | `() => void` | Retry connection after failure |
| `disconnect` | `() => void` | Disconnect from the server |
| `authenticate` | `() => void` | Trigger OAuth authentication |
| `clearStorage` | `() => void` | Clear persisted auth/session data |
| `ensureIconLoaded` | `() => Promise<string \| null>` | Ensure server icon is loaded and available in `serverInfo` |
| `client` | `BrowserMCPClient \| null` | The underlying `BrowserMCPClient` instance (use with `MCPAgent`) |

### callTool options

The `callTool` method accepts an optional options object with additional controls:

```typescript
const result = await mcp.callTool(
  "analyze-sentiment",
  { text: "Hello" },
  {
    timeout: 300000,              // 5 minutes per call
    maxTotalTimeout: 600000,      // 10 minutes absolute cap
    resetTimeoutOnProgress: true, // Reset timer on each progress event
    signal: abortController.signal, // AbortSignal to cancel
  }
)
```

---

## Common Mistakes

### Mistake 1: Using useMcpServer Outside McpClientProvider

`useMcpServer` requires `McpClientProvider` as an ancestor.

❌ BAD:
```typescript
import { useMcpServer } from "mcp-use/react";

function BrokenComponent() {
  // This will throw — no McpClientProvider in the tree
  const server = useMcpServer("myServer");
  return <div>{server?.tools.length}</div>;
}

function Root() {
  return <BrokenComponent />;
}
```

✅ GOOD:
```typescript
import { McpClientProvider, useMcpServer } from "mcp-use/react";

function WorkingComponent() {
  const server = useMcpServer("myServer");
  return <div>{server?.tools.length ?? 0}</div>;
}

function Root() {
  return (
    <McpClientProvider
      mcpServers={{ myServer: { url: "http://localhost:3000/mcp" } }}
    >
      <WorkingComponent />
    </McpClientProvider>
  );
}
```

### Mistake 2: Checking state === "ready" Only

Always handle `"failed"`, `"pending_auth"`, and `"authenticating"` states to avoid blank screens and missed auth prompts.

### Mistake 3: Nesting McpClientProvider Instances

❌ BAD — Do not nest providers:
```typescript
<McpClientProvider mcpServers={{ server1: { url: "..." } }}>
  <McpClientProvider mcpServers={{ server2: { url: "..." } }}>
    <App />
  </McpClientProvider>
</McpClientProvider>
```

✅ GOOD — Pass all servers to a single provider:
```typescript
<McpClientProvider
  mcpServers={{
    server1: { url: "http://localhost:3001/mcp" },
    server2: { url: "http://localhost:3002/mcp" },
  }}
>
  <App />
</McpClientProvider>
```

### Mistake 4: Missing OAuth Callback Route

When using OAuth, always create a callback route that calls `onMcpAuthorization()`. Without it, the OAuth flow never completes.

### Mistake 5: Wrong reconnectionOptions field names

The SDK-level `reconnectionOptions` uses:
- `initialReconnectionDelay` (not `baseDelay`)
- `maxReconnectionDelay` (not `maxDelay`)
- `reconnectionDelayGrowFactor` (not `backoffFactor`)
- `maxRetries`

### Mistake 6: Using proxy string URL instead of autoProxyFallback

❌ BAD:
```typescript
useMcp({ url: "...", proxy: "http://localhost:8080" });
```

✅ GOOD:
```typescript
useMcp({
  url: "...",
  autoProxyFallback: true,
  // Or with custom proxy address:
  proxyConfig: { proxyAddress: "http://localhost:8080/inspector/api/proxy" },
});
```

### Mistake 7: Checking mcp.status instead of mcp.state

The hook and server objects expose `state`, not `status`.

❌ BAD:
```typescript
if (mcp.status !== "ready") return <div>Loading...</div>;
```

✅ GOOD:
```typescript
if (mcp.state !== "ready") return <div>Loading...</div>;
```
