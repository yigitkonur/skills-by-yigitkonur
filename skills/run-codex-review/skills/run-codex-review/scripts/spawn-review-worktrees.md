# spawn-review-worktrees.py

Phase 2 entry point. For each branch in the input list: create or reuse a dedicated worktree, push the branch to the fork (refuses any remote other than `origin` per fork-safety), and emit/update the durable manifest used by every other script in this skill.

## Usage

```bash
# Default: dry-run
python3 scripts/spawn-review-worktrees.py --branches feat/a feat/b docs/c

# Apply
python3 scripts/spawn-review-worktrees.py --branches feat/a feat/b docs/c --execute

# Customise base / manifest / worktree path prefix
python3 scripts/spawn-review-worktrees.py \
  --branches feat/a \
  --base canary \
  --manifest /tmp/codex-review-manifest.json \
  --worktree-prefix ../mywork-wt- \
  --execute
```

## Behavior, per branch

1. **Existence check**: branch must exist locally OR on `origin`. If only on origin, the script creates a tracking branch via `git worktree add -b <branch> <path> origin/<branch>`.
2. **Worktree handling**:
   - If a worktree already exists for the branch and it's clean → reuse.
   - If it exists and dirty → fail with explicit error (refuse to silently include WIP changes).
   - Else → create at `../<repo>-wt-<branch-slug>` (or `--worktree-prefix<slug>`).
3. **Push**: `git push -u origin <branch>` from inside the worktree. Refuses any non-`origin` remote.
4. **Manifest**: appends a `SPAWNED` entry per the schema in `references/branch-decomposition-ledger.md` (atomic write via `tempfile + os.replace`).

## Flags

| Flag | Default | Effect |
|---|---|---|
| `--branches <b1> <b2> ...` | required | Branches to spawn worktrees for. |
| `--remote <name>` | `origin` | Remote to push to. Hard-refuses anything other than `origin` (fork-safety). |
| `--base <ref>` | `main` | Default base branch (recorded in manifest top-level). |
| `--manifest <path>` | `/tmp/codex-review-manifest.json` | Manifest file. Created if absent. |
| `--worktree-prefix <p>` | `../<repo>-wt-` | Custom path prefix before the slug. |
| `--dry-run` | on (when neither `--dry-run` nor `--execute` given) | Print plan without creating anything. |
| `--execute` | off | Actually create worktrees, push, and write the manifest. |

`--dry-run` and `--execute` are mutually exclusive in spirit; if neither is supplied the script defaults to dry-run.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | All branches spawned (or pre-existing & clean) and manifest written (`--execute` only). |
| `1` | Dry-run with planned actions. |
| `2` | At least one branch failed during `--execute`; partial state persisted to manifest. |
| `3` | Refused due to fork-safety (`--remote` != `origin`). |

## Safety

- Hard-refuses any `--remote` other than `origin`. Cannot be overridden by a flag — must edit the script if you legitimately need a different remote (rare; you usually don't).
- Never force-pushes. `git push -u <remote> <branch>` fails fast on non-fast-forward.
- Refuses pre-existing worktrees that are dirty (uncommitted changes from a prior session). Investigate before forcing.
- Atomic manifest writes: readers always see the old or new state, never a torn one.

## Worktree path scheme

Default: `../<repo-name>-wt-<branch-slug>`. Slug = branch with `/` → `-`.

Examples for repo named `myrepo`:

| Branch | Worktree path |
|---|---|
| `feat/foo` | `../myrepo-wt-feat-foo` |
| `fix/auth-bug` | `../myrepo-wt-fix-auth-bug` |
| `docs/contributors` | `../myrepo-wt-docs-contributors` |

Custom prefix: `--worktree-prefix /tmp/wt-` produces `/tmp/wt-feat-foo`, etc.

## Sample dry-run output

```
repo:     /Users/.../myrepo
remote:   origin  (you/myrepo)
manifest: /tmp/codex-review-manifest.json  (DRY-RUN)

  [DRY] feat/onboarding: would create worktree at /Users/.../myrepo-wt-feat-onboarding; push -u origin feat/onboarding
  [DRY] fix/auth-bug:    would create worktree at /Users/.../myrepo-wt-fix-auth-bug; push -u origin fix/auth-bug
  [DRY] docs/contribs:   would reuse existing worktree /Users/.../myrepo-wt-docs-contribs; would push -u origin docs/contribs

DRY-RUN complete. Re-run with --execute to apply.
```

## When to run

- **Phase 2**, exactly once per session, after Phase 1 produced a clean per-concern branch decomposition.
- **Re-run after manual decomposition** if a branch was added or removed mid-session — the script is idempotent: existing entries get updated, missing ones get created.

## Failure cases

| Failure | What you see | Recovery |
|---|---|---|
| Branch missing locally and on origin | `branch '<b>' not found locally or on origin` | Create the branch first. |
| Pre-existing worktree dirty | `existing worktree <path> is dirty; refuse to proceed` | Inspect the dirty worktree; commit or stash before re-running. |
| Push rejected (non-fast-forward) | `git push -u origin <b> failed: <error>` | `git fetch origin && git pull --rebase` inside the worktree, resolve, then re-run. |
| Remote != origin | exit 3 with `refusing to spawn against remote '<name>'` | Use `origin`. Don't override. |
| Filesystem path occupied | `git worktree add` error | `git worktree prune` then retry; or pick a different `--worktree-prefix`. |

## Concern one-liner

The manifest entry's `concern_one_liner` is left `null` by this script. The main agent or human fills it in after spawn — typically before Phase 3 dispatch — so the deliverable's "Concern" column is meaningful. Per `references/branch-decomposition-ledger.md`, this field is **required** before Phase 5 (it reads from the manifest into the PR body).

## Idempotency

Running the script twice with the same `--branches` is safe:
- Existing entries get updated (worktree path verified, head_sha refreshed).
- The push step is a no-op if there's nothing new to push.
- The manifest is rewritten atomically with the same logical state.

## Extending

- Add `--concern-one-liner <branch>:<text>` repeatable flag to populate the concern field at spawn time.
- Add `--from-branch-list <file>` for large branch sets driven by a separate planning step.
- Add per-branch base override (e.g., `--base feat/parent` for stacked PRs); currently the script uses the global `--base`.
