# Notifications and Logging

Complete reference for notifications and logging — real-time server events, roots management, and structured log messages.

---

## Notification Flow

Notifications are JSON-RPC messages that require no response. They flow in both directions:

- **Server → Client** — Event notifications: tool/resource/prompt list changes, custom events
- **Client → Server** — Environment notifications: roots changed

---

## Type Definitions

### Notification Interface

```typescript
interface Notification {
  method: string;                       // The notification method name
  params?: Record<string, any>;        // Optional parameters
}
```

### NotificationHandler Type

```typescript
import { type NotificationHandler, type Notification } from "mcp-use";

const handler: NotificationHandler = async (notification: Notification) => {
  console.log(notification.method, notification.params);
};
```

### Root Interface

```typescript
interface Root {
  uri: string;      // Must start with "file://"
  name?: string;    // Optional human-readable name
}
```

---

## Receiving Notifications (Server → Client)

### session.on("notification", handler)

Register a handler on a specific session:

```typescript
import { MCPClient } from "mcp-use";

const client = new MCPClient({
  mcpServers: { myServer: { url: "http://localhost:3000/mcp" } },
});
const session = await client.createSession("myServer");

session.on("notification", async (notification) => {
  console.log(`Received: ${notification.method}`, notification.params);
});
```

---

## Standard MCP Notifications

Three built-in notification types signal that server-side lists have changed:

| Method | Meaning | Client Action |
|---|---|---|
| `notifications/tools/list_changed` | Server's tool list changed | Re-fetch tools |
| `notifications/resources/list_changed` | Server's resource list changed | Re-fetch resources |
| `notifications/prompts/list_changed` | Server's prompt list changed | Re-fetch prompts |

### Tools List Changed

```typescript
session.on("notification", async (notification) => {
  if (notification.method === "notifications/tools/list_changed") {
    const tools = await session.listTools();
    console.log("Updated tools:", tools.map((t) => t.name));
  }
});
```

### Resources List Changed

```typescript
session.on("notification", async (notification) => {
  if (notification.method === "notifications/resources/list_changed") {
    const resources = await session.listAllResources();
    console.log("Updated resources:", resources.length);
  }
});
```

### Prompts List Changed

```typescript
session.on("notification", async (notification) => {
  if (notification.method === "notifications/prompts/list_changed") {
    const prompts = await session.listPrompts();
    console.log("Updated prompts:", prompts.map((p) => p.name));
  }
});
```

---

## Custom Notification Handling

Handle server-specific custom notifications with switch/case:

```typescript
session.on("notification", async (notification) => {
  switch (notification.method) {
    // Standard MCP notifications
    case "notifications/tools/list_changed":
      await refreshTools();
      break;
    case "notifications/resources/list_changed":
      await refreshResources(); // Use session.listAllResources() to refresh
      break;
    case "notifications/prompts/list_changed":
      await refreshPrompts();
      break;

    // Custom server notifications
    case "custom/heartbeat":
      console.log(`Heartbeat #${notification.params?.count}`);
      break;
    case "custom/user-joined":
      console.log(`User joined: ${notification.params?.username}`);
      break;
    case "custom/data-updated":
      console.log("Data updated:", notification.params);
      await reloadData(notification.params?.resource);
      break;
    case "custom/job-complete":
      console.log(`Job ${notification.params?.jobId} finished`);
      break;

    default:
      console.log(`Unknown notification: ${notification.method}`, notification.params);
  }
});
```

---

## Sending Notifications (Client → Server)

### session.setRoots()

Set or update the client's roots and automatically send `notifications/roots/list_changed` to the server:

```typescript
import { MCPClient, type Root } from "mcp-use";

const client = new MCPClient({
  mcpServers: { myServer: { url: "http://localhost:3000/mcp" } },
});
const session = await client.createSession("myServer");

// Set roots — sends notifications/roots/list_changed to server
await session.setRoots([
  { uri: "file:///home/user/project", name: "My Project" },
  { uri: "file:///home/user/data", name: "Data Directory" },
]);

// Update roots later
await session.setRoots([
  { uri: "file:///home/user/project", name: "My Project" },
  { uri: "file:///home/user/data", name: "Data Directory" },
  { uri: "file:///tmp/scratch", name: "Scratch" },
]);
```

### session.getRoots()

Retrieve the current roots:

```typescript
const roots = session.getRoots();
console.log("Current roots:", roots);
// => [{ uri: "file:///home/user/project", name: "My Project" }, ...]
```

---

## Initial Roots at Connection

Set roots during connector creation so they're available at initialization:

```typescript
import { HttpConnector, MCPSession } from "mcp-use";

