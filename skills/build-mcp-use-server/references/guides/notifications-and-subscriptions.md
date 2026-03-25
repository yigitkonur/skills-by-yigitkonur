# Notifications and Subscriptions

Definitive guide to sending notifications, tracking progress, managing resource subscriptions, and receiving client events with the mcp-use TypeScript server library.

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
| `server.sendNotificationToSession(id, method, params)` | One client | Targeting a specific session by ID |
| `ctx.sendNotification(method, params)` | Current client | Notifying only the caller inside a tool handler |
| `server.sendToolsListChanged()` | All clients | Tools were added or removed dynamically |
| `server.sendResourcesListChanged()` | All clients | Resources were added or removed dynamically |
| `server.sendPromptsListChanged()` | All clients | Prompts were added or removed dynamically |
| `server.notifyResourceUpdated(uri)` | Subscribers | A resource's content changed |
| `ctx.reportProgress(progress, total?, msg?)` | Current client | Reporting progress in a long-running tool |
| `ctx.log(level, message, logger?)` | Current client | Sending log messages to the client during tool execution |
| `server.onRootsChanged(callback)` | Server handler | Reacting to client root changes |
| `server.listRoots(sessionId)` | One client | Fetching current roots from a session |
| `server.getActiveSessions()` | Server | Listing all connected session IDs |

---

## Broadcast Patterns and Notification Shapes

Broadcasting is more than calling `sendNotification()`. The best servers encode context, correlate events with the originating call, and throttle high-frequency updates.

### Parameter Table: `server.sendNotification()`

| Parameter | Type | Required | Description |
|---|---|---|---|
| `method` | `string` | Yes | Notification method name. Use `custom/*` or domain-specific namespaces. |
| `params` | `Record<string, unknown>` | No | Structured payload. Keep it JSON-serializable. |

### Fanout Broadcast with Correlation IDs

```typescript
import { MCPServer } from 'mcp-use/server';

const server = new MCPServer({ name: 'notify-demo', version: '1.0.0' });

function broadcastDeployment({ id, status }: { id: string; status: string }) {
  return server.sendNotification('custom/deploy-status', {
    deploymentId: id,
    status,
    correlationId: `deploy-${id}`,
    emittedAt: new Date().toISOString(),
  });
}
```

### Targeted Broadcast with Filters

```typescript
import { MCPServer } from 'mcp-use/server';

const server = new MCPServer({ name: 'notify-demo', version: '1.0.0' });

async function notifyPaidAccounts() {
  for (const sessionId of server.getActiveSessions()) {
    await server.sendNotificationToSession(sessionId, 'custom/billing-summary', {
      plan: 'pro',
      reportUrl: 'https://billing.example.com/reports/2024-11',
    });
  }
}
```

### ❌ BAD: Unnamespaced Methods

```typescript
await server.sendNotification('status', { state: 'ready' });
await server.sendNotification('update', { state: 'ready' });
```

### ✅ GOOD: Namespaced, Versioned Methods

```typescript
await server.sendNotification('custom/status/ready', { state: 'ready' });
await server.sendNotification('custom/status/v2', { state: 'ready', region: 'us-east-1' });
```

---

## Progress Tracking with Progress Tokens

Progress notifications are the only safe way to keep a caller informed during a long-running tool call. MCP clients can attach a `progressToken` to a request. mcp-use exposes it on the handler context; use it to decide whether to emit updates.

### Parameter Table: `ctx.reportProgress()`

| Parameter | Type | Required | Description |
|---|---|---|---|
| `progress` | `number` | Yes | Current step or percentage (0 → total). |
| `total` | `number` | No | Total steps; omit for indeterminate tasks. |
| `message` | `string` | No | Human-readable update shown by clients. |

### Long-Running Tool with Progress

```typescript
import { MCPServer, text } from 'mcp-use/server';
import { z } from 'zod';

const server = new MCPServer({ name: 'progress-demo', version: '1.0.0' });

server.tool(
  {
    name: 'bulk-import',
    description: 'Import a batch of records with progress updates.',
    schema: z.object({ count: z.number().min(1).max(500) }),
  },
  async ({ count }, ctx) => {
    const total = count;

    for (let i = 1; i <= total; i += 1) {
      await doWork(i);
      if (ctx?.reportProgress) {
        await ctx.reportProgress(i, total, `Imported ${i}/${total} records`);
      }
    }

    return text(`Imported ${count} records.`);
  }
);
```

### Progress Tokens: When to Emit

| Situation | Recommended Behavior |
|---|---|
| Token provided | Call `ctx.reportProgress()` periodically. |
| No token | Skip progress updates to avoid extra noise. |
| Indeterminate duration | Emit `ctx.reportProgress(0, undefined, "Starting")` then update messages only. |

### ❌ BAD: Flooding Progress Updates

```typescript
for (let i = 0; i < total; i += 1) {
  await ctx.reportProgress(i, total, `step ${i}`); // sends hundreds of events
}
```

### ✅ GOOD: Throttled Updates

