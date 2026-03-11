# RPC Methods Reference

The SDK wraps all server communication in typed RPC helpers generated from `api.schema.json`. Server-scoped methods are accessed via `CopilotClient` convenience methods. Session-scoped methods are accessed via `session.rpc.*` on a `CopilotSession` instance.

---

## Server RPC Methods

These do not require an active session. They map to `client.*` convenience methods.

### `ping` → `client` (internal)

Echoes a message and returns server metadata. Used for liveness checks.

```typescript
// Params
interface PingParams {
  message?: string;
}

// Result
interface PingResult {
  message: string;        // Echoed or default greeting
  timestamp: number;      // Server timestamp in ms
  protocolVersion: number;
}
```

### `models.list` → `client.listModels()`

Returns all available models with capabilities, policy, and billing data.

```typescript
// No params

// Result
interface ModelsListResult {
  models: {
    id: string;           // e.g. "claude-sonnet-4.5"
    name: string;
    capabilities: {
      supports: {
        vision?: boolean;
        reasoningEffort?: boolean;
      };
      limits: {
        max_prompt_tokens?: number;
        max_output_tokens?: number;
        max_context_window_tokens: number;
      };
    };
    policy?: { state: string; terms: string };
    billing?: { multiplier: number };
    supportedReasoningEfforts?: string[];
    defaultReasoningEffort?: string;
  }[];
}
```

### `tools.list` → (via `session.rpc` or direct)

Lists built-in tools, optionally filtered by model.

```typescript
interface ToolsListParams {
  model?: string;  // Filter for model-specific tool overrides
}

interface ToolsListResult {
  tools: {
    name: string;
    namespacedName?: string;  // e.g. "playwright/navigate" for MCP tools
    description: string;
    parameters?: Record<string, unknown>;  // JSON Schema
    instructions?: string;
  }[];
}
```

### `account.getQuota`

Returns per-quota-type usage snapshots.

```typescript
// No params

interface AccountGetQuotaResult {
  quotaSnapshots: {
    [quotaType: string]: {
      entitlementRequests: number;
      usedRequests: number;
      remainingPercentage: number;
      overage: number;
      overageAllowedWithExhaustedQuota: boolean;
      resetDate?: string;  // ISO 8601
    };
  };
}
```

---

## Session RPC Methods (`session.rpc.*`)

Access these via `session.rpc` on a `CopilotSession`. The `sessionId` is automatically injected — omit it from params.

### `session.rpc.model`

```typescript
// Get current model
session.rpc.model.getCurrent(): Promise<{ modelId?: string }>

// Switch to a different model
session.rpc.model.switchTo({
  modelId: string;
  reasoningEffort?: "low" | "medium" | "high" | "xhigh";
}): Promise<{ modelId?: string }>
```

### `session.rpc.mode`

Controls the agent mode: `"interactive"` (default), `"plan"` (plan before acting), `"autopilot"` (execute without confirmation).

```typescript
session.rpc.mode.get(): Promise<{ mode: "interactive" | "plan" | "autopilot" }>

session.rpc.mode.set({
  mode: "interactive" | "plan" | "autopilot";
}): Promise<{ mode: "interactive" | "plan" | "autopilot" }>
```

When mode changes, the session emits a `session.mode_changed` event with `previousMode` and `newMode`.

### `session.rpc.plan`

Reads and manages the session plan file (used in plan mode).

```typescript
session.rpc.plan.read(): Promise<{
  exists: boolean;
  content: string | null;  // null if plan does not exist
  path: string | null;     // null if workspace not enabled
}>

session.rpc.plan.update({ content: string }): Promise<{}>

session.rpc.plan.delete(): Promise<{}>
```

Plan changes emit `session.plan_changed` events with `operation: "create" | "update" | "delete"`.

### `session.rpc.workspace`

Reads and writes files in the session workspace directory (persistent storage for the session).

```typescript
session.rpc.workspace.listFiles(): Promise<{
  files: string[];  // Relative paths within the workspace files directory
}>

session.rpc.workspace.readFile({ path: string }): Promise<{
  content: string;  // UTF-8 string
}>

session.rpc.workspace.createFile({
  path: string;     // Relative path within workspace
  content: string;  // UTF-8 string to write
}): Promise<{}>
```

File changes emit `session.workspace_file_changed` events.

### `session.rpc.fleet`

Starts fleet mode (parallel execution across multiple agents).

```typescript
session.rpc.fleet.start({
  prompt?: string;  // Optional user prompt to combine with fleet instructions
}): Promise<{
  started: boolean;
}>
```

### `session.rpc.agent`

Lists and selects custom agents configured via `SessionConfig.customAgents`.

