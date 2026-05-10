# Manifest contract

The manifest is the single source of truth for an orchestrate-codex run. Every mode reads from it; every status transition writes to it. It is the input to rescue mode and the audit gate for tidy.

## Contents

- Path
- Top-level schema
- Entry schema
- Per-mode `mode_state`
- History schema
- Atomic write
- Lifecycle
- Concurrent runs
- Recovery
- Why outside the repo

## Path

```
resolveStateDir(cwd)/orchestrate-codex/manifest.json
```

The `<workspace-slug>-<hash>` is computed from cwd using the same algorithm codex-companion's `lib/state.mjs:resolveStateDir(cwd)` uses (verified against `scripts/codex-cc/lib/state.mjs:38-39`):

- `workspace-slug` = `basename(workspace_root)`, sanitized by replacing every run of characters outside `[a-zA-Z0-9._-]` with a single `-`, then stripping leading/trailing `-`. Empty result falls back to `workspace`. **Implementation note:** `state.mjs` **preserves case** and **allows `.` and `_`**; it does NOT lowercase, does NOT collapse internal `-` runs to a single `-`, and does NOT strip `.`/`_`. Treat the implementation as truth; this contract was reworded to match. (TODO: align spine wording or `state.mjs` if a future iteration tightens the slug rule.)
- `hash` = first 16 hex characters of `sha256(realpath(workspace_root))`. The `realpath` fallback is the unresolved `workspace_root` if `realpath` errors.

Sharing the slug+hash with codex-companion is intentional: rescue mode correlates manifest entries with codex-companion's `state.json` and `jobs/<id>.json` records under the same `<workspace-slug>-<hash>` directory.

Plugin-data resolution is shared across orchestrate-codex (dispatcher + bash runners) and the vendored codex-companion (`scripts/codex-cc/lib/state.mjs`). Both follow the same chain:

1. If `${CLAUDE_PLUGIN_DATA}` is set, the state root is `${CLAUDE_PLUGIN_DATA}/state/<workspace-slug>-<hash>/`. The orchestrate-codex manifest lives at `${CLAUDE_PLUGIN_DATA}/state/<workspace-slug>-<hash>/orchestrate-codex/manifest.json`.
2. If `${CLAUDE_PLUGIN_DATA}` is unset, the state root is `${TMPDIR:-/tmp}/codex-companion/<workspace-slug>-<hash>/`. The orchestrate-codex manifest lives at `${TMPDIR:-/tmp}/codex-companion/<workspace-slug>-<hash>/orchestrate-codex/manifest.json`.

If the resolved state dir is not writable, the dispatcher surfaces `error.code = "plugin_data_unwritable"` and stops with exit 5.

Verified against `scripts/codex-cc/lib/state.mjs:10, 41-43` (`FALLBACK_STATE_ROOT_DIR = path.join(os.tmpdir(), "codex-companion")`; resolver returns `pluginDataDir ? <plugin-data>/state : FALLBACK_STATE_ROOT_DIR`) and `scripts/bootstrap.sh:114-120` (`STATE_ROOT="$CLAUDE_PLUGIN_DATA/state"` or `STATE_ROOT="${TMPDIR:-/tmp}/codex-companion"`). There is no XDG path, no `~/.local/share/claude-code` fallback, and no md5 path. See `references/universal/plugin-data.md` for the canonical resolver.

Both writers always agree on the same `<slug>-<hash>` directory because they use the same algorithm against the same `cwd`; rescue's correlation between manifest entries (orchestrate-codex's `manifest.json`) and codex-companion job records (`state.json`, `jobs/<id>.json`) holds whenever both writers ran in the same process tree (so they observed the same `${CLAUDE_PLUGIN_DATA}` value). If the env var flips partway through the session — e.g. set on dispatch but unset for a later helper invocation — the two writers land in different roots and rescue cannot correlate. Always export `${CLAUDE_PLUGIN_DATA}` once for the session, or always invoke through `bootstrap.sh`. Never use `/tmp` directly as the manifest path of record yourself — cross-session collisions are silent.

