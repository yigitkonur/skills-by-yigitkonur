# Event Types Reference

## Import Patterns

```typescript
import type {
  SessionEvent,
  SessionEventType,
  SessionEventPayload,
  SessionEventHandler,
  TypedSessionEventHandler,
} from "@github/copilot-sdk";
```

---

## `SessionEvent` Union Type

`SessionEvent` is a discriminated union of 46 core event shapes (defined in `session-events.ts`), plus 13 broadcast event types handled by the SDK's internal broadcast dispatcher. Every variant shares these base fields:

```typescript
// Common fields on every event variant:
{
  id: string;           // UUID v4, unique per event
  timestamp: string;    // ISO 8601
  parentId: string | null;  // ID of preceding event (null for first event)
  ephemeral?: boolean;  // true = not persisted to disk; some variants have ephemeral: true (literal)
  type: string;         // Discriminant field
  data: object;         // Event-specific payload
}
```

---

## All 59 Event Variants

### Session Lifecycle Events

| `type` | `ephemeral` | Key `data` fields |
|--------|-------------|-------------------|
| `session.start` | optional | `sessionId`, `version`, `producer`, `copilotVersion`, `startTime`, `selectedModel?`, `context?{cwd,gitRoot?,repository?,branch?}` |
| `session.resume` | optional | `resumeTime`, `eventCount`, `context?` |
| `session.error` | optional | `errorType`, `message`, `stack?`, `statusCode?`, `providerCallId?` |
| `session.idle` | `true` | `{}` (empty data object) |
| `session.title_changed` | `true` | `title` |
| `session.info` | optional | `infoType`, `message` |
| `session.warning` | optional | `warningType`, `message` |
| `session.model_change` | optional | `previousModel?`, `newModel` |
| `session.mode_changed` | optional | `previousMode`, `newMode` |
| `session.plan_changed` | optional | `operation: "create" \| "update" \| "delete"` |
| `session.workspace_file_changed` | optional | `path`, `operation: "create" \| "update"` |
| `session.handoff` | optional | `handoffTime`, `sourceType: "remote" \| "local"`, `repository?{owner,name,branch?}`, `context?`, `summary?`, `remoteSessionId?` |
| `session.truncation` | optional | `tokenLimit`, `preTruncationTokensInMessages`, `preTruncationMessagesLength`, `postTruncationTokensInMessages`, `postTruncationMessagesLength`, `tokensRemovedDuringTruncation`, `messagesRemovedDuringTruncation`, `performedBy` |
| `session.snapshot_rewind` | `true` | `upToEventId`, `eventsRemoved` |
| `session.shutdown` | `true` | `shutdownType: "routine" \| "error"`, `errorReason?`, `totalPremiumRequests`, `totalApiDurationMs`, `sessionStartTime`, `codeChanges{linesAdded,linesRemoved,filesModified}`, `modelMetrics{[modelId]:{requests:{count,cost},usage:{inputTokens,outputTokens,cacheReadTokens,cacheWriteTokens}}}`, `currentModel?` |
| `session.context_changed` | optional | `cwd`, `gitRoot?`, `repository?`, `branch?` |
| `session.usage_info` | `true` | `tokenLimit`, `currentTokens`, `messagesLength` |
| `session.compaction_start` | optional | `{}` (empty) |
| `session.compaction_complete` | optional | `success`, `error?`, `preCompactionTokens?`, `postCompactionTokens?`, `preCompactionMessagesLength?`, `messagesRemoved?`, `tokensRemoved?`, `summaryContent?`, `checkpointNumber?`, `checkpointPath?`, `compactionTokensUsed?{input,output,cachedInput}`, `requestId?` |
| `session.task_complete` | optional | `summary?` |

### User Events

| `type` | `ephemeral` | Key `data` fields |
|--------|-------------|-------------------|
| `user.message` | optional | `content`, `transformedContent?`, `attachments?[]`, `source?`, `agentMode?`, `interactionId?` |
| `pending_messages.modified` | `true` | `{}` (empty) |

### Assistant Events

