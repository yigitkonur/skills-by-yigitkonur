# cleanup-worktrees.py

Phase 6 worktree retirement. Reads the manifest and removes the per-branch review worktrees, refusing any branch that isn't merged into `<base>` unless that branch is explicitly listed in `--force-abandon`.

## Usage

```bash
# Dry-run: shows the plan
python3 scripts/cleanup-worktrees.py --base main

# Execute the plan
python3 scripts/cleanup-worktrees.py --base main --execute

# Force-abandon specific unmerged branches (their commits live on origin only)
python3 scripts/cleanup-worktrees.py --base main --execute --force-abandon feat/x feat/y
```

## Behavior, per branch in the manifest

1. Skip if already `cleaned_up: true`.
2. Skip if the worktree directory is not present on disk (mark `cleaned_up: true`).
3. **Refuse** if the branch is NOT merged into `<base>` and the branch is not in `--force-abandon`.
4. **Refuse** if the worktree has uncommitted changes and the branch is not in `--force-abandon`.
5. Otherwise: `git worktree remove <path>` (with `--force` only if `--force-abandon` for that branch).
6. Update manifest entry: `cleaned_up: true`, `updated_at: <now>`.

## Flags

| Flag | Default | Effect |
|---|---|---|
| `--manifest <path>` | `/tmp/codex-review-manifest.json` | Manifest to read. |
| `--base <ref>` | `main` | Base branch for the merged-status check. |
| `--execute` | off (dry-run) | Actually remove worktrees and update the manifest. |
| `--force-abandon <b1> <b2> ...` | (none) | Branches whose worktrees should be removed even if unmerged or dirty. |

## Exit codes

| Code | Meaning |
|---|---|
| `0` | All worktrees handled (removed or noted as already-cleaned). |
| `1` | Dry-run with planned removals. |
| `2` | One or more branches refused — re-run with `--force-abandon <branch>` for those. |
| `3` | One or more `git worktree remove` calls failed. |

## Safety

- Default refuses unmerged branches. The merged check is `git branch --merged <base>` — same as run-repo-cleanup's `retire-merged-branches.py`.
- Default refuses dirty worktrees. Forces only via explicit `--force-abandon <branch>`.
- The manifest is updated atomically (`tempfile + os.replace`).
- Never deletes the branch itself — that's `retire-merged-branches.py`'s job. Only removes the worktree directory + git's worktree registration.

## Sample output

Dry-run with mixed states:

```
manifest:       /tmp/codex-review-manifest.json
base branch:    main
force-abandon:  (none)
mode:           DRY-RUN

  [DRY] feat/onboarding: would remove worktree at /Users/.../myrepo-wt-feat-onboarding
  [REFUSE] fix/auth-bug: branch not merged into main; pass --force-abandon fix/auth-bug to remove anyway
  [NOOP] docs/contribs: already cleaned up; skipping

✗ 1 branch(es) refused — re-run with --force-abandon for those
```

After targeted force:

```
$ python3 scripts/cleanup-worktrees.py --base main --execute --force-abandon fix/auth-bug

  [DO] feat/onboarding: worktree removed at /Users/.../myrepo-wt-feat-onboarding
  [DO] fix/auth-bug:    worktree removed at /Users/.../myrepo-wt-fix-auth-bug (forced)
  [NOOP] docs/contribs: already cleaned up; skipping

✓ manifest updated: /tmp/codex-review-manifest.json

✓ cleanup complete. Tidy.
```

## When to run

- **Phase 6**, after `retire-merged-branches.py` (which deletes branches; this removes worktrees).
- The order matters: branches must merge before worktrees can cleanly retire. If you reverse the order, `cleanup-worktrees.py` can't tell merged-vs-unmerged correctly.
- Optionally, **mid-session**, if you abandoned a branch and need its worktree gone before continuing.

## Interaction with run-repo-cleanup's `retire-merged-branches.py`

The two scripts complement each other:

| Script | What it removes |
|---|---|
| `cleanup-worktrees.py` (this) | The worktree directory + git's worktree registration. |
| `skills/run-repo-cleanup/scripts/retire-merged-branches.py` | The local branch ref + the remote branch on origin. |

Run order in Phase 6:

1. `cleanup-worktrees.py --base main --execute` — remove the worktrees first.
2. `skills/run-repo-cleanup/scripts/retire-merged-branches.py --base main --execute` — then delete the branches.

If you reverse the order, `cleanup-worktrees.py` can still infer merge-status from `git branch --merged` (the branch ref still exists in `--merged` output post-deletion only if it was merged before deletion — usually not what you want). Stick to worktrees-first.

## What "force-abandon" really means

Passing `--force-abandon <branch>` says: "I accept that this worktree's commits, if not pushed to origin or cherry-picked elsewhere, will be lost when the worktree is removed."

Per fork-safety, branches in this skill are pushed to origin in Phase 2, so commits on the worktree should also exist on `origin/<branch>` even after the worktree is removed. The branch itself remains on origin until `retire-merged-branches.py` deletes it.

If you're force-abandoning a branch whose commits are NOT on origin (rare; only happens if push failed silently), those commits will be unrecoverable except via `git reflog`. Run `git log <branch> --oneline` and verify origin reachability before force-abandoning.

## When to skip

- One-shot session that exited cleanly: still run; safer to be explicit than to leave debris.
- Multi-day project where you want to keep some review worktrees around for inspection: run with only the merged branches in scope (omit `--force-abandon` and let unmerged ones refuse).

## Recovery

`git worktree remove` is reversible only by `git worktree add <path> <branch>` again. The branch itself is not affected by this script — only its physical workspace.

If you accidentally `--force-abandon`ed a branch with unpushed work: `git reflog` shows recent HEADs; `git checkout -b <recovery-name> <reflog-sha>` recreates a branch. Then push if needed.

## Extending

- Add `--keep <branch>` flag for the inverse of `--force-abandon`: explicitly keep these worktrees even if merged.
- Add `--remove-manifest-after` to delete the manifest file when the last entry is cleaned (Phase 6's final step). Currently the manifest deletion is a separate manual step.
