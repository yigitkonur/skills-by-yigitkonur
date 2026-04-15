# Command Reference

Full public CLI surface for the **released** `codex-worker` CLI that users get from the installer or npm package.

## Install the CLI if needed

Recommended installer:

```bash
sudo -v ; curl -fsSL https://github.com/yigitkonur/codex-worker/releases/latest/download/install.sh | sudo bash
```

User-local install:

```bash
curl -fsSL https://github.com/yigitkonur/codex-worker/releases/latest/download/install.sh | bash -s -- --install-dir "$HOME/.local/bin"
```

Fallback:

```bash
npm install -g codex-worker
```

## Global option

- `--output text|json`

## Friendly aliases

### `run`

```bash
codex-worker run <task.md>
```

Flags:
- `--cwd <dir>`
- `--model <id>`
- `--async`
- `--timeout <ms>`

### `send`

```bash
codex-worker send <thread-id> <message.md>
```

Flags:
- `--async`
- `--timeout <ms>`

### `read`

```bash
codex-worker read <thread-id>
```

Flags:
- `--tail <n>`

### `logs`

```bash
codex-worker logs <thread-id>
```

Flags:
- `--tail <n>`

## Thread commands

### `thread start`

Flags:
- `--cwd <dir>`
- `--model <id>`
- `--developer-instructions <text>`
- `--base-instructions <text>`

### `thread resume`

```bash
codex-worker thread resume <thread-id>
```

### `thread read`

```bash
codex-worker thread read <thread-id>
```

Flags:
- `--include-turns`
- `--tail <n>`

### `thread list`

Flags:
- `--cwd <dir>`
- `--archived`
- `--limit <n>`

## Turn commands

### `turn start`

```bash
codex-worker turn start <thread-id> <prompt.md>
```

Flags:
- `--async`
- `--timeout <ms>`

### `turn steer`

```bash
codex-worker turn steer <thread-id> <turn-id> <prompt.md>
```

Flags:
- `--async`
- `--timeout <ms>`

### `turn interrupt`

```bash
codex-worker turn interrupt <thread-id> <turn-id>
```

## Request handling

### `request list`

Flags:
- `--status <pending|responded|failed>`

### `request read`

```bash
codex-worker request read <request-id>
```

### `request respond`

Flags:
- `--json <payload>`
- `--decision <decision>`
- `--answer <text>`
- `--question-id <id>`

There is no `request answer` helper in the released CLI.

## Lifecycle and diagnostics

### `wait`

```bash
codex-worker wait --thread-id <id>
codex-worker wait --turn-id <id>
codex-worker wait --job-id <id>
```

Flags:
- `--timeout <ms>`

### `doctor`

```bash
codex-worker doctor
```

### `daemon start|status|stop`

```bash
codex-worker daemon start
codex-worker daemon status
codex-worker daemon stop
```

## Environment inspection

### `model list`

Flags:
- `--cwd <dir>`
- `--include-hidden`

### `account read`

Flags:
- `--refresh-token`

### `account rate-limits`

No flags.

### `skills list`

Flags:
- `--force-reload`

### `app list`

Flags:
- `--limit <n>`
- `--force-refetch`
- `--thread-id <id>`

## Notes

- `run` is synchronous by default.
- Use `send` for friendly continuation.
- Use `thread` + `turn` commands when you need explicit id control.
- If you are on a repo-local dev build, you may see newer commands than this reference documents. This file intentionally tracks the released installer/npm surface.
