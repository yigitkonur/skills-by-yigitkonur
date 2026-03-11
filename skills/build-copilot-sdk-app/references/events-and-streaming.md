# Events and Streaming

## Event subscription API

```typescript
// Typed — fires only for the specific event type
const unsub = session.on("assistant.message", (event) => {
  console.log(event.data.content);
});

// Wildcard — fires for every event
session.on((event) => {
  switch (event.type) {
    case "assistant.message": /* ... */ break;
    case "session.idle": /* ... */ break;
  }
});

// Unsubscribe
unsub();
```

## Event base fields

Every event shares:

```typescript
{
  id: string;              // UUID v4
  type: string;            // event type
  timestamp: string;       // ISO 8601
  parentId: string | null; // linked chain (null for first)
  ephemeral?: boolean;     // true = not persisted to disk
  data: { ... };           // type-specific payload
}
```

## Streaming

Enable with `streaming: true` in SessionConfig:

```typescript
const session = await client.createSession({
  streaming: true,
  onPermissionRequest: approveAll,
});

let fullMessage = "";

session.on("assistant.message_delta", (event) => {
  process.stdout.write(event.data.deltaContent);
  fullMessage += event.data.deltaContent;
});

session.on("assistant.reasoning_delta", (event) => {
  // Reasoning/thinking chunks (if model supports it)
  console.log("[thinking]", event.data.deltaContent);
});

session.on("assistant.message", (event) => {
  // Final complete message (also arrives after all deltas)
  console.log("\nFinal:", event.data.content);
});

session.on("session.idle", () => {
  console.log("--- turn complete ---");
});
```

### Streaming pattern with waitForIdle

```typescript
let idleResolve: (() => void) | null = null;
const waitForIdle = () => new Promise<void>((r) => { idleResolve = r; });

session.on((event) => {
  if (event.type === "assistant.message_delta") {
    process.stdout.write(event.data.deltaContent ?? "");
  } else if (event.type === "session.idle") {
    idleResolve?.();
  } else if (event.type === "session.error") {
    console.error(event.data.message);
    idleResolve?.();
  }
});

let idle = waitForIdle();
await session.send({ prompt: "Hello" });
await idle;

// For subsequent turns:
idle = waitForIdle();
await session.send({ prompt: "Follow up" });
await idle;
```

## All event types by category

### Session lifecycle

| Type | Ephemeral | Key Data |
|------|-----------|----------|
| `session.start` | no | `sessionId, version, selectedModel?, context?` |
| `session.resume` | no | `resumeTime, eventCount, context?` |
| `session.idle` | **yes** | `backgroundTasks?: { agents: [], shells: [] }` |
| `session.error` | no | `errorType, message, stack?, statusCode?` |
| `session.title_changed` | **yes** | `title: string` |
| `session.info` | no | `infoType, message` |
| `session.warning` | no | `warningType, message` |
| `session.model_change` | no | `previousModel?, newModel` |
| `session.mode_changed` | no | `previousMode, newMode` (`"interactive"\|"plan"\|"autopilot"`) |
| `session.plan_changed` | no | `operation: "create"\|"update"\|"delete"` |
| `session.workspace_file_changed` | no | `path, operation: "create"\|"update"` |
| `session.handoff` | no | `handoffTime, sourceType, summary?` |
| `session.truncation` | no | `tokenLimit, tokensRemovedDuringTruncation, ...` |
| `session.snapshot_rewind` | **yes** | `upToEventId, eventsRemoved` |
| `session.shutdown` | no | `shutdownType, totalPremiumRequests, codeChanges, modelMetrics` |
| `session.context_changed` | no | `cwd, gitRoot?, repository?, branch?` |
| `session.usage_info` | **yes** | `tokenLimit, currentTokens, messagesLength` |
| `session.compaction_start` | no | `data: {}` |
| `session.compaction_complete` | no | `success, tokensRemoved?, checkpointPath?` |
| `session.task_complete` | no | `summary?` |

### User / pending messages

| Type | Ephemeral | Key Data |
|------|-----------|----------|
| `user.message` | no | `content, attachments?, source?, agentMode?` |
| `pending_messages.modified` | **yes** | `data: {}` |

User message `agentMode`: `"interactive"\|"plan"\|"autopilot"\|"shell"`

Attachment types: `file`, `directory`, `selection`, `github_reference`

### Assistant

| Type | Ephemeral | Key Data |
|------|-----------|----------|
| `assistant.turn_start` | no | `turnId, interactionId?` |
| `assistant.intent` | **yes** | `intent: string` |
| `assistant.reasoning` | no | `reasoningId, content` |
| `assistant.reasoning_delta` | **yes** | `reasoningId, deltaContent` |
| `assistant.streaming_delta` | **yes** | `totalResponseSizeBytes` |
| `assistant.message` | no | `messageId, content, toolRequests?, phase?, outputTokens?` |
| `assistant.message_delta` | **yes** | `messageId, deltaContent, parentToolCallId?` |
| `assistant.turn_end` | no | `turnId` |
| `assistant.usage` | **yes** | `model, inputTokens?, outputTokens?, cost?, duration?` |

