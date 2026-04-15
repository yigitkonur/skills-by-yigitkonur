# Thread Records, Artifacts, And State Layout

`codex-worker` is thread-centric. A thread owns the workspace context, its turns, pending requests, and the local transcript/log artifacts.

## Quick Inspection Commands

```bash
codex-worker thread list
codex-worker read <thread-id>
codex-worker logs <thread-id>
codex-worker --output json thread read <thread-id>
```

## Verified Thread Creation Shape

`thread start` returns the thread record, selected model/provider, and convenience actions:

```bash
codex-worker --output json thread start --cwd /abs/project
```

Representative fields:
- `thread.id`
- `thread.cwd`
- `thread.status`
- `model`
- `modelProvider`
- `actions.read`
- `actions.send`
- `actions.requests`

## `read` / `thread read` JSON Shape

Important top-level fields from `codex-worker --output json read <thread-id>`:

- `thread`: current remote-or-local thread record
- `localThread`: persisted local view
- `turns`: locally tracked turns for this thread
- `pendingRequests`: unresolved server requests for this thread
- `artifacts.rawLogPath` — raw NDJSON firehose (the source of truth; see `guides/log-artifacts.md`)
- `artifacts.transcriptPath`
- `artifacts.logPath`
- `artifacts.recentEvents`
- `artifacts.logTail`
- `artifacts.displayLog`
- `actions`

Use `read` as the main operator view. Tail `artifacts.rawLogPath` for live monitoring and diagnostics. Use `logs` when you only want the readable output tail.

## Default Disk Layout

By default, state lives under:

```text
~/.codex-worker/
```

Verified files and directories:

```text
~/.codex-worker/daemon.json
~/.codex-worker/registry.json
~/.codex-worker/workspaces/<workspace-hash>/threads/<thread-id>.jsonl
~/.codex-worker/workspaces/<workspace-hash>/logs/<thread-id>.output
~/.codex-worker/workspaces/<workspace-hash>/logs/<thread-id>.raw.ndjson
```

The workspace hash is derived from the thread working directory. The same thread id appears in the transcript, log, and raw-log file names.

Additionally read by `codex-worker@0.1.3+`:

```text
~/.codex/config.toml
```

Top-level scalars honored: `model`, `model_provider`, `approval_policy`, `sandbox_mode`, `requires_openai_auth`. When `requires_openai_auth = false`, `account read` returns `{account: null, requiresOpenaiAuth: false}` and `account rate-limits` returns `{data: null, note: "rate limits unavailable: requires_openai_auth=false"}` — these are healthy for custom providers (e.g. `model_provider = "codex-lb"`), not errors.

## State Root Override

Use a custom root when you need isolation:

```bash
export CODEX_WORKER_STATE_DIR=/tmp/codex-worker-state
codex-worker doctor
```

## Artifact Meaning

### Raw NDJSON (`logs/<thread-id>.raw.ndjson`)

Firehose: every app-server event with a `{ts, dir, method?, params?, ...}` envelope. `dir` ∈ `rpc_out | rpc_in | notification | server_request | stderr | exit | protocol_error | daemon`. Source of truth for live monitoring and post-mortems. Added in `codex-worker@0.1.4`.

### Transcript (`threads/<thread-id>.jsonl`)

Derived view. JSONL event stream the daemon chose to surface: the original user prompt as a `user` record, streamed assistant deltas, pending request records, fallback notification envelopes. Good for replay; for forensic work prefer the raw NDJSON.

### Log (`logs/<thread-id>.output`)

Plain-text execution log persisted for the thread. `logs` prefers the synthesized readable view (`displayLog`) and falls back to this raw text tail.

## Operator Queries

List the most recent local threads:

```bash
codex-worker --output json thread list --limit 20 | jq '.data[] | {id, status, cwd}'
```

Resolve artifact paths for one thread:

```bash
codex-worker --output json read <thread-id> | jq '.artifacts'
```

Tail the raw NDJSON firehose (recommended for live monitoring):

```bash
tail -F "$(codex-worker --output json read <thread-id> | jq -r '.artifacts.rawLogPath')"
```

Apply a milestone filter — see `guides/monitoring-patterns.md` and `scripts/diagnostic-queries.md`.

Inspect the transcript JSONL directly:

```bash
jq . "$(codex-worker --output json read <thread-id> | jq -r '.artifacts.transcriptPath')"
```
