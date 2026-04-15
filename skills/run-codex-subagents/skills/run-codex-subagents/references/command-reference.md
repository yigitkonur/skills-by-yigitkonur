# Command Reference

Full public CLI surface for `codex-worker`. Run `codex-worker --help` or `codex-worker <command> --help` to verify any flag before using it.

## Global Options

Available on the top-level CLI:

- `--output text|json` — output format (default: text)

## Agent-Friendly Commands

These commands wrap thread/turn operations with ergonomic defaults for agent orchestration.

### `run`

One-shot task execution. Synchronous by default — blocks until the task completes.

```bash
codex-worker run <taskFile>
```

Flags:

| Flag | Type | Description |
|---|---|---|
| `--cwd <path>` | string | working directory |
| `--model <model>` | string | model override |
| `--async` | boolean | return immediately with ids |
| `--timeout <ms>` | number | wait timeout in milliseconds |
| `--follow` | boolean | stream events until completion |
| `--compact` | boolean | concise emoji-prefixed event output (requires `--follow`) |
| `--plan` | boolean | instruct agent to plan before implementing |
| `--skip-plan` | boolean | skip planning, implement directly |
| `--effort <level>` | string | reasoning effort: `low`, `medium`, `high` |
| `--label <text>` | string | label for tracking in multi-wave batches |
| `--session <id>` | string | continue an existing session/thread |

### `task start`

Start a file-backed task. Async by default — returns thread/session ids immediately.

```bash
codex-worker task start <taskFile>
```

Flags: same as `run`, plus:

| Flag | Type | Description |
|---|---|---|
| `--follow` | boolean | override async default: stream events until completion |
| `--compact` | boolean | concise output (with `--follow`) |

When `--follow` is set, the command blocks and streams events. Without it, it returns ids and exits.

### `task steer`

Send follow-up instructions to a completed/failed/interrupted task. Auto-resolves the latest turn id.

```bash
codex-worker task steer <threadId> <messageFile>
```

Flags:

| Flag | Type | Description |
|---|---|---|
| `--follow` | boolean | stream events |
| `--compact` | boolean | concise output (with `--follow`) |
| `--timeout <ms>` | number | wait timeout |

Use only after the prior task is terminal. Rejected while running or waiting_request.

### `task follow`

Stream normalized events from a running task until it reaches a terminal state.

```bash
codex-worker task follow <threadId>
```

Flags:

| Flag | Type | Description |
|---|---|---|
| `--compact` | boolean | concise emoji-prefixed output |
| `--tail <n>` | number | start from last N events |

### `task list`

List known tasks with optional filtering.

```bash
codex-worker task list
```

Flags:

| Flag | Type | Description |
|---|---|---|
| `--status <status>` | string | filter by status |
| `--quiet` | boolean | output thread ids only, one per line |
| `--limit <n>` | number | max results |

### `task read`

Read full task state: status, session, requests, artifacts, timeline/summary/stderr tails.

```bash
codex-worker task read <threadId>
```

Flags:

| Flag | Type | Description |
|---|---|---|
| `--tail <n>` | number | number of lines from log tails |
| `--field <path>` | string | extract single dotted-path field (e.g., `status`, `thread.model`) |

### `task events`

Read task event history.

```bash
codex-worker task events <threadId>
```

Flags:

| Flag | Type | Description |
|---|---|---|
| `--raw` | boolean | dump raw JSONL events from disk |
| `--tail <n>` | number | show only last N events |

### `task wait`

Block until the task reaches a terminal state or waiting_request.

```bash
codex-worker task wait <threadId>
```

Flags:

| Flag | Type | Description |
|---|---|---|
| `--timeout <ms>` | number | wait timeout |
| `--follow` | boolean | stream events while waiting |
| `--compact` | boolean | concise output (with `--follow`) |

### `task cancel`

Cancel the active turn of a running task. Auto-resolves the latest turn id.

```bash
codex-worker task cancel <threadId>
```

## Session Commands

### `session list`

List all sessions/threads.

```bash
codex-worker session list
```

Flags:

| Flag | Type | Description |
|---|---|---|
| `--limit <n>` | number | max results |

### `session read`

Read session details.

```bash
codex-worker session read <sessionId>
```

Flags:

| Flag | Type | Description |
|---|---|---|
| `--tail <n>` | number | number of lines from log tails |

## Request Commands

### `request list`

List pending requests.

```bash
codex-worker request list
```

Flags:

| Flag | Type | Description |
|---|---|---|
| `--status <status>` | string | filter by status (e.g., `pending`) |

### `request read`

