# Tool Reference

Complete parameter reference for all 5 mcp-codex-worker tools.

## spawn-task

Create and start a provider-agnostic task. Returns immediately with a task_id.

### Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `prompt` | string | Yes | — | What the task should do. Be specific. |
| `cwd` | string | No | server cwd | Working directory for the agent |
| `task_type` | enum | No | `coder` | `coder`, `planner`, `tester`, `researcher`, `general` |
| `provider` | enum | No | auto-routed | `codex`, `copilot`, `claude-cli` |
| `model` | string | No | provider default | Model override |
| `timeout_ms` | integer | No | provider default | 1,000–3,600,000 ms |
| `developer_instructions` | string | No | — | System-level constraints before user prompt |
| `labels` | string[] | No | — | Arbitrary labels for filtering |
| `depends_on` | string[] | No | — | Task IDs that must complete first |
| `keep_alive` | number | No | — | Result retention period in ms |
| `context_files` | array | No | — | Files to include: `[{ path, description? }]` |

### Response shape

```json
{
  "task_id": "bold-falcon-42",
  "status": "working",
  "poll_frequency": 5000,
  "provider_session_id": "019d728c-a9bc-...",
  "resources": {
    "scoreboard": "task:///all",
    "detail": "task:///bold-falcon-42",
    "log": "task:///bold-falcon-42/log"
  }
}
```

### Writing effective prompts

Good: "Create `src/utils/slugify.ts` exporting `slugify(text: string): string`. Handle Unicode via `normalize('NFKD')`. Collapse consecutive hyphens. Trim leading/trailing hyphens. Add tests in `src/utils/slugify.test.ts` using vitest."

Bad: "Write a slugify function."

---

## wait-task

Block until a task reaches terminal state or input_required.

### Parameters

| Parameter | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `task_id` | string | Yes | — | Non-empty |
| `timeout_ms` | integer | No | 30,000 | 1–300,000 ms |
| `poll_interval_ms` | integer | No | 1,000 | 250–30,000 ms |

### Response shape

```json
{
  "task_id": "bold-falcon-42",
  "status": "completed",
  "provider_session_id": "019d728c-a9bc-...",
  "output": ["last", "few", "lines"]
}
```

When `status` is `input_required`:
```json
{
  "task_id": "bold-falcon-42",
  "status": "input_required",
  "provider_session_id": "019d728c-a9bc-...",
  "pending_question": {
    "type": "command_approval",
    "requestId": "req-7",
    "command": "npm install express",
    "sandboxPolicy": "workspaceWrite"
  }
}
```

### Timeout behavior

When timeout elapses without a terminal/input_required state, wait-task returns the current status. The task keeps running. Call wait-task again to resume waiting, or cancel-task to abort.

---

## respond-task

Respond to a paused task. The `type` field determines which additional fields are required.

### Parameters (common)

| Parameter | Type | Required | Description |
|---|---|---|---|
| `task_id` | string | Yes | ID of the paused task |
| `type` | enum | Yes | Must match `pending_question.type` from wait-task |

### Parameters by type

**user_input:**
| Parameter | Type | Description |
|---|---|---|
| `answers` | object | Map of question ID → answer string |

**command_approval:**
| Parameter | Type | Description |
|---|---|---|
| `decision` | `accept` or `reject` | Whether to allow the command |

**file_approval:**
| Parameter | Type | Description |
|---|---|---|
| `decision` | `accept` or `reject` | Whether to allow file changes |

**elicitation:**
| Parameter | Type | Description |
|---|---|---|
| `action` | `accept` or `decline` | Whether to confirm |
| `content` | object | Optional structured payload |

**dynamic_tool:**
| Parameter | Type | Description |
|---|---|---|
| `result` | string | Tool result if successful |
| `error` | string | Error message if tool failed |

---

## message-task

Send a follow-up message to an existing task.

### Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `task_id` | string | Yes | ID of the active task |
| `message` | string | Yes | Follow-up instruction |
| `model` | string | No | Override model for this turn |

### Constraints

- Only works on **active** (non-terminal) tasks
- Terminal tasks (completed, failed, cancelled) reject messages — spawn a new task in the same `cwd` instead

---

## cancel-task

Cancel one or more tasks.

### Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `task_id` | string or string[] | Yes | Single ID or array for batch cancel |

### Response shape

```json
{
  "cancelled": ["task-1", "task-2"],
  "already_terminal": ["task-3"],
  "not_found": ["bogus-id"]
}
```

- `cancelled` — actively running tasks that were interrupted
- `already_terminal` — tasks already in a final state (no-op)
- `not_found` — unknown task IDs
