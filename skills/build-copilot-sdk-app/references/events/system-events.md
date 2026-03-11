# System Events

Infrastructure-level events for system messages, notifications, abort signals, and message queue changes.

## Events

### `system.message`

Emitted when a system or developer prompt is injected into the conversation.

```typescript
session.on("system.message", (event) => {
  const { content, role, name, metadata } = event.data;
  console.log(`[${role}] ${name ?? "system"}: ${content.substring(0, 100)}...`);
});
```

**Data shape:**

```typescript
{
  content: string;          // System/developer prompt text
  role: "system" | "developer";
  name?: string;            // Optional message source identifier
  metadata?: {
    promptVersion?: string; // Version ID of the prompt template
    variables?: {           // Template variables used
      [key: string]: unknown;
    };
  };
}
```

### `system.notification`

Emitted for system-level notifications. Common trigger: background agent completion.

```typescript
session.on("system.notification", (event) => {
  const { content, kind } = event.data;
  console.log("Notification:", content);

  if (kind.type === "agent_completed") {
    console.log(`Agent ${kind.agentId} (${kind.agentType}): ${kind.status}`);
  }
});
```

**Data shape:**

```typescript
{
  content: string;            // Notification text (may include XML tags)
  kind:
    | {
        type: "agent_completed";
        agentId: string;       // Background agent ID
        agentType: string;     // e.g., "explore", "task", "general-purpose"
        status: "completed" | "failed";
        description?: string;  // Agent task description
        prompt?: string;       // Full prompt given to the agent
      }
    | {
        type: string;          // Other notification types
        [key: string]: unknown;
      };
}
```

### `abort`

Emitted when the current turn is aborted (e.g., user called `session.abort()`).

```typescript
session.on("abort", (event) => {
  console.log("Aborted:", event.data.reason);
});
```

**Data shape:**

```typescript
{
  reason: string;    // e.g., "user initiated"
}
```

Use `abort` to clean up in-progress UI state:

```typescript
session.on("abort", () => {
  clearProgressIndicators();
  resetToolUI();
});
```

### `pending_messages.modified`

Emitted when the pending message queue changes. Empty payload — signals that queued prompts have been added or removed.

```typescript
session.on("pending_messages.modified", () => {
  console.log("Message queue changed");
});
```

**Data shape:** `{}` (empty)

Use this to update UI showing queued messages:

```typescript
session.on("pending_messages.modified", async () => {
  // Refresh queued message display
  updateQueueUI();
});
```

### `session.error`

Emitted when a session-level error occurs.

```typescript
session.on("session.error", (event) => {
  const { errorType, message } = event.data;
  console.error(`[${errorType}] ${message}`);
});
```

**Data shape:**

```typescript
{
  errorType: string;    // "authentication" | "authorization" | "quota" | "rate_limit" | "query" | ...
  message: string;      // Human-readable error message
  code?: string;        // Machine-readable error code
  retryable?: boolean;  // Whether the operation can be retried
  retryAfterMs?: number; // Suggested retry delay in milliseconds
}
```

**Error type handling:**

```typescript
session.on("session.error", (event) => {
  switch (event.data.errorType) {
    case "authentication":
      console.error("Auth failed — re-authenticate");
      break;
    case "rate_limit":
      console.warn(`Rate limited. Retry after ${event.data.retryAfterMs}ms`);
      break;
    case "quota":
      console.error("Quota exhausted");
      break;
    default:
      console.error(`Error: ${event.data.message}`);
  }
});
```

## Event handling patterns

### Graceful shutdown on errors

```typescript
session.on("session.error", async (event) => {
  if (event.data.errorType === "authentication") {
    await session.disconnect();
    await client.stop();
    process.exit(1);
  }
});
```

### Combined system event monitor

```typescript
// Log all system-level events
for (const eventType of [
  "system.message",
  "system.notification",
  "abort",
  "session.error",
  "pending_messages.modified",
] as const) {
  session.on(eventType, (event) => {
    console.log(`[${event.type}]`, JSON.stringify(event.data, null, 2));
  });
}
```
