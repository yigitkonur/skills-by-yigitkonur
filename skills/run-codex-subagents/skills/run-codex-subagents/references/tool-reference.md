# codex-worker command reference

## Install

```bash
# Global install (canonical). Puts the binary on PATH.
npm install -g codex-worker
which codex-worker
#   macOS with Homebrew-managed node: /opt/homebrew/bin/codex-worker
#   Other:  $(npm prefix -g)/bin/codex-worker
codex-worker --version
```

If `which codex-worker` is empty, your npm global bin is not on PATH. Run `npm prefix -g` and add the resulting `bin/` to `PATH` in `~/.zshrc`.

Throwaway, no install:

```bash
npx -y codex-worker --help
```

All examples below use the global form for brevity. Prefix with `npx -y` when you are not installed globally.

## Environment Variables

All vars are read per-call. Set inline for a single command, or export persistently and restart the daemon (`codex-worker daemon stop && codex-worker doctor`).

| Var | Effect | Inline example |
|---|---|---|
| `CODEX_WORKER_TURN_TIMEOUT_MS` | Idle watchdog window in ms. Default 1800000 (30 min). Resets on every notification. | `CODEX_WORKER_TURN_TIMEOUT_MS=3600000 codex-worker run task.md` |
| `CODEX_WORKER_RAW_LOG` | Set to `0` to disable the per-thread raw NDJSON firehose. Default on. | `CODEX_WORKER_RAW_LOG=0 codex-worker run task.md` |
| `CODEX_WORKER_STATE_DIR` | Override the state root (default `~/.codex-worker`). | `CODEX_WORKER_STATE_DIR=/tmp/iso codex-worker doctor` |
| `CLI_CODEX_WORKER_STATE_DIR` | Legacy fallback for `CODEX_WORKER_STATE_DIR`. Prefer the new name. | — |
| `CODEX_HOME` | Override the Codex profile directory (default `~/.codex`). | `CODEX_HOME=/alt codex-worker thread list` |
| `CODEX_HOME_DIRS` | Colon-separated list of Codex profile dirs for multi-account failover. | `CODEX_HOME_DIRS=~/.codex:~/.codex-work codex-worker doctor` |
| `CODEX_ENABLE_FLEET` | Set to `1` to append fleet developer instructions on thread-start. | `CODEX_ENABLE_FLEET=1 codex-worker run task.md` |

See `guides/log-artifacts.md` for what `CODEX_WORKER_RAW_LOG` controls and `guides/failure-diagnosis.md` for how to tune `CODEX_WORKER_TURN_TIMEOUT_MS`.

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
