# Notifications and Subscriptions

Definitive guide to sending notifications, tracking progress, managing resource subscriptions, and receiving client events with mcp-use v1.21.4.

> **Stateful only:** Notifications require persistent sessions (SSE or StreamableHTTP). They are not supported in stateless edge environments.

---

## Sending Notifications

### Broadcasting to All Clients

Send a notification to every connected client with `server.sendNotification()`:

```typescript
import { MCPServer } from "mcp-use/server";

const server = new MCPServer({ name: "my-server", version: "1.0.0" });

await server.sendNotification("custom/status-update", {
  status: "ready",
  timestamp: Date.now(),
});
```

### Sending to the Current Client

Inside a tool handler, use `ctx.sendNotification()` to message only the calling client:

```typescript
import { MCPServer, text } from "mcp-use/server";

server.tool(
  {
    name: "start-job",
    description: "Kick off a background job and notify the caller.",
  },
  async (params, ctx) => {
    await ctx.sendNotification("custom/job-started", {
      jobId: "j_42",
      startedAt: Date.now(),
    });
    return text("Job started.");
  }
);
```

### Sending to a Specific Session

Target a single client by session ID with `server.sendNotificationToSession()`. Returns `true` on success, `false` if the session is not found or expired:

```typescript
const sessions = server.getActiveSessions();

if (sessions.length > 0) {
  const success = await server.sendNotificationToSession(
    sessions[0],
    "custom/welcome",
    { message: "Hello, client!" }
  );

  if (!success) {
    console.log("Session not found or expired");
  }
}
```

You can also send cross-session notifications from within a tool handler via `ctx.sendNotificationToSession()`:

```typescript
server.tool(
  { name: "notify-peer", description: "Send a message to another session." },
  async (params, ctx) => {
    const sent = await ctx.sendNotificationToSession(
      params.targetSessionId,
      "custom/message",
      { text: "Hello from another session" }
    );
    return text(sent ? "Sent." : "Target session not found.");
  }
);
```

---

## Built-in Notification Types

MCP defines standard notification methods that clients handle automatically.

### Tools / Resources / Prompts List Changed

Call these after dynamically adding or removing capabilities so clients re-fetch the lists:

```typescript
// Tools changed
await server.sendToolsListChanged();

// Resources changed
await server.sendResourcesListChanged();

// Prompts changed
await server.sendPromptsListChanged();

// Equivalent long-form calls
await server.sendNotification("notifications/tools/list_changed");
await server.sendNotification("notifications/resources/list_changed");
await server.sendNotification("notifications/prompts/list_changed");
```

### Resource Updated

Notify subscribers that a specific resource has new content:

```typescript
await server.notifyResourceUpdated("config://app-settings");
```

