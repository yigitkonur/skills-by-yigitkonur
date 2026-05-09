# cleanup-worktrees.py

Safe worktree teardown. Removes worktrees whose entries are `done` AND whose branches are merged. Default dry-run; `--execute` is the gate.

## Inputs

```bash
python3 cleanup-worktrees.py --manifest <path> --base <branch> [--execute] [--force-abandon <id>...]
```

| Arg | Default | Notes |
|---|---|---|
| `--manifest <path>` | required | The manifest to consult |
| `--base <branch>` | `main` | The merge target; branches merged into this are eligible |
| `--execute` | dry-run | Without this flag, prints what would be removed without removing |
| `--force-abandon <id>` | none | Per-entry; removes the worktree even if dirty/unmerged. Repeatable. |

## Outputs

Default (dry-run):
```
[DRY] entry-merged-1: would remove ../myrepo-wt-exec-01 (branch wave1/search-rewrite merged)
[DRY] entry-merged-2: would remove ../myrepo-wt-exec-02 (branch wave1/cache-eviction merged)
[REFUSE] entry-dirty: branch 'feat-dirty' not merged into main; pass --force-abandon entry-dirty to remove anyway
```

With `--execute`:
```
[OK] entry-merged-1: removed ../myrepo-wt-exec-01
[OK] entry-merged-2: removed ../myrepo-wt-exec-02
[REFUSE] entry-dirty: branch 'feat-dirty' not merged into main; pass --force-abandon entry-dirty to remove anyway
```

JSON (`--json`):
```json
{
  "ok": true,
  "executed": true,
  "removed": ["entry-merged-1", "entry-merged-2"],
  "refused": [{"id": "entry-dirty", "reason": "branch not merged"}],
  "manifest_path": "...",
  "base_branch": "main"
}
```

## Exit codes

| Code | Meaning |
|---|---|
| 0 | All actionable removals done (or none needed) |
| 1 | Dry-run with actionable removals (re-run with `--execute`) |
| 2 | Some entries refused; pass `--force-abandon` for those |
| 3 | `git worktree remove` failed for at least one entry |

## Behavior

- Reads the manifest. For each entry where `status=="done"` and `worktree_path` is set:
  - Checks `git branch --merged <base>` for the entry's branch. If merged, eligible for removal.
  - Checks `git -C <worktree> status --short` for dirtiness. Dirty → refused unless `--force-abandon`.
- Calls `git worktree remove <path>` (without `--force` unless `--force-abandon` is set).
- Updates manifest: `mode_state.cleaned_up = true`, `updated_at = now`.
- After all eligible entries are removed AND every entry is in a terminal status, **deletes the manifest** (per the lifecycle in `references/universal/manifest-contract.md`).

## Notes

Default dry-run is intentional: removing worktrees is destructive (uncommitted work in a dirty worktree is gone after `--force-abandon`). The user always reviews the dry-run before executing.

`--force-abandon` is per-entry. There's no global force flag — surprises are surfaced per id.

If the manifest's deletion fails (e.g. permission), the cleanup still succeeds for the worktrees; surface the manifest-deletion error for human follow-up.
