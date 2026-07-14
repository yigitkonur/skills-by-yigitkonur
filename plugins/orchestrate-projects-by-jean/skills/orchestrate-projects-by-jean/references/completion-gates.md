# Completion Gates

Use this reference whenever a Jean session claims completion, a notification requests approval, or a project must be merged and closed.

## Contents

- [Gate principle](#gate-principle)
- [Re-anchor first](#re-anchor-first)
- [Proof ladder](#proof-ladder)
- [Git identity gate](#git-identity-gate)
- [Scope gate](#scope-gate)
- [Test and CI gate](#test-and-ci-gate)
- [Deploy and runtime gate](#deploy-and-runtime-gate)
- [Worktree and branch closure](#worktree-and-branch-closure)
- [Approval decision](#approval-decision)
- [Terminal external blockers](#terminal-external-blockers)
- [Multi-project closeout table](#multi-project-closeout-table)
- [Common false proofs](#common-false-proofs)
- [Troubleshooting](#troubleshooting)

## Gate principle

An agent report is a claim. A completion badge is a claim. A green run on another commit is a claim about another commit. Approve only the highest rung freshly evidenced for the intended final state.

## Re-anchor first

Restate:

- original product outcome;
- in-scope task/plan items;
- target repo and branch;
- project-specific definition of done;
- authorization boundary for merge/deploy/delete;
- exact state that must be preserved.

Read the project `AGENTS.md`, named plan/decision files, and current session handback before evaluating evidence.

If Jean exposes only a bare plan/decision filename, resolve it inside the confirmed repo/worktree with a bounded file listing such as `rg --files -g '<basename>'`. Use the session's verified cwd/path to disambiguate duplicates. Never invent a conventional directory such as `.planning/` or `.herdr-pm/`.

## Proof ladder

| Rung | Evidence | Claim allowed |
|---|---|---|
| 1. Code | relevant diff and files read | implementation exists |
| 2. Static | focused lint/types/schema checks | static checks pass |
| 3. Test | regression/unit test terminal output | tested behavior passes |
| 4. Integration | real dependency/path exercised | integrated path passes |
| 5. Runtime | UI/API/browser behavior observed | behavior works in target runtime |
| 6. Deploy | provider says ready for exact artifact/SHA and live behavior observed | deployed behavior works |

Do not imply a higher rung than reached. Project instructions can forbid local full builds; in that case use the permitted CI route and say what was not run locally.

## Git identity gate

Capture:

- repository root;
- target branch;
- `git rev-parse HEAD` full SHA;
- `git status --short --branch`;
- `git worktree list`;
- task branch and merge-base when applicable;
- `git stash list` if any session used a stash.

Confirm the intended changes are present at the target SHA and unrelated user dirt remains preserved. A branch commit is not complete when the requested outcome requires integration into `main` and that integration is authorized.

Existence-gate historical branch/ref probes. Inventory current refs first; before `merge-base`, `diff`, or `show` on a named branch, verify that exact local/remote ref still exists. A safely removed merged branch is cleanup evidence, not a command failure; prove its former commit through the target branch, reflog/session evidence, or recorded SHA instead of probing the missing name repeatedly.

Never touch `entire/*` branches. Never use destructive history shortcuts. Follow project-specific merge rules.

## Scope gate

Map every requested item to one of:

- verified implemented;
- intentionally out of scope by the user's instruction;
- genuinely blocked with a failed probe and exact next dependency.

Partial implementation, “follow-up,” forgotten edge cases, untested behavior, or a plan file marked done without code proof are not completion.

For multi-item plans, require a concise checklist with evidence per item. Do not let a large successful diff hide one missing requested behavior.

## Test and CI gate

Require the narrowest relevant local proof allowed by repo rules, then the repository-required CI proof.

For CI:

1. pin the exact final SHA;
2. find the run that includes that SHA and change;
3. drive it to terminal `success`, `failure`, `cancelled`, or timeout;
4. on failure, read failed logs and route remediation;
5. reject stale green runs and success-only watchers.

After integration, pin the target branch's new exact SHA and verify that state. A green feature-branch SHA is not proof for a later merge commit or a target branch that moved.

Use non-interactive, deadline-bound polling. Do not use indefinite `watch` commands or a TUI.

If no remote or CI exists, verify that fact and mark CI not applicable; do not invent a missing pipeline as proof.

## Deploy and runtime gate

Deployment proof requires:

- correct project/environment;
- artifact or commit tied to the final SHA when the platform supports it;
- terminal provider state;
- live UI/API behavior observed at the target URL or endpoint;
- relevant browser console/network or service logs checked when applicable.

Inventory and test every user-reachable production entrypoint relevant to the change: canonical domain, custom aliases, callback/origin variants, tenant domains, and redirected routes. One healthy URL does not prove sibling aliases, especially for authentication and trusted-origin changes.

Respect the repository's deployment path. If it forbids local/cloud builds and requires a prebuilt CI artifact, do not improvise another build or invent a deployment flag. Verify the artifact exists; otherwise attach the exact missing-artifact blocker.

For web/UI, prefer the repo-required browser tool and deployed target. For backend/API, use the narrowest real request, CLI, replay, query, or logs.

## Worktree and branch closure

Before cleanup:

1. inventory all worktrees and branches;
2. read the relevant branch commits and diff;
3. verify the intended branch is integrated into the target;
4. verify no uncommitted task work remains;
5. identify unrelated dirt, untracked files, and stashes;
6. confirm no live Jean session, worker, external supervisor, or process still owns the worktree;
7. capture final session evidence before removal;
8. remove only safely merged worktrees/branches under the repo's rules and authorization;
9. re-run Jean and git inventory.

Do not blindly merge every old branch. Do not delete unmerged work. Do not remove `entire/*` branches. Do not claim “all worktrees merged” merely because the active worktree is clean.

## Approval decision

Move a claim to `verified-ready` when all applicable technical conditions are true:

- requested behavior is fully implemented;
- final diff matches product intent and project rules;
- focused verification is fresh;
- exact-SHA CI is terminal success or verified not applicable;
- deployment/runtime proof is complete when requested;
- target branch contains the intended work;
- merged worktrees/branches are retired safely;
- user overlays and unrelated dirt are preserved;
- no executable in-scope technical action remains before an authorization boundary.

If the only remaining action is an authorization-gated merge, deploy, publish, delete, or cleanup, record `awaiting-authorization` with the exact verified SHA/artifact and proposed action. This is neither `claims-complete` nor `terminal-blocked`. Do not perform the gated action from standing YOLO/session approval unless the user's current outcome authorization covers it.

Move to `verified-complete` only after every authorized closure action is terminal and the exact post-action state is reverified. If no gated closure applies, `verified-ready` may move directly to `verified-complete`.

If a technical gate fails, mark `verification-failed`, keep the session open, and send a missing-proof prompt:

```text
The implementation claim is not yet approvable. Preserve all current work.
Missing gate(s): <precise list>.
Current verified state: <branch/SHA/tests/CI/deploy/cleanup>.
Do only the remaining work and return with: <exact evidence contract>.
Do not redo completed milestones or ask for routine approval.
```

## Terminal external blockers

Do not confuse “implementation complete” with “fully verified.” Before declaring an owner-only credential/access blocker:

1. probe existing logged-in CLI/API/browser access read-only;
2. inspect scoped config or credentials already available to the same provider without exposing secrets;
3. try the documented provider API or console route;
4. use a safe substitute when it still satisfies the product outcome;
5. record the exact failed probe and the smallest unavailable dependency.

Never rotate existing keys or create spend to escape a blocker. When the ladder is exhausted, mark the project `terminal blocked`, preserve its exact implementation evidence, stop churning that session, and continue independent projects.

## Multi-project closeout table

Use a final table:

| Project | Product outcome | Final disposition | Final SHA | Tests/CI | Deploy/runtime | Worktrees/branches | Preserved state |
|---|---|---|---|---|---|---|---|

Use `verified complete`, `awaiting authorization`, `terminal blocked`, or another explicit state. Avoid “done” without evidence.

## Common false proofs

| False proof | Why it fails |
|---|---|
| Agent says tests pass | Need fresh output and exact state |
| CI badge is green | May be stale or for another SHA |
| Provider URL exists | May serve an older artifact |
| Canonical domain works | A custom alias, callback, or tenant route may still be broken |
| Branch is ahead of main | Requested integration is not complete |
| Worktree is clean | Other branches/worktrees may remain |
| Large diff covers most scope | Missing one requested item is still partial |
| Vercel/Cloudflare CLI started | Started is not terminal provider state |

## Troubleshooting

If evidence conflicts, rank live repo/provider/runtime observation above prose. If a Jean tab title conflicts with its current history and verified repo state, treat the title as stale and record the mismatch. If target `main` moved after verification, re-anchor to the new exact SHA and re-run affected gates. If cleanup would risk an unknown overlay, preserve it and classify ownership before acting. If a removed Jean worktree makes normal session reads fail, use the transcript fallback in `jean-state-and-steering.md` before declaring evidence lost.
