# Session Event Types — Complete SDK Reference

All 59 event types emitted by `@github/copilot-sdk` sessions. Use this reference when subscribing to events, building UIs, or tracing agent behavior.

---

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

## Core Event Infrastructure

### `SessionEvent`

Discriminated union of all session events (generated from `session-events.ts`). Every event shares these base fields:

```typescript
{
  id: string;                    // UUID v4, unique per event
  timestamp: string;             // ISO 8601 timestamp
  parentId: string | null;       // Links to parent event (causal chain); null for first
  ephemeral?: boolean;           // true = not persisted to disk
  type: string;                  // Discriminant — one of 59 event type strings
  data: object;                  // Event-specific payload (varies by type)
}
```

### Type Helpers

```typescript
// Union of all 59 event type strings
type SessionEventType = SessionEvent["type"];

// Extract payload shape for a specific event type
type SessionEventPayload<T extends SessionEventType> = Extract<SessionEvent, { type: T }>;

// Typed handler for one event type
type TypedSessionEventHandler<T extends SessionEventType> = (
  event: SessionEventPayload<T>
) => void;

// Handler for any event
type SessionEventHandler = (event: SessionEvent) => void;
```

---

## All 59 Event Types by Category

### Session Lifecycle (20 events)

| `type` | Ephemeral | Key `data` fields |
|--------|-----------|-------------------|
| `session.start` | No | `sessionId`, `version`, `producer`, `copilotVersion`, `startTime`, `selectedModel?`, `context?{cwd, gitRoot?, repository?, branch?}` |
| `session.resume` | No | `resumeTime`, `eventCount`, `context?` |
| `session.error` | No | `errorType`, `message`, `stack?`, `statusCode?`, `providerCallId?` |
| `session.idle` | **Yes** | `{}` — signals turn complete, no pending work |
| `session.shutdown` | **Yes** | `shutdownType: "routine"\|"error"`, `errorReason?`, `totalPremiumRequests`, `totalApiDurationMs`, `sessionStartTime`, `codeChanges{linesAdded, linesRemoved, filesModified}`, `modelMetrics`, `currentModel?` |
| `session.title_changed` | **Yes** | `title` |
| `session.info` | No | `infoType`, `message` |
| `session.warning` | No | `warningType`, `message` |
| `session.model_change` | No | `previousModel?`, `newModel` |
| `session.mode_changed` | No | `previousMode`, `newMode` |
| `session.plan_changed` | No | `operation: "create"\|"update"\|"delete"` |
| `session.workspace_file_changed` | No | `path`, `operation: "create"\|"update"` |
| `session.handoff` | No | `handoffTime`, `sourceType: "remote"\|"local"`, `repository?{owner, name, branch?}`, `context?`, `summary?`, `remoteSessionId?` |
| `session.truncation` | No | `tokenLimit`, `preTruncationTokensInMessages`, `preTruncationMessagesLength`, `postTruncationTokensInMessages`, `postTruncationMessagesLength`, `tokensRemovedDuringTruncation`, `messagesRemovedDuringTruncation`, `performedBy` |
| `session.snapshot_rewind` | **Yes** | `upToEventId`, `eventsRemoved` |
| `session.context_changed` | No | `cwd`, `gitRoot?`, `repository?`, `branch?` |
| `session.usage_info` | **Yes** | `tokenLimit`, `currentTokens`, `messagesLength` |
| `session.compaction_start` | No | `{}` — signals compaction beginning |
| `session.compaction_complete` | No | `success`, `error?`, `preCompactionTokens?`, `postCompactionTokens?`, `preCompactionMessagesLength?`, `messagesRemoved?`, `tokensRemoved?`, `summaryContent?`, `checkpointNumber?`, `checkpointPath?`, `compactionTokensUsed?{input, output, cachedInput}`, `requestId?` |
| `session.task_complete` | No | `summary?` |

### User Events (2 events)

| `type` | Ephemeral | Key `data` fields |
|--------|-----------|-------------------|
| `user.message` | No | `content`, `transformedContent?`, `attachments?[]`, `source?`, `agentMode?`, `interactionId?` |
| `pending_messages.modified` | **Yes** | `{}` — signals pending message queue changed |

**Attachment types** (4 variants in `user.message` data):

