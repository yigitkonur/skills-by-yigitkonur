# Diagnostic Queries Against The Raw NDJSON Log

All queries here target `artifacts.rawLogPath` (shipped in `codex-worker@0.1.4`). This is the firehose — every event with real method names and the `dir` taxonomy. The transcript JSONL (`artifacts.transcriptPath`) is a derived view with collapsed types and is **not** the right source for diagnostics. See `guides/log-artifacts.md` for the full map.

## Resolve paths

```bash
THREAD_ID=<thread-id>
JSON=$(codex-worker --output json read "$THREAD_ID")
RAW=$(printf '%s' "$JSON" | jq -r '.artifacts.rawLogPath')
```

All queries below assume `$RAW` is set.

## Count events by method / direction

```bash
jq -r '.method // ("[" + .dir + "]")' "$RAW" | sort | uniq -c | sort -rn
```

Balanced counts are a health signal:

- `hook/started` ≈ `hook/completed`
- `item/started` ≈ `item/completed`

Big gap = a hook or tool call stalled.

## Turn lifecycle trace

```bash
jq -rc '
  select(
    .method == "turn/started" or
    .method == "turn/completed" or
    .method == "thread/status/changed" or
    .dir == "daemon" or
    .dir == "exit" or
    .method == "error"
  ) |
  "\(.ts[11:19])  \(.dir)  \(.method // .message)"
' "$RAW"
```

## Tool calls that completed

```bash
jq -rc '
  select(.method == "item/completed" and .params.item.type == "commandExecution") |
  "\(.ts[11:19])  \(.params.item.commandName // .params.item.displayText // "?")"
' "$RAW"
```

## File changes that completed

```bash
jq -rc '
  select(.method == "item/completed" and .params.item.type == "fileChange") |
  "\(.ts[11:19])  \(.params.item.path // .params.item.displayText // "?")"
' "$RAW"
```

## Assistant messages (full text, not word deltas)

Completed assistant messages, end-of-thought each:

```bash
jq -rc '
  select(.method == "item/completed" and .params.item.type == "agentMessage") |
  .params.item.text
' "$RAW"
```

Reconstruct from deltas (useful if the thread never completed):

```bash
jq -r 'select(.method == "item/agentMessage/delta") | .params.delta' "$RAW"
```

## Streamed command output

```bash
jq -r 'select(.method == "item/commandExecution/outputDelta") | .params.delta' "$RAW"
```

## Server requests (places the turn asked for input)

```bash
jq -rc '
  select(.dir == "server_request") |
  "\(.ts[11:19])  id=\(.id)  \(.method)"
' "$RAW"
```

## Stderr from the codex child

Rare; copy verbatim into bug reports if present.

```bash
jq -rc 'select(.dir == "stderr") | "\(.ts[11:19])  \(.data[0:200])"' "$RAW"
```

## Find the cause of a failed turn

```bash
jq -c '
  select(
    .dir == "daemon"         or
    .dir == "exit"           or
    .dir == "protocol_error" or
    .method == "error"
  )
' "$RAW"
```

Interpretation:

- `{"dir":"daemon","message":"watchdog_fire …"}` — the worker's idle watchdog fired. Tune `CODEX_WORKER_TURN_TIMEOUT_MS` (see `guides/failure-diagnosis.md`).
- `{"dir":"exit","data":{"code":…,"signal":…}}` — the `codex` child exited on its own.
- `{"method":"error","params":{"message":"…"}}` — runtime error reported by codex.

## Token-usage tempo

Every `thread/tokenUsage/updated` is one model generation. Burst counts and gaps are a proxy for model latency.

```bash
jq -rc 'select(.method == "thread/tokenUsage/updated") | .ts[11:19]' "$RAW"
```

## Is the log still growing?

```bash
stat -f %Sm "$RAW"      # last-modified time
wc -l "$RAW"            # total events so far
```

Fresh mtime + growing line count = the thread is still working, regardless of `Status:`.
