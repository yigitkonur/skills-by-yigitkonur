# Blocked Turns And `request respond`

When a running turn needs a decision or user input, `codex-worker` persists a pending request and returns control to you. The current turn is still the same turn; you answer the request and then continue waiting or inspecting the same thread.

## Core Flow

```bash
codex-worker --output json run task.md --async
codex-worker request list
codex-worker request read <request-id>
codex-worker request respond <request-id> --decision accept-session
codex-worker wait --thread-id <thread-id>
```

After `request respond`, do not start a fresh thread unless you are intentionally abandoning the original turn. Use `wait`, `read`, or `logs` against the same thread.

## Approval Requests

Common decisions:

```bash
codex-worker request respond <request-id> --decision accept-session
codex-worker request respond <request-id> --decision accept
codex-worker request respond <request-id> --decision reject
```

Use `request read` first when you need the exact request type or payload.

## User-Input Requests

Text answer:

```bash
codex-worker request respond <request-id> --question-id answer_style --answer "Short"
```

Raw JSON answer:

```bash
codex-worker request respond <request-id> --json '{"answers":{"answer_style":{"answers":["Short"]}}}'
```

This CLI does not offer `--choice`, `--text-file`, or `--json-file`. Build the response with `--answer` plus `--question-id`, or pass the full payload through `--json`.

## Discovering Question Ids

```bash
codex-worker request read <request-id> | jq '.params.questions'
```

For single-question prompts, the first question id is usually enough. For multi-question prompts, answer each question in the JSON payload.

## Continue After Responding

Block again on the same background turn:

```bash
codex-worker wait --thread-id <thread-id>
```

Or inspect the current state without blocking:

```bash
codex-worker read <thread-id>
codex-worker logs <thread-id>
```

## Failure Modes

- Request still appears in `request list`: the payload shape was invalid or the daemon rejected it. Re-read the request and respond again with a correct payload.
- Thread stays failed after responding: the request was only one blocker; inspect `logs` and `read` for the actual runtime failure.
- You lost the thread id: recover it from `request read`, then use `wait --thread-id`, `read`, or `send`.
