# Request handling

Use this file when a task becomes blocked and you need to inspect or answer a runtime request correctly.

## Detect the blocked state

Treat either of these as a blocked task:

- the task status is `waiting_request`
- `task wait`, `task follow`, `run --wait`, or `task start --wait/--follow` exits with code `2`

This is not a failure. The runtime is waiting for input.

## Standard loop

```bash
cli-codex-subagent request list --status pending --json
cli-codex-subagent request read <requestId> --json
cli-codex-subagent request answer <requestId> ...
cli-codex-subagent task follow <taskId>
```

If you do not know the task id, `request read` returns the associated task and session ids.

## What `request answer` supports

Use the smallest supported answer form:

- `--choice <index>`
  - best for numbered user-input options
  - `1` means the first visible option
- `--text-file <file>`
  - best for a freeform textual answer you already wrote
- `--custom-file <file>`
  - best when the runtime expects JSON but you want a convenience path
  - if the file parses as a JSON object, it is sent as JSON
  - otherwise, the file body is treated as plain text
- `--decision <decision>`
  - supported decisions: `accept`, `accept-session`, `decline`, `cancel`
- `--json-file <file>`
  - exact escape hatch for advanced payloads or unsupported request types

## Safe defaults by request shape

### User input

When the runtime presents numbered choices:

```bash
cli-codex-subagent request answer req_123 --choice 1
```

When you want to provide a custom textual answer:

```bash
cli-codex-subagent request answer req_123 --text-file answer.txt
```

### Command, file, and review approvals

Common approval responses:

```bash
cli-codex-subagent request answer req_123 --decision accept
cli-codex-subagent request answer req_123 --decision accept-session
cli-codex-subagent request answer req_123 --decision decline
```

Use `accept-session` only when you intentionally want the approval to apply to later turns in the same session.

### Permissions approvals

The built-in mapping supports acceptance for the current turn or the whole session:

```bash
cli-codex-subagent request answer req_123 --decision accept
cli-codex-subagent request answer req_123 --decision accept-session
```

For a declined or custom permissions payload, use `--json-file`. The convenience `--decision decline` mapping is not supported for that request family.

### Custom or unknown request types

When `request read` shows a method you do not recognize, stop guessing and use `--json-file` after inspecting the exact payload.

## Recovery rules

1. Read the request before answering it. Do not answer by guesswork.
2. Prefer `--choice` over freeform text when numbered options exist.
3. Prefer current-turn `accept` over `accept-session` unless session-wide approval is intentional.
4. Resume with `task follow` or `task wait` after the answer.
5. If the task blocks repeatedly, answer each request in sequence. A task can pause more than once.

## Useful inspection commands

```bash
cli-codex-subagent request list --status pending --field id --json
cli-codex-subagent request read req_123 --field method --json
cli-codex-subagent task read tsk_123 --json
```

Use `task read` when you want the full picture: current request, previous requests, artifact paths, and suggested next commands.