Read a specific request's details.

```bash
codex-worker request read <requestId>
```

### `request answer`

Answer a blocked request. Alias for `request respond` with ergonomic additions.

```bash
codex-worker request answer <requestId>
```

Flags:

| Flag | Type | Description |
|---|---|---|
| `--decision <value>` | string | approval decision (e.g., `accept`, `reject`) |
| `--answer <text>` | string | free text answer |
| `--choice <N>` | number | 1-indexed choice from request options |
| `--text-file <path>` | string | read answer text from file |
| `--json <payload>` | string | raw JSON answer payload |
| `--question-id <id>` | string | question id within multi-question request |

### `request respond`

Lower-level respond. Use `request answer` for most cases.

```bash
codex-worker request respond <requestId>
```

Flags: same as `request answer` minus `--choice` and `--text-file`.

## Protocol-First Commands

Direct thread/turn control. Use when you need explicit id management.

### `thread start`

Create a new thread (session).

```bash
codex-worker thread start
```

Flags:

| Flag | Type | Description |
|---|---|---|
| `--cwd <path>` | string | working directory |
| `--model <model>` | string | model selection |
| `--developer-instructions <text>` | string | developer instructions |
| `--base-instructions <file>` | string | base instructions file |

### `thread resume`

Reconnect to an existing thread.

```bash
codex-worker thread resume <threadId>
```

### `thread read`

Read thread state.

```bash
codex-worker thread read <threadId>
```

Flags:

| Flag | Type | Description |
|---|---|---|
| `--include-turns` | boolean | include turn details |
| `--tail <n>` | number | event tail length |

### `thread list`

List all threads.

```bash
codex-worker thread list
```

Flags:

| Flag | Type | Description |
|---|---|---|
| `--cwd <path>` | string | filter by working directory |
| `--archived` | boolean | include archived threads |
| `--limit <n>` | number | max results |

### `turn start`

Start a new turn in a thread.

```bash
codex-worker turn start <threadId> <promptFile>
```

Flags:

| Flag | Type | Description |
|---|---|---|
| `--async` | boolean | return immediately |
| `--timeout <ms>` | number | wait timeout |

### `turn steer`

Send follow-up instructions to an existing turn.

```bash
codex-worker turn steer <threadId> <turnId> <promptFile>
```

Flags: same as `turn start`.

### `turn interrupt`

Interrupt a running turn.

```bash
codex-worker turn interrupt <threadId> <turnId>
```

### `send`

Send a message to a thread (convenience alias for turn start).

```bash
codex-worker send <threadId> <promptFile>
```

Flags:

| Flag | Type | Description |
|---|---|---|
| `--async` | boolean | return immediately |
| `--timeout <ms>` | number | wait timeout |

### `read`

Read thread state (convenience alias for thread read).

```bash
codex-worker read <threadId>
```

Flags:

| Flag | Type | Description |
|---|---|---|
| `--tail <n>` | number | event tail length |

### `logs`

Read thread execution logs.

```bash
codex-worker logs <threadId>
```

Flags:

| Flag | Type | Description |
|---|---|---|
| `--tail <n>` | number | lines from log tail |

### `wait`

Block until a job completes.

```bash
codex-worker wait
```

Flags:

| Flag | Type | Description |
|---|---|---|
| `--thread-id <id>` | string | thread to wait on |
| `--turn-id <id>` | string | turn to wait on |
| `--job-id <id>` | string | job to wait on |
| `--timeout <ms>` | number | wait timeout |
| `--compact` | boolean | concise output |

## Diagnostics

```bash
codex-worker model list                # available models
codex-worker model list --include-hidden  # include hidden models
codex-worker account read              # account info
codex-worker account rate-limits       # current rate limits
codex-worker doctor                    # check prerequisites and runtime health
codex-worker daemon status             # daemon state
codex-worker daemon start              # start the daemon
codex-worker daemon stop               # stop the daemon
```

## Exit Codes

| Code | Meaning |
|---|---|
| 0 | success |
| 1 | error (check stderr) |
| 2 | task blocked on pending request (check `request list`) |

## Output Format Examples

### JSON output (--output json)

```json
{
  "thread_id": "thr_abc123",
  "session_id": "ses_abc123",
  "status": "completed"
}
```

### Compact follow output (--follow --compact)

```
👤 Build a REST API for user management...
🔧 bash (completed)
📝 created: src/routes/users.ts
💬 I've created the user management API with...
✅ Turn completed
```

### Quiet list output (--quiet)

```
thr_abc123
thr_def456
thr_ghi789
```