## Top-level schema

```json
{
  "schema_version": 1,
  "run_id": "20260508T182030Z-7a4f",
  "mode": "exec",
  "started_at": "2026-05-08T18:20:30Z",
  "updated_at": "2026-05-08T18:42:11Z",
  "workspace_root": "/abs/path/to/repo",
  "state_dir": "/abs/state/<slug-hash>/orchestrate-codex",
  "base_commit": "abc1234567890def...",
  "policy": {
    "model": "gpt-5.5",
    "effort": "xhigh",
    "sandbox": "danger-full-access",
    "bypass": true,
    "overrides": {}
  },
  "concurrency_cap": 5,
  "monitor_root": "/abs/path/to/monitor-root",
  "paths": {},
  "preflight": {},
  "entries": [ /* one row per task; see below */ ],
  "history": [ /* append-only audit trail */ ]
}
```

All ISO 8601 timestamps in this manifest are written by `manifest-update.py` and `manifest-update.sh` at **second precision** with a `Z` suffix and **no fractional seconds, no numeric offset** (e.g. `2026-05-08T18:20:30Z`). Readers should not assume milliseconds.

| Field | Type | Required | Notes |
|---|---|---|---|
| `schema_version` | int | Yes | Currently `1`. Rescue refuses to resume a manifest with newer `schema_version` than the skill version. |
| `run_id` | string | Yes | `<UTC ISO compact>-<4-hex>`. `os.urandom(2).hex()` for the suffix (lowercase `[0-9a-f]{4}`); collision-resistant for sub-second double-starts. |
| `mode` | string | Yes | One of `exec | batch | single | review | rescue`. Rescue mode preserves the original mode here. |
| `started_at` | ISO 8601 UTC | Yes | Written once at run start. Second precision, `Z` suffix. |
| `updated_at` | ISO 8601 UTC | No | Bumped on every mutation when the writer chooses to set it. Not written by every helper invocation today; treat as advisory. |
| `workspace_root` | abs path | Yes | `git rev-parse --show-toplevel` for git repos; cwd otherwise. |
| `base_commit` | sha \| `""` | Yes | Pinned at start. Empty string for non-git workdirs (batch mode). Used by rescue and audit to detect "did the user move main?" |
| `policy.model` | string | Yes | `gpt-5.5` default. Override via env `ORCHESTRATE_CODEX_MODEL`. |
| `policy.effort` | string | Yes | `xhigh` default. Override via env `ORCHESTRATE_CODEX_EFFORT`. |
| `policy.sandbox` | string | Yes | `danger-full-access`. The skill always uses bypass; this field documents what was passed. |
| `policy.bypass` | bool | Yes | `true` always. Documenting the bypass for auditing. |
| `policy.overrides` | object | Yes | Container for session overrides recorded for rescue replay. Concurrency-cap override lands at `policy.overrides.concurrency` (see Concurrency cap section below). |
| `concurrency_cap` | int | Yes | Mode-specific default (see table below); raise via `--concurrency N --i-have-measured`. |
| `monitor_root` | abs path | Yes | Where the runner writes log files; the Monitor command tails files under here. |
| `entries` | array | Yes | One row per task. May be empty during rescue-detect inspection but never absent. |
| `history` | array | Yes | Append-only audit trail. Empty `[]` is valid at run start. |

### `concurrency_cap` per-mode defaults

The dispatcher (`scripts/orchestrate-codex.mjs:64-69`) seeds `concurrency_cap` from this table when the user does not pass `--concurrency`:

| Mode | Default `concurrency_cap` |
|---|---|
| exec | 5 |
| batch | 10 |
| single | 1 |
| review | 4 |
| rescue | inherits the original mode's cap (read from the manifest being rescued) |

