# Command reference

Use this file when you need the exact public CLI surface for `cli-codex-subagent`.

Recheck `--help` before documenting a command you have not used recently. This reference is intentionally limited to the agent-facing contract.

## Global output flags

Available on the top-level CLI:

- `--output text|json|jsonl`
- `--json`
- `--stream-json`

Use:

- text for interactive reading
- `--json` for machine-readable command results
- `--stream-json` for streaming commands such as `task follow` or `task start --follow`

## Execution modes

For `run`, `task start`, and `task steer`:

- default: async, returns quickly with ids
- `--wait`: block until terminal state, no live event stream
- `--follow`: block and stream normalized events before the final result

These modes are mutually exclusive.

## `run`

Usage:

```bash
cli-codex-subagent run <taskFile>
```

Arguments:

- `<taskFile>` markdown task file

Flags:

- `--cwd <path>`
- `--model <model>`
- `--effort none|minimal|low|medium|high|xhigh`
- `--label <label>`
- `--session <sessionId>`
- `--base-instructions-file <file>`
- `--context-file <file>` repeatable
- `--output-schema <file>`
- `--async`
- `--wait`
- `--follow`
- `--timeout-ms <ms>`
- `--approval-policy never|on-failure|on-request|untrusted`
- `--auto-approve`

Use `run` for the short common path. It is functionally the same as `task start`.

## `task`

### `task start`

Usage:

```bash
cli-codex-subagent task start <taskFile>
```

Flags are the same as `run`.

### `task steer`

Usage:

```bash
cli-codex-subagent task steer <taskId> <messageFile>
```

Arguments:

- `<taskId>` existing task id
- `<messageFile>` markdown follow-up file

Flags:

- `--cwd <path>`
- `--label <label>`
- `--effort none|minimal|low|medium|high|xhigh`
- `--base-instructions-file <file>`
- `--context-file <file>` repeatable
- `--async`
- `--wait`
- `--follow`
- `--timeout-ms <ms>`
- `--approval-policy never|on-failure|on-request|untrusted`
- `--auto-approve`

Use `task steer` only after the earlier task is terminal. It is rejected while the anchor task is still `running` or `waiting_request`.

### `task status`

Usage:

```bash
cli-codex-subagent task status [taskId]
```

Filters and extraction:

- `--status <status>`
- `--session <sessionId>`
- `--label <label>`
- `--cwd <path>`
- `--limit <n>`
- `--all`
- `--field <path>`
- `-q, --quiet`

Use with no id when you want a filtered task view but do not need `task read`.

### `task read`

Usage:

```bash
cli-codex-subagent task read <taskId>
```

Flags:

- `--tail <n>`
- `--field <path>`

Returns task status, related session, related requests, artifact paths, and timeline/summary/stderr tails.

### `task follow`

Usage:

```bash
cli-codex-subagent task follow <taskId>
```

Streams normalized events until the task stops running. In `--stream-json` mode, each line is a structured event or terminal result.

### `task wait`

Usage:

```bash
cli-codex-subagent task wait <taskId>
```

Flags:

- `--timeout-ms <ms>`

Blocks until the task completes, fails, is interrupted, or becomes `waiting_request`.

### `task cancel`

Usage:

```bash
cli-codex-subagent task cancel <taskId>
```

Cancels the active turn behind a running task.

### `task events`

Usage:

```bash
cli-codex-subagent task events <taskId>
```

Flags:

- `--raw`
- `--tail <n>`

Use `--raw` only when the normalized event log is not enough.

### `task list`

Usage:

```bash
cli-codex-subagent task list
```

Filters and extraction:

- `--status <status>`
- `--session <sessionId>`
- `--label <label>`
- `--cwd <path>`
- `--limit <n>`
- `--all`
- `--field <path>`
- `-q, --quiet`

Newest-first and bounded by default.

## `session`

### `session create`

Usage:

```bash
cli-codex-subagent session create
```

Flags:

- `--cwd <path>`
- `--model <model>`
- `--base-instructions-file <file>`
- `--context-file <file>` repeatable

Pre-create a session when continuity matters across multiple tasks.

### `session resume`

Usage:

```bash
cli-codex-subagent session resume <sessionId>
```

Reconnects to the existing runtime thread and refreshes local session state.

### `session read`

Usage:

```bash
cli-codex-subagent session read <sessionId>
```

Flags:

- `--field <path>`

### `session list`

Usage:

```bash
cli-codex-subagent session list
```

Filters and extraction:

- `--status <status>`
- `--model <model>`
- `--cwd <path>`
- `--limit <n>`
- `--all`
- `--field <path>`
- `-q, --quiet`

## `request`

### `request list`

Usage:

```bash
cli-codex-subagent request list
```

Filters and extraction:

- `--status <status>`
- `--task <taskId>`
- `--session <sessionId>`
- `--method <method>`
- `--limit <n>`
- `--all`
- `--field <path>`
- `-q, --quiet`

### `request read`

Usage:

```bash
cli-codex-subagent request read <requestId>
```

Flags:

- `--field <path>`

### `request answer`

Usage:

```bash
cli-codex-subagent request answer <requestId>
```

Flags:

- `--choice <index>`
- `--text-file <file>`
- `--custom-file <file>`
- `--decision <decision>`
- `--json-file <file>`

Use the smallest structured flag that fits. Reach for `--json-file` only when default mappings are insufficient.

## `prompt`

### `prompt inspect`

Usage:

```bash
cli-codex-subagent prompt inspect <taskFile>
```

Flags:

- `--cwd <path>`
- `--label <label>`
- `--model <model>`
- `--session <sessionId>`
- `--base-instructions-file <file>`
- `--context-file <file>` repeatable
- `--write-bundle <dir>`
- `--field <path>`

Shows the fully resolved prompt bundle without starting a task.

### `prompt lint`

Usage:

```bash
cli-codex-subagent prompt lint <taskFile>
```

Flags:

- `--cwd <path>`
- `--label <label>`
- `--model <model>`
- `--session <sessionId>`
- `--base-instructions-file <file>`
- `--context-file <file>` repeatable
- `--field <path>`

Use `prompt lint` when you only need validation, not the resolved body.

## Diagnostics and environment

### Inspection

- `cli-codex-subagent model list`
- `cli-codex-subagent account read`
- `cli-codex-subagent account rate-limits`
- `cli-codex-subagent doctor`

### Daemon control

- `cli-codex-subagent daemon status`
- `cli-codex-subagent daemon stop`
- `cli-codex-subagent daemon run`

Use `daemon run` only for foreground debugging.
