# Hook Events

Events emitted during hook execution and plan mode transitions. These events track hook lifecycle and multi-client coordination for external tools and plan mode.

## Hook Lifecycle Events

### `hook.start`

Emitted when a hook begins executing.

```typescript
session.on("hook.start", (event) => {
  const { hookInvocationId, hookType, input } = event.data;
  console.log(`Hook started: ${hookType} (${hookInvocationId})`);
  if (input) {
    console.log("Input:", JSON.stringify(input));
  }
});
```

**Data shape:**

```typescript
{
  hookInvocationId: string;   // UUID matching the corresponding hook.end
  hookType: string;           // "preToolUse" | "postToolUse" | "sessionStart" | "sessionEnd" | "userPromptSubmitted" | "errorOccurred"
  input?: {                   // Hook input data (varies by hook type)
    [key: string]: unknown;
  };
}
```

### `hook.end`

Emitted when a hook finishes executing.

```typescript
session.on("hook.end", (event) => {
  const { hookInvocationId, hookType, success, output, error } = event.data;
  if (success) {
    console.log(`Hook ${hookType} completed`);
  } else {
    console.error(`Hook ${hookType} failed: ${error?.message}`);
  }
});
```

**Data shape:**

```typescript
{
  hookInvocationId: string;   // Matches the corresponding hook.start
  hookType: string;           // Same as hook.start
  output?: {                  // Hook output data
    [key: string]: unknown;
  };
  success: boolean;           // Whether the hook completed without errors
  error?: {
    message: string;          // Error message
    stack?: string;           // Stack trace when available
  };
}
```

## External Tool Events (Protocol v3)

### `external_tool.requested`

Broadcast to all connected clients when an external tool needs to be executed. This is a protocol v3 feature for multi-client architectures where tools may be handled by different clients.

```typescript
session.on("external_tool.requested", (event) => {
  const { requestId, sessionId, toolCallId, toolName, arguments: args } = event.data;
  console.log(`External tool: ${toolName}`);

  if (canHandleTool(toolName)) {
    const result = await executeTool(toolName, args);
    await session.rpc.session.respondToExternalTool({
      requestId,
      result,
    });
  }
});
```

**Data shape:**

```typescript
{
  requestId: string;          // UUID — respond via session.respondToExternalTool()
  sessionId: string;          // Session this belongs to
  toolCallId: string;         // Tool call ID
  toolName: string;           // Name of the external tool
  arguments?: {               // Tool arguments
    [key: string]: unknown;
  };
}
```

**Multi-client pattern:** When building a distributed system, different clients can handle different tools. Use `toolName` to route:

```typescript
// IDE client handles file tools
session.on("external_tool.requested", async (event) => {
  if (event.data.toolName.startsWith("editor_")) {
    const result = await handleEditorTool(event.data);
    await session.rpc.session.respondToExternalTool({
      requestId: event.data.requestId,
      result,
    });
  }
  // Ignore tools this client doesn't handle
});
```

### `external_tool.completed`

Emitted when an external tool request is resolved. Ephemeral event.

```typescript
session.on("external_tool.completed", (event) => {
  dismissToolUI(event.data.requestId);
});
```

**Data shape:**

```typescript
{
  requestId: string;    // Matches the original external_tool.requested
}
```

## Plan Mode Events

### `exit_plan_mode.requested`

Emitted when the agent has finished creating a plan and is requesting to exit plan mode. Ephemeral event.

```typescript
session.on("exit_plan_mode.requested", (event) => {
  const { requestId, summary, planContent, actions, recommendedAction } = event.data;
  console.log("Plan summary:", summary);
  console.log("Recommended action:", recommendedAction);
  console.log("Available actions:", actions.join(", "));
});
```

**Data shape:**

```typescript
{
  requestId: string;          // UUID — respond via session.respondToExitPlanMode()
  summary: string;            // Brief plan summary
  planContent: string;        // Full plan text
  actions: string[];          // Available actions (e.g., ["approve", "edit", "reject"])
  recommendedAction: string;  // Suggested action (usually "approve")
}
```

**Auto-approve plan and switch to autopilot:**

```typescript
session.on("exit_plan_mode.requested", async (event) => {
  // Auto-approve the plan
  await session.rpc.session.respondToExitPlanMode({
    requestId: event.data.requestId,
    action: event.data.recommendedAction, // Usually "approve"
  });
  // Switch to autopilot for execution
  await session.rpc.mode.set({ mode: "autopilot" });
});
```

### `exit_plan_mode.completed`

Emitted when the exit plan mode request is resolved. Ephemeral event.

```typescript
session.on("exit_plan_mode.completed", (event) => {
  console.log("Plan mode transition complete");
});
```

**Data shape:**

```typescript
{
  requestId: string;
}
```

## Monitoring hook performance

```typescript
const hookTimings = new Map<string, number>();

session.on("hook.start", (event) => {
  hookTimings.set(event.data.hookInvocationId, Date.now());
});

session.on("hook.end", (event) => {
  const startTime = hookTimings.get(event.data.hookInvocationId);
  if (startTime) {
    const duration = Date.now() - startTime;
    console.log(`Hook ${event.data.hookType}: ${duration}ms (success: ${event.data.success})`);
    hookTimings.delete(event.data.hookInvocationId);
  }
});
```
