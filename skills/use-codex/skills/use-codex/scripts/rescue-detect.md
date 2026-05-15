# rescue-detect.py

Read manifest + filesystem + codex-companion job records; classify each entry into `done | failed | never_started | in_flight | unknown`; emit JSON with redo recommendations. Read-only.

## Inputs

```bash
python3 rescue-detect.py --manifest <path> [--workspace-root <dir>] [--stale-tick-seconds N] [--stale-multiplier N] [--json]
```

| Arg | Default | Notes |
|---|---|---|
| `--manifest <path>` | required | The manifest to classify |
| `--workspace-root <dir>` | from manifest | Workspace root for codex-companion correlation. Priority: this flag → `manifest.workspace_root` → cwd |
| `--stale-tick-seconds N` | 60 | Per-tick interval baseline |
| `--stale-multiplier N` | 3 | A log file is "stale" if it hasn't been touched in `tick × multiplier` (default 180 s) |
| `--json` | text | Emit machine-readable JSON for the dispatcher |

## Outputs

```json
{
  "manifest_path": "/abs/path/.../manifest.json",
  "manifest_run_id": "20260508T182030Z-7q4f",
  "manifest_mode": "exec",
  "workspace_root": "/repo",
  "workspace_root_source": "manifest",
  "counts": {"done": 3, "failed": 1, "never_started": 1, "in_flight": 0, "unknown": 0},
  "redispatch_options": {
    "failed_only": ["02-cache-eviction"],
    "never_started_only": ["04-alert-fsm"],
    "all_non_done": ["02-cache-eviction", "04-alert-fsm"]
  },
  "warnings": ["[03-foo] manifest paths null but found /repo/answers/03-foo.md ..."],
  "entries": [
    {
      "id": "01-search-rewrite", "manifest_status": "done",
      "classification": "done", "warnings": [],
      "evidence": {"log_path": "...", "log_size": 2140, "fs_fallback_used": false}
    },
    {
      "id": "05-thread-stuck", "manifest_status": "running",
      "classification": "unknown",
      "resume_hint": "codex exec resume thread_abc123def456",
      "evidence": {"codex_thread_id": "thread_abc123def456", "correlation_id": "thread_abc123def456"}
    }
  ]
}
```

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Classification produced; entries[] valid |
| 2 | Manifest missing or unparseable, or bad input |
| 3 | Environmental error (permissions, etc.) |

## Classification rules

| Class | Conditions |
|---|---|
| `done` | `manifest.status == "done"` AND log present AND (answer non-empty if applicable) AND (worktree committed past base if exec). Also `status == "skipped"` and `status == "rescued"` (terminal-OK, treated as done for redispatch). |
| `failed` | `manifest.status == "failed"` OR `exit_code != 0`. **Exception**: when worktree has commits past base AND the log shows codex exit 0, classification is promoted to `unknown` with a warning (manifest writer likely crashed before flipping status). |
| `never_started` | `manifest.status == "queued"` AND no log file AND (no worktree if exec/review) |
| `in_flight` | `manifest.status == "running"` AND worker pid alive AND log file fresh (modified within `stale-tick × multiplier`) |
| `unknown` | Anything else (e.g. `running` but pid gone — codex-companion job record pruned past `MAX_JOBS=50`) |

## Filesystem fallback for batch entries

When `manifest.mode == "batch"` and an entry's `log_path` / `answer_path` are null in the manifest, the script derives candidate paths from the filesystem:

- `answer_path` ← `<answers_dir>/<slug>.md`, `<workspace_root>/answers/<slug>.md`, or `<monitor_root>/answers/<slug>.md`
- `log_path` ← `<monitor_root>/logs/<slug>.log` or `<workspace_root>/logs/<slug>.log`

If a non-empty answer file is found and the manifest status is non-terminal, classification is promoted to `done` with a warning (so the operator can backfill the manifest via `manifest-update.py`). The boolean `evidence.fs_fallback_used` flags this case.

## codex-companion correlation

The script tries `entry.codex_session_id` first as the cc job key, falling back to `entry.codex_thread_id` (batch never sets `codex_session_id`). The `correlation_id` field in evidence shows which key was used.

## resume_hint (single mode)

When `manifest.mode == "single"` and the entry carries a `codex_thread_id`, the entry's classification record includes a `resume_hint` field:

```json
{"resume_hint": "codex exec resume <thread-id>"}
```

The dispatcher can construct the resume invocation directly without re-deriving from evidence.

## Behavior

- Read-only: never modifies state.
- Cross-correlates manifest with codex-companion's `jobs/<id>.json` records (workspace slug+hash matches; see `references/universal/plugin-data.md`).
- `pid_alive(pid)`: `os.kill(pid, 0)` returns success → alive; `ProcessLookupError` → dead; `PermissionError` → alive (different user).
- When codex-companion records are pruned past MAX_JOBS, falls back to filesystem-only signals; warnings appear in `warnings[]`.

## Notes

Rescue mode invokes this. The dispatcher embeds `redispatch_options` in the JSON envelope. Redispatch is explicit: rerun `use-codex.mjs rescue --redo failed|never-started|all-non-done`; pass `--accept-stale` only when replaying unknown entries intentionally.

The `--stale-tick-seconds` and `--stale-multiplier` should match `codex-monitor.sh`'s `INTERVAL` env var. In production, set both consistently in `bootstrap.sh`.