```typescript
for (let i = 0; i < total; i += 1) {
  if (i % 10 === 0) {
    await ctx.reportProgress(i, total, `Processed ${i}/${total}`);
  }
}
```

---

## Resource Subscriptions and Update Notifications

When clients subscribe to a resource (`resources/subscribe`), mcp-use tracks subscriptions automatically. Use `notifyResourceUpdated()` whenever the underlying content changes so subscribers receive a push notification.

### Parameter Table: `server.notifyResourceUpdated()`

| Parameter | Type | Required | Description |
|---|---|---|---|
| `uri` | `string` | Yes | URI of the resource that changed. |

### Update Flow for Mutable Resources

```typescript
import { MCPServer, text, object } from 'mcp-use/server';

const server = new MCPServer({ name: 'resource-demo', version: '1.0.0' });

server.resource(
  {
    name: 'daily-report',
    uri: 'file:///reports/daily.json',
    mimeType: 'application/json',
  },
  async () => {
    const report = await loadDailyReport();
    return object(report);
  }
);

async function refreshReport() {
  await updateReportFromSource();
  await server.notifyResourceUpdated('file:///reports/daily.json');
}
```

### Subscriptions vs. List Changes

| Change Type | Call This | Client Outcome |
|---|---|---|
| Resource content changed | `server.notifyResourceUpdated(uri)` | Subscribers refresh resource content. |
| Resource added/removed | `server.sendResourcesListChanged()` | Clients re-fetch resource list. |

### ❌ BAD: Updating Content Without Notification

```typescript
await updateReportFromSource();
// Clients never hear about the change.
```

### ✅ GOOD: Notify Subscribers Immediately

```typescript
await updateReportFromSource();
await server.notifyResourceUpdated('file:///reports/daily.json');
```

---

## Client Events: Roots and Environment Updates

Roots represent the client-controlled filesystem scope. Servers can both listen for root changes and request the current roots from a specific session.

### Parameter Table: `server.onRootsChanged()`

| Parameter | Type | Required | Description |
|---|---|---|---|
| `callback` | `(roots: Root[]) => void` | Yes | Invoked whenever the client updates roots. |

### Reacting to Root Changes

```typescript
import { MCPServer } from 'mcp-use/server';

const server = new MCPServer({ name: 'roots-demo', version: '1.0.0' });

server.onRootsChanged(async (roots) => {
  console.log(`Client updated roots: ${roots.length} root(s)`);
  roots.forEach((root) => console.log(`  - ${root.name || "unnamed"}: ${root.uri}`));
});
```

### Requesting Roots on Demand

```typescript
const sessions = server.getActiveSessions();

if (sessions.length > 0) {
  const roots = await server.listRoots(sessions[0]);
  console.log('Roots:', roots?.map((r) => r.uri));
}
```

### ❌ BAD: Assuming Roots Never Change

```typescript
const roots = await server.listRoots(sessionId);
// Store forever, never refresh.
```

### ✅ GOOD: Update on Change Events

```typescript
let cachedRoots: Root[] = [];
server.onRootsChanged((roots) => {
  cachedRoots = roots;
});
```

---

## HMR + `list_changed` Notifications

`mcp-use dev` uses HMR to reload tools, resources, prompts, and widgets. When files change, the dev server emits `notifications/*/list_changed` so connected clients can refresh. In production, you should emit list change notifications any time you add or remove tools/resources/prompts dynamically.

### Parameter Table: List Change Helpers

| Method | When to Call | Typical Trigger |
|---|---|---|
| `server.sendToolsListChanged()` | Tool list changed | Adding/removing tools or swapping schemas |
| `server.sendResourcesListChanged()` | Resource list changed | Publishing new resource URIs |
| `server.sendPromptsListChanged()` | Prompt list changed | Dynamic prompt templates |

### Debouncing List Changes

```typescript
let pending = false;

async function scheduleListChanged() {
  if (pending) return;
  pending = true;
  setTimeout(async () => {
    pending = false;
    await server.sendToolsListChanged();
  }, 200);
}
```

### ❌ BAD: Spamming `list_changed`

```typescript
server.on('tool:registered', async () => {
  await server.sendToolsListChanged();
  await server.sendToolsListChanged();
});
```

### ✅ GOOD: Coalesce Changes

```typescript
server.on('tool:registered', scheduleListChanged);
server.on('tool:removed', scheduleListChanged);
```

---

## Notification Patterns & Reliability

Use clear naming, payload schemas, and retry-safe patterns. Notifications are fire-and-forget; design them to be idempotent and easy to ignore.

### Suggested Naming Convention

| Pattern | Example | Notes |
|---|---|---|
| `custom/domain/action` | `custom/billing/invoice-created` | Easy to filter by prefix. |
| `custom/domain/v2` | `custom/analytics/v2` | Version when payload changes. |

### Payload Schema Checklist

- Include a stable identifier (`jobId`, `deploymentId`, `resourceUri`).
- Add `emittedAt` ISO timestamps for ordering.
- Avoid sending raw errors; send an `errorCode` and `message` instead.

### ❌ BAD: Non-idempotent Updates

```typescript
await server.sendNotification('custom/credits', { delta: -1 });
```

