# audit-fleet-state.py

Read-only manifest+filesystem state dump. Surfaces drift between `manifest.status` and reality (worktree existence, log file presence/growth, codex-companion job correlation).

## Inputs

```bash
python3 audit-fleet-state.py --manifest <path> [--json] [--workspace-root <dir>] [--stale-minutes N]
```

| Arg | Notes |
|---|---|
| `--manifest <path>` | Required. The manifest to audit. |
| `--workspace-root <dir>` | Override the workspace root for git / state-dir lookups. Default priority: this flag → `manifest.workspace_root` → cwd. |
| `--stale-minutes N` | Log freshness threshold in minutes. Default 30. |
| `--json` | Emit machine-readable JSON instead of human table. |

## Outputs

Human (default) ends with a one-line drift summary + recommendations:

```
─────────────────────────────────────────────
use-codex fleet state
─────────────────────────────────────────────
manifest:        /…/manifest.json
  present:       true
  run_id:        20260508T182030Z-7q4f
  mode:          exec
  ...
workspace_root:  /repo  (source: manifest)
...

  [D] 01-foo  (done)
      worktree fs=✗ git=✗ /repo/wt-gone
      ⚠ DRIFT: worktree_path set but missing on disk and not in `git worktree list`: /repo/wt-gone

Drift summary: 1 missing worktree.

Recommendations:
  • Run rescue mode for entries with `worktree_missing` drift (manifest still says active but worktree is gone).

→ ACTIONABLE
```

JSON (`--json`):

```json
{
  "manifest_path": "...",
  "manifest_present": true,
  "workspace_root": "/repo",
  "workspace_root_source": "manifest",
  "actionable": true,
  "drift_total": 1,
  "drift_kinds": {"worktree_missing": 1},
  "drift_summary": "Drift summary: 1 missing worktree.",
  "recommendations": [
    "Run rescue mode for entries with `worktree_missing` drift ..."
  ],
  "entries": [
    {
      "id": "01-foo", "status": "done", "drift": [...], "drift_kinds": ["worktree_missing"],
      "worktree_present": false, "answer_path_source": "manifest", ...
    }
  ],
  "orphan_worktrees": []
}
```

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Manifest read; fleet state clean (no drift, no orphans) |
| 1 | Drift detected (orphans, stale logs, dead pids w/ running, missing worktree, etc.) |
| 2 | Manifest missing (still emits a report) — actionable |
| 3 | Environmental error (permission denied, etc.) |

## Behavior

- Reads the manifest and the filesystem; cross-correlates per-entry.
- Detects per-entry drift kinds:
  - `worktree_missing`: `worktree_path` is set in manifest but the directory is absent on disk AND git doesn't know about it. Most common operational drift.
  - `worktree_unregistered`: directory exists on disk but `git worktree list` doesn't show it.
  - `pid_dead`: `status=running` but the recorded codex-companion pid is not alive.
  - `log_stale`: `status=running` and the log's mtime is older than `--stale-minutes`.
  - `log_missing`: log file is missing or empty when status implies it should exist.
  - `answer_missing`: `status=done` but answer file is missing or empty.
  - `failed_without_exit_code`: `status=failed` but `exit_code` is null/0.
  - `queued_with_log_content`: `status=queued` but log file already has content.
  - `answer_path_null_with_fs_evidence` (batch only): manifest's `answer_path` is null but `<workspace_root>/answers/<slug>.md` exists and is non-empty.
- Detects orphan worktrees: paths matching `<repo>-wt-*` not referenced in any manifest entry.
- Read-only: never writes.

## Workspace-root resolution

When invoked from a sibling directory (e.g. cwd is not the workspace), the script picks workspace_root in this order:

1. explicit `--workspace-root <dir>`
2. `manifest.workspace_root` (when present)
3. process cwd

The chosen source is recorded in JSON as `workspace_root_source` (`flag | manifest | cwd`). This prevents misclassifying every real worktree as drift just because the auditor is running from a different directory.

## Filesystem fallback for batch entries

When `manifest.mode == "batch"` and an entry's `answer_path` is `null`, the audit checks `<workspace_root>/answers/<slug>.md` and `<monitor_root>/answers/<slug>.md`. If a non-empty file is found, the audit reports it as a soft drift (`answer_path_null_with_fs_evidence`) and surfaces the path so the operator can backfill the manifest.

## Notes

Drift detected → use `manifest-update.py` to flip the affected entries to `failed`, then run rescue. Never hand-edit the manifest based on drift; the history row matters.

`audit-fleet-state.py` is **read-only by design**. The `--repair-dry-run` / `--repair-execute` flags listed in earlier drafts are **Planned — not yet wired**; the script's argparse defines only `--manifest`, `--workspace-root`, `--stale-minutes`, and `--json`. For corrupt-manifest recovery use the preserve-and-replace flow in `references/universal/manifest-contract.md` "Recovery". The `recommendations` field gives the next action for drift cases (entries needing flip, orphaned worktrees, etc.).

For batch fleets, run `bash scripts/audit-sizes.sh <answers-dir>` separately to check below-floor outputs — `audit-fleet-state.py` does NOT inspect answer-file sizes beyond presence/non-emptiness. A 50-byte truncated batch answer (well under the default `MIN_BYTES=10000` floor) is non-empty and therefore reports clean here. The two auditors are intentionally split: this one walks manifest-vs-filesystem drift; `audit-sizes.sh` walks answer-content size signals. Both run after `--- all jobs finished ---`.
