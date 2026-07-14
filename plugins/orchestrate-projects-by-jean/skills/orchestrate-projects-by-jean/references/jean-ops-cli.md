# Jean Operations CLI

Use this reference for trusted Jean MCP discovery, compact read-only inventory, run-aware session watching, durable controller leases, and Codex shell-handle continuation.

## Contents

- [Hybrid boundary](#hybrid-boundary)
- [Runtime and trust model](#runtime-and-trust-model)
- [Command and schema contract](#command-and-schema-contract)
- [Inventory workflow](#inventory-workflow)
- [Run-aware watcher workflow](#run-aware-watcher-workflow)
- [Events, checkpoints, and exits](#events-checkpoints-and-exits)
- [Computer Use handoff](#computer-use-handoff)
- [Troubleshooting](#troubleshooting)

## Hybrid boundary

The canonical truth-source table lives in `jean-state-and-steering.md`. In short: use `jean_ops.py` for deterministic read-only MCP evidence and waits; native Jean MCP for explicit-ID control only under the ownership protocol; Computer Use for selected UI state, approvals, model/mode, prompt placement, and visible start proof; repo/provider/runtime probes for git, CI, deploy, and behavior truth.

A terminal watcher verdict routes the manager to completion gates. It never approves work.

## Runtime and trust model

Resolve the installed script from any working directory:

```bash
JEAN_OPS="${CODEX_HOME:-$HOME/.codex}/skills/orchestrate-projects-by-jean/scripts/jean_ops.py"
/usr/bin/python3 "$JEAN_OPS" --help
```

The Python 3.9-compatible script never launches or mutates Jean. Its normal trust path:

1. reads only the default user-owned, non-writable `~/.codex/config.toml`;
2. parses it with `tomllib`, `tomli`, or a deliberately restricted fail-closed fallback;
3. requires the owned installed Jean app binary plus exactly `--jean-mcp-stdio`;
4. requires an owned Unix `JEAN_MCP_SOCKET` that already exists;
5. permits only `mcp2cli` or exact cached `uvx --offline mcp2cli` backends;
6. passes a minimal environment plus Jean-scoped config values, not the full Codex shell environment;
7. discovers live tool schemas, rejects normalized-name collisions, and blocks known mutation tools;
8. bounds output strings/bytes and redacts configured credential values.

`--allow-unsafe-config` and `--allow-unsafe-backend` are explicit trust escapes for controlled diagnostics, not routine supervision. A missing socket is an observation-path failure; never restart Jean to repair it.

Run offline validation after any script change without creating bytecode artifacts:

```bash
/usr/bin/python3 "$JEAN_OPS" self-test
/usr/bin/python3 -O "$JEAN_OPS" self-test
```

Both modes must execute and report the same named checks; the suite does not use `assert`.

## Command and schema contract

| Command | Purpose |
|---|---|
| `doctor [--probe] [--require A,B]` | validate trust, socket/backend, required tools/inputs, and schema hash |
| `tools` | list allowed reads, blocked mutations, tool count, and schema hash |
| `schema TOOL` | return one live MCP tool schema and catalog hash |
| `capabilities [--require A,B]` | validate required tools/inputs and emit schema hash |
| `projects` | compact project identities and roots |
| `worktrees --project-id ID` | verify the project ID, then return compact worktree identities, paths, branches, and labels |
| `sessions --worktree-id ID` | verify the worktree ID, then return compact session identities and active session ID |
| `status --session-id ID` | raw status plus normalized session/run markers |
| `messages --session-id ID --limit N` | at most `N=1..100` recent message records; compact and tool-payload-free by default |
| `changes --worktree-id ID --max-files N` | bounded change summary, `N=1..500` |
| `read TOOL --arg key=value` | another live-schema-validated allowlisted read |
| `leases` | list durable session controller leases and liveness |
| `watch-session ...` | guarded NDJSON observation under a durable lease |

Non-watcher commands emit one `jean-ops/v2` envelope with `ok`, `command`, `observed_at`, `data`, and `meta`, or `error` plus semantic `exit_code`. `meta.bounds` records applied byte/string limits. Parent-validated inventory includes `meta.parent_id_verified=true`; unknown parents exit 13 with `mcp_not_found` instead of looking like an empty child list. Watcher events use a distinct versioned NDJSON contract below.

Global options precede the command. `--call-timeout` is `1..120` seconds; it caps each child process while the watcher’s one absolute `--timeout` remains authoritative. Never invent arguments: run `schema TOOL` first.

## Inventory workflow

```bash
/usr/bin/python3 "$JEAN_OPS" doctor --probe
/usr/bin/python3 "$JEAN_OPS" capabilities
/usr/bin/python3 "$JEAN_OPS" projects
/usr/bin/python3 "$JEAN_OPS" worktrees --project-id PROJECT_ID
/usr/bin/python3 "$JEAN_OPS" sessions --worktree-id WORKTREE_ID
/usr/bin/python3 "$JEAN_OPS" status --session-id SESSION_ID
/usr/bin/python3 "$JEAN_OPS" messages --session-id SESSION_ID --limit 12
/usr/bin/python3 "$JEAN_OPS" messages --session-id SESSION_ID --limit 1 --include-tool-details --max-tool-calls 10
/usr/bin/python3 "$JEAN_OPS" changes --worktree-id WORKTREE_ID --max-files 80
```

Use returned IDs, never display-name-derived paths. Reconcile the chain with the visible Jean header and with exact repo root, branch, HEAD, dirt, and worktree inventory before mutation. Cached Jean counts are triage hints, not git truth.

For `messages`, `--limit` always means returned message records even if Jean's upstream limit represents a turn or pair. `meta.messages` reports the requested limit, upstream count, wrapper trimming, and applied unit. The default form preserves message content and compact tool/content-block summaries while omitting tool inputs/outputs, caps each message's content at 4,000 characters, and caps the command at 100,000 bytes. Use `--include-tool-details` only when the actual payload is required; it is bounded by `--max-tool-calls`, per-string limits, and a 250,000-byte ceiling. The generic `read read_session_messages` path remains the raw live-schema escape hatch and retains global bounds.

The generic `read` path validates names and arguments against the live schema and rejects credential-shaped arguments. Do not route sends, cancellation, creation, or label mutation through the script.

## Run-aware watcher workflow

Capture a baseline run ID before sending. Start the watcher through unified shell execution without `&`, `nohup`, or an invented callback:

```bash
/usr/bin/python3 "$JEAN_OPS" watch-session \
  --session-id SESSION_ID \
  --after-run-id BASELINE_RUN_ID \
  --until terminal \
  --timeout 1800 \
  --interval 2 \
  --max-interval 30 \
  --controller-id CODEX_TASK_ID
```

When the new run ID is already known, prefer `--expect-run-id NEW_RUN_ID`. Use `--allow-existing-terminal` only for an intentional one-shot audit of an already-ended run. Without a run flag, the watcher refuses to accept its first already-terminal run and waits for a new run; session-level `activelyManaged`/running state always outranks an older terminal `latestRun`.

The watcher records run ID, status, `endedAt`, `userMessageId`, latest message marker, and timestamps when Jean provides them. A run change after adoption exits as superseded rather than silently observing the replacement.

One process owns one Jean session lease under the private state root. The lease records watcher/controller IDs, PID, host, run guard/current run, start/heartbeat/expiry times, sequence, and result path. A conflicting live lease exits 14. Inspect `leases`; never evade ownership with another `--state-root`.

If shell execution returns a shell `session_id`, continue only with its matching stdin/poll tool. The shell handle, Jean session ID, Jean run ID, Codex task ID, and automation ID are different typed identifiers.

The watcher uses one-shot mcp2cli processes with one shared absolute deadline, bounded transient retries, ownership checks during calls, and process-group TERM/KILL cleanup. The first observation is always `state`, never `heartbeat`. Change detection hashes Jean session/run markers plus guard identity and eligibility; explanatory guard-reason wording is emitted for diagnosis but never counts as external progress.

## Events, checkpoints, and exits

Every NDJSON event includes `schema_version`, `watcher_id`, `session_id`, `sequence`, `event`, and `observed_at`. Normal flow is `start`, first `state`, later changed `state`/optional `heartbeat`, then `target`, `timeout`, `superseded`, `controller_lost`, `interrupted`, or `error`. A checkpoint failure emits `persistence_error` and a structured terminal `error`; it cannot return success.

The default result path is collision-safe and private. A custom `--result-file` must not already exist. Each event checkpoints a `0600` JSON file containing `last_event`, identity, schema version, and update time. If persistence fails, further writes are disabled while stdout remains valid NDJSON.

| Exit | Class | Manager action |
|---|---|---|
| 0 | target observed | refresh identity/UI; run completion gates for terminal runs |
| 2 | usage | correct syntax/range from help or schema |
| 10 | config | repair the verified config problem; do not restart Jean |
| 11 | trust | inspect executable/config/socket/schema collision; do not bypass casually |
| 12 | unavailable | inspect missing backend/socket/executable while preserving Jean |
| 13 | MCP | inspect stable error code/retryability and live capabilities |
| 14 | lease | reconcile the existing owner; do not duplicate it |
| 15 | persistence | rely on structured stdout, repair result path, and verify lease cleanup |
| 16 | superseded | re-inventory current run/owner before any new watcher or send |
| 124 | deadline | inspect last state; timeout is not task completion |
| 129 | controller lost/HUP | inspect checkpoint and owner/process state before resuming |
| 130/143 | INT/TERM | reconcile checkpoint, process, lease, and intended stop |

The result file is durable evidence, not a push notification. Codex must still own/wait on the shell handle or be woken by a verified automation capability.

## Computer Use handoff

Return to bundled Computer Use for selected UI identity, backend/model/provider/YOLO state, approvals, prompt placement, visible start proof, or any UI/MCP conflict. Fetch fresh app state before each action. After a UI mutation, record the new run/message marker before handing observation back to the watcher.

Use the native MCP fast path only under the guarded workflow in `jean-state-and-steering.md`. Never let UI and native MCP send concurrently.

## Troubleshooting

| Symptom | Response |
|---|---|
| Socket absent | continue safe repo/provider proof; do not launch/restart Jean |
| Backend unavailable | use current native MCP reads if available; do not fetch during supervision |
| Capability mismatch | run `tools`, `schema TOOL`, and `capabilities`; treat live schema/hash as authority |
| Parent ID returns not-found | rerun explicit project → worktree → session discovery; do not reinterpret it as an empty project |
| Message history is too large | keep compact defaults; lower global bounds or request one record; opt into bounded tool details only for a specific diagnostic |
| Watcher remains `unknown` | inspect raw `status` and fresh UI; do not guess |
| Stale terminal latest run while session runs | keep watching baseline/new run; never approve the old run |
| Lease conflict | inspect `leases`, shell handles, PID/controller, expiry, and run identity |
| Persistence failure | use structured stdout, verify nonzero exit and lease cleanup, then choose a new private path |
| UI and MCP disagree | stop mutations and reconcile explicit session/run/history before one controller resumes |
