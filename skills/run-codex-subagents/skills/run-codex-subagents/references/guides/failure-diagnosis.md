# Failure Diagnosis

Run this post-mortem whenever a thread is `failed`, reports an error, or looks hung. The raw NDJSON log is authoritative — see `guides/log-artifacts.md` for the file map.

## 1. Locate artifacts

```bash
THREAD_ID=<thread-id>
JSON=$(codex-worker --output json read "$THREAD_ID")
RAW=$(printf '%s' "$JSON" | jq -r '.artifacts.rawLogPath')
TRANSCRIPT=$(printf '%s' "$JSON" | jq -r '.artifacts.transcriptPath')
```

If `$RAW` is `null`, the thread pre-dates `codex-worker@0.1.4`. Fall back to `$TRANSCRIPT`, but upgrade and re-run for better forensics.

## 2. Cause of death in one query

```bash
jq -rc '
  select(.dir=="daemon" or .dir=="exit" or .method=="error" or .dir=="protocol_error") |
  "\(.ts[11:19])  \(.dir)  \(.method // .message // "")"
' "$RAW"
```

Three categories:

- **Daemon killed it** — `{"dir":"daemon","message":"watchdog_fire …"}` or `{"dir":"daemon","message":"failExecution …"}`. The codex child was `SIGTERM`'d by the worker, usually from idle timeout. Tune the watchdog in step 4.
- **Codex child died** — `{"dir":"exit","data":{"code":…,"signal":…}}`. Either OOM, provider drop, or a segfault. Inspect any `stderr` lines just before the `exit` for a hint.
- **Codex reported an error** — `{"method":"error", "params":{"message": "…"}}`. The backend surfaced a runtime error up to us; read `.params.message` verbatim.

## 3. Before you call it failed — check the healthy-looking-error patterns

These surfaces are designed to look empty when a custom provider does not need OpenAI auth:

- `codex-worker --output json account read` returning `{account: null, requiresOpenaiAuth: false}` is **correct** when `~/.codex/config.toml` sets `requires_openai_auth = false` (common for custom providers such as `model_provider = "codex-lb"`). Honored since `codex-worker@0.1.3`.
- `codex-worker --output json account rate-limits` returning `{data: null, note: "rate limits unavailable: requires_openai_auth=false"}` is **correct** for the same reason; the rate-limits endpoint is OpenAI-only.
- `Status: active` for tens of minutes is **not** a failure. Tail `$RAW`; if lines are arriving, the turn is healthy. Status only flips at turn boundaries.

## 4. Idle watchdog tuning

The per-turn idle watchdog fires after `CODEX_WORKER_TURN_TIMEOUT_MS` (default 30 min) of wire silence. Heavy agentic missions can hit it.

```bash
# one-off, for a single run:
CODEX_WORKER_TURN_TIMEOUT_MS=3600000 codex-worker run task.md

# persistent — add to ~/.zshrc or shell profile:
export CODEX_WORKER_TURN_TIMEOUT_MS=3600000
```

After changing a persistent value, restart the daemon so it picks up the new env:

```bash
codex-worker daemon stop
codex-worker doctor     # starts a fresh daemon
```

## 5. Blocked vs failed

Blocked turns still look `active` but are pinned waiting for `request respond`.

```bash
codex-worker --output json request list
jq -c 'select(.dir=="server_request")' "$RAW"
```

If either is non-empty, see `guides/pause-flow-handling.md`. If both are empty and the thread `Status` is `failed`, return to step 2.

## 6. Common cases

### `"method":"error"` with `"Codex reported an error."`

Generic runtime bucket. Read the preceding `stderr` chunks and `mcpServer/startupStatus/updated` notifications — the real cause is usually one of: MCP server startup failure, provider authentication issue, or model-specific error.

```bash
jq -c 'select(.dir=="stderr" or .method=="mcpServer/startupStatus/updated")' "$RAW"
```

### Pending request that nobody answered

The turn will stay `waiting_request` indefinitely. `request list` shows it. Respond via `request respond` (see `pause-flow-handling.md`) or `turn interrupt` if the request is unresolvable.

### `dir:"exit"` with code 137 or signal `SIGKILL`

OS killed the codex child — usually memory pressure. Check `Activity Monitor`/`top` during the next run.

### No useful data in the raw log

Rare, but possible if `CODEX_WORKER_RAW_LOG=0` was set. Re-enable (unset the env) and re-run.

## 7. Recovery

Before retrying, decide whether to salvage partial work — see `guides/partial-work-recovery.md`.