`toolRequests` on `assistant.message`:
```typescript
toolRequests?: Array<{
  toolCallId: string;
  name: string;
  arguments?: string;
  type?: "function" | "custom";
}>;
```

### Tool execution

| Type | Ephemeral | Key Data |
|------|-----------|----------|
| `tool.user_requested` | no | `toolCallId, toolName, arguments?` |
| `tool.execution_start` | no | `toolCallId, toolName, arguments?, mcpServerName?, parentToolCallId?` |
| `tool.execution_partial_result` | **yes** | `toolCallId, partialOutput` |
| `tool.execution_progress` | **yes** | `toolCallId, progressMessage` |
| `tool.execution_complete` | no | `toolCallId, success, result?, error?, parentToolCallId?` |

Tool result types in `tool.execution_complete`:
- `{ type: "text", text }`
- `{ type: "terminal", text, exitCode?, cwd? }`
- `{ type: "image", data, mimeType }`
- `{ type: "resource_link", name, uri }`
- `{ type: "resource", resource: { uri, text? } }`

### Skill

| Type | Ephemeral | Key Data |
|------|-----------|----------|
| `skill.invoked` | no | `name, path, content, allowedTools?, pluginName?` |

### Sub-agent

| Type | Ephemeral | Key Data |
|------|-----------|----------|
| `subagent.started` | no | `toolCallId, agentName, agentDisplayName, agentDescription` |
| `subagent.completed` | no | `toolCallId, agentName, agentDisplayName` |
| `subagent.failed` | no | `toolCallId, agentName, error` |
| `subagent.selected` | no | `agentName, agentDisplayName, tools` |
| `subagent.deselected` | no | `data: {}` |

`parentToolCallId` on various events links sub-agent activity to the parent tool call.

### Hook

| Type | Ephemeral | Key Data |
|------|-----------|----------|
| `hook.start` | no | `hookInvocationId, hookType, input?` |
| `hook.end` | no | `hookInvocationId, hookType, output?, success, error?` |

### System

| Type | Ephemeral | Key Data |
|------|-----------|----------|
| `system.message` | no | `content, role: "system"\|"developer"` |
| `system.notification` | no | `content, kind: agent_completed\|shell_completed\|shell_detached_completed` |
| `abort` | no | `reason: string` |

### Permission

| Type | Ephemeral | Key Data |
|------|-----------|----------|
| `permission.requested` | **yes** | `requestId, permissionRequest` |
| `permission.completed` | **yes** | `requestId, result: { kind }` |

### User input / elicitation

| Type | Ephemeral | Key Data |
|------|-----------|----------|
| `user_input.requested` | **yes** | `requestId, question, choices?, allowFreeform?` |
| `user_input.completed` | **yes** | `requestId` |
| `elicitation.requested` | **yes** | `requestId, message, requestedSchema` |
| `elicitation.completed` | **yes** | `requestId` |

### External tool (v3 broadcast)

| Type | Ephemeral | Key Data |
|------|-----------|----------|
| `external_tool.requested` | **yes** | `requestId, sessionId, toolCallId, toolName, arguments?` |
| `external_tool.completed` | **yes** | `requestId` |

### Command / plan mode

| Type | Ephemeral | Key Data |
|------|-----------|----------|
| `command.queued` | **yes** | `requestId, command` |
| `command.completed` | **yes** | `requestId` |
| `exit_plan_mode.requested` | **yes** | `requestId, summary, planContent, actions, recommendedAction` |
| `exit_plan_mode.completed` | **yes** | `requestId` |

## Event helper pattern

```typescript
function getNextEventOfType<T extends SessionEventType>(
  session: CopilotSession,
  type: T,
): Promise<SessionEventPayload<T>> {
  return new Promise((resolve, reject) => {
    const unsub = session.on((event) => {
      if (event.type === type) {
        unsub();
        resolve(event as SessionEventPayload<T>);
      }
      if (event.type === "session.error") {
        unsub();
        reject(new Error(event.data.message));
      }
    });
  });
}
```

## session.shutdown event data

Rich session summary including usage metrics:

```typescript
session.on("session.shutdown", (event) => {
  const d = event.data;
  console.log(`Type: ${d.shutdownType}`);       // "routine" | "error"
  console.log(`Premium requests: ${d.totalPremiumRequests}`);
  console.log(`Code changes: +${d.codeChanges.linesAdded} -${d.codeChanges.linesRemoved}`);
  console.log(`Files modified: ${d.codeChanges.filesModified}`);
  // Per-model metrics:
  for (const [model, metrics] of Object.entries(d.modelMetrics)) {
    console.log(`${model}: ${metrics.requests.count} calls, ${metrics.usage.inputTokens} input tokens`);
  }
});
```
