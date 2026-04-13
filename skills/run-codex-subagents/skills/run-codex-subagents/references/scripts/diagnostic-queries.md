# Diagnostic Queries For Transcript And Log Artifacts

Resolve the artifact paths from the thread first:

```bash
THREAD_ID=<thread-id>
THREAD_JSON=$(codex-worker --output json read "$THREAD_ID")
TRANSCRIPT=$(printf '%s' "$THREAD_JSON" | jq -r '.artifacts.transcriptPath')
LOG_PATH=$(printf '%s' "$THREAD_JSON" | jq -r '.artifacts.logPath')
```

All queries below assume `$TRANSCRIPT` points to `threads/<thread-id>.jsonl`.

## Show prompts and requests only

```bash
jq -r '
  if .type == "user" then
    "PROMPT  " + (.prompt // .text // "")
  elif .type == "request" then
    "REQUEST " + (.method // "")
  else
    empty
  end
' "$TRANSCRIPT"
```

## Reconstruct assistant text

```bash
jq -r 'select(.type == "assistant.delta") | .delta' "$TRANSCRIPT"
```

## Count notification methods

```bash
jq -r 'select(.type == "notification") | .method' "$TRANSCRIPT" | sort | uniq -c | sort -rn
```

## List request payloads

```bash
jq -r 'select(.type == "request") | {requestId, method, params}' "$TRANSCRIPT"
```

## Show streamed command output deltas

```bash
jq -r 'select(.type == "item/commandExecution/outputDelta") | .delta' "$TRANSCRIPT"
```

## Show streamed file-change output deltas

```bash
jq -r 'select(.type == "item/fileChange/outputDelta") | .delta' "$TRANSCRIPT"
```

## Tail the readable log

```bash
tail -n 50 "$LOG_PATH"
```

## Watch the transcript grow

```bash
tail -f "$TRANSCRIPT"
```

## Find generic runtime failures

```bash
jq -r '
  select(.type == "notification" and .method == "error") |
  .params.message // "unknown error"
' "$TRANSCRIPT"
```