### ✅ GOOD: Full State Updates

```typescript
await server.sendNotification('custom/credits', { remaining: 42, accountId: 'acct_123' });
```

---

## Server Logging

mcp-use provides two complementary logging systems: a server-side `Logger` class for server process output, and `ctx.log()` for sending log messages to clients during tool execution.

### Tool Logging with `ctx.log()`

Tools can send log messages directly to the connected client using `ctx.log()`. This gives the client real-time visibility into tool execution, especially useful for long-running operations.

```typescript
import { text } from "mcp-use/server";
import { z } from "zod";

server.tool(
  {
    name: "process_data",
    description: "Process data with progress logging",
    schema: z.object({
      items: z.array(z.string()),
    }),
  },
  async ({ items }, ctx) => {
    await ctx.log("info", "Starting data processing");
    await ctx.log("debug", `Processing ${items.length} items`, "my-tool");

    for (const item of items) {
      if (!item.trim()) {
        await ctx.log("warning", "Empty item found, skipping");
        continue;
      }
      try {
        await processItem(item);
      } catch (err) {
        await ctx.log("error", `Failed to process item: ${err.message}`);
      }
    }

    await ctx.log("info", "Processing completed");
    return text("All items processed");
  }
);
```

#### `ctx.log()` Signature

```typescript
ctx.log(level, message, logger?)
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `level` | `string` | Yes | One of the eight log levels (see table below). |
| `message` | `string` | Yes | The log message content. |
| `logger` | `string` | No | Logger name for categorization (defaults to `'tool'`). |

#### `ctx.log()` Log Levels

| Level | Use Case |
|---|---|
| `debug` | Detailed debugging information, verbose output |
| `info` | General informational messages about progress |
| `notice` | Normal but significant events |
| `warning` | Warning messages for recoverable issues |
| `error` | Error messages for failures that don't stop execution |
| `critical` | Critical conditions requiring immediate attention |
| `alert` | Action must be taken immediately |
| `emergency` | System is unusable |

### Server-Side `Logger` Class

The `Logger` class (introduced in v1.12.0, replacing `winston`) controls server process log output. It works in both Node.js and browser environments.

```typescript
import { Logger } from "mcp-use";

// Configure logging level and format
Logger.configure({
  level: "debug",    // Set log level
  format: "detailed", // Set output format
});

// Or configure via debug numeric shorthand
Logger.setDebug(0); // Production mode (info level)
Logger.setDebug(1); // Debug mode
Logger.setDebug(2); // Verbose mode (debug level)
```

Get a named logger instance for custom component logging:

```typescript
const logger = Logger.get("my-component");

logger.info("Component initialized");
logger.debug("Processing request", { userId: 123 });
logger.error("Operation failed", new Error("Connection timeout"));
```

#### `Logger` Log Levels (server-side)

| Level | Use Case |
|---|---|
| `error` | Error conditions that need attention |
| `warn` | Warning messages for potential issues |
| `info` | General informational messages (default) |
| `http` | HTTP request/response logging |
| `verbose` | Verbose informational messages |
| `debug` | Detailed debugging information |
| `silly` | Very detailed debug information |

#### Log Formats

| Format | Description | Example Output |
|---|---|---|
| `minimal` (default) | Timestamp, label, level, message | `14:23:45 [mcp-use] info: Session initialized: abc123` |
| `detailed` | More verbose with full context | `14:23:45 [mcp-use] INFO: Session initialized: abc123` |

#### Environment Variable Log Levels

| Command | Effect |
|---|---|
| `node server.js` | Production mode — shows MCP operations only |
| `DEBUG=1 node server.js` | Debug mode — shows registrations and call start/end |
| `DEBUG=2 node server.js` | Verbose mode — full JSON-RPC request/response logging |

#### Migration from Winston (v1.12.0+)

```typescript
// Before (winston — removed in v1.12.0):
import winston from "winston";
const logger = winston.createLogger({ level: "info", transports: [new winston.transports.Console()] });
logger.info("Server started");

// After (SimpleConsoleLogger):
import { Logger } from "mcp-use";
Logger.configure({ level: "info", format: "minimal" });
const logger = Logger.get();
logger.info("Server started");
```

---

## Troubleshooting Notifications

| Symptom | Likely Cause | Fix |
|---|---|---|
| Notifications never arrive | Stateless transport | Switch to SSE/StreamableHTTP. |
| Only first client gets updates | Using `ctx.sendNotification()` | Use `server.sendNotification()` to broadcast. |
| UI widgets not updating | Missing `notifyResourceUpdated()` | Trigger resource update notifications. |
| Progress stuck at 0% | Client did not send `progressToken` | Check that the client attaches a `progressToken` to the request; guard with a conditional before calling `ctx.reportProgress()`. |

### Debug Checklist

1. Confirm transport is stateful (SSE or StreamableHTTP).
2. Verify the session ID via `server.getActiveSessions()`.
3. Use Inspector to watch incoming notifications.
4. Log `notification.method` and `notification.params` on the client.
5. Validate payloads are JSON serializable.
