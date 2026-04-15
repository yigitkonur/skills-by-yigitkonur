# `read` And `logs` Output Format

Older worker CLIs exposed a dedicated `timeline.log`. `codex-worker` does not. The current surfaces are:

- live TTY streaming from a blocking `run`, `send`, `turn start`, `turn steer`, or `wait`
- `codex-worker read <thread-id>`
- `codex-worker logs <thread-id>`
- the persisted `.raw.ndjson` firehose, `.jsonl` transcript, and `.output` log files

For live forensic-grade monitoring, prefer `artifacts.rawLogPath` over `displayLog`. See `guides/log-artifacts.md`.

## Text Output From `read`

`codex-worker read <thread-id>` prints:

```text
Thread: <thread-id>
Status: <status>
Model: <model>
cwd: <cwd>
Turns tracked: <n>
Pending requests: <n>

Artifacts:
- transcript: <path>
- log: <path>

Recent turns:
- <turn-id> <status> <prompt preview>

Recent log:
...
```

Use the text form for operator triage. Use JSON when you need stable field access.

## Text Output From `logs`

`codex-worker logs <thread-id>` prints the resolved log path and a readable tail:

```text
Log: <path>

<display log line 1>
<display log line 2>
...
```

If no readable output exists yet, the command falls back to:

```text
(no log lines yet)
```

## JSON Fields To Prefer

From `codex-worker --output json read <thread-id>`:

- `artifacts.rawLogPath` — raw NDJSON firehose; source of truth for live monitoring
- `artifacts.displayLog`
- `artifacts.logTail`
- `artifacts.recentEvents`
- `artifacts.logPath`
- `artifacts.transcriptPath`

## Direct File Tail Patterns

Raw NDJSON firehose (preferred for live monitoring):

```bash
tail -F "$(codex-worker --output json read <thread-id> | jq -r '.artifacts.rawLogPath')"
```

Apply a milestone `jq` filter — see `guides/monitoring-patterns.md`.

Readable log (noisy for assistant deltas — one word per line):

```bash
tail -f "$(codex-worker --output json read <thread-id> | jq -r '.artifacts.logPath')"
```

Transcript JSONL (derived view):

```bash
tail -f "$(codex-worker --output json read <thread-id> | jq -r '.artifacts.transcriptPath')"
```

## Interpretation Notes

- `read` is richer than `logs`; it includes turns and pending requests.
- `logs` is better when you want only the recent readable output.
- `wait` is the blocking primitive; `read` and `logs` are the inspection primitives.
