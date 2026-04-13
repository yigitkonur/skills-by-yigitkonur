# Live Stream And Transcript Event Types

`codex-worker` exposes three related views of execution:

1. Live TTY streaming while `run`, `send`, `turn start`, `turn steer`, or `wait` is blocking.
2. Persisted transcript events in `artifacts.recentEvents` and the transcript JSONL file.
3. A synthesized readable log in `artifacts.displayLog`.

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

## Persisted Transcript Record Types

The daemon stores normalized records in `threads/<thread-id>.jsonl`. Common record types visible through `read` are:

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

- For automation, parse `--output json read <thread-id>` and use `artifacts.recentEvents` plus `pendingRequests`.
- For human monitoring, use `logs <thread-id>`.
- For raw forensic work, parse the transcript JSONL file directly.
