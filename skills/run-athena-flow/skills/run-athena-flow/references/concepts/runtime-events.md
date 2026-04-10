# Runtime Events

The RuntimeEvent is Athena's core abstraction — every action from any harness is normalized into this format.

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

## RuntimeEventKind — All 28 Types

| Kind | Source | Can Block | Description |
|------|--------|-----------|-------------|
| `session.start` | Harness | No | New session begins |
| `session.end` | Harness | No | Session ends |
| `user.prompt` | Harness | No | User submits a prompt |
| `turn.start` | Harness | No | Agent turn begins |
| `turn.complete` | Harness | No | Agent turn completes |
| `message.delta` | Harness | No | Streaming message chunk |
| `message.complete` | Harness | No | Full message received |
| `plan.delta` | Harness | No | Plan/reasoning streaming chunk |
| `reasoning.delta` | Harness | No | Extended thinking chunk |
| `usage.update` | Harness | No | Token usage update |
| `tool.delta` | Harness | No | Streaming tool output chunk |
| `tool.pre` | Harness | Yes | Before tool invocation |
| `tool.post` | Harness | No | After successful tool result |
| `tool.failure` | Harness | No | After tool error |
| `permission.request` | Harness | Yes | Permission request from agent |
| `stop.request` | Harness | No | Agent stop signal |
| `subagent.start` | Harness | No | Subagent session starts |
| `subagent.stop` | Harness | No | Subagent session ends |
| `notification` | Harness | No | Informational notification |
| `compact.pre` | Harness | No | Before context compaction |
| `setup` | Harness | No | Session init/maintenance |
| `teammate.idle` | Harness | No | Teammate agent is idle |
| `task.completed` | Harness | No | Task completion event |
| `config.change` | Harness | No | Configuration changed |
| `unknown` | Harness | No | Unrecognized event type |

## Feed Event Kinds (Display Layer)

Runtime events are expanded into display events for the TUI:

`session.start`, `session.end`, `run.start`, `run.end`, `user.prompt`, `tool.delta`, `tool.pre`, `tool.post`, `tool.failure`, `permission.request`, `permission.decision`, `stop.request`, `stop.decision`, `subagent.start`, `subagent.stop`, `notification`, `compact.pre`, `setup`, `unknown.hook`, `todo.add`, `todo.update`, `todo.done`, `agent.message`, `teammate.idle`, `task.completed`, `config.change`

One runtime event can produce multiple feed events (e.g., a tool.post that includes a TodoWrite triggers both `tool.post` and `todo.add` feed events).

## Event Data by Kind

### tool.pre

```json
{
  "tool_name": "Read",
  "tool_input": { "file_path": "/src/index.ts" }
}
```

### tool.post

```json
{
  "tool_name": "Read",
  "tool_result": "...",
  "duration_ms": 42
}
```

### permission.request

```json
{
  "tool_name": "Write",
  "tool_input": { "file_path": "/src/new-file.ts", "content": "..." },
  "scoped_permissions": ["Write to /src/"]
}
```

### agent.message

```json
{
  "content": "I've completed the implementation...",
  "role": "assistant"
}
```

## Interaction Model

Events with `interaction.expectsDecision: true` pause the event stream until a `RuntimeDecision` is sent back. The auto-passthrough timeouts are:

- **Tool events:** 5 seconds
- **Permission/question events:** 5 minutes

If Athena doesn't respond in time, the hook forwarder exits with code `0` (allow).
