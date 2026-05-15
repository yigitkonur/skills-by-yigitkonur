# cleanup-worktrees.py

Safe worktree teardown. Removes worktrees whose entries are terminal AND whose branches are merged into the base. Default dry-run; `--execute` is the gate. After every entry is terminal+cleaned, deletes the manifest (and its `.lock` sibling).

## Inputs

```bash
python3 cleanup-worktrees.py --manifest <path> --base <branch> [--execute] [--force-abandon <id>...] [--workspace-root <dir>] [--json]
```

| Arg | Default | Notes |
|---|---|---|
| `--manifest <path>` | required | The manifest to consult |
| `--base <branch>` | `main` | The merge target; branches merged into this are eligible |
| `--execute` | dry-run | Without this flag, prints what would be removed without removing |
| `--force-abandon <id>` | none | Per-entry; removes the worktree even if dirty/unmerged. Repeatable. |
| `--workspace-root <dir>` | cwd | Workspace root for git operations |
| `--json` | text | Emit machine-readable JSON |

## Outputs

Default (dry-run):
```
[DRY] entry-merged-1: would remove ../myrepo-wt-exec-01
[DRY] entry-merged-2: would remove ../myrepo-wt-exec-02
[REFUSE] entry-bad: branch 'feat-bad' not merged into main; worktree '/repo/wt' is dirty (uncommitted changes); pass --force-abandon entry-bad to remove anyway
```

With `--execute`:
```
[OK] entry-merged-1: worktree removed at ../myrepo-wt-exec-01
[OK] entry-merged-2: worktree removed at ../myrepo-wt-exec-02
[REFUSE] entry-bad: branch 'feat-bad' not merged into main; worktree '/repo/wt' is dirty (uncommitted changes); pass --force-abandon entry-bad to remove anyway

✓ manifest deleted (all entries terminal+cleaned): /…/manifest.json
```

JSON (`--json`):
```json
{
  "ok": true,
  "executed": true,
  "manifest_path": "/…/manifest.json",
  "manifest_deleted": true,
  "actions": [
    {"entry_id": "01-merged", "action": "removed", "message": "worktree removed at /…/wt-01", "worktree_path": "/…/wt-01"},
    {"entry_id": "02-bad", "action": "refuse",
     "reasons": ["branch 'feat-bad' not merged into main", "worktree '/…/wt-02' is dirty (uncommitted changes)"],
     "message": "...; pass --force-abandon 02-bad to remove anyway"}
  ],
  "summary": {"total": 2, "removed": 1, "planned": 0, "refused": 1, "failed": 0, "noop": 0}
}
```

Output markers:

| Marker | Meaning |
|---|---|
| `[OK]` | worktree removed (executed) |
| `[DRY]` | would remove (dry-run) |
| `[REFUSE]` | refused — pass `--force-abandon <id>` to override |
| `[FAIL]` | git command failed (e.g. git status couldn't run) |
| `[NOOP]` | nothing to do (already cleaned, or worktree path absent) |

## Exit codes

| Code | Meaning |
|---|---|
| 0 | All actionable removals done (or none needed) |
| 1 | Dry-run with actionable removals (re-run with `--execute`) |
| 2 | Some entries refused; pass `--force-abandon` for those |
| 3 | `git worktree remove` failed for at least one entry |
| 4 | Manifest write failed |

## Behavior

- Reads the manifest. For each entry, computes (in this order):
  - whether the manifest entry's `status` is non-terminal (`running` or `queued`) — if so, refuse with `[REFUSE]` and `manifest_status` field on the action; the entry may be owned by another runner. Override is per-id `--force-abandon <id>`.
  - whether the worktree is present on disk (`os.path.isdir`)
  - whether the worktree's branch is merged into `--base` (`git branch --merged`)
  - whether the worktree is dirty (`git status --porcelain`). A `git status` non-zero exit surfaces as a `[FAIL]` action — never as silent dirtiness.
- When **both** dirty AND unmerged are true, surfaces **both** reasons in the refusal message and `actions[].reasons[]`.
- Calls `git worktree remove <path>` (with `--force` only when `--force-abandon` is set OR the worktree is dirty).
- Updates manifest: `entries[].cleaned_up = true`, `entries[].updated_at = now`, under `flock`.
- After the per-entry loop, if every entry is in a terminal status (`done | failed | skipped | rescued`) AND every entry with a `worktree_path` has `cleaned_up=true`, **deletes the manifest** AND its sibling `<manifest>.lock`. Lifecycle rule: `references/universal/manifest-contract.md:248`.

## Notes

Default dry-run is intentional: removing worktrees is destructive (uncommitted work in a dirty worktree is gone after `--force-abandon`). The user always reviews the dry-run before executing.

`--force-abandon` is per-entry. There's no global force flag — surprises are surfaced per id.

If the manifest's deletion fails (e.g. permission), the cleanup still succeeds for the worktrees; the manifest-deletion error surfaces on stderr for human follow-up.