Hard ceiling: `--concurrency > 20` is refused unless `--i-have-measured "<justification>"` is also passed. The justification is recorded in `policy.overrides.concurrency` (see Concurrency below). Absolute ceiling at 100 is refused unconditionally.

`paths` and `preflight` (top-level objects, not in the field table above): `paths` carries mode-level artifact directories such as `prompts_dir`, `answers_dir`, `rounds_dir`, `audit_report`. `preflight` carries parsed `bootstrap.sh` KEY=VALUE output or `{skipped:true}` in dry-run tests. Both are optional, defaulting to `{}`.

## Entry schema

```json
{
  "id": "01-search-rewrite",
  "slug": "01-search-rewrite",
  "branch": "wave1/search-rewrite",
  "base_branch": "main",
  "prompt_path": "/abs/path/to/prompts/01-search-rewrite.md",
  "worktree_path": "/abs/path/to/repo-wt-exec-search-rewrite",
  "log_path": "/abs/path/to/monitor-root/01-search-rewrite.log",
  "jsonl_path": "/abs/path/to/monitor-root/01-search-rewrite.jsonl",
  "answer_path": "/abs/path/to/monitor-root/01-search-rewrite.last-message.md",
  "status": "running",
  "attempts": 1,
  "started_at": "2026-05-08T18:21:01Z",
  "finished_at": null,
  "exit_code": null,
  "last_error": null,
  "codex_thread_id": null,
  "codex_session_id": null,
  "mode_state": { /* mode-specific; see below */ }
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | Yes | Stable, unique within the manifest. The runner identifies entries by id. |
| `slug` | string | Yes | Same value as `id` by default; separately settable so display labels can differ from internal ids. |
| `branch` | string \| null | No | Top-level branch field for exec/review runners. |
| `base_branch` | string \| null | No | Base ref for worktree setup and review. |
| `prompt_path` | abs path \| null | No | Prompt file consumed by exec/batch/single runners. |
| `mode_state` | object | Yes | Mode-specific. See per-mode tables below. May be `{}` for rescue-amended entries. |
| `worktree_path` | abs path \| null | Yes | Absolute path to the worktree (exec / review). Null for batch / single. |
| `log_path` | abs path | Yes | Per-entry log of stdout+stderr. The runner's per-job redirect target. |
| `jsonl_path` | abs path | Yes | Per-entry JSONL events captured from `codex exec --json`. |
| `answer_path` | abs path \| null | Yes | Output of `codex exec -o <file>`. Null for review (review writes findings JSON). |
| `status` | enum | Yes | Common: `queued | running | done | failed | skipped | rescued`. Review adds `converged | blocked | cap_reached`. The enum has no hung-specific value; record hung-process failures as `status="failed"` with `last_error="hung_25min"`. |
| `attempts` | int | Yes | Incremented on each retry; rescue uses this to detect repeat failures. |
| `started_at` | ISO 8601 UTC \| null | Yes | Set on first state-flip to `running`. Null while `queued`. Second precision, `Z` suffix. |
| `finished_at` | ISO 8601 UTC \| null | Yes | Set on terminal status. Null otherwise. Second precision, `Z` suffix. |
| `exit_code` | int \| null | Yes | Exit code of the codex spawn (or wrapper). Null while non-terminal. |
| `last_error` | string \| null | Yes | Free-form last-failure reason. Populated on `status="failed"` or as advisory (e.g. `json_event_dropped`, `hung_25min`). |
| `codex_thread_id` | string \| null | Yes | Captured from the first `thread.started` JSONL event; rescue uses it for `codex exec resume`. |
| `codex_session_id` | string \| null | Yes | Captured for codex-companion correlation. |

### Per-mode `mode_state`

**exec mode:**
```json
{
  "branch": "wave1/search-rewrite",
  "base_branch": "main",
  "prompt": null,
  "prompt_file": "/abs/path/to/prompts/01-search-rewrite.md",
  "post_verify_cmd": "pnpm test",
  "post_verify_exit": null
}
```

**batch mode:**
```json
{
  "batch": {
    "input": "https://example.com/foo",
    "input_row": "https://example.com/foo",
    "prompt_file": "/abs/path/to/prompts/01-foo.md"
  },
  "answer_size_bytes": 12345,
  "below_floor": false
}
```

`answer_size_bytes` and `below_floor` are written at the **top level of
`mode_state`** (not nested under `mode_state.batch`). The runner writes the
top-level shape; `audit-sizes.sh` and rescue/audit helpers read it from
there. The nested `mode_state.batch.*` block carries only the per-row inputs
seeded by the dispatcher.

**single mode:**
```json
{
  "prompt_file": "/abs/path/to/prompt.md",
  "cwd": "/abs/path/to/repo",
  "reuse_worktree": false
}
```

**review mode:**
```json
{
  "branch": "feat/auth",
  "base_branch": "main",
  "rounds": [
    { "round": 1, "findings_path": "/abs/.../feat-auth.1.json", "major_count": 3, "minor_count": 7 },
    { "round": 2, "findings_path": "/abs/.../feat-auth.2.json", "major_count": 0, "minor_count": 4 }
  ],
  "terminal_state": "converged"
}
```

**rescue mode:** rescue does not create new entries; it amends existing ones. The history trail shows what changed. `mode_state` is preserved from the original mode.

## History schema

The `history` array is append-only. Every status flip appends one record:

```json
{
  "ts": "2026-05-08T18:21:01Z",
  "entry_id": "01-search-rewrite",
  "from": "queued",
  "to": "running"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `ts` | ISO 8601 UTC | Yes | Second precision, `Z` suffix. |
| `entry_id` | string | Yes | Matches an `entries[].id`. |
| `from` | status enum \| null | Yes | Previous status; `null` if entry was just created. |
| `to` | status enum | Yes | New status. |
| `actor` | string | **Optional — writers do not currently populate; reserved for future iterations.** Both `manifest-update.py` and `manifest-update.sh` emit only `{ts, entry_id, from, to}`. Audit code must treat the key as missing-by-default. |
| `reason` | string \| null | **Optional — writers do not currently populate; reserved for future iterations.** Same status as `actor`. |

Use cases:
- Rescue inspects history to detect oscillation (`failed → queued → failed → queued → ...`).
- Audit detects manual edits (history doesn't have an entry for a status change → manifest was hand-edited; refuse to act on it).
- Post-mortem: tail the history for a forensic timeline.

## Atomic write

Every mutation goes through this sequence. The dispatcher uses Node `mktemp` + rename for seed/reset writes; bash runners use `scripts/manifest-update.sh`; Python diagnostics use `scripts/manifest-update.py` when they need write support.

```python
import fcntl, json, os, tempfile
from pathlib import Path

def atomic_write(manifest_path: Path, mutator):
    lock = manifest_path.with_suffix(manifest_path.suffix + ".lock")
    with lock.open("w") as lf:
        fcntl.flock(lf.fileno(), fcntl.LOCK_EX)
        # Read current state.
        if manifest_path.exists():
            with manifest_path.open() as f:
                data = json.load(f)
        else:
            data = {}
        # Mutate.
        mutator(data)
        # Write to temp in same dir, then rename.
        fd, tmp_path = tempfile.mkstemp(
            dir=manifest_path.parent,
            prefix=".manifest.",
            suffix=".tmp",
        )
        with os.fdopen(fd, "w") as tmp:
            json.dump(data, tmp, indent=2)
            tmp.write("\n")
        os.replace(tmp_path, manifest_path)
        # flock released on lf close.
```

Properties:
- Single-writer at a time (advisory `flock` on POSIX; tempfile-rename is the durability backstop).
- Readers do not block. They may see a previous version until the rename completes; `os.replace` is atomic on the same filesystem.
- The `.lock` file remains after release (intentional — saves an `unlink` race on next acquire). Tidy removes it.

Concurrent invocations of either manifest-update helper against the same manifest serialize through the lock. Never hand-roll manifest edits inside a runner.

## Lifecycle

| Event | Manifest action |
|---|---|
| Run start | Dispatcher creates manifest; writes `schema_version`, `run_id`, `mode`, `started_at`, `policy`, `concurrency_cap`, all entries with `status="queued"`. |
| Worker starts | Worker (via runner) sets `entries[i].status="running"`, `started_at`, increments `attempts`. |
| Worker progresses | `codex_thread_id` written from first JSONL event; `log_path`/`jsonl_path` populated. |
| Worker finishes OK | `status="done"` for exec/batch/single, `status="converged"` for review no-major rounds; `finished_at`, `exit_code=0`, possibly verify/classifier paths. |
| Worker fails | `status="failed"`, `finished_at`, `exit_code=N`, `last_error="..."`. |
| Rescue redispatch | Re-flip selected entries to `queued`, clear prior terminal fields, append history rows, then invoke the original mode's runner with `--only`. The runner increments `attempts`. |
| Tidy success | Manifest **deleted** (only after all entries terminal AND every worktree removed). |

Hand-editing the manifest is forbidden. If audit reveals drift, fix via `manifest-update.py entry --entry <id> --set 'status=failed' --set 'last_error=manual-correction'`. The history shows the correction.

## Concurrent runs on the same workspace

Only one run per workspace at a time. The dispatcher checks for an existing manifest at the resolved path; if one exists with non-terminal entries (`queued | running`), it refuses with `error.code="concurrent_run_in_progress"`.

To start a second run on the same workspace:
- Wait for the first to finish (its tidy will delete the manifest).
- Run rescue mode against the existing manifest (the supported path).
- Pass `--force-new-run --run-id <custom>` to write a sibling manifest at `manifest.<custom-run-id>.json` in the same state directory. **Implemented** in `orchestrate-codex.mjs` for exec/batch/single. See `references/universal/idempotency.md` for the runner-level race caveats.

## Recovery

If the manifest is corrupted (e.g. partially-written JSON because the disk filled):

1. **Diagnose.** `python3 scripts/audit-fleet-state.py --manifest <path> --json` reports `manifest_present: false` for an unparseable manifest (the audit script never tries to repair). The dispatcher's `node scripts/orchestrate-codex.mjs rescue --manifest <path>` returns `error.code="manifest_corrupt"` with the parse error in `message`. Either signal confirms the file is broken.
2. **Preserve.** Copy the manifest to `<path>.broken-<timestamp>` so its history survives.
3. **Replace.** Delete the original at `<path>` so the dispatcher's concurrency gate clears, then start a fresh run via the normal `node scripts/orchestrate-codex.mjs <mode>` invocation. Or, to keep the broken file in place, use `--force-new-run --run-id <custom>` to write a sibling at `manifest.<custom-run-id>.json`. Surface the `.broken-<timestamp>` path so the user can inspect.

Never silently delete a corrupted manifest. The history may be the only record of what was attempted.

> *Note: an automated repair flow (`--repair-dry-run` / `--repair-execute`) is **Planned — not yet wired**. Today, audit-fleet-state.py is read-only by design; recovery is the preserve-and-replace flow above.*

## Why outside the repo

The manifest lives under `resolveStateDir(cwd)` instead of inside the repo because:
- The orchestrator owns the state, not the project. Multiple repos share the same orchestrate-codex skill but each has its own state.
- It matches codex-companion's state model. Rescue can correlate by directory layout.
- Multiple Claude Code sessions can run the skill on the same repo serially without leaving orphan files in the repo's working tree.

The cost: a rescue run on a machine where the manifest doesn't exist (e.g. a different machine than the original run) cannot resume. Rescue is local-machine-only by design.