| `type` | `ephemeral` | Key `data` fields |
|--------|-------------|-------------------|
| `assistant.turn_start` | optional | `turnId`, `interactionId?` |
| `assistant.intent` | `true` | `intent` |
| `assistant.reasoning` | optional | `reasoningId`, `content` |
| `assistant.reasoning_delta` | `true` | `reasoningId`, `deltaContent` |
| `assistant.streaming_delta` | `true` | `totalResponseSizeBytes` |
| `assistant.message` | optional | `messageId`, `content`, `toolRequests?[{toolCallId,name,arguments?,type?}]`, `reasoningOpaque?`, `reasoningText?`, `encryptedContent?`, `phase?`, `interactionId?`, `parentToolCallId?` |
| `assistant.message_delta` | `true` | `messageId`, `deltaContent`, `parentToolCallId?` |
| `assistant.turn_end` | optional | `turnId` |
| `assistant.usage` | `true` | `model`, `inputTokens?`, `outputTokens?`, `cacheReadTokens?`, `cacheWriteTokens?`, `cost?`, `duration?`, `initiator?`, `apiCallId?`, `providerCallId?`, `parentToolCallId?`, `quotaSnapshots?`, `copilotUsage?` |

### Tool Events

| `type` | `ephemeral` | Key `data` fields |
|--------|-------------|-------------------|
| `abort` | optional | `reason` |
| `tool.user_requested` | optional | `toolCallId`, `toolName`, `arguments?` |
| `tool.execution_start` | optional | `toolCallId`, `toolName`, `arguments?`, `mcpServerName?`, `mcpToolName?`, `parentToolCallId?` |
| `tool.execution_partial_result` | `true` | `toolCallId`, `partialOutput` |
| `tool.execution_progress` | `true` | `toolCallId`, `progressMessage` |
| `tool.execution_complete` | optional | `toolCallId`, `success`, `model?`, `interactionId?`, `isUserRequested?`, `result?{content,detailedContent?,contents?[]}`, `error?{message,code?}`, `toolTelemetry?`, `parentToolCallId?` |

### Skill Events

| `type` | `ephemeral` | Key `data` fields |
|--------|-------------|-------------------|
| `skill.invoked` | optional | `name`, `path`, `content`, `allowedTools?`, `pluginName?`, `pluginVersion?` |

### Subagent Events

| `type` | `ephemeral` | Key `data` fields |
|--------|-------------|-------------------|
| `subagent.started` | optional | `toolCallId`, `agentName`, `agentDisplayName`, `agentDescription` |
| `subagent.completed` | optional | `toolCallId`, `agentName`, `agentDisplayName` |
| `subagent.failed` | optional | `toolCallId`, `agentName`, `agentDisplayName`, `error` |
| `subagent.selected` | optional | `agentName`, `agentDisplayName`, `tools: string[] \| null` |
| `subagent.deselected` | optional | `{}` (empty) |

### Hook Events

| `type` | `ephemeral` | Key `data` fields |
|--------|-------------|-------------------|
| `hook.start` | optional | `hookInvocationId`, `hookType`, `input?` |
| `hook.end` | optional | `hookInvocationId`, `hookType`, `output?`, `success`, `error?{message,stack?}` |

### System Events

| `type` | `ephemeral` | Key `data` fields |
|--------|-------------|-------------------|
| `system.message` | optional | `content`, `role: "system" \| "developer"`, `name?`, `metadata?{promptVersion?,variables?}` |
| `system.notification` | optional | `content`, `kind: {type:"agent_completed",agentId,agentType,status,description?,prompt?} \| {type:"shell_completed",shellId,exitCode?,description?} \| {type:"shell_detached_completed",shellId,description?}` |

### Permission Events

| `type` | `ephemeral` | Key `data` fields |
|--------|-------------|-------------------|
| `permission.requested` | `true` | `requestId`, `permissionRequest` (discriminated by `kind`: `"shell"`, `"write"`, `"read"`, `"mcp"`, `"url"`, `"memory"`, `"custom-tool"`) |
| `permission.completed` | `true` | `requestId`, `result{kind: "approved" \| "denied-*"}` |

