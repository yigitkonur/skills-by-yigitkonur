# Recovery and diagnostics

Use this file when a run fails, is interrupted, or behaves unexpectedly.

## First response

Inspect before retrying:

```bash
codex-worker read <thread-id> --tail 50
codex-worker logs <thread-id> --tail 100
codex-worker doctor
```

## What `read` gives you

`read` is the main local recovery surface. It returns:
- thread state
- local turns
- pending requests
- artifact paths
- recent display log and recent transcript events

Use JSON mode when you need machine-readable status:

```bash
codex-worker --output json read <thread-id>
```

## Useful artifacts

- `artifacts.transcriptPath` — transcript JSONL
- `artifacts.logPath` — readable execution log
- `artifacts.rawLogPath` — raw protocol NDJSON when available
- `logs <thread-id>` — formatted log tail

## Recovery playbook

### Failed

1. Read the thread: `codex-worker read <thread-id> --tail 50`
2. Read readable logs: `codex-worker logs <thread-id> --tail 100`
3. Run `codex-worker doctor`
4. Decide whether to:
   - answer a pending request
   - send a tighter follow-up prompt
   - steer from the last turn with explicit control
   - restart cleanly

### Interrupted

1. Read the thread and logs
2. Decide whether useful partial work exists
3. Choose between `send`, `turn steer`, or a fresh `run`

### Waiting request

Treat it as normal control flow:

```bash
codex-worker request list --status pending
codex-worker request read <request-id>
codex-worker request respond <request-id> ...
codex-worker wait --thread-id <thread-id> --timeout 300000
```

## When `doctor` matters

Use `doctor` when the failure looks environmental:
- authentication
- rate limits
- daemon state
- model/provider discovery
- local runtime prerequisites