```typescript
type UserMessageAttachment =
  | { type: "file"; path: string; displayName: string; lineRange?: { start: number; end: number } }
  | { type: "directory"; path: string; displayName: string; lineRange?: { start: number; end: number } }
  | { type: "selection"; filePath: string; displayName: string; text: string;
      selection: { start: { line: number; character: number }; end: { line: number; character: number } } }
  | { type: "github_reference"; number: number; title: string;
      referenceType: "issue" | "pr" | "discussion"; state: string; url: string };
```

### Assistant Events (9 events)

| `type` | Ephemeral | Key `data` fields |
|--------|-----------|-------------------|
| `assistant.turn_start` | No | `turnId`, `interactionId?` |
| `assistant.intent` | **Yes** | `intent` — short description of current action |
| `assistant.reasoning` | No | `reasoningId`, `content` — full reasoning trace |
| `assistant.reasoning_delta` | **Yes** | `reasoningId`, `deltaContent` — streaming reasoning chunk |
| `assistant.streaming_delta` | **Yes** | `totalResponseSizeBytes` — byte-level streaming progress |
| `assistant.message` | No | `messageId`, `content`, `toolRequests?[{toolCallId, name, arguments?, type?}]`, `reasoningOpaque?`, `reasoningText?`, `encryptedContent?`, `phase?`, `interactionId?`, `parentToolCallId?` |
| `assistant.message_delta` | **Yes** | `messageId`, `deltaContent`, `parentToolCallId?` |
| `assistant.turn_end` | No | `turnId` |
| `assistant.usage` | **Yes** | `model`, `inputTokens?`, `outputTokens?`, `cacheReadTokens?`, `cacheWriteTokens?`, `cost?`, `duration?`, `initiator?`, `apiCallId?`, `providerCallId?`, `parentToolCallId?`, `quotaSnapshots?`, `copilotUsage?` |

### Tool Execution Events (6 events)

| `type` | Ephemeral | Key `data` fields |
|--------|-----------|-------------------|
| `abort` | No | `reason` — signals abort requested |
| `tool.user_requested` | No | `toolCallId`, `toolName`, `arguments?` |
| `tool.execution_start` | No | `toolCallId`, `toolName`, `arguments?`, `mcpServerName?`, `mcpToolName?`, `parentToolCallId?` |
| `tool.execution_partial_result` | **Yes** | `toolCallId`, `partialOutput` |
| `tool.execution_progress` | **Yes** | `toolCallId`, `progressMessage` |
| `tool.execution_complete` | No | `toolCallId`, `success`, `model?`, `interactionId?`, `isUserRequested?`, `result?{content, detailedContent?, contents?[]}`, `error?{message, code?}`, `toolTelemetry?`, `parentToolCallId?` |

**Tool result content blocks** (6 variants in `tool.execution_complete` `result.contents[]`):

```typescript
type ContentBlock =
  | { type: "text"; text: string }
  | { type: "terminal"; text: string; exitCode?: number; cwd?: string }
  | { type: "image"; data: string; mimeType: string }      // base64-encoded
  | { type: "audio"; data: string; mimeType: string }      // base64-encoded
  | { type: "resource_link"; name: string; uri: string; title?: string;
      description?: string; mimeType?: string; size?: number;
      icons?: { src: string; mimeType?: string; sizes?: string[]; theme?: "light" | "dark" }[] }
  | { type: "resource"; resource:
      | { uri: string; mimeType?: string; text: string }
      | { uri: string; mimeType?: string; blob: string } };  // base64-encoded
```

### Skill Events (1 event)

| `type` | Ephemeral | Key `data` fields |
|--------|-----------|-------------------|
| `skill.invoked` | No | `name`, `path`, `content`, `allowedTools?`, `pluginName?`, `pluginVersion?` |

### Sub-agent Events (5 events)

| `type` | Ephemeral | Key `data` fields |
|--------|-----------|-------------------|
| `subagent.started` | No | `toolCallId`, `agentName`, `agentDisplayName`, `agentDescription` |
| `subagent.completed` | No | `toolCallId`, `agentName`, `agentDisplayName` |
| `subagent.failed` | No | `toolCallId`, `agentName`, `agentDisplayName`, `error` |
| `subagent.selected` | No | `agentName`, `agentDisplayName`, `tools: string[] \| null` |
| `subagent.deselected` | No | `{}` — signals agent deselection |

