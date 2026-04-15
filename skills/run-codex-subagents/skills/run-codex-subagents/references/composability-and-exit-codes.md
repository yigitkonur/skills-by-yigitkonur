# Composability and exit codes

Use this file when you need shell-safe orchestration, machine-readable output, or predictable failure handling.

## Output modes

Available on the top-level CLI:

- `--output text` (default) — human-readable formatted output
- `--output json` — machine-readable JSON

For task monitoring:

- `--follow` — stream events in real time (with `run`, `task start`, `task wait`)
- `--compact` — concise emoji-prefixed event output (requires `--follow`)
- `--quiet` — bare IDs, one per line (on `task list`)
- `--field <path>` — extract single dotted-path field (on `task read`)
- `--raw` — raw JSONL dump (on `task events`)

## Bounded list behavior

`task list`, `session list`, and `request list` are bounded by default and return the newest entries first.

Useful controls:

- `--limit <n>` — max results
- `--status <status>` — filter by status (on `task list`, `request list`)
- `--quiet` — output bare IDs only (on `task list`)

## Pipe-friendly examples

Get all pending request ids:

```bash
codex-worker --output json request list --status pending | jq -r '.data[].id'
```

Get bare thread ids:

```bash
codex-worker task list --quiet
```

Extract a field:

```bash
codex-worker task read thr_abc123 --field status
```

Check if a task is running:

```bash
STATUS="$(codex-worker task read thr_abc123 --field status)"
if [ "$STATUS" = "running" ]; then
  codex-worker task follow thr_abc123 --compact
fi
```

## Exit-code contract

Lifecycle commands use exit codes as control flow:

- `0` — success
- `1` — error (check stderr)
- `2` — blocked on approval or user input

## Read vs lifecycle commands

Important distinction:

- inspection commands succeed with exit `0` when the read itself succeeds, even if the underlying task is in a failed state
- lifecycle commands reflect the underlying task outcome and may exit `1` or `2`

Typical inspection commands:

- `task read`
- `task list`
- `task events`
- `session read`
- `session list`
- `request read`
- `request list`
- `model list`
- `account read`
- `account rate-limits`
- `doctor`
- `daemon status`

Typical lifecycle commands:

- `run`
- `task start`
- `task steer`
- `task follow`
- `task wait`
- `task cancel`
- `request answer`
- `request respond`
