# Event Types

Codex notifications written to `events.jsonl`. Each line is a JSON object with at least `t` (ISO timestamp) and `method` (event type). Most also have `params`.

## Event format

```json
{"t":"2026-04-10T17:24:03.487Z","method":"thread/status/changed","params":{...}}
```

## Categories

### Thread lifecycle (3 types)

| Method | Captured in timeline? | Description |
|---|---|---|
| `thread/status/changed` | STARTED (first active) | Thread status transition. `params.status.type`: `"active"`, `"completed"`, `"failed"`, etc. `params.status.activeFlags` array. |
| `thread/started` | — | Thread initialized. |
| `thread/closed` | — | Thread terminated. |

Example:
```json
{
  "t": "2026-04-10T17:24:03.487Z",
  "method": "thread/status/changed",
  "params": {
    "threadId": "019d786c-1915-...",
    "status": { "type": "active", "activeFlags": [] }
  }
}
```

### Turn lifecycle (3 types)

| Method | Captured in timeline? | Description |
|---|---|---|
| `turn/started` | TURN | New turn begins. Contains `turn.id`, `turn.items`, `turn.status`. |
| `turn/completed` | DONE | Turn finished. `turn.status`: `"completed"`, `"failed"`. `turn.error` if failed. |
| `turn/plan/updated` | PLAN | Agent's execution plan changed. Array of `{step, status}`. |

Example — turn/plan/updated:
```json
{
  "t": "2026-04-10T10:40:27.154Z",
  "method": "turn/plan/updated",
  "params": {
    "threadId": "019d76fa-330a-...",
    "turnId": "019d76fa-3314-...",
    "explanation": "I've read the governing AGENTS files...",
    "plan": [
      { "step": "Inspect gesture-related code...", "status": "inProgress" },
      { "step": "Implement NotchGestureRouter...", "status": "pending" },
      { "step": "Build, run tests, verify...", "status": "pending" }
    ]
  }
}
```

### Item lifecycle (2 core + type variants)

| Method | Captured in timeline? | Description |
|---|---|---|
| `item/started` | THINK (reasoning), CMD (commandExecution) | Item begins. `params.item.type` discriminates. |
| `item/completed` | THINK, CMD, FILE, MSG, MCP | Item finished. Same shape with exit codes, output, etc. |

Item types in `params.item.type`:
- `"reasoning"` — agent thinking. Has `summary` array and `content` array.
- `"commandExecution"` — shell command. Has `command`, `exitCode`, `durationMs`, `aggregatedOutput`.
- `"fileChange"` — file modification. Has file path and change kind.
- `"agentMessage"` — text message. Has `content` array with `{type: "text", text: "..."}`.
- `"userMessage"` — the original prompt or follow-up.
- `"mcpToolCall"` — MCP tool invocation.

Example — item/completed (commandExecution):
```json
{
  "t": "2026-04-10T17:24:10.022Z",
  "method": "item/completed",
  "params": {
    "item": {
      "type": "commandExecution",
      "id": "call_4psukQeFA5vGzh1fj6MsDBF8",
      "command": "/bin/zsh -lc \"rtk find FastNotch -name '*.swift'\"",
      "cwd": "/Users/yigitkonur/dev/fast-notch",
      "processId": "59005",
      "source": "unifiedExecStartup",
      "status": "completed",
      "aggregatedOutput": "0 for 'FastNotch'...",
      "exitCode": 0,
      "durationMs": 0
    },
    "threadId": "019d786c-1915-...",
    "turnId": "019d786c-191e-..."
  }
}
```

### Delta events (5 types — filtered from timeline summary)

These are streaming increments. High volume. Not captured in the timeline, only in events.jsonl.

| Method | Description |
|---|---|
| `item/reasoning/summaryPartAdded` | New summary section started. Has `summaryIndex`. |
| `item/reasoning/summaryTextDelta` | Streaming text for reasoning summary. `params.delta` is the text chunk. |
| `item/agentMessage/delta` | Streaming agent message text. `params.delta`. |
| `item/commandExecution/outputDelta` | Streaming command stdout/stderr. `params.delta`. |
| `item/fileChange/outputDelta` | Streaming file change diff. `params.delta`. |

These are the bulk of events.jsonl by count. A single reasoning block can produce 50-100 `summaryTextDelta` events.

### Additional item events

| Method | Description |
|---|---|
| `item/plan/delta` | Streaming plan text. `params.delta`. |
| `item/commandExecution/terminalInteraction` | Terminal I/O event during command. |
| `turn/diff/updated` | Diff state changed. |

### Hook events (2 types — filtered from timeline)

| Method | Description |
|---|---|
| `hook/started` | Hook execution begins. Has `run.eventName`, `run.handlerType`, `run.sourcePath`. |
| `hook/completed` | Hook finished. Same shape with `durationMs`. |

Common hook events: `sessionStart`, `userPromptSubmit`. These run custom user hooks (e.g. from `.codex/hooks.json`).

### Token usage (1 type)

| Method | Captured in timeline? | Description |
|---|---|---|
| `thread/tokenUsage/updated` | TOKENS | Token counts. Deduplicated in timeline. |

Key fields in `params.tokenUsage`: `total` (`totalTokens`, `inputTokens`, `cachedInputTokens`, `outputTokens`, `reasoningOutputTokens`), `last` (same shape for this turn only), `modelContextWindow` (e.g. 996147).

### Server request events (2 types)

| Method | Captured in timeline? | Description |
|---|---|---|
| `serverRequest/resolved` | — | Server request resolved (after auto-answer or manual respond). |
| `error` | — | Error event. Has `params.error.message`, `params.error.codexErrorInfo`, `params.willRetry`. |

### Synthetic events (5 types — injected by the daemon)

These are NOT from the Codex API. The daemon synthesizes them for diagnostics.

| Method | Captured in timeline? | Description |
|---|---|---|
| `_server_version` | VERSION | Server version. `version` field (e.g. `"1.0.29"`). |
| `_process_exit` | EXIT | Codex process terminated. `code`, `signal`, `stderr_tail`. |
| `_stderr` | STDERR | Process stderr output. `data` field (ANSI included in events, stripped in timeline). |
| `_server_request:item/tool/requestUserInput` | AUTO (via _auto_answer) | Agent requested user input. Full question payload. |
| `_auto_answer` | AUTO | Server auto-answered a question. `answers` map, `summary` string. |

### Synthetic turn event

| Method | Description |
|---|---|
| `turn/failed` (synthetic) | Emitted when a turn fails. May not appear in raw Codex events. |

## Summary

~16 of 25+ event types are captured in the timeline. The rest (deltas, hooks, diffs, terminal interactions) are in events.jsonl only. See `timeline-format.md` for the mapping.
