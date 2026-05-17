# Post-PR Verification (Phase 5)

After every PR is opened, dispatch a **subagent** for an independent re-audit. The calling agent may have missed state drift introduced during a long session; a fresh subagent with only the checklist context catches those drifts.

## Why use a subagent

- **Fresh context.** The calling agent has hundreds of turns of history; details have decayed. A subagent reads only the prompt you give it.
- **Forced verification.** The subagent can't "remember" what should be true — it has to check.
- **Output hygiene.** The subagent returns a short pass/fail report, keeping the main session's context clean.

## The subagent prompt — copy / adapt

```
You are running the post-PR tidy check for the <fork-owner>/<fork-repo>
repo on the private fork. Open PRs you should expect:
  - #<N>: <title>
  - #<M>: <title>

Run each command below and report pass/fail with the exact stdout that
you used for the verdict. Return a compact Markdown report. Do NOT
mutate repo state; every command is read-only.

1. `git status --short`
   PASS if empty.
2. `git worktree list`
   PASS if only the main worktree is listed.
3. `git branch -vv`
   PASS if only `main` and open-PR branches are present. List any
   extra branches that shouldn't be there.
4. `git fetch --all --prune && git branch -r`
   PASS if only `origin/main` and remote branches for the open PRs.
5. `python3 <skill-dir>/scripts/audit-state.py`
   PASS if exit code 0.
6. `gh pr list --repo <fork-owner>/<fork-repo> --state open`
   PASS if the list exactly matches the expected open PRs.
7. `gh pr list --repo <upstream-owner>/<upstream-repo> --author @me`
   PASS if the list is empty (no accidental upstream PRs).

Final verdict: TIDY / NOT TIDY. If NOT TIDY, list the exact remedial
commands.
```

Replace `<…>` placeholders before dispatching.

## What the subagent should report

```markdown
# Post-PR tidy report — <timestamp>

| Check | Result | Detail |
|---|---|---|
| 1. working tree clean | PASS |  |
| 2. worktree list | PASS | only main |
| 3. local branches | FAIL | extra `tmp/debug` branch present |
| 4. remote branches | PASS | after `git fetch --prune` |
| 5. audit-state.py | PASS | exit 0 |
| 6. open PRs (fork) | PASS | #1, #2 as expected |
| 7. upstream PRs by me | PASS | empty |

## Verdict
NOT TIDY (1 failure).

## Remedial commands
  git branch -D tmp/debug
```

## How to consume the report

- **TIDY verdict** → Phase 5 complete. Move on.
- **NOT TIDY verdict with simple remedial commands** → Execute them, then rerun the subagent. Do not rerun more than 2 iterations without re-reading state manually.
- **Subagent report itself looks wrong** → Read the actual state yourself. The subagent may have a bad prompt; fix and redispatch.

## What the subagent must NOT do

- **Never mutate.** All 7 checks are read-only. If the subagent proposes a mutation, the calling agent executes it, not the subagent.
- **Never issue PRs or comments.** Even a "cleanup comment" on a PR.
- **Never push.** `git push` is an explicit mutation.
- **Never open upstream.** The subagent's prompt should forbid anything involving the upstream remote other than read listing.

## When to dispatch

- After the **last** PR of a session is opened.
- After a multi-PR stack has all been opened (dispatch once, not per-PR).
- Before ending a session (final cleanliness probe).

Do not dispatch between PRs within a session — that's overhead. Dispatch once at the end.

## The subagent context — what to include

Use a minimal brief so the subagent doesn't inherit irrelevant session state:

- Fork repo (`<owner>/<repo>`) and upstream repo.
- Expected open PR numbers + titles.
- Path to `scripts/audit-state.py`.
- Explicit "no mutations" rule.

Do NOT paste:
- The full commit history.
- PR bodies.
- Previous audit outputs.

Minimal context → focused audit.

## Handling subagent limitations

If the subagent can't run shell commands directly (constrained environment), the calling agent runs each command and passes the outputs to the subagent for interpretation. The subagent still produces the pass/fail verdict — just from paste-in data rather than live runs.

## When to skip the subagent

Skip Phase 5 subagent dispatch only when:

- You closed exactly one small PR and have no worktrees.
- The session is under 10 turns total.
- You've read the checklist manually and verified each item.

Skipping is rare. Default is dispatch.

## Common mistakes

| Mistake | Consequence | Fix |
|---|---|---|
| Skip Phase 5 | Debris accumulates across sessions | Always dispatch, or manual checklist |
| Over-specify the subagent prompt | Context bloat, slower runs | Keep the prompt to the 7 checks |
| Dispatch between PRs | Overhead, no new info | Dispatch once, at the end |
| Accept "mostly clean" | Tidy is binary | Fix the failing item |
| Let subagent mutate | Uncontrolled changes | Subagent reads only |
| Rerun subagent > 2x on same failure | Not converging | Read state manually |

## The mindset

A fresh pair of eyes is cheap and catches what tired eyes miss. The calling agent did the work; the subagent verifies the work. Trust the checklist, not the memory.
