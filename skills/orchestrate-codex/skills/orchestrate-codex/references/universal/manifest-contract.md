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

The `<workspace-slug>-<hash>` is computed from cwd using the same algorithm codex-companion's `lib/state.mjs:resolveStateDir(cwd)` uses:

- `workspace-slug` = `basename(workspace_root)` sanitized to `[A-Za-z0-9._-]` (other chars → `-`, leading/trailing `-` stripped). Empty result falls back to `workspace`.
- `hash` = first 16 hex characters of `sha256(realpath(workspace_root))`.
- State root = `$CLAUDE_PLUGIN_DATA/state` when set; otherwise `${TMPDIR:-/tmp}/codex-companion`.

Sharing the slug+hash with codex-companion is intentional: rescue mode correlates manifest entries with codex-companion's `state.json` and `jobs/<id>.json` records under the same `<workspace-slug>-<hash>` directory.

The dispatcher and `bootstrap.sh` both use this algorithm. There is no separate XDG or md5 path.

## Top-level schema

```json
{
  "schema_version": 1,
  "run_id": "20260508T182030Z-7q4f",
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

| Field | Type | Notes |
|---|---|---|
| `schema_version` | int | Currently `1`. Rescue refuses to resume a manifest with newer `schema_version` than the skill version. |
| `run_id` | string | `<UTC ISO compact>-<4-hex>`. `os.urandom(2).hex()` for the suffix; collision-resistant for sub-second double-starts. |
| `mode` | string | One of `exec | batch | single | review | rescue`. Rescue mode preserves the original mode here. |
| `started_at` / `updated_at` | ISO 8601 UTC | `started_at` written once; `updated_at` bumped on every mutation. |
| `workspace_root` | abs path | `git rev-parse --show-toplevel` for git repos; cwd otherwise. |
| `state_dir` | abs path | `dirname(manifest_path)`. |
| `base_commit` | sha | Pinned at start. Used by rescue and audit to detect "did the user move main?" |
| `policy.model` | string | `gpt-5.5` default. Override via env `ORCHESTRATE_CODEX_MODEL`. |
| `policy.effort` | string | `xhigh` default. Override via env `ORCHESTRATE_CODEX_EFFORT`. |
| `policy.sandbox` | string | `danger-full-access`. The skill always uses bypass; this field documents what was passed. |
| `policy.bypass` | bool | `true` always. Documenting the bypass for auditing. |
| `policy.overrides` | object | Free-form key/value of session overrides recorded for rescue replay. |
| `concurrency_cap` | int | Mode-specific default; raise via `--concurrency N --i-have-measured`. |
| `monitor_root` | abs path | Where the runner writes log files; the Monitor command tails files under here. |
| `paths` | object | Mode-level artifact directories such as `prompts_dir`, `answers_dir`, `rounds_dir`, `audit_report`. |
| `preflight` | object | Parsed `bootstrap.sh` KEY=VALUE output or `{skipped:true}` in dry-run tests. |

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

| Field | Type | Notes |
|---|---|---|
| `id` | string | Stable, unique within the manifest. The runner identifies entries by id. |
| `slug` | string | Same value as `id` by default; separately settable so display labels can differ from internal ids. |
| `branch` | string \| null | Top-level branch field for exec/review runners. |
| `base_branch` | string \| null | Base ref for worktree setup and review. |
| `prompt_path` | abs path \| null | Prompt file consumed by exec/batch/single runners. |
| `mode_state` | object | Mode-specific. See per-mode tables below. |
| `worktree_path` | abs path \| null | Absolute path to the worktree (exec / review). Null for batch / single. |
| `log_path` | abs path | Per-entry log of stdout+stderr. The runner's per-job redirect target. |
| `jsonl_path` | abs path | Per-entry JSONL events captured from `codex exec --json`. |
| `answer_path` | abs path \| null | Output of `codex exec -o <file>`. Null for review (review writes findings JSON). |
| `status` | enum | Common: `queued | running | done | failed | skipped`. Review adds `converged | blocked | cap_reached`. |
| `attempts` | int | Incremented on each retry; rescue uses this to detect repeat failures. |
| `started_at` / `finished_at` | ISO 8601 UTC | `started_at` set on first state-flip to `running`; `finished_at` set on terminal status. |
| `exit_code` | int \| null | Exit code of the codex spawn (or wrapper). |
| `last_error` | string \| null | Free-form last-failure reason. Populated on `status="failed"` or as advisory (e.g. `json_event_dropped`). |
| `codex_thread_id` | string \| null | Captured from the first `thread.started` JSONL event; rescue uses it for `codex exec resume`. |
| `codex_session_id` | string \| null | Captured for codex-companion correlation. |

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
  "input_row": "https://example.com/foo",
  "prompt_file": "/abs/path/to/prompts/01-foo.md",
  "answer_size_bytes": 12345,
  "below_floor": false
}
```

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
  "to": "running",
  "actor": "run-fleet.sh",
  "reason": null
}
```

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

Hand-editing the manifest is forbidden. If audit reveals drift, fix via `manifest-update.py --entry <id> --set 'status=failed' --set 'last_error=manual-correction'`. The history shows the correction.

## Concurrent runs on the same workspace

Only one run per workspace at a time. The dispatcher checks for an existing manifest at the resolved path; if one exists with non-terminal entries (`queued | running`), it refuses with `error.code="concurrent_run_in_progress"`.

To start another run on the same workspace, wait for the first to finish or rescue/tidy it. This dispatcher does not support multiple active manifests in one state-root.

## Recovery

If the manifest is corrupted (e.g. partially-written JSON because the disk filled):

1. Run `python3 scripts/audit-fleet-state.py --manifest <path> --json --repair-dry-run`. It reads the manifest with a tolerant parser, lists what's salvageable, and writes a candidate repaired JSON to stdout.
2. Inspect the candidate. If acceptable, apply with `audit-fleet-state.py --repair-execute`.
3. If unsalvageable, copy the manifest to `<path>.broken-<timestamp>` and start a fresh run. Surface the broken file path so the user can inspect.

Never silently delete a corrupted manifest. The history may be the only record of what was attempted.

## Why outside the repo

The manifest lives under `resolveStateDir(cwd)` instead of inside the repo because:
- The orchestrator owns the state, not the project. Multiple repos share the same orchestrate-codex skill but each has its own state.
- It matches codex-companion's state model. Rescue can correlate by directory layout.
- Multiple Claude Code sessions can run the skill on the same repo serially without leaving orphan files in the repo's working tree.

The cost: a rescue run on a machine where the manifest doesn't exist (e.g. a different machine than the original run) cannot resume. Rescue is local-machine-only by design.