### Hook Events (2 events)

| `type` | Ephemeral | Key `data` fields |
|--------|-----------|-------------------|
| `hook.start` | No | `hookInvocationId`, `hookType`, `input?` |
| `hook.end` | No | `hookInvocationId`, `hookType`, `output?`, `success`, `error?{message, stack?}` |

### System Events (2 events)

| `type` | Ephemeral | Key `data` fields |
|--------|-----------|-------------------|
| `system.message` | No | `content`, `role: "system"\|"developer"`, `name?`, `metadata?{promptVersion?, variables?}` |
| `system.notification` | No | `content`, `kind` (see notification kinds below) |

**Notification kinds** (3 variants in `system.notification` data):

```typescript
type NotificationKind =
  | { type: "agent_completed"; agentId: string; agentType: string;
      status: "completed" | "failed"; description?: string; prompt?: string }
  | { type: "shell_completed"; shellId: string; exitCode?: number; description?: string }
  | { type: "shell_detached_completed"; shellId: string; description?: string };
```

### Permission Events (2 events)

| `type` | Ephemeral | Key `data` fields |
|--------|-----------|-------------------|
| `permission.requested` | **Yes** | `requestId`, `permissionRequest` (discriminated by `kind`) |
| `permission.completed` | **Yes** | `requestId`, `result{kind}` |

**Permission request kinds** (7 variants):

```typescript
type PermissionRequest =
  | { kind: "shell"; toolCallId?; fullCommandText; intention; commands: {identifier, readOnly}[];
      possiblePaths; possibleUrls; hasWriteFileRedirection; canOfferSessionApproval; warning? }
  | { kind: "write"; toolCallId?; intention; fileName; diff; newFileContents? }
  | { kind: "read"; toolCallId?; intention; path }
  | { kind: "mcp"; toolCallId?; serverName; toolName; toolTitle; args?; readOnly }
  | { kind: "url"; toolCallId?; intention; url }
  | { kind: "memory"; toolCallId?; subject; fact; citations }
  | { kind: "custom-tool"; toolCallId?; toolName; toolDescription; args? };
```

**Permission result kinds** (5 outcomes):

```typescript
type PermissionResultKind =
  | "approved"
  | "denied-by-rules"
  | "denied-no-approval-rule-and-could-not-request-from-user"
  | "denied-interactively-by-user"
  | "denied-by-content-exclusion-policy";
```

### User Input Events (2 events)

| `type` | Ephemeral | Key `data` fields |
|--------|-----------|-------------------|
| `user_input.requested` | **Yes** | `requestId`, `question`, `choices?`, `allowFreeform?` |
| `user_input.completed` | **Yes** | `requestId` |

### Elicitation Events (2 events)

| `type` | Ephemeral | Key `data` fields |
|--------|-----------|-------------------|
| `elicitation.requested` | **Yes** | `requestId`, `message`, `mode?`, `requestedSchema{type:"object", properties, required?}` |
| `elicitation.completed` | **Yes** | `requestId` |

### External Tool Events (2 events)

| `type` | Ephemeral | Key `data` fields |
|--------|-----------|-------------------|
| `external_tool.requested` | **Yes** | `requestId`, `sessionId`, `toolCallId`, `toolName`, `arguments?` |
| `external_tool.completed` | **Yes** | `requestId` |

### Command Events (2 events)

| `type` | Ephemeral | Key `data` fields |
|--------|-----------|-------------------|
| `command.queued` | **Yes** | `requestId`, `command` |
| `command.completed` | **Yes** | `requestId` |

### Plan Mode Events (2 events)

| `type` | Ephemeral | Key `data` fields |
|--------|-----------|-------------------|
| `exit_plan_mode.requested` | **Yes** | `requestId`, `summary`, `planContent`, `actions`, `recommendedAction` |
| `exit_plan_mode.completed` | **Yes** | `requestId` |

---

## Ephemeral vs. Persisted Events

Events with `ephemeral: true` are transient — they drive real-time UI but are **not** written to the session event log on disk. They will not be available after `session.resume`.

