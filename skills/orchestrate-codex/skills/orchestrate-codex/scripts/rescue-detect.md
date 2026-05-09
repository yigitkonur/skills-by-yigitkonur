# rescue-detect.py

Read manifest + filesystem + codex-companion job records; classify each entry into `done | failed | never_started | in_flight | unknown`; emit JSON with redo recommendations. Read-only.

## Inputs

```bash
python3 rescue-detect.py --manifest <path> [--workspace-root <dir>] [--stale-tick-seconds N] [--stale-multiplier N]
```

| Arg | Default | Notes |
|---|---|---|
| `--manifest <path>` | required | The manifest to classify |
| `--workspace-root <dir>` | from manifest | Workspace root for codex-companion correlation |
| `--stale-tick-seconds N` | 60 | Per-tick interval baseline |
| `--stale-multiplier N` | 3 | A log file is "stale" if it hasn't been touched in `tick × multiplier` (default 180 s) |

## Outputs

```json
{
  "manifest_path": "/abs/path/.../manifest.json",
  "manifest_run_id": "20260508T182030Z-7q4f",
  "manifest_mode": "exec",
  "counts": {"done": 3, "failed": 1, "never_started": 1, "in_flight": 0, "unknown": 0, "total": 5},
  "redispatch_options": {
    "failed_only": ["02-cache-eviction"],
    "never_started_only": ["04-alert-fsm"],
    "all_non_done": ["02-cache-eviction", "04-alert-fsm"]
  },
  "entries": [
    {"id": "01-search-rewrite", "manifest_status": "done", "classification": "done", "evidence": [...]},
    {"id": "02-cache-eviction", "manifest_status": "failed", "classification": "failed", "evidence": ["exit_code=1", "503 in log"]},
    ...
  ],
  "warnings": []
}
```

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Classification produced; entries[] valid |
| 2 | Manifest missing |
| 3 | Manifest unparseable |

## Classification rules

| Class | Conditions |
|---|---|
| `done` | `manifest.status=="done"` AND log file exists AND (answer file non-empty if applicable) AND (worktree committed past baseline if applicable) |
| `failed` | `manifest.status=="failed"` OR `exit_code != 0` OR (worktree dirty + no commits past baseline + worker pid dead) |
| `never_started` | `manifest.status=="queued"` AND no log file AND (no worktree if exec/review) |
| `in_flight` | `manifest.status=="running"` AND worker pid alive AND log file fresh (modified within `stale-tick × multiplier`) |
| `unknown` | Anything else (e.g. status `running` but pid gone — codex-companion job record pruned past `MAX_JOBS=50`) |

## Behavior

- Read-only: never modifies state.
- Cross-correlates manifest with codex-companion's `jobs/<id>.json` records when present (workspace slug+hash matches; see `references/universal/plugin-data.md`).
- `pid_alive(pid)`: `os.kill(pid, 0)` returns success → alive; `ProcessLookupError` → dead; `PermissionError` → alive (different user).
- When codex-companion records are pruned past MAX_JOBS, falls back to filesystem-only signals; emits a warning in `warnings[]`.

## Notes

Rescue mode invokes this. The dispatcher embeds `redispatch_options` in the JSON envelope. Redispatch is explicit: rerun `orchestrate-codex.mjs rescue --redo failed|never-started|all-non-done`; pass `--accept-stale` only when replaying unknown entries intentionally.

The `--stale-tick-seconds` and `--stale-multiplier` should match `codex-monitor.sh`'s `INTERVAL` env var. In production, set both consistently in `bootstrap.sh`.
