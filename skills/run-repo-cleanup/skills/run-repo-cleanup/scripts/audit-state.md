# audit-state.py

Read-only state dump for Phase 0 of the run-repo-cleanup flow. Prints a scannable human-readable report (or `--json`) covering everything you need to know before mutating the repo.

## Usage

```bash
python3 scripts/audit-state.py          # human report
python3 scripts/audit-state.py --json   # machine-readable
```

## What it reports

- Current branch + its upstream + ahead/behind counts.
- Remote config (origin vs upstream) with a fork-safety warning if origin and upstream share an owner.
- Modified + staged + untracked files grouped by top-level directory (first 8 per group, then a "… and N more" overflow).
- Worktrees (`git worktree list --porcelain` parsed), with multi-worktree warning when > 1.
- Local + remote branch counts.
- In-progress git operation (rebase / merge / cherry-pick / revert / bisect).
- Open PRs on the fork.
- Open PRs on upstream authored by you (should always be zero; if not, that's a fork-safety leak).

## Flags

| Flag | Default | Effect |
|---|---|---|
| `--json` | off | Emit JSON instead of the text report. Keys mirror the text report sections. |

## Exit codes

| Code | Meaning |
|---|---|
| 0 | State is CLEAN (no dirty files, no unpushed commits, no mid-op). |
| 1 | State is ACTIONABLE (dirty files, unpushed commits, or mid-op). Common at session start. |
| 2 | Not inside a git repository / fatal shell error. |

## When to run

- **First thing, every Phase 0.** The audit is the pre-flight.
- **After `gh pr create`** — confirms the PR landed on the fork, not upstream.
- **At the end of a session** — tidy verification.
- **After any surprise** — "why is my tree dirty when I thought it was clean?"

## Safety

Pure read operations. Never mutates. Never pushes. Safe to pipe to logs / dashboards.

If `gh` CLI is missing, the script gracefully omits the open-PR sections and continues with git-only info.

## Sample output

```
repo:    /Users/you/dev/myrepo
branch:  feat/wope-lockdown
upstream: origin/feat/wope-lockdown  (ahead 2, behind 0)

remotes:
  origin     git@github.com:you/fork.git
  upstream   git@github.com:them/repo.git

dirty files, grouped by top-level dir (3 total):
  src/  (2)
    [M ] src/features/Foo/index.tsx
    [M ] src/routes/bar.ts
  docs/  (1)
    [??] docs/new-guide.md

worktrees: 1 (main only)
branches: 4 local, 7 remote

open PRs on fork (you/fork): (none)

→ state is ACTIONABLE (dirty tree, unpushed commits, or mid-op).
```

## Extending

If you need additional checks (e.g. per-submodule status, CI job status), add a new section to `build_report()` and render it in `render()`. Keep it pure-read.
