# Recovery and diagnostics

Use this file when a task fails, is interrupted, or behaves unexpectedly.

## First response

Do this before retrying:

```bash
codex-worker task read <threadId> --tail 40
codex-worker task events <threadId> --tail 100
codex-worker doctor
```

The task may already contain:

- useful partial file edits
- a clear stderr failure reason
- a recoverable state to continue from

## What `task read` gives you

`task read` is the main recovery surface. It returns:

- thread status and metadata
- related turns and their states
- recent events
- log tails (timeline, summary, stderr)

Use `--field` when you only need one value:

```bash
codex-worker task read thr_abc123 --field status
codex-worker task read thr_abc123 --field thread.model
```

## Log artifacts to inspect

These are the most useful recovery data:

- `task events --raw` — raw JSONL event stream
- `task events --tail 50` — recent formatted events
- `logs <threadId>` — execution output logs
- `read <threadId>` — thread state with turn details

## Event types in transcripts

The event stream uses these types:

- `user` — user prompt events
- `assistant.delta` — streaming text (skipped in non-raw mode)
- `request` — blocked runtime requests
- `notification` with methods:
  - `item/completed` — completed items (messages, commands, file changes)
  - `item/agentMessage/delta` — agent message streaming
  - `item/commandExecution/outputDelta` — command output streaming
  - `turn/completed` — turn completion
  - `error` — runtime errors

Common readings:

- `request` events mean the task is blocked, not dead
- `error` notifications explain the terminal reason
- `item/completed` events show what the worker actually touched

## Recovery playbook

### Failed

1. Read `task read <threadId> --tail 40`
2. Check logs: `logs <threadId> --tail 100`
3. Check recent events: `task events <threadId> --tail 50`
4. Decide whether the fix is:
   - a request answer
   - a prompt correction
   - an environment/runtime issue
   - a follow-up `task steer`
   - a clean retry with better context

### Interrupted

1. Read the state: `task read <threadId>`
2. Check whether the worker already produced useful files
3. Decide whether to:
   - resume via `task steer` with a follow-up
   - start a fresh task
   - discard and restart cleanly

### Waiting request

Switch to the request loop immediately. Do not misclassify it as a failure.

```bash
codex-worker request list --status pending
codex-worker request read <requestId>
codex-worker request answer <requestId> --decision accept
codex-worker task follow <threadId> --compact
```

## When `doctor` matters

Use `doctor` when the failure looks environmental:

- authentication issues
- rate limits
- transport problems
- daemon readiness
- runtime profile/config problems

`doctor` is especially useful after repeated auth or connection failures because it surfaces recent failure hints from local state.