> Only clients that have subscribed to the URI receive this notification. See [Resource Subscriptions](#resource-subscriptions) below.

---

## Progress Notifications

Progress notifications keep clients informed during long-running operations and prevent timeouts.

### Automatic Progress in Sampling

When using `ctx.sample()`, progress notifications are sent automatically every 5 seconds:

```typescript
import { text } from "mcp-use/server";

server.tool(
  { name: "long-llm-task", description: "Run an LLM call with auto-progress." },
  async (params, ctx) => {
    // Progress notifications sent automatically every 5 seconds
    const result = await ctx.sample({
      messages: [{ role: "user", content: { type: "text", text: params.prompt } }],
    });
    return text(result.content.text);
  }
);
```

### Manual Progress Reporting

Report progress explicitly with `ctx.reportProgress(progress, total?, message?)`:

```typescript
import { text } from "mcp-use/server";

server.tool(
  { name: "process-data", description: "Process data with progress tracking." },
  async (params, ctx) => {
    if (ctx?.reportProgress) {
      await ctx.reportProgress(0, 100, "Starting...");

      await processStage1();
      await ctx.reportProgress(33, 100, "Stage 1 complete");

      await processStage2();
      await ctx.reportProgress(66, 100, "Stage 2 complete");

      await processStage3();
      await ctx.reportProgress(100, 100, "Complete");
    }
    return text("Done");
  }
);
```

### How Progress Prevents Timeouts

When a client enables `resetTimeoutOnProgress: true`:

- Each progress notification resets the client's timeout counter
- The default timeout is 60 seconds, but with progress reports operations can run indefinitely
- Both automatic (sampling) and manual (`ctx.reportProgress()`) progress notifications reset the timer

### Progress Notification Format

```typescript
{
  method: "notifications/progress",
  params: {
    progressToken: number,  // Token from the original request's _meta.progressToken
    progress: number,       // Current progress value
    total?: number,         // Total expected (if known)
    message?: string        // Optional status message
  }
}
```

---

## Custom Notifications

Send application-specific events with any method name. Use a namespace prefix (e.g. `custom/`) to avoid collisions with protocol-defined methods:

```typescript
await server.sendNotification("custom/user-joined", {
  userId: "user-123",
  username: "alice",
  joinedAt: new Date().toISOString(),
});

await server.sendNotification("custom/data-updated", {
  resourceId: "res-456",
  changes: ["field1", "field2"],
});
```

---

## Resource Subscriptions

Resource subscriptions let clients opt in to change notifications for specific resource URIs. Unlike broadcast notifications, only subscribed clients are notified.

### How It Works

1. Client sends `resources/subscribe` with a resource URI
2. Server tracks the subscription per session
3. When the resource changes, server calls `server.notifyResourceUpdated(uri)`
4. All subscribed clients receive `notifications/resources/updated`
5. Clients fetch the latest content via `resources/read`
6. Subscriptions are cleaned up automatically when a session closes

### Server-Side: Notifying Subscribers

Define a resource, then notify subscribers when it changes:

```typescript
import { MCPServer, object, text } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({ name: "config-server", version: "1.0.0" });

let appConfig = { theme: "light", language: "en" };

// Define the resource
server.resource(
  {
    name: "app_config",
    uri: "config://app-settings",
    title: "Application Configuration",
    description: "Current application settings",
  },
  async () => object(appConfig)
);

// Tool that updates the resource and notifies subscribers
server.tool(
  {
    name: "update-config",
    description: "Update application configuration.",
    schema: z.object({
      theme: z.enum(["light", "dark"]).optional().describe("Color theme"),
      language: z.string().optional().describe("Language code"),
    }),
  },
  async (params) => {
    if (params.theme) appConfig.theme = params.theme;
    if (params.language) appConfig.language = params.language;

    // Notify all subscribed clients
    await server.notifyResourceUpdated("config://app-settings");

    return text("Configuration updated and subscribers notified.");
  }
);

await server.listen();
```

### Subscriptions vs Notifications

| Feature | Resource Subscriptions | Server Notifications |
|---|---|---|
| **Purpose** | Track changes to a specific resource | Broadcast arbitrary events |
| **Targeting** | Only subscribed clients | All clients (or one session) |
| **Protocol** | `resources/subscribe` / `resources/updated` | `notifications/*` |
| **Use case** | Data synchronization | Status updates, custom events |
| **Client action** | Must subscribe first | Receives without subscribing |

---

## Receiving Notifications from Clients

### Roots Changed

Clients notify the server when their available roots (directories/files) change. Register a handler with `server.onRootsChanged()`:

```typescript
import { MCPServer } from "mcp-use/server";

const server = new MCPServer({ name: "my-server", version: "1.0.0" });

server.onRootsChanged(async (roots) => {
  console.log(`Client updated roots: ${roots.length} root(s)`);

  roots.forEach((root) => {
    console.log(`  - ${root.name || "unnamed"}: ${root.uri}`);
  });
});
```

### Listing Roots

Request the current roots from a specific client session with `server.listRoots()`:

```typescript
const sessions = server.getActiveSessions();

if (sessions.length > 0) {
  const roots = await server.listRoots(sessions[0]);

  if (roots) {
    console.log(`Client has ${roots.length} roots:`);
    roots.forEach((r) => console.log(`  - ${r.uri}`));
  }
}
```

### Root Type

```typescript
interface Root {
  uri: string;   // Must start with "file://"
  name?: string; // Optional human-readable name
}
```

---

## Active Sessions

List all connected client sessions with `server.getActiveSessions()`. Returns an array of session ID strings:

```typescript
const sessions = server.getActiveSessions();
console.log(`${sessions.length} client(s) connected`);

// Broadcast to each session individually with per-session data
for (const sessionId of sessions) {
  await server.sendNotificationToSession(sessionId, "custom/ping", {
    serverTime: Date.now(),
  });
}
```

---

## Quick Reference

| API | Scope | Use When |
|---|---|---|
| `server.sendNotification(method, params)` | All clients | Broadcasting events to every connection |
| `ctx.sendNotification(method, params)` | Current client | Notifying only the caller inside a tool handler |
| `server.sendNotificationToSession(id, method, params)` | One client | Targeting a specific session by ID |
| `server.sendToolsListChanged()` | All clients | Tools were added or removed dynamically |
| `server.sendResourcesListChanged()` | All clients | Resources were added or removed dynamically |
| `server.sendPromptsListChanged()` | All clients | Prompts were added or removed dynamically |
| `server.notifyResourceUpdated(uri)` | Subscribers | A resource's content changed |
| `ctx.reportProgress(progress, total?, msg?)` | Current client | Reporting progress in a long-running tool |
| `server.onRootsChanged(callback)` | Server handler | Reacting to client root changes |
| `server.listRoots(sessionId)` | One client | Fetching current roots from a session |
| `server.getActiveSessions()` | Server | Listing all connected session IDs |
