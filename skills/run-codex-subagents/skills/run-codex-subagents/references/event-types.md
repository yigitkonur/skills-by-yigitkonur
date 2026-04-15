# Live Stream And Transcript Event Types

`codex-worker` exposes four related views of execution:

1. The raw NDJSON firehose at `artifacts.rawLogPath` — **the source of truth**. See below.
2. Live TTY streaming while `run`, `send`, `turn start`, `turn steer`, or `wait` is blocking.
3. Persisted, deduplicated transcript events in `artifacts.recentEvents` and the transcript JSONL file.
4. A synthesized readable log in `artifacts.displayLog`.

## Raw NDJSON (`artifacts.rawLogPath`) — the source of truth

Every app-server event, untouched. One JSON object per line. Added in `codex-worker@0.1.4`.

Envelope:

```json
{"ts":"2026-04-15T05:52:28.252Z","dir":"notification","method":"item/completed","params":{...}}
```

`dir` taxonomy:

- `rpc_out` — daemon → app-server request
- `rpc_in` — RPC result returned to daemon
- `notification` — app-server push event
- `server_request` — app-server asking the daemon for input (turn is paused until `request respond`)
- `stderr` — codex child stderr chunk
- `exit` — codex child process exited (`{code, signal}`)
- `protocol_error` — undecodable RPC line
- `daemon` — worker lifecycle: `launchTurn`, `completeExecution`, `failExecution`, `watchdog_fire`

Use this file for forensic work, live monitoring, and post-mortems. The transcript JSONL below is a derived view — it collapses and renames event types.

## Live TTY Format

When stdout is a TTY and the command is not `--async`, each notification is printed as:

```text
[event/name] {"json":"payload"}
```

Examples:

```text
[thread/status/changed] {"thread":{"status":"running"}}
[item/agentMessage/delta] {"delta":"Inspecting the repository"}
[item/completed] {"item":{"type":"agentMessage","text":"I updated the auth flow."}}
[error] {"message":"Codex reported an error."}
```

The exact event names come from the underlying app-server notification channel. Treat the bracketed token as the event name and the rest as JSON.

## Derived view: transcript JSONL (`artifacts.transcriptPath`)

The daemon stores normalized records in `threads/<thread-id>.jsonl`. Use this for replay-style queries. Types are collapsed/renamed relative to the raw NDJSON — for example, `item/agentMessage/delta` notifications become `assistant.delta` records here. Common record types visible through `read` are:

- `user`: the prompt text that started or continued the turn
- `assistant.delta`: streamed assistant text chunks
- `request`: a pending server request that needs `request respond`
- `notification`: raw app-server notifications not collapsed into a more specific local type
- `item/commandExecution/outputDelta`: streamed shell output
- `item/fileChange/outputDelta`: streamed file-change output

## Readable Display Log

`read` and `logs` build a human-friendly `displayLog` from the transcript. It prefers:
- full assistant messages when available
- `request: <method>` lines for blocked requests
- raw log lines only when the transcript cannot produce a readable summary

## What To Parse

- For live monitoring and forensic work, parse `artifacts.rawLogPath`. See `scripts/diagnostic-queries.md`.
- For structured automation, parse `--output json read <thread-id>` and use `artifacts.recentEvents` plus `pendingRequests`.
- For human monitoring, use `logs <thread-id>`.
- The transcript JSONL is the fallback when the raw log is unavailable (threads started before `codex-worker@0.1.4`).
