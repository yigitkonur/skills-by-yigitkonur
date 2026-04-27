# Worktree, Stash, and Branch Recipes

Procedural git recipes for moving dirty work between bases cleanly. Every recipe preserves uncommitted changes; none rewrite published history.

## Recipe 1: branch off `main` when working tree is dirty

You started work on branch `feat/foo` but realize the changes really belong on a fresh branch off `main` (because `feat/foo` has unrelated commits).

```bash
# 1. Make sure you actually have the latest main
git fetch origin main

# 2. Stash everything (including untracked files)
git stash push -u -m "wope-lockdown-work"

# 3. Create the new branch off origin/main
git checkout -b feat/new-branch origin/main

# 4. Pop the stash onto the new branch
git stash pop

# 5. Confirm clean base + your changes applied
git log --oneline -3
git status --short
```

If `git stash pop` produces merge conflicts, the stashed work genuinely depends on something that only exists on the old branch. Abort (`git checkout --theirs/--ours`), reset the new branch, and reconsider whether the work is really main-base or needs to stack on the old branch.

## Recipe 2: stack a new PR on an existing open-PR branch

Your first PR is `feat/parent` (open). The follow-up work genuinely depends on it — so the new PR stacks on top.

```bash
# 1. Current branch: feat/parent (or switch to it)
git checkout feat/parent

# 2. Create the child branch off the parent
git checkout -b docs/child

# 3. Do the work, commit normally
...
git add <files>
git commit -m "📝 docs(foo): ..."

# 4. Push the child branch
git push -u origin docs/child

# 5. Open PR targeting the parent branch, not main
gh pr create \
  --repo <fork>/<repo> \
  --base feat/parent \
  --head docs/child \
  --title "..." \
  --body-file /tmp/child-pr-body.md
```

The child PR's body must mention "stacked on #<parent-PR>". When the parent PR merges, retarget the child to `main` (GitHub shows a one-click "Change base to main"). The child's diff stays the same size — GitHub auto-rebases conceptually.

## Recipe 3: selectively commit some dirty files

Working tree has 20 modified files. Only 8 belong to this commit.

```bash
# 1. Audit
git status --short

# 2. Stage exactly the 8 files you want — list them explicitly
git add path/a.ts path/b.ts dir/c.ts ...

# 3. Verify the staged diff is what you intended
git diff --cached --stat
git diff --cached

# 4. Commit
git commit -m "..."

# 5. Remaining files still in working tree — continue or stash
git status --short
```

Don't use `git commit -am` when you have unrelated changes — it stages every tracked modification.

## Recipe 4: split a hunk-level mixed change

One file has two unrelated changes (e.g. typo fix and refactor). You want them in separate commits.

```bash
# Interactive hunk-by-hunk staging
git add -p path/to/file.ts

# Answers during -p:
#   y = stage this hunk
#   n = skip this hunk
#   s = split this hunk into smaller pieces
#   e = edit this hunk (manual patch editing)
#   q = quit without staging remaining

# Commit what you staged
git commit -m "fix(typo): ..."

# Stage the rest
git add path/to/file.ts

# Commit the second concern
git commit -m "refactor(foo): ..."
```

## Recipe 5: revert a published commit (don't amend)

A commit has been pushed. It's wrong. The answer is always `revert`, never `amend` or rebase-and-force.

```bash
# Find the SHA
git log --oneline -5

# Revert (creates a new commit that undoes the target)
git revert <sha> --no-edit

# Optionally fix the default message to Conventional Commits form
git commit --amend
# (The message now starts with `Revert "…"` — prefix it with ⏪ revert:)

# Push
git push
```

If the revert needs to happen on a PR branch mid-review, revert on the branch and push — the PR auto-updates. If the commit has already merged to `main`, revert on a new branch and open a follow-up PR.

## Recipe 6: rebase onto a new base

Your branch was cut from stale `main`. `main` has moved. You want your commits on top of the fresh `main`.

```bash
# Fetch latest
git fetch origin main

# Rebase onto origin/main (your branch must not have uncommitted changes)
git rebase origin/main

# Resolve conflicts if any:
#   edit the file(s)
#   git add <file>
#   git rebase --continue
# Or abort with `git rebase --abort`

# If you already pushed, force-push ONLY if no one else is on the branch
git push --force-with-lease origin <your-branch>
```

`--force-with-lease` prevents overwriting a remote branch that moved while you were rebasing. `--force` without `-with-lease` is a bigger foot-gun; avoid it.

**Do not rebase a branch that has a review in progress** unless the reviewer asked for it — rebasing invalidates inline comments (they get "marked outdated").

## Recipe 7: worktrees when you need two branches physically checked out

If you need `feat/parent` and `docs/child` simultaneously (e.g. to compare or run tests in parallel):

```bash
# From within the main repo directory
git worktree add ../repo-child docs/child

# Now ../repo-child is a separate directory, same repo, different branch
cd ../repo-child
# do work

# Remove when done
cd ../main-repo
git worktree remove ../repo-child
```

Worktrees avoid the "stash, switch, stash-pop" churn when working across branches. They cost disk but not much else.

## Recipe 8: recover from a broken rebase / merge / cherry-pick

```bash
# See what state you're in
git status

# Abort any in-progress op
git rebase --abort
git merge --abort
git cherry-pick --abort

# Find where you were before the op started
git reflog
# pick a HEAD entry from BEFORE the bad op
git reset --hard HEAD@{<N>}
```

`git reflog` is the safety net. It remembers every HEAD update for ~90 days. Nothing is ever truly lost unless you run `git gc --prune=now` aggressively.

## Anti-patterns

| Don't | Why | Instead |
|---|---|---|
| `git commit -am "fix stuff"` with 30 unrelated files | Bundles unrelated concerns | Stage explicitly, commit per concern |
| `git push --force` on a shared branch | Destroys others' work | `--force-with-lease`, or revert commit |
| Amending a published commit | Rewrites history reviewers already saw | New fix commit on top |
| `git stash pop` when the target branch is far from where you stashed | Cascading conflicts | Fresh branch, apply stash carefully |
| Rebasing during an open review | Invalidates inline comments | Wait, or add on top; rebase after merge |
| Using `git reset --hard` on unpushed work you don't have a reflog for | Irrecoverable | `git stash` or a throwaway branch first |
| Working on `main` directly | No branch = no PR = no review | Branch first, always |

## Bottom line

Stash before switching. Branch before working. Commit per concern. Rebase only on unpublished branches. Revert, don't amend, when commits are published. `git reflog` is the undo button.
