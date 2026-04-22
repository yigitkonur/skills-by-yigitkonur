# Handoff Mechanics

Diff-walk commits → push → `gh pr create`. The mechanical steps between a dirty tree and a reviewable PR. Referenced from SKILL.md Step 3 and Step 7.

If the `run-repo-cleanup` skill is installed (check `~/.claude/skills/run-repo-cleanup/` or `~/.agents/skills/run-repo-cleanup/`), invoke its Phase 1 (dirty-tree → conventional commits) and Phase 3 (PR creation) rather than duplicating them. This file is the inline fallback for when that skill is absent.

## 1. Branch safety

Before committing anything, confirm:

```bash
git branch --show-current
```

If the result is `main`, `master`, or the repo's default branch:

```bash
git switch -c <type>/<scope>-<slug>
```

Where:
- `<type>` ∈ `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`
- `<scope>` is a short noun identifying the area (e.g., `auth`, `session`, `payment-retry`)
- `<slug>` is 2-4 words describing the change

Examples: `feat/auth-token-rotation`, `fix/session-timeout-edge-case`, `docs/api-getting-started`.

**Never commit to the default branch directly.** Always branch first.

## 2. Diff-walk discipline

Read before staging. For every modified file:

```bash
git diff <file>
```

For every untracked file:

```bash
cat <file>
```

Never stage a change you have not read. No `git commit -am`. No blind stage-everything.

## 3. Group by domain, not by file

Typical split for a feature branch:

- Feature implementation
- Docs / README updates for the feature
- Env / config / scripts scaffolding for the feature
- Drive-by fixes unrelated to the feature → **separate branch/PR**, not this one

If one file contains two unrelated concerns, split the staging with `git add -p` and commit the halves separately.

## 4. One concern per commit

For each concern:

```bash
git diff <files-for-this-concern>
git add <files-for-this-concern>
git diff --cached                            # confirm nothing extra snuck in
git commit -m "<type>(<scope>): <imperative subject>"
```

Conventional Commits format. Subject under 50 characters. Imperative mood ("add", not "added"). No WIP, no "misc", no "updates".

Good:
- `fix(auth): refresh token on privilege elevation`
- `feat(payment-retry): exponential backoff with jitter`
- `docs(api): add getting-started walkthrough`
- `refactor(session): extract store adapter interface`

Bad:
- `fix: various fixes` → too vague, split it
- `WIP` → not a commit, a pause
- `Update stuff` → rewrite
- `fix bug` → what bug in what scope?

## 5. Push with tracking

```bash
git push -u origin <branch>
```

The `-u` sets upstream tracking so later `git push` / `git pull` work without arguments.

If the branch is already pushed but tracking isn't set, run the same command — git will update the tracking without recreating the branch.

## 6. Open the PR

Always pass `--repo` explicitly. `gh` defaults to the tracked upstream, which is frequently wrong for fork-based workflows.

```bash
gh pr create \
  --repo <owner>/<repo> \
  --base <target-branch> \
  --head <current-branch> \
  --title "<type>(<scope>): <subject>" \
  --body-file /tmp/pr-body.md
```

Use a file for the body, not `--body "..."` — multi-line markdown via a shell argument is error-prone and can break on special characters.

## 7. Verify immediately

```bash
gh pr view <N> --repo <owner>/<repo> --json url,baseRefName,headRefName,state
```

Check:
- URL points to the intended `<owner>/<repo>` (not an upstream, not a different fork)
- Base is the intended target branch (not `main` of an upstream you didn't mean to PR against)
- Head matches the branch you pushed

If the PR is on the wrong repo or wrong base: close it, fix `--repo` / `--base`, reopen.

## Commit-message style matching

Before writing commit messages, match the repo's existing style:

```bash
git log --oneline -20
```

Look for:
- Emoji prefix? (some repos use gitmoji, many don't)
- Scope format? (`feat(scope):` vs. `feat/scope:` vs. just `feat:`)
- PR-number suffix? (`...(#42)` on merge)
- Imperative vs. past tense
- Subject length

Match what you see. The repo style wins over personal preference.

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| `git commit -am "fix"` | Diff-walk; stage per-concern; specific subject |
| `rm <unknown file>` before committing | If `run-repo-cleanup` is available, use its `to-delete/` pattern. Otherwise move to a local `./out-of-scope/` and do not commit that path. |
| Force-push to a reviewed branch | No. Add a new commit. |
| Amending a published commit | Creates rebase pain for reviewers. New commit on top. |
| PR body as `--body "..."` inline arg | Use `--body-file /tmp/pr-body.md` |
| `gh pr create` without `--repo` | Always explicit, always |
| PR opened against `main` from `main` | Branch first, always |
| Mixing unrelated drive-by fixes into the feature branch | Separate branch for drive-by fixes |

## Recovery: accidentally committed to `main`

Do **not** force-push. Instead:

```bash
# 1. Create a branch pointing at where you are now
git switch -c <type>/<scope>-<slug>

# 2. Reset main back to its last pre-accident commit
git switch main
git reset --hard <last-clean-main-sha>

# 3. Push the new branch, keep main intact
git switch <type>/<scope>-<slug>
git push -u origin HEAD
```

If `main` has already been pushed with the accidental commit, **do not** `git push --force origin main`. Ask the user. A revert commit is safer than a force-push on a shared branch.
