# Hook Event Reference

## Wire Protocol

```
Claude Code → stdin JSON → athena-hook-forwarder → UDS NDJSON → Athena runtime
```

The forwarder reads the hook event from stdin, writes it as a single NDJSON line to the Unix Domain Socket, and exits. For blocking events, the forwarder waits for a response before exiting.

Exit code `0` = passthrough. Exit code `2` = block.

Auto-passthrough timeout: 5 seconds default, 5 minutes for permission/question events.

## Event Envelope

```typescript
type RuntimeEvent = {
  id: string;
  timestamp: number;
  kind: RuntimeEventKind;
  data: object;
  sessionId: string;
  context: object;
  interaction: { expectsDecision: boolean };
};
```

## Hook Event Envelope (Wire Format)

```typescript
type HookEventEnvelope = {
  hookName: string;
  sessionId: string;
  data: object;
  timestamp: number;
};

type HookResultEnvelope = {
  eventId: string;
  result: HookResultPayload;
};
```

## Tool Events

Require a `"*"` matcher to receive all tool calls.

### `PreToolUse`

| Field | Value |
|-------|-------|
| When | Before Claude invokes a tool |
| RuntimeEventKind | `tool.pre` |
| Can block | Yes |
| Blocking response | `passthrough`, `block` (with reason), or `json` (structured) |

### `PostToolUse`

| Field | Value |
|-------|-------|
| When | After a tool completes and returns its result |
| RuntimeEventKind | `tool.post` |
| Can block | No |

### `PostToolUseFailure`

| Field | Value |
|-------|-------|
| When | After a tool invocation results in an error |
| RuntimeEventKind | `tool.failure` |
| Can block | No |

### `PermissionRequest`

| Field | Value |
|-------|-------|
| When | Claude Code requests explicit permission for a tool |
| RuntimeEventKind | `permission.request` |
| Can block | Yes |
| Blocking response | `passthrough` (allow) or `block` (deny) |

## Non-Tool Events

### `SessionStart`
- When: New Claude Code session begins
- RuntimeEventKind: `session.start`

### `SessionEnd`
- When: Claude Code session ends
- RuntimeEventKind: `session.end`

### `UserPromptSubmit`
- When: User submits a prompt
- RuntimeEventKind: `user.prompt`

### `Stop`
- When: Claude Code's stop hook fires
- RuntimeEventKind: `stop.request`

### `SubagentStart`
- When: A subagent session starts
- RuntimeEventKind: `subagent.start`

### `SubagentStop`
- When: A subagent session ends
- RuntimeEventKind: `subagent.stop`

### `Notification`
- When: Informational notification from Claude Code
- RuntimeEventKind: `notification`

### `PreCompact`
- When: Before context compaction occurs
- RuntimeEventKind: `compact.pre`

### `Setup`
- When: Session init or maintenance
- RuntimeEventKind: `setup`

### `TeammateIdle`
- When: A teammate agent is idle
- RuntimeEventKind: `teammate.idle`

### `TaskCompleted`
- When: A task is marked complete
- RuntimeEventKind: `task.completed`

### `ConfigChange`
- When: Configuration changes during session
- RuntimeEventKind: `config.change`

### `InstructionsLoaded`
- When: Instructions (CLAUDE.md etc.) are loaded
- RuntimeEventKind: mapped to `setup`

### `WorktreeCreate` / `WorktreeRemove`
- When: Git worktree operations
- RuntimeEventKind: mapped to `notification`

## Feed Event Kinds (Display Layer)

Runtime events are expanded into these display events:

`session.start`, `session.end`, `run.start`, `run.end`, `user.prompt`, `tool.delta`, `tool.pre`, `tool.post`, `tool.failure`, `permission.request`, `permission.decision`, `stop.request`, `stop.decision`, `subagent.start`, `subagent.stop`, `notification`, `compact.pre`, `setup`, `unknown.hook`, `todo.add`, `todo.update`, `todo.done`, `agent.message`, `teammate.idle`, `task.completed`, `config.change`

## Interaction Rules per Event Kind

| Event Kind | Expects Decision | Timeout | Can Block |
|------------|-----------------|---------|-----------|
| `tool.pre` | Yes | 5s | Yes |
| `permission.request` | Yes | 5min | Yes |
| `tool.post` | No | — | No |
| `tool.failure` | No | — | No |
| `session.start` | No | — | No |
| `session.end` | No | — | No |
| `user.prompt` | No | — | No |
| `stop.request` | No | — | No |
| All others | No | — | No |