const connector = new HttpConnector("http://localhost:3000/mcp", {
  roots: [
    { uri: "file:///workspace", name: "Workspace" },
    { uri: "file:///config", name: "Config" },
  ],
});

// Pass false to disable autoConnect (connect manually below)
const session = new MCPSession(connector, false);
await session.connect();
await session.initialize();

// Roots available to the server from the start
console.log("Initial roots:", session.getRoots());

// Update roots later
await session.setRoots([
  { uri: "file:///workspace", name: "Workspace" },
  { uri: "file:///config", name: "Config" },
  { uri: "file:///tmp/scratch", name: "Scratch" },
]);
```

---

## Root-Level onNotification Callback

Set a default notification handler for all servers in the second MCPClient argument:

```typescript
import { MCPClient, type NotificationHandler } from "mcp-use";

const onNotification: NotificationHandler = async (notification) => {
  console.log(`[Global] ${notification.method}`, notification.params);
};

const client = new MCPClient(
  {
    mcpServers: {
      serverA: { url: "http://localhost:3001/mcp" },
      serverB: { url: "http://localhost:3002/mcp" },
    },
  },
  { onNotification }
);
```

---

## Per-Server onNotification Callback

Override the global callback for individual servers:

```typescript
import { MCPClient, type NotificationHandler } from "mcp-use";

const serverAHandler: NotificationHandler = async (notification) => {
  console.log(`[Server A] ${notification.method}`);
};

const serverBHandler: NotificationHandler = async (notification) => {
  console.log(`[Server B] ${notification.method}`);
};

const client = new MCPClient(
  {
    mcpServers: {
      serverA: {
        url: "http://localhost:3001/mcp",
        onNotification: serverAHandler,
      },
      serverB: {
        url: "http://localhost:3002/mcp",
        onNotification: serverBHandler,
      },
      serverC: {
        url: "http://localhost:3003/mcp",
        // No callback — uses the global default
      },
    },
  },
  {
    onNotification: async (n) => console.log(`[Default] ${n.method}`),
  }
);
```

---

## Complete Example — Notification Dashboard

```typescript
import { MCPClient, type Notification, type NotificationHandler } from "mcp-use";

const notificationLog: Array<{ timestamp: Date; method: string; params?: any }> = [];

const onNotification: NotificationHandler = async (notification: Notification) => {
  notificationLog.push({
    timestamp: new Date(),
    method: notification.method,
    params: notification.params,
  });

  switch (notification.method) {
    case "notifications/tools/list_changed":
      console.log("🔧 Tools updated — re-fetching...");
      break;
    case "notifications/resources/list_changed":
      console.log("📁 Resources updated — re-fetching...");
      break;
    case "notifications/prompts/list_changed":
      console.log("💬 Prompts updated — re-fetching...");
      break;
    default:
      console.log(`📨 ${notification.method}:`, notification.params);
  }
};

const client = new MCPClient(
  { mcpServers: { myServer: { url: "http://localhost:3000/mcp" } } },
  { onNotification }
);

await client.createAllSessions();
const session = client.getSession("myServer");

// Set initial roots
await session.setRoots([
  { uri: "file:///home/user/project", name: "Project" },
]);

// Also register session-level handler for fine-grained control
session.on("notification", async (notification) => {
  if (notification.method === "notifications/tools/list_changed") {
    const tools = await session.listTools();
    console.log(`  Now have ${tools.length} tools`);
  }
});
```

---

## React Notification Management

The `useMcpServer` hook provides built-in notification state:

```typescript
import { useMcpServer } from "mcp-use/react";

