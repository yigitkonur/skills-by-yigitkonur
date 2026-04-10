# Tool Reference

Complete parameter and response schemas for all 5 mcp-codex-worker tools.

## spawn-task

Create and start a provider-agnostic task. Returns immediately with a task_id.

### Parameters (11 total)

| Parameter | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `prompt` | string | **Yes** | — | `minLength: 1`. Name files, symbols, expected outcome, and what NOT to touch. |
| `cwd` | string | No | server process cwd | Absolute path. Agent sees files relative to this. |
| `task_type` | enum | No | `coder` | `coder` \| `planner` \| `tester` \| `researcher` \| `general` |
| `reasoning` | enum | No | `gpt-5.4(medium)` | `gpt-5.4(low)` \| `gpt-5.4(medium)` \| `gpt-5.4(high)` \| `gpt-5.4(xhigh)` |
| `provider` | enum | No | auto-routed by task_type | `codex` \| `copilot` \| `claude-cli`. Leave unset in almost all cases. |
| `timeout_ms` | integer | No | provider default | Min `1000`, max `3600000` (1 hour). Task marked `timed_out` if exceeded. |
| `developer_instructions` | string | No | — | System-level constraints injected ahead of user prompt. |
| `labels` | string[] | No | — | Free-form tags for filtering and grouping on the scoreboard. |
| `depends_on` | string[] | No | — | Task IDs that must complete before this task starts. |
| `keep_alive` | number | No | — | Retention window (ms) — how long the server keeps the completed result. |
| `context_files` | array of `{path, description?}` | No | — | Files to prepend as context. `path` is required (absolute), `description` is optional. |

### Response shape

```json
{
  "task_id": "bold-falcon-42",
  "status": "working",
  "poll_frequency": 5000,
  "disk_paths": {
    "dir": "~/.mcp-codex-worker/tasks/bold-falcon-42",
    "events_log": "~/.mcp-codex-worker/tasks/bold-falcon-42/events.jsonl",
    "timeline_log": "~/.mcp-codex-worker/tasks/bold-falcon-42/timeline.log",
    "meta": "~/.mcp-codex-worker/tasks/bold-falcon-42/meta.json"
  },
  "labels": ["wave-1", "auth"],
  "provider_session_id": "019d728c-a9bc-7e12-8c40-9a68b6640c8e",
  "resources": {
    "scoreboard": "task:///all",
    "detail": "task:///bold-falcon-42",
    "log": "task:///bold-falcon-42/log"
  }
}
```

Key fields: `task_id` is the handle for all subsequent calls. `disk_paths.timeline_log` is the path to `tail -f` via Monitor.

---

## wait-task

Block until a task reaches terminal state or `input_required`.

### Parameters

| Parameter | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `task_id` | string | **Yes** | — | `minLength: 1` |
| `timeout_ms` | integer | No | `30000` | `exclusiveMinimum: 0`, max `300000` (5 minutes) |
| `poll_interval_ms` | integer | No | `1000` | Min `250`, max `30000` |

### Response shape

```json
{
  "task_id": "bold-falcon-42",
  "status": "completed",              // or "failed", "input_required", "working", "cancelled"
  "provider_session_id": "019d728c-a9bc-...",
  "output": ["[10:24:10] cmd: ...", "[10:24:27] agent: ...", "[10:24:27] turn completed"],
  "token_usage": { "totalTokens": 109621, "inputTokens": 108526, "outputTokens": 1095, "contextWindow": 996147 },
  "pct_used": "11.0%",
  "pending_question": null            // populated when status is "input_required"
}
```

When `status` is `input_required`, `pending_question` contains `{type, requestId, ...}` — see pause-flow-handling.md.

When `timeout_ms` elapses without a terminal state, returns current status (e.g. `"working"`). Task keeps running. Call wait-task again or cancel-task.

---

## respond-task

Unblock a task that is in `input_required`. Payload is discriminated by `type` which must match `pending_question.type` from wait-task.

### Common parameters

| Parameter | Type | Required |
|---|---|---|
| `task_id` | string | **Yes** |
| `type` | enum | **Yes** — must match `pending_question.type` |

### Payload by type

| type | Additional fields | Example payload |
|---|---|---|
| `user_input` | `answers`: `{questionId: "answer"}` | `{task_id, type: "user_input", answers: {"db_choice": "PostgreSQL"}}` |
| `command_approval` | `decision`: `"accept"` or `"reject"` | `{task_id, type: "command_approval", decision: "accept"}` |
| `file_approval` | `decision`: `"accept"` or `"reject"` | `{task_id, type: "file_approval", decision: "accept"}` |
| `elicitation` | `action`: `"accept"` or `"decline"`, optional `content`: object | `{task_id, type: "elicitation", action: "accept"}` |
| `dynamic_tool` | `result`: string (success) OR `error`: string (failure) | `{task_id, type: "dynamic_tool", result: "Passed."}` |

See `pause-flow-handling.md` for full request/response JSON for each type.

---

## message-task

Send a follow-up message to an existing task on its original session.

### Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `task_id` | string | **Yes** | `minLength: 1`. Must be an active (non-terminal) task. |
| `message` | string | **Yes** | `minLength: 1`. The follow-up instruction. Be as specific as the original prompt. |
| `reasoning` | enum | No | Override reasoning for this follow-up turn only. Same 4 enum values as spawn-task. |

### Constraints

- Only works on **active** tasks (status = `working` or `input_required`)
- Terminal tasks (`completed`, `failed`, `cancelled`, `timed_out`) reject messages
- For terminal tasks, spawn a new task in the same `cwd` instead
- After calling, follow up with `wait-task` exactly like after `spawn-task`

---

## cancel-task

Cancel one or more running tasks.

### Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `task_id` | string or string[] | **Yes** | Single ID (`minLength: 1`) or array (`minItems: 1`, each `minLength: 1`). |

### Response shape

```json
{
  "cancelled": ["task-1", "task-2"],
  "already_terminal": ["task-3"],
  "not_found": ["bogus-id"]
}
```

Three categories:
- `cancelled` — tasks that were actively running and are now aborted
- `already_terminal` — tasks already in a final state (completed/failed/cancelled) — no-op
- `not_found` — unknown task IDs
