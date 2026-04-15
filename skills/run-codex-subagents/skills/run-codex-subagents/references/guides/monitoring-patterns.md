# Monitoring Patterns

Three questions cover every live-monitoring need: **Is it moving? Is it blocked? What is it doing?** Map each to the right artifact. Do not poll `Status:` — see the note at the bottom.

Resolve paths once:

```bash
THREAD_ID=<thread-id>
RAW=$(codex-worker --output json read "$THREAD_ID" | jq -r '.artifacts.rawLogPath')
```

All queries below assume `$RAW` is set. See `guides/log-artifacts.md` for the file taxonomy.

## Is it moving?

`tail -n +1 -F` replays the whole raw log first, then live-tails. Without `-n +1`, fast turns finish before the default 10-line tail catches them and you miss the lifecycle. The extra cost on first attach is a single batched notification — worth it.

```bash
tail -n +1 -F "$RAW" | jq -rc '
  select(
    .method == "turn/started"              or
    .method == "turn/completed"            or
    .method == "item/completed"            or
    .method == "thread/tokenUsage/updated" or
    .method == "thread/status/changed"     or
    .dir    == "server_request"            or
    .dir    == "exit"                      or
    .dir    == "stderr"                    or
    (.dir == "daemon" and (.message | test("watchdog|fail")))
  ) |
  "\(.ts[11:19])  \(.dir)  \(.method // .message)  \(.params.item.type // \"\")"
'
```

Rule: any line = alive. Silence for longer than `CODEX_WORKER_TURN_TIMEOUT_MS` (default 30 min) = actually stuck — and the idle watchdog will fire on its own anyway.

Mtime variant when `jq` is unavailable:

```bash
stat -f %Sm "$RAW"   # last activity timestamp; advances = alive
```

## Is it blocked on me?

Two equivalent signals. The first is one-shot, the second is live.

```bash
codex-worker --output json request list
tail -F "$RAW" | jq -rc 'select(.dir == "server_request") | "\(.ts[11:19])  \(.method)  id=\(.id)"'
```

Any hit means the turn is paused for `request respond`. Unblock via `guides/pause-flow-handling.md`.

## What is it doing right now?

Snapshot state plus rich context:

```bash
codex-worker --output json read "$THREAD_ID" | jq '{
  status: .localThread.status,
  pendingRequests,
  raw: .artifacts.rawLogPath,
  transcript: .artifacts.transcriptPath
}'
```

Then tail the raw log for the live view, or `scripts/diagnostic-queries.md` for replay-style queries.

## Watching many threads at once

Use `scripts/merged-monitor.sh <tid-1> <tid-2> ...`. It resolves each thread's `rawLogPath`, applies the milestone filter, and prefixes each line with the 8-char short id.

## Why `Status:` is the wrong signal for live monitoring

Thread `Status:` only flips at turn boundaries:

- `turn/started` → `active`
- `turn/completed` → `idle`
- watchdog or codex exit → `failed`
- `server_request` → `waiting_request`

A healthy long-running turn stays `active` for its entire duration. Polling `codex-worker thread read | awk '/^Status:/'` will report one transition at turn start and silence until the turn ends. That is not a progress signal. Use `rawLogPath`.

## Triage cheatsheet

| Symptom | What to run |
|---|---|
| Need live progress of one thread | `tail -F "$RAW" \| jq` with the "Is it moving?" filter |
| Need live progress of many threads | `scripts/merged-monitor.sh <tid>...` |
| Need to know if I need to respond | `codex-worker request list` or the `dir=="server_request"` tail |
| Need a wait-for-terminal on a job | `codex-worker wait --job-id "$JOB_ID"` |
| Need the structured snapshot | `codex-worker --output json read <tid>` |
| Suspect stuck | `stat -f %Sm "$RAW"` — stale = stuck, fresh = running |
| Want to know why a finished thread failed | `guides/failure-diagnosis.md` |
