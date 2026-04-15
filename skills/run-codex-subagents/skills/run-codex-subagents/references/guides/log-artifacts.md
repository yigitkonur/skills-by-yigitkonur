# Log Artifacts — What Each File Contains, When It Is Authoritative

`codex-worker` writes three files per thread. Read them for different questions. Use the right one or you will misread what the worker is doing.

## The three files

Resolve paths from `read`:

```bash
THREAD_ID=<thread-id>
JSON=$(codex-worker --output json read "$THREAD_ID")
RAW=$(printf '%s' "$JSON" | jq -r '.artifacts.rawLogPath')
TRANSCRIPT=$(printf '%s' "$JSON" | jq -r '.artifacts.transcriptPath')
LOG=$(printf '%s' "$JSON" | jq -r '.artifacts.logPath')
```

| File | Field | Content | Authority |
|---|---|---|---|
| `<hash>/logs/<id>.raw.ndjson` | `rawLogPath` | Every app-server event verbatim, one JSON object per line, timestamped. Added in `codex-worker@0.1.4`. | **Source of truth** for forensic work and live monitoring. |
| `<hash>/threads/<id>.jsonl` | `transcriptPath` | Deduplicated structured transcript (user prompt, assistant deltas, server requests, file/command deltas). | Derived view. Good for replaying what the model said and did. |
| `<hash>/logs/<id>.output` | `logPath` | Plain-text tail, one `logLine` per notification. Assistant deltas are one word per line. | Feeds the readable `logs` command. Noisy to tail directly. |

Tail `rawLogPath`. Everything else is a derived view.

## Raw NDJSON envelope

Each line:

```json
{"ts":"2026-04-15T05:52:28.252Z","dir":"notification","method":"item/completed","params":{...}}
```

Fields: `ts` (ISO), `dir` (direction tag), then any of `method`, `id`, `params`, `result`, `error`, `data`, `message`.

### `dir` taxonomy

- `rpc_out` — daemon → app-server call (`initialize`, `thread/start`, `turn/start`, `account/read`, …).
- `rpc_in` — RPC result returned to the daemon.
- `notification` — app-server push event (`turn/started`, `turn/completed`, `item/started`, `item/completed`, `item/agentMessage/delta`, `item/commandExecution/outputDelta`, `thread/tokenUsage/updated`, `hook/started`, `hook/completed`, `mcpServer/startupStatus/updated`, `thread/status/changed`, `error`).
- `server_request` — app-server asking the daemon for input (`item/tool/requestUserInput`, approval prompts). Until you respond via `request respond`, the turn is paused.
- `stderr` — stderr chunk from the `codex` child. Rare but high signal.
- `exit` — codex child exited. Payload: `{code, signal}`.
- `protocol_error` — undecodable RPC line from the child.
- `daemon` — our own lifecycle markers: `launchTurn`, `completeExecution`, `failExecution`, `watchdog_fire`.

## Which file answers which question

| Question | Signal |
|---|---|
| Is the turn moving? | `tail -n +1 -F "$RAW"` — replays history, then streams live. Any new line = alive. Silence ≥ `CODEX_WORKER_TURN_TIMEOUT_MS` = stuck. |
| Is the turn blocked on me? | A `{"dir":"server_request"}` line in `$RAW`, or non-empty `pendingRequests` in `read`. |
| What tool call ran last? | `jq 'select(.method=="item/completed" and .params.item.type=="commandExecution")' "$RAW"`. |
| Why did the turn fail? | `jq 'select(.dir=="daemon" or .dir=="exit" or .method=="error" or .dir=="protocol_error")' "$RAW"`. |
| Replay what the model said? | `jq -r 'select(.method=="item/agentMessage/delta") \| .params.delta' "$RAW"`. |

`Status:` from `codex-worker read` is **not** a live progress signal. It flips at turn boundaries (`turn/started` → `active`, `turn/completed` → `idle`, watchdog or exit → `failed`). A healthy running turn stays `active` for its entire duration.

## Signatures worth spotting

Watchdog killed the turn:

```bash
jq -c 'select(.dir=="daemon" and (.message | test("watchdog_fire")))' "$RAW"
```

Codex child exited unexpectedly:

```bash
jq -c 'select(.dir=="exit")' "$RAW"
```

Any reported error:

```bash
jq -c 'select(.method=="error")' "$RAW"
```

## Normal states that look like errors

- **`account/read` returning `{account: null, requiresOpenaiAuth: false}`** is healthy when `~/.codex/config.toml` has `requires_openai_auth = false` (custom provider, e.g. `model_provider = "codex-lb"`). Honored since `codex-worker@0.1.3`.
- **`account rate-limits` returning `{data: null, note: "rate limits unavailable: requires_openai_auth=false"}`** — same reason; rate limits are OpenAI-only.
- **`Status: active` for a long time** — a healthy long turn. Tail the raw log and confirm fresh events; do not flip to `Status:`-polling.

## Idle watchdog

`codex-worker@0.1.5` armed a per-turn idle watchdog:

- Default window: 30 min of wire silence. Resets on every `notification` / `server_request`.
- Inline override:
  ```bash
  CODEX_WORKER_TURN_TIMEOUT_MS=3600000 codex-worker run task.md
  ```
- Persistent: `export CODEX_WORKER_TURN_TIMEOUT_MS=3600000` in `~/.zshrc`.
- Disable raw firehose (rare): `CODEX_WORKER_RAW_LOG=0`. Loses forensic detail.

Death signature:

```json
{"dir":"daemon","message":"watchdog_fire turnId=<id> idle_ms=<n> limit_ms=<n>"}
```

When you see that line, the daemon timed out the turn and `SIGTERM`'d the codex child. Raise `CODEX_WORKER_TURN_TIMEOUT_MS` and re-run.
