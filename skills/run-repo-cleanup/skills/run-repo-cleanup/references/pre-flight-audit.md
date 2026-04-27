# Pre-Flight Audit (Phase 0)

**Purpose:** know the exact state of the repo before you mutate anything. Surprise state (unexpected branch, in-progress rebase, unfamiliar worktree) is the #1 cause of dirty-cleanup incidents.

## What Phase 0 produces

By the end of Phase 0 you have written-down answers to:

1. What branch am I on, and what does it track?
2. What remotes exist? Which is origin, which is upstream?
3. What's in the working tree (modified, staged, untracked)?
4. How many worktrees exist, and are any of them unknown to me?
5. Is there an in-progress operation (rebase / merge / cherry-pick / bisect)?
6. What's in `.gitignore`? Is `to-delete/` there yet?
7. Are there open PRs on the fork I should be aware of? Any on upstream (which would be a leak)?

If you can't answer all seven in 60 seconds, run the audit again.

## The one-shot audit

```bash
python3 scripts/audit-state.py
```

Reads only. Never mutates. Emits a scannable human report (or `--json`). Exit codes: `0` clean, `1` actionable (dirty / unpushed / mid-op), `2` not a git repo.

The report includes:
- current branch + upstream + ahead/behind counts
- remote configuration (origin, upstream)
- dirty files grouped by top-level directory
- worktrees
- any in-progress git operation
- open PRs on the fork
- open PRs on upstream authored by you (should be zero)

## Reading `.gitignore` first

Before you do anything that touches the file system:

```bash
cat .gitignore
```

You want to know:
- Are session artifacts already ignored (`.continues-handoff.md`, `.claude-session*`, etc.)?
- Is `to-delete/` already listed?
- Are editor scratch paths ignored (`.vscode/settings.local.json`, `*.swp`)?

If `to-delete/` is not present, run `python3 scripts/init-to-delete.py` to create the folder and add the entry idempotently. If session-artifact patterns are missing, add them in a single `chore(git): …` commit before touching anything else. See `to-delete-folder.md` for the recommended patterns.

## Verifying remotes

```bash
git remote -v
```

Required layout:

```
origin    git@github.com:<you>/<fork>.git       (fetch)
origin    git@github.com:<you>/<fork>.git       (push)
upstream  git@github.com:<them>/<repo>.git      (fetch)
upstream  git@github.com:<them>/<repo>.git      (push)
```

If `origin` points at the upstream, **stop and fix** before proceeding. Renaming remotes is safe:

```bash
git remote rename origin upstream          # move mis-named origin to upstream
git remote add origin <correct-fork-url>
```

Also verify that current branch tracks origin, not upstream:

```bash
git branch -vv
```

Any `* <branch> [upstream/...]` marker in the output means that branch is tracking upstream; fix before Phase 1:

```bash
git branch --set-upstream-to=origin/<branch> <branch>
```

## Detecting surprise state

### In-progress operation

If `audit-state.py` flags a mid-operation (rebase / merge / cherry-pick / bisect), **do not start Phase 1**. Either finish or abort the in-progress op first:

```bash
git status              # git will tell you exactly what to do
git rebase --abort      # or --continue if you want to finish
git merge --abort
git cherry-pick --abort
git bisect reset
```

### Unknown worktree

If `git worktree list` shows a worktree you don't remember creating, it's likely a subagent's work. Do not discard it without inspection. Enumerate what's inside:

```bash
cd <unknown-worktree-path>
git status
git log --oneline main..HEAD
git diff main..HEAD --stat
```

If the work looks relevant, include it in Phase 2's merge-ordering decision. If it's clearly abandoned (no commits, no meaningful diff), archive into `to-delete/` (copy the directory), then `git worktree remove` the original.

### Branch on `main`

If you're currently on `main` and have uncommitted work, the work must move off main immediately:

```bash
git stash push -u -m "phase-0-offramp"
git checkout -b <proper-feature-branch> origin/main
git stash pop
```

Never commit directly to `main`.

## Phase 0 checkpoint

Only proceed to Phase 1 when **all** are true:

- [ ] `audit-state.py` printed a report you understand.
- [ ] `origin` is confirmed the private fork.
- [ ] Current branch is not `main` (or whatever the protected default is).
- [ ] No in-progress rebase / merge / cherry-pick / bisect.
- [ ] `.gitignore` includes `to-delete/` and session-artifact patterns.
- [ ] Every worktree present is accounted for (yours or a known subagent's).

If any box is unchecked, the answer is always: fix that first. Phase 1 has assumptions that Phase 0 enforces. Skip Phase 0 and Phase 1 makes bad commits.

## Common Phase 0 mistakes

| Mistake | Consequence | Fix |
|---|---|---|
| Start committing before running audit | Stage unknown files | Always run `audit-state.py` first |
| `git status` once, glance, proceed | Miss in-progress rebase | Read the full porcelain output |
| Trust remote names without verifying | Push to upstream | `git remote -v` every session |
| Ignore `.gitignore` gaps | Commit session artifacts | Update `.gitignore` in Phase 0 |
| Dismiss an unfamiliar worktree | Lose subagent's work | Inspect before removing |
| Start Phase 1 while rebasing | Worse mess | Abort the rebase first |

## The Phase 0 mindset

The first question isn't "what do I commit?" — it's "**what would surprise me in this state?**" If you can enumerate every surprise in the repo and explain why it's there, you're ready. If not, re-audit until you can.
