# Request handling

Use this file when a task becomes blocked and you need to inspect or answer a runtime request correctly.

## Detect the blocked state

Treat either of these as a blocked task:

- the task status is `waiting_request`
- `task wait`, `task follow`, or `run` exits with code `2`

This is not a failure. The runtime is waiting for input.

## Standard loop

```bash
codex-worker request list --status pending
codex-worker request read <requestId>
codex-worker request answer <requestId> ...
codex-worker task follow <threadId> --compact
```

If you do not know the thread id, `request read` returns the associated thread and session ids.

## What `request answer` supports

Use the smallest supported answer form:

- `--choice <N>`
  - best for numbered user-input options
  - `1` means the first visible option
- `--text-file <file>`
  - best for a freeform textual answer you already wrote
  - reads file content and sends as answer text
- `--answer <text>`
  - inline text answer for simple responses
- `--decision <decision>`
  - supported decisions: `accept`, `deny`
- `--json <payload>`
  - exact escape hatch for advanced payloads or unsupported request types

## Safe defaults by request shape

### User input

When the runtime presents numbered choices:

```bash
codex-worker request answer req_123 --choice 1
```

When you want to provide a custom textual answer:

```bash
codex-worker request answer req_123 --answer "Yes, proceed with the refactor"
```

Or from a file:

```bash
codex-worker request answer req_123 --text-file answer.txt
```

### Command, file, and review approvals

Common approval responses:

```bash
codex-worker request answer req_123 --decision accept
codex-worker request answer req_123 --decision deny
```

### Custom or unknown request types

When `request read` shows a method you do not recognize, stop guessing and use `--json` after inspecting the exact payload:

```bash
codex-worker request answer req_123 --json '{"result": {"approved": true}}'
```

## Recovery rules

1. Read the request before answering it. Do not answer by guesswork.
2. Prefer `--choice` over freeform text when numbered options exist.
3. Resume with `task follow` or `task wait` after the answer.
4. If the task blocks repeatedly, answer each request in sequence. A task can pause more than once.