function ServerNotifications({ serverId }: { serverId: string }) {
  const server = useMcpServer(serverId);

  if (server.state !== "ready") return <div>Not connected</div>;

  return (
    <div>
      <h3>Notifications ({server.unreadNotificationCount} unread)</h3>

      <button onClick={() => server.markAllNotificationsRead()}>
        Mark All Read
      </button>
      <button onClick={() => server.clearNotifications()}>
        Clear All
      </button>

      <ul>
        {server.notifications.map((notification) => (
          <li key={notification.id}>
            <strong>{notification.method}</strong>
            <pre>{JSON.stringify(notification.params, null, 2)}</pre>
            <button onClick={() => server.markNotificationRead(notification.id)}>
              Mark Read
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

### React Notification API

| Property / Method | Type | Description |
|---|---|---|
| `server.notifications` | `McpNotification[]` | All notifications for this server |
| `server.unreadNotificationCount` | `number` | Count of unread notifications |
| `server.markNotificationRead(id)` | `(id: string) => void` | Mark one notification read |
| `server.markAllNotificationsRead()` | `() => void` | Mark all notifications read |
| `server.clearNotifications()` | `() => void` | Remove all notifications |

---

## Requirements for Notifications

| Requirement | Why |
|---|---|
| **Stateful Connection** | Server must maintain sessions to route notifications |
| **Active Session** | Client must have an active, initialized session |
| **Streaming Transport** | Either SSE or Streamable HTTP transport required |

❌ **BAD** — STDIO connections don't support notifications:

```typescript
const client = new MCPClient({
  mcpServers: {
    myServer: {
      command: "npx", args: ["-y", "my-server"],
      // STDIO — notifications won't work
    },
  },
});
```

✅ **GOOD** — HTTP/SSE connections support notifications:

```typescript
const client = new MCPClient({
  mcpServers: {
    myServer: {
      url: "http://localhost:3000/mcp",
      // HTTP — notifications work
    },
  },
});
```

---

## Logging

Servers send structured log messages to the client over a dedicated logging channel, separate from the main notification stream. The client intercepts these via a `loggingCallback` passed to `MCPClient`.

### Logging Levels

| Level | Description | Use Case |
|---|---|---|
| `debug` | Detailed diagnostic information | Development troubleshooting |
| `info` | General informational messages | Normal operation events |
| `warning` | Potential issues that aren't errors | Deprecation notices, unusual conditions |
| `error` | Failure messages | Request failures, unexpected states |

### LoggingMessageNotificationParams

```typescript
import { types } from "mcp-use";

// types.LoggingMessageNotificationParams
{
  level: "debug" | "info" | "warning" | "error";
  message: string;
}
```

### loggingCallback Option

Pass a `loggingCallback` as the second argument to `MCPClient` to receive all log messages from the server:

```typescript
import { MCPClient, types } from "mcp-use";

async function handleLogs(
  logParams: types.LoggingMessageNotificationParams
): Promise<void> {
  console.log(`LOG [${logParams.level.toUpperCase()}]: ${logParams.message}`);
}

const client = new MCPClient(
  { mcpServers: { PrimitiveServer: { url: `${primitiveServer}/mcp` } } },
  { loggingCallback: handleLogs }
);

await client.createAllSessions();
const session = client.getSession("PrimitiveServer");

// Any tool that triggers server-side logging will invoke handleLogs
const result = await session.callTool("logging_tool", {});
console.assert(result.content[0].text === "Logging tool completed");

await client.closeAllSessions();
```

### Logging System Characteristics

- Uses a **dedicated logging channel** separate from the main notification stream.
- Provides **structured messages** with level-based categorization.
- Enables **server diagnostics** without interfering with core protocol messages.
- Allows **client-side handling** via a user-supplied `loggingCallback`.

---

## Available Imports

```typescript
// Core client and types namespace (includes LoggingMessageNotificationParams, etc.)
import { MCPClient, types } from "mcp-use";

// Notification types
import {
  type Notification,
  type NotificationHandler,
  type Root,
} from "mcp-use";

// Low-level connector and session
import { HttpConnector, MCPSession } from "mcp-use";

// React hooks
import { useMcp, McpClientProvider, useMcpClient, useMcpServer } from "mcp-use/react";
```

---

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Not re-fetching after list_changed | UI shows stale tools/resources/prompts | Call `listTools()` / `listAllResources()` / `listPrompts()` |
| Expecting notifications over STDIO | STDIO is stateless, no notification support | Use HTTP/SSE transport |
| Not setting roots | Server can't scope its operations | Call `setRoots()` after connection |
| Ignoring unknown notification methods | Misses custom server events | Add a default case in switch |
| Registering handlers after tool calls | Notifications fired before handler attached | Register handlers immediately after `createSession()` |

---

## Run the Example

A full Node.js notification example is available in the mcp-use repository:

```bash
# From packages/mcp-use — starts server then client automatically:
pnpm run example:notifications

# Or manually:
# 1. Start the notification server:
pnpm run example:server:notification

# 2. Run the client:
pnpm run example:client:notification
# (or: tsx examples/client/node/communication/notification-client.ts)
```

The example demonstrates bidirectional notifications: receiving `tools/list_changed`, `resources/list_changed`, `prompts/list_changed`, and custom notifications, as well as sending `roots/list_changed` from the client. See `examples/client/node/communication/notification-client.ts`.
