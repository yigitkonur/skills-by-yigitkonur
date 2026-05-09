# audit-fleet-state.py

Read-only manifest+filesystem state dump. Surfaces drift between `manifest.status` and reality (worktree existence, log file presence/growth, codex-companion job correlation).

## Inputs

```bash
python3 audit-fleet-state.py --manifest <path> [--json] [--workspace-root <dir>]
```

| Arg | Notes |
|---|---|
| `--manifest <path>` | Required. The manifest to audit. |
| `--json` | Emit machine-readable JSON instead of human table |
| `--workspace-root <dir>` | Override `manifest.workspace_root` for the file-existence checks |

## Outputs

Human (default):

```
Fleet state — run_id 20260508T182030Z-7q4f, mode exec, started 2026-05-08T18:20:30Z

Entry ID                 Status   Drift   Worktree     Log     Answer    Notes
01-search-rewrite        done     -       present      ok      8.2 KB    -
02-cache-eviction        running  STALE   present      ok      -         pid dead 5m
03-config-editor         failed   -       missing      gone    -         "503 Service Unavailable"
04-alert-fsm             queued   -       n/a          n/a     n/a       -

Drift summary: 1 stale running entry; consider rescue.
```

JSON (`--json`):

```json
{
  "manifest_path": "...",
  "run_id": "...",
  "mode": "exec",
  "started_at": "...",
  "actionable": true,
  "drift_total": 1,
  "entries": [
    {"id": "01-search-rewrite", "status": "done", "drift": [], "worktree_present": true, ...},
    {"id": "02-cache-eviction", "status": "running", "drift": ["pid_dead"], "worktree_present": true, ...},
    ...
  ],
  "orphan_worktrees": [],
  "recommendations": ["consider rescue for 1 stale running entry"]
}
```

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Manifest read; fleet state clean OR drift surfaced |
| 1 | Manifest is corrupt (couldn't parse) |
| 2 | Manifest missing |

## Behavior

- Reads the manifest and the filesystem; cross-correlates per-entry.
- Detects:
  - `pid_dead`: status==running but the recorded pid is no longer alive (`os.kill(pid, 0)` raises `ProcessLookupError`).
  - `worktree_missing`: `worktree_path` set but `git worktree list` doesn't show it.
  - `log_stale`: log file's last-modified is older than `2 × MONITOR_INTERVAL` (default 60 s).
  - `answer_missing`: status==done but answer file doesn't exist.
  - `answer_empty`: status==done but answer file is empty.
- Detects orphan worktrees: paths matching `<repo>-wt-*` not referenced in any manifest entry.
- Read-only: never writes.

## Notes

Drift detected → use `manifest-update.py` to flip the affected entries to `failed`, then run rescue. Never hand-edit the manifest based on drift; the history row matters.

The `--repair-dry-run` and `--repair-execute` flags are reserved for a future iteration; current implementation is audit-only. The recommendations field gives the next action.