**Ephemeral events (29):** `session.idle`, `session.title_changed`, `session.snapshot_rewind`, `session.usage_info`, `session.shutdown`, `assistant.intent`, `assistant.reasoning_delta`, `assistant.streaming_delta`, `assistant.message_delta`, `assistant.usage`, `pending_messages.modified`, `tool.execution_partial_result`, `tool.execution_progress`, `permission.requested`, `permission.completed`, `user_input.requested`, `user_input.completed`, `elicitation.requested`, `elicitation.completed`, `external_tool.requested`, `external_tool.completed`, `command.queued`, `command.completed`, `exit_plan_mode.requested`, `exit_plan_mode.completed`.

**Persisted events (30):** All others — these form the durable session history available via `getMessages()`.

---

## Usage Examples

### 1. Typed event subscription

```typescript
// Subscribe to a specific type — event is narrowed automatically
const unsub = session.on("assistant.message", (event) => {
  // event.data.content is typed as string
  console.log("Assistant:", event.data.content);
  if (event.data.toolRequests?.length) {
    console.log("Tool calls:", event.data.toolRequests.map((t) => t.name));
  }
});

// Unsubscribe when done
unsub();
```

### 2. Wildcard handler with switch/case

```typescript
session.on((event: SessionEvent) => {
  switch (event.type) {
    case "session.error":
      console.error(`Error [${event.data.errorType}]: ${event.data.message}`);
      break;
    case "tool.execution_start":
      console.log(`Running tool: ${event.data.toolName}`);
      break;
    case "tool.execution_complete":
      console.log(`Tool ${event.data.toolCallId}: ${event.data.success ? "ok" : "fail"}`);
      break;
    case "session.idle":
      console.log("Turn complete");
      break;
  }
});
```

### 3. Streaming delta aggregation

```typescript
let fullContent = "";

session.on("assistant.message_delta", (event) => {
  fullContent += event.data.deltaContent;
  process.stdout.write(event.data.deltaContent);
});

session.on("assistant.message", (event) => {
  // event.data.content has the complete text — use as source of truth
  fullContent = event.data.content;
});
```

### 4. Tool execution tracking with parentId chain

```typescript
session.on("tool.execution_start", (event) => {
  const parent = event.data.parentToolCallId;
  const prefix = parent ? `[sub-agent ${parent}]` : "[top-level]";
  console.log(`${prefix} Starting: ${event.data.toolName} (${event.data.toolCallId})`);
  if (event.data.mcpServerName) {
    console.log(`  MCP: ${event.data.mcpServerName}/${event.data.mcpToolName}`);
  }
});

session.on("tool.execution_complete", (event) => {
  const duration = event.data.toolTelemetry;
  console.log(`Completed: ${event.data.toolCallId} — success=${event.data.success}`);
  if (event.data.error) {
    console.error(`  Error: ${event.data.error.message}`);
  }
});
```

### 5. Waiting for idle

```typescript
// Preferred — built-in helper
await session.waitForIdle();

// Manual equivalent
await new Promise<void>((resolve) => {
  const unsub = session.on("session.idle", () => {
    unsub();
    resolve();
  });
});
```

---

## Important Caveats

1. **Register handlers before `send()`** — events fire immediately; late registration causes missed events.
2. **`session.idle` is your completion signal** — it fires when the agent has no pending work (no tool calls in flight, no messages queued).
3. **Ephemeral events are NOT in `getMessages()`** — do not rely on deltas or progress events for durable state.
4. **`assistant.message_delta` requires streaming** — only fires when the session has streaming enabled.
5. **`parentId` / `parentToolCallId` trace the causal chain** — essential for multi-agent and sub-agent flows. Use `parentToolCallId` on `tool.execution_start` and `assistant.message` to link sub-agent work back to the parent.
6. **Event handlers must be synchronous** — return `void`, not `Promise`. Do async work in a separate microtask.
7. **`assistant.usage` fires after each LLM call** — contains per-call token counts, cost, and quota snapshots. It is ephemeral and will not appear in resumed sessions.
8. **Permission kinds include `"memory"`** — 7 total: `shell`, `write`, `read`, `mcp`, `url`, `memory`, `custom-tool`.
9. **`session.shutdown` contains full session metrics** — code changes, model metrics, total cost. Use it for telemetry and billing.
