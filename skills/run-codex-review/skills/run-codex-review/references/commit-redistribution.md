# Commit Redistribution

When a branch holds commits that mix concerns, split them into granular conventional commits before Codex reviews the branch. Mixed-concern commits trigger Codex feedback about branch structure that's better fixed at the source.

This is the **only** place in the skill where history rewrites happen, and only on **unpublished** commits. Published commits never get rewritten — they get cherry-picked into a new branch.

## When to split

Split a commit when:
- It can't be described in one sentence.
- It touches files in two or more unrelated domains (e.g. `src/` and `docs/` and `scripts/` in one commit, with no shared concern).
- Codex feedback in a prior round called out branch structure as a problem.
- Reviewer cognitive load: > ~500 lines of meaningful diff in one commit.

## When NOT to split

Don't split:
- A coherent 200-line refactor where every line serves the same concern.
- Cosmetic vs structural changes that genuinely belong together (e.g. renaming a function and updating all its callers in one commit).
- Anything where the split would force the reader to mentally re-merge the commits to understand the change.

The test: *if I had to commit this in isolation, would the message change?* If yes, split. If no, leave it.

## Mechanics — unpublished commits (safe to rewrite)

`scripts/redistribute-commits.py` automates this with a backup ref so nothing is lost.

```bash
# 1. Dry-run: see the proposed split plan
python3 scripts/redistribute-commits.py --branch <b> --base main

# 2. Execute: creates backup ref, drives interactive rebase
python3 scripts/redistribute-commits.py --branch <b> --base main --execute
```

What `--execute` does:

1. Verifies commits in `<base>..<branch>` are NOT on `origin/<branch>` (unpublished). Refuses if published unless `--allow-published` is set explicitly.
2. Creates `backup/codex-review/<branch>/<UTC-timestamp>` ref pointing at current HEAD. This is the safety net — recovery is `git reset --hard <backup-ref>`.
3. Drives `git rebase -i <base>` programmatically via `GIT_SEQUENCE_EDITOR`, marking each split-target commit as `edit`.
4. At each `edit` stop:
   - `git reset HEAD~` (un-applies the commit, leaves changes in working tree).
   - For each proposed group: `git add <files-for-concern-N>` then `git commit -m '<emoji> <type>(<scope>): <subject>'`.
5. `git rebase --continue` advances to the next `edit` stop.
6. On any conflict, `git rebase --abort` + `git reset --hard <backup-ref>` + exit 3.

You end with a more-granular history. The backup ref stays around until you delete it manually (the script never deletes its own backups).

## Mechanics — published commits (cherry-pick into new branch)

When commits are already on `origin/<branch>` and visible to others, **do not rewrite**. Instead:

```bash
# 1. New branch off the right base
git fetch origin main
git checkout -b <type>/<scope>-<concern-A> origin/main

# 2. Cherry-pick the relevant commit WITHOUT auto-committing
git cherry-pick -n <commit-sha>

# 3. The full diff is now staged. Unstage and split with `git add -p`
git reset
git add -p <files>             # stage only concern-A's hunks
git diff --cached
git commit -m "<emoji> <type>(<scope>): <subject for concern A>"

# 4. Repeat for concern B in a sibling branch
git checkout -b <type>/<scope>-<concern-B> origin/main
git cherry-pick -n <commit-sha>
git reset
git add -p <files>
git commit -m "..."

# 5. Original branch untouched. Eventually retire it.
```

The original published branch stays on the fork until Phase 6 retirement — no rewrites, no force-pushes.

## Anti-patterns

| Don't | Why | Do instead |
|---|---|---|
| `git rebase -i` then `--force` push | Invalidates review attribution; breaks round-log → review-id mapping | Cherry-pick into new branch |
| Squash before review | Loses the granular evidence Codex needs | Split, don't merge |
| Split mid-loop (after rounds have started) | Round-counter and review-id continuity break | Split in Phase 1, before any review runs |
| Skip the backup ref | One bad rebase = lost work | Always pass through `redistribute-commits.py --execute` (it makes the backup) |
| `--allow-published` casually | Rewrites history others depend on | Use cherry-pick-into-new-branch instead |
| Delete the backup ref same day | If recovery is needed it's needed soon | Leave backup refs for at least the session |

## Recovery from a broken redistribute

```bash
# Find the backup ref
git for-each-ref --format='%(refname:short)' 'refs/heads/backup/codex-review/<branch>/*'

# Reset the branch to the backup
git checkout <branch>
git reset --hard backup/codex-review/<branch>/<timestamp>
```

The reset is destructive of the rebase attempt but restores the original commits exactly. The backup ref itself stays — you can run `redistribute-commits.py --execute` again with a different plan.

## Interaction with the manifest

`redistribute-commits.py` runs **before** Phase 2 (`spawn-review-worktrees.py`). The manifest doesn't exist yet during Phase 1. If you redistribute after Phase 2 (i.e. mid-loop), you must:

1. Halt the affected branch's subagent.
2. Mark the branch `BLOCKED` in the manifest with `terminal_reason: "branch redistributed mid-loop; restart loop"`.
3. Run the redistribute.
4. Re-spawn the worktree (it may need to re-track the new branch).
5. Re-dispatch the subagent.

This is enough overhead that the right answer is almost always "do the redistribution in Phase 1 and never repeat".

## Decision tree

```
Branch holds commits that need splitting?
├── No  → leave alone, proceed to Phase 2
└── Yes
    ├── Commits unpublished (not on origin/<branch>)?
    │   ├── Yes → redistribute-commits.py --execute
    │   └── No  → cherry-pick into new branch (do NOT --execute)
    └── (after split) verify with `git log --oneline <base>..HEAD` — every commit one-sentence describable
```

## Granularity check (after split)

After redistribution, every commit in `<base>..<branch>` must pass:

- One-sentence describable (the commit message subject).
- Single concern (no "and" in the subject).
- Single domain in the touched files (or, if cross-domain, the concern is genuinely cross-domain like "rename function + update callers").

If any commit fails, split it further. If the split feels artificial, don't — leave it as one commit and accept that Codex may flag the breadth in review (you can address it then or accept the trade-off).
