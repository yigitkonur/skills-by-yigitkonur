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
- `artifacts.transcriptPath`
- `artifacts.logPath`
- `artifacts.recentEvents`
- `artifacts.logTail`
- `artifacts.displayLog`
- `actions`

Use `read` as the main operator view. Use `logs` when you only want the readable output tail.

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
```

The workspace hash is derived from the thread working directory. The same thread id appears in both the transcript and log file names.

## State Root Override

Use a custom root when you need isolation:

```bash
export CODEX_WORKER_STATE_DIR=/tmp/codex-worker-state
codex-worker doctor
```

## Artifact Meaning

### Transcript (`threads/<thread-id>.jsonl`)

JSONL event stream persisted by the daemon. It includes:
- the original user prompt as a `user` record
- streamed assistant deltas
- pending request records
- raw notification envelopes needed to reconstruct history

### Log (`logs/<thread-id>.output`)

Plain-text execution log persisted for the thread. `logs` prefers the synthesized readable view (`displayLog`) and falls back to the raw log tail.

## Operator Queries

List the most recent local threads:

```bash
codex-worker --output json thread list --limit 20 | jq '.data[] | {id, status, cwd}'
```

Resolve artifact paths for one thread:

```bash
codex-worker --output json read <thread-id> | jq '.artifacts'
```

Watch the raw log file directly:

```bash
tail -f "$(codex-worker --output json read <thread-id> | jq -r '.artifacts.logPath')"
```

Inspect the transcript JSONL directly:

```bash
jq . "$(codex-worker --output json read <thread-id> | jq -r '.artifacts.transcriptPath')"
```