### User Input Events

| `type` | `ephemeral` | Key `data` fields |
|--------|-------------|-------------------|
| `user_input.requested` | `true` | `requestId`, `question`, `choices?`, `allowFreeform?` |
| `user_input.completed` | `true` | `requestId` |

### Elicitation Events

| `type` | `ephemeral` | Key `data` fields |
|--------|-------------|-------------------|
| `elicitation.requested` | `true` | `requestId`, `message`, `mode?`, `requestedSchema{type:"object",properties,required?}` |
| `elicitation.completed` | `true` | `requestId` |

### External Tool Events

| `type` | `ephemeral` | Key `data` fields |
|--------|-------------|-------------------|
| `external_tool.requested` | `true` | `requestId`, `sessionId`, `toolCallId`, `toolName`, `arguments?` |
| `external_tool.completed` | `true` | `requestId` |

### Command Events

| `type` | `ephemeral` | Key `data` fields |
|--------|-------------|-------------------|
| `command.queued` | `true` | `requestId`, `command` |
| `command.completed` | `true` | `requestId` |

### Plan Mode Events

| `type` | `ephemeral` | Key `data` fields |
|--------|-------------|-------------------|
| `exit_plan_mode.requested` | `true` | `requestId`, `summary`, `planContent`, `actions`, `recommendedAction` |
| `exit_plan_mode.completed` | `true` | `requestId` |

---

## Event Type Inference

```typescript
// Get the union of all event type strings
type SessionEventType = SessionEvent["type"];

// Narrow to a specific event shape
type SessionEventPayload<T extends SessionEventType> = Extract<SessionEvent, { type: T }>;

// Examples:
type AssistantMessage = SessionEventPayload<"assistant.message">;
// { id: string; timestamp: string; parentId: string|null; type: "assistant.message"; data: { messageId: string; content: string; toolRequests?: ...; ... } }

type ToolStart = SessionEventPayload<"tool.execution_start">;
// data: { toolCallId: string; toolName: string; arguments?: ...; mcpServerName?: ...; }
```

---

## Subscription Patterns

```typescript
// Subscribe to all events
const unsub = session.on((event: SessionEvent) => {
  console.log(event.type, event.data);
});
unsub(); // returns void unsubscribe function

// Subscribe to a specific type (event is narrowed automatically)
const unsub2 = session.on("assistant.message_delta", (event) => {
  // event.data.deltaContent is typed as string
  process.stdout.write(event.data.deltaContent);
});

// Accumulate streaming message
let fullContent = "";
session.on("assistant.message_delta", (e) => { fullContent += e.data.deltaContent; });
session.on("assistant.message", (e) => { /* e.data.content is the complete text */ });

// React to tool execution
session.on("tool.execution_start", (e) => {
  console.log(`[${e.data.toolCallId}] Starting: ${e.data.toolName}`);
});
session.on("tool.execution_complete", (e) => {
  console.log(`[${e.data.toolCallId}] Success: ${e.data.success}`);
});

// Detect session idle (agent has no more pending work)
await session.waitForIdle();
// Or manually:
await new Promise<void>((resolve) => {
  const unsub = session.on("session.idle", () => { unsub(); resolve(); });
});
```

---

## Ephemeral vs. Persisted Events

Ephemeral events (`ephemeral: true`) are transient and not written to the session event log on disk. Do not rely on them being available after a session resume. Non-ephemeral events form the durable history.

Key ephemeral events: `session.idle`, `session.title_changed`, `session.snapshot_rewind`, `session.usage_info`, `assistant.intent`, `assistant.reasoning_delta`, `assistant.streaming_delta`, `assistant.message_delta`, `assistant.usage`, `tool.execution_partial_result`, `tool.execution_progress`, `permission.requested`, `permission.completed`, `user_input.requested`, `user_input.completed`, `elicitation.*`, `external_tool.*`, `command.*`, `exit_plan_mode.*`, `pending_messages.modified`.
