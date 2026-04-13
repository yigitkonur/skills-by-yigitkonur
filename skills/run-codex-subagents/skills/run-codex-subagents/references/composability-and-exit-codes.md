# Composability and exit codes

Use this file when you need shell-safe orchestration, machine-readable output, or predictable failure handling.

## Preferred output modes

Default rules:

- use `--json` for one-shot inspection and lifecycle commands
- use `--stream-json` for streaming commands
- use `--field <path>` when you only need one value from a read/list command
- use `--quiet` for bare one-value-per-line list output

## Bounded list behavior

`task list`, `session list`, and `request list` are bounded by default and return the newest entries first.

Useful controls:

- `--limit <n>`
- `--all`
- `--status ...`
- command-specific filters such as `--label`, `--cwd`, `--task`, or `--method`

JSON list output includes:

- `count`
- `returned`
- `truncated`
- `filters`

## Pipe-friendly examples

Get all pending request ids:

```bash
cli-codex-subagent request list --status pending --field id --json
```

Get bare task ids for a label:

```bash
cli-codex-subagent task list --label wave-1 --quiet
```

Extract a handoff path:

```bash
cli-codex-subagent task read tsk_123 --field artifacts.handoffManifestPath --json
```

## Exit-code contract

Lifecycle commands use exit codes as control flow:

- `0` success
- `1` terminal task failure
- `2` blocked on approval or user input
- `3` retryable runtime or backend failure
- `4` invalid usage or malformed prompt bundle
- `5` target not found
- `6` conflict or invalid state transition

## Read vs lifecycle commands

Important distinction:

- inspection commands succeed with exit `0` when the read itself succeeds, even if the underlying task/session/request is in a failed state
- lifecycle commands reflect the underlying task outcome and may exit `1`, `2`, `3`, or `6`

Typical inspection commands:

- `task read`
- `task status`
- `task list`
- `task events`
- `session read`
- `session list`
- `request read`
- `request list`
- `prompt inspect`
- `prompt lint`
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

## Structured errors

In machine modes, failed commands return a structured error object with fields such as:

- `ok`
- `kind`
- `status`
- `error.code`
- `error.category`
- `error.message`
- `error.retryable`
- `suggestion`
- `actions`

Treat the structured error plus exit code as the contract. Do not rely on prose parsing first.
