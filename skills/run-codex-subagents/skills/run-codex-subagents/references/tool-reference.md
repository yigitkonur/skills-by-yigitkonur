# codex-worker command reference

Use `codex-worker` directly after a global install:

```bash
npm install -g codex-worker
codex-worker --help
```

Or use it ad hoc through `npx`:

```bash
npx -y codex-worker --help
```

All examples below use the global form for brevity. Prefix with `npx -y` when you are not installed globally.

## Global Output Mode

Set JSON output before the command when scripting:

```bash
codex-worker --output json read <thread-id>
codex-worker --output json run task.md --async
```

## Friendly Aliases

### `run <task.md>`

Creates a thread and starts its first turn from the Markdown prompt file.

```bash
codex-worker run task.md
codex-worker run task.md --cwd /abs/project
codex-worker run task.md --model gpt-5.4
codex-worker --output json run task.md --async
```

Key flags:
- `--cwd <dir>`: working directory for the new thread
- `--model <id>`: override model selection
- `--async`: return immediately with thread, turn, and job ids
- `--timeout <ms>`: override wait timeout for blocking runs

### `send <thread-id> <message.md>`

Resume the existing thread and add a new turn from a Markdown file.

```bash
codex-worker send <thread-id> followup.md
codex-worker --output json send <thread-id> followup.md --async
```

### `read <thread-id>`

Read the tracked thread state, turns, pending requests, and artifact paths.

```bash
codex-worker read <thread-id>
codex-worker read <thread-id> --tail 50
codex-worker --output json read <thread-id>
```

### `logs <thread-id>`

Print the readable execution tail for a thread.

```bash
codex-worker logs <thread-id>
codex-worker logs <thread-id> --tail 100
codex-worker --output json logs <thread-id>
```

## Protocol-First Commands

### `thread start`

Create an idle thread before the first turn.

```bash
codex-worker thread start --cwd /abs/project
codex-worker --output json thread start --cwd /abs/project --model gpt-5.4
codex-worker thread start --developer-instructions "Prefer rg over grep."
codex-worker thread start --base-instructions "Always verify before claiming success."
```

### `thread resume`

Reattach to a known thread id.

```bash
codex-worker thread resume <thread-id>
```

### `thread read`

Protocol-first variant of `read`.

```bash
codex-worker thread read <thread-id>
codex-worker thread read <thread-id> --include-turns
codex-worker thread read <thread-id> --tail 50
```

### `thread list`

List tracked threads.

```bash
codex-worker thread list
codex-worker thread list --cwd /abs/project
codex-worker thread list --limit 20
codex-worker --output json thread list
```

### `turn start`

Start a new turn inside an existing thread.

```bash
codex-worker turn start <thread-id> prompt.md
codex-worker --output json turn start <thread-id> prompt.md --async
```

### `turn steer`

Continue from a known turn boundary.

```bash
codex-worker turn steer <thread-id> <turn-id> followup.md
codex-worker --output json turn steer <thread-id> <turn-id> followup.md --async
```

### `turn interrupt`

Request interruption of the active turn.

```bash
codex-worker turn interrupt <thread-id> <turn-id>
```

## Request Handling

### `request list`

```bash
codex-worker request list
codex-worker request list --status pending
codex-worker --output json request list
```

### `request read`

```bash
codex-worker request read <request-id>
```

### `request respond`

Approval requests:

```bash
codex-worker request respond <request-id> --decision accept-session
codex-worker request respond <request-id> --decision reject
```

User-input requests:

```bash
codex-worker request respond <request-id> --question-id style --answer "Short"
```

Raw payload:

```bash
codex-worker request respond <request-id> --json '{"answers":{"style":{"answers":["Short"]}}}'
```

## Waiting

Use `wait` to block on a background run or a resumed blocked turn.

```bash
codex-worker wait --thread-id <thread-id>
codex-worker wait --turn-id <turn-id>
codex-worker wait --job-id <job-id>
codex-worker wait --thread-id <thread-id> --timeout 300000
```

## Runtime Inspection

```bash
codex-worker doctor
codex-worker --output json doctor
codex-worker daemon start
codex-worker daemon status
codex-worker daemon stop
codex-worker model list
codex-worker model list --cwd /abs/project --include-hidden
codex-worker account read
codex-worker account read --refresh-token
codex-worker account rate-limits
```

## Old To New

| Old idea | Current command |
|---|---|
| Start a task | `run` or `thread start` + `turn start` |
| Continue a task/session | `send` or `turn steer` |
| Read task artifacts | `read`, `logs`, `thread read` |
| Follow live work | foreground `run`/`send`, or `wait` + `read`/`logs` |
| Answer a request | `request respond` |