```typescript
// List available custom agents
session.rpc.agent.list(): Promise<{
  agents: { name: string; displayName: string; description: string }[];
}>

// Get the currently active custom agent
session.rpc.agent.getCurrent(): Promise<{
  agent: { name: string; displayName: string; description: string } | null;
}>

// Select a custom agent by name
session.rpc.agent.select({ name: string }): Promise<{
  agent: { name: string; displayName: string; description: string };
}>

// Return to the default agent
session.rpc.agent.deselect(): Promise<{}>
```

Agent changes emit `subagent.selected` / `subagent.deselected` events.

### `session.rpc.compaction`

Manually triggers context compaction (normally handled automatically by infinite sessions).

```typescript
session.rpc.compaction.compact(): Promise<{
  success: boolean;
  tokensRemoved: number;
  messagesRemoved: number;
}>
```

Emits `session.compaction_start` and `session.compaction_complete` events.

### `session.rpc.tools`

Handles pending tool calls (for external tool flow where the SDK delivers a tool call to the host).

```typescript
session.rpc.tools.handlePendingToolCall({
  requestId: string;
  result?: string | {
    textResultForLlm: string;
    resultType?: string;
    error?: string;
    toolTelemetry?: Record<string, unknown>;
  };
  error?: string;
}): Promise<{ success: boolean }>
```

Use this when you receive an `external_tool.requested` event and want to respond with the tool result.

### `session.rpc.permissions`

Handles pending permission requests manually (alternative to using `onPermissionRequest` callback).

```typescript
session.rpc.permissions.handlePendingPermissionRequest({
  requestId: string;
  result:
    | { kind: "approved" }
    | { kind: "denied-by-rules"; rules: unknown[] }
    | { kind: "denied-no-approval-rule-and-could-not-request-from-user" }
    | { kind: "denied-interactively-by-user"; feedback?: string }
    | { kind: "denied-by-content-exclusion-policy"; path: string; message: string };
}): Promise<{ success: boolean }>
```

Use this when you receive a `permission.requested` event and handle permissions via events rather than the `onPermissionRequest` callback.

### `session.rpc.log`

Emits a log entry into the session event stream.

```typescript
session.rpc.log({
  message: string;
  level?: "info" | "warning" | "error";  // Default: "info"
  ephemeral?: boolean;  // true = not persisted to disk
}): Promise<{ eventId: string }>
```

---

## RPC vs. Session Methods: Decision Guide

| Task | Use |
|------|-----|
| Send a prompt | `session.send()` or `session.sendAndWait()` |
| Abort the current turn | `session.abort()` |
| Subscribe to events | `session.on()` |
| Wait for the agent to finish | `session.sendAndWait()` or listen for `"session.idle"` event |
| Switch the active model | `session.rpc.model.switchTo()` |
| Switch agent mode | `session.rpc.mode.set()` |
| Read/write the plan file | `session.rpc.plan.*` |
| Read/write workspace files | `session.rpc.workspace.*` |
| Select a custom agent | `session.rpc.agent.select()` |
| Trigger manual compaction | `session.rpc.compaction.compact()` |
| Respond to external tool calls | `session.rpc.tools.handlePendingToolCall()` |
| Respond to permission requests | `session.rpc.permissions.handlePendingPermissionRequest()` |
| Emit log entries | `session.rpc.log()` |
| List all models | `client.listModels()` |
| Check authentication | `client.getAuthStatus()` |
| List sessions | `client.listSessions()` |

---

## Usage Examples

```typescript
// Switch to plan mode before a complex task
await session.rpc.mode.set({ mode: "plan" });
await session.send({ prompt: "Refactor the auth module" });
// Wait for plan to be ready
await new Promise<void>((resolve) => {
  session.on("exit_plan_mode.requested", () => resolve());
});

// Read the generated plan
const plan = await session.rpc.plan.read();
if (plan.exists) {
  console.log(plan.content);
  // Approve: switch to interactive and continue
  await session.rpc.mode.set({ mode: "interactive" });
}

// Use a custom agent
await session.rpc.agent.select({ name: "code-reviewer" });
const response = await session.sendAndWait({ prompt: "Review the latest PR changes" });
console.log(response?.data.content);
await session.rpc.agent.deselect();

// Handle external tool events manually
session.on("external_tool.requested", async (e) => {
  const result = await runExternalTool(e.data.toolName, e.data.arguments);
  await session.rpc.tools.handlePendingToolCall({
    requestId: e.data.requestId,
    result: { textResultForLlm: result, resultType: "success" },
  });
});

// Manually trigger compaction before a large task
const compact = await session.rpc.compaction.compact();
console.log(`Freed ${compact.tokensRemoved} tokens`);
```
