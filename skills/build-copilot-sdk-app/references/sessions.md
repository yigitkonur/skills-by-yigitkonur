# Sessions

## Create a session

```typescript
const session: CopilotSession = await client.createSession(config: SessionConfig);
```

### SessionConfig (all fields)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `onPermissionRequest` | `PermissionHandler` | **YES** | — | Permission handler (no default) |
| `sessionId` | `string` | no | UUID | Custom session ID for persistence |
| `clientName` | `string` | no | — | Included in User-Agent header |
| `model` | `string` | no | — | Model ID (e.g. `"gpt-4.1"`, `"gpt-5"`) |
| `reasoningEffort` | `ReasoningEffort` | no | — | `"low"\|"medium"\|"high"\|"xhigh"` |
| `configDir` | `string` | no | — | Override config directory |
| `tools` | `Tool<any>[]` | no | `[]` | Custom tools |
| `systemMessage` | `SystemMessageConfig` | no | — | System prompt config |
| `availableTools` | `string[]` | no | — | Tool allowlist (overrides `excludedTools`) |
| `excludedTools` | `string[]` | no | — | Tool blocklist |
| `provider` | `ProviderConfig` | no | — | BYOK provider |
| `onUserInputRequest` | `UserInputHandler` | no | — | Handler for `ask_user` tool |
| `hooks` | `SessionHooks` | no | — | Lifecycle hooks |
| `workingDirectory` | `string` | no | — | Session working directory |
| `streaming` | `boolean` | no | `false` | Enable streaming events |
| `mcpServers` | `Record<string, MCPServerConfig>` | no | — | MCP servers |
| `customAgents` | `CustomAgentConfig[]` | no | — | Custom agents |
| `agent` | `string` | no | — | Agent to activate at start |
| `skillDirectories` | `string[]` | no | — | Skill directories to load |
| `disabledSkills` | `string[]` | no | — | Skills to disable |
| `infiniteSessions` | `InfiniteSessionConfig` | no | — | Auto-compaction config |
| `onEvent` | `SessionEventHandler` | no | — | Early event handler (registered before `session.create` RPC) |

## Resume a session

```typescript
const session = await client.resumeSession(sessionId: string, config: ResumeSessionConfig);
```

`ResumeSessionConfig` includes all fields from `SessionConfig` except `sessionId`, plus:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `disableResume` | `boolean` | `false` | Skip emitting `session.resume` event |

```typescript
// Resume with new settings
const session = await client.resumeSession("user-123", {
  onPermissionRequest: approveAll,
  streaming: true,    // can change streaming on resume
  tools: [newTool],   // can add new tools
});
```

## Sending messages

### sendAndWait (blocking)

```typescript
const response: AssistantMessageEvent | undefined = await session.sendAndWait(
  options: MessageOptions,
  timeout?: number, // default 60_000ms
);
```

Waits for `session.idle` event. Rejects on `session.error`. Returns the last `assistant.message` event or `undefined`.

### send (fire-and-forget)

```typescript
const messageId: string = await session.send(options: MessageOptions);
```

Returns immediately. Events arrive via `session.on()`.

### MessageOptions

```typescript
interface MessageOptions {
  prompt: string;
  attachments?: Array<
    | { type: "file"; path: string; displayName?: string }
    | { type: "directory"; path: string; displayName?: string }
    | { type: "selection"; filePath: string; displayName: string;
        selection?: { start: { line: number; character: number };
                      end: { line: number; character: number } };
        text?: string }
  >;
  mode?: "enqueue" | "immediate"; // default "enqueue"
}
```

## Session lifecycle

### disconnect()

```typescript
await session.disconnect();
```

Sends `session.destroy` RPC. Clears handlers. **Session data on disk is preserved** for later resumption.

### abort()

```typescript
await session.abort();
```

Cancels in-flight work. Session remains usable for new messages. An `abort` event is added to history.

### setModel()

```typescript
await session.setModel("gpt-5");
```

Switches model mid-session. Takes effect on next message.

### log()

```typescript
await session.log("Processing...", {
  level: "info",      // "info" | "warning" | "error"
  ephemeral: true,    // not persisted to disk
});
```

### getMessages()

```typescript
const messages: SessionEvent[] = await session.getMessages();
```

Returns full conversation history.

### Symbol.asyncDispose

```typescript
await using session = await client.createSession({ ... });
// session.disconnect() called automatically when scope exits
```

## Session persistence

Sessions are persisted to disk at `~/.copilot/session-state/{sessionId}/`.

```typescript
// 1. Create with stable ID
const session = await client.createSession({
  sessionId: "project-alpha",
  onPermissionRequest: approveAll,
});
await session.sendAndWait({ prompt: "Analyze the codebase" });
await session.disconnect(); // data stays on disk

// 2. Resume (same or different process/client)
const resumed = await client.resumeSession("project-alpha", {
  onPermissionRequest: approveAll,
});
// Full context restored — model remembers previous conversation

// 3. List and clean up
const sessions = await client.listSessions();
await client.deleteSession("project-alpha"); // removes from disk
```

### SessionMetadata

```typescript
interface SessionMetadata {
  sessionId: string;
  startTime: Date;
  modifiedTime: Date;
  summary?: string;
  isRemote: boolean;
  context?: SessionContext;
}

interface SessionContext {
  cwd: string;
  gitRoot?: string;
  repository?: string; // "owner/repo"
  branch?: string;
}
```

## Infinite sessions and compaction

Keep sessions running indefinitely with automatic context compaction.

```typescript
const session = await client.createSession({
  onPermissionRequest: approveAll,
  infiniteSessions: {
    enabled: true,                          // default true
    backgroundCompactionThreshold: 0.80,    // start compacting at 80% context usage
    bufferExhaustionThreshold: 0.95,        // block until compaction done at 95%
  },
});
```

### InfiniteSessionConfig

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | `boolean` | `true` | Enable infinite sessions |
| `backgroundCompactionThreshold` | `number` | `0.80` | Start background compaction at this context usage % |
| `bufferExhaustionThreshold` | `number` | `0.95` | Block new messages until compaction done at this % |

### Compaction events

```typescript
session.on("session.compaction_start", () => {
  console.log("Compacting...");
});

session.on("session.compaction_complete", (event) => {
  console.log(`Removed ${event.data.tokensRemoved} tokens`);
  console.log(`Success: ${event.data.success}`);
  console.log(`Checkpoint: ${event.data.checkpointPath}`);
});
```

### Manual compaction

```typescript
const result = await session.rpc.compaction.compact();
// { success, tokensRemoved, messagesRemoved }
```

### Workspace path

When infinite sessions are enabled, `session.workspacePath` returns a directory containing:
- `checkpoints/` — compaction checkpoint data
- `plan.md` — the session plan file
- `files/` — workspace files

## System message configuration

```typescript
// Append to Copilot's default system message (default):
systemMessage: {
  mode: "append",
  content: "Always respond in bullet points.",
}

// Replace entire system message (removes all SDK guardrails):
systemMessage: {
  mode: "replace",
  content: "You are a specialized code reviewer.",
}
```

### SystemMessageConfig

```typescript
type SystemMessageConfig =
  | { mode?: "append"; content?: string }      // append to default
  | { mode: "replace"; content: string };       // replace entirely
```
