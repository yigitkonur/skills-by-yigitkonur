# Derailment Recovery

Use this reference when a Jean session errors, stalls, loops, loses its backend, repeats work, or follows a bad command.

## Contents

- [Preserve before intervening](#preserve-before-intervening)
- [Failure classes](#failure-classes)
- [Bounded stall rule](#bounded-stall-rule)
- [Bounded probe replacements](#bounded-probe-replacements)
- [Recovery sequence](#recovery-sequence)
- [Exact-state recovery prompt](#exact-state-recovery-prompt)
- [Model/backend switching](#modelbackend-switching)
- [Dirty state recovery](#dirty-state-recovery)
- [Rationalizations to reject](#rationalizations-to-reject)
- [Troubleshooting](#troubleshooting)

## Preserve before intervening

Capture:

- project and session header;
- repo/worktree/branch and known HEAD;
- last successful milestone;
- current prompt and latest agent message;
- expanded current/last tool name, command, elapsed state, and output;
- visible error text and backend/model;
- dirty tree, stash, or untracked artifacts if known.

Do not restart Jean. Do not discard the session. Do not send a generic retry before identifying the failure class.

## Failure classes

| Class | Evidence | Recovery |
|---|---|---|
| Streaming/transient response | stream disconnect, empty response, transport error | Retry the same session once from exact state |
| Token/context limit | explicit context/token error, truncation loop | Switch to an available larger-context backend/model in place; provide compact exact-state prompt |
| Quota/provider limit | explicit quota/rate/model unavailable | Select another already available backend/model in place; preserve worktree and prompt state |
| Hung command | no output past deadline or three unchanged checks | Cancel only the turn; replace with a documented bounded probe |
| Backend tool bridge | trivial local reads hang across models on the same backend, or no underlying command starts | Cancel only the turn; switch backend—not merely model—in the same session; resume from exact state |
| UI/MCP ownership conflict | MCP says resumable/started while fresh UI shows a different running state or no new turn | Stop sends; treat UI-visible ownership as live truth, reconcile IDs/history, then resume once |
| Broad scan loop | repeated recursive reads with no new finding | Cancel turn; name the exact files/worktree and narrow objective |
| Invented command/flag | help/schema rejects option | Stop turn; verify actual `--help` or live schema; re-prompt with valid syntax |
| Repeated implementation | edits or prompts redo completed milestones | Stop; list verified achievements and prohibit redoing them |
| False completion | report lacks SHA/test/CI/deploy/cleanup evidence | Keep session open; send missing-gates checklist |
| Wrong project/session | header/path differs from intended target | Stop all input; navigate fresh and verify header |
| Dirty overlay/stash drift | unrelated files moved/stashed/overwritten | Preserve, identify ownership, restore only the intended overlay |

## Bounded stall rule

A session is stalled when at least one is true:

- its command exceeded a declared/documented deadline;
- three monitor checks show no meaningful state change;
- two checks show no change and the expanded tool reveals an unbounded provider, recursive, watch, or interactive command;
- the UI exposes a running tool but the underlying process is known finished or failed;
- the agent repeats the same failed approach after evidence disproved it.

Scale the deadline to the operation. A local `pwd`, `git status`, `ls`, or small file read should show output within one short check; a known build, CI run, deploy, or provider operation gets its documented budget. If two models on one backend both hang on the same trivial deterministic tool and the process never starts, classify the backend/tool bridge instead of waiting longer or changing models again.

Do not cancel merely because a legitimate build or CI job is still within its deadline. Do not leave an obviously unbounded `vercel list`, `gh ... --watch`, provider login, recursive worktree scan, or interactive TUI running indefinitely.

## Bounded probe replacements

Use the repository's permitted route and verify syntax first. Patterns include:

- HTTP: `curl --max-time <seconds> ...`
- shell: a platform-available timeout wrapper with an explicit duration;
- GitHub: non-interactive `gh run list` / `gh run view` polls pinned to branch and SHA;
- provider: documented JSON/status API with deadline and limited result count;
- filesystem: explicit worktree/path list rather than an unrestricted recursive scan.

These are patterns, not universal literal commands. Run `--help`, inspect the live tool schema, or read official docs before supplying provider-specific flags.

## Recovery sequence

1. Fetch fresh Jean state and verify project/session.
2. Expand/read the current or last tool result.
3. Classify the failure from evidence.
4. Before cancelling, capture any non-idempotent operation identity: child PID/process group, deploy/provider job ID, migration/publish/webhook identity, git index/lock state, and known partial external effect.
5. Cancel only the current agent turn when stall criteria or an actively harmful command are met.
6. Reconcile after cancellation: confirm whether child/provider work actually stopped, inspect partial effects and locks, and decide whether the safe next action is observe, resume, compensate, or retry. Retry only when the operation is proven idempotent or its prior attempt is terminal and non-duplicating.
7. Keep Jean, the session, worktree, and completed state intact.
8. Switch the existing session's backend/model only when the evidence calls for it and the authorization rule below permits it.
9. Send an exact-state recovery prompt.
10. Verify the prompt appears in the intended UI history and the new turn starts; a fire-and-forget API response alone is insufficient.
11. Monitor the exact new run against a deadline and require terminal evidence.

## Exact-state recovery prompt

```text
Resume this existing task in place. Do not restart Jean, create a replacement
session, redo completed work, or discard the current worktree.

Product outcome: <one sentence>.
Repo/worktree/branch/HEAD: <exact state>.
Already complete and must be preserved: <milestones with evidence>.
Failure just observed: <tool/command/error and elapsed evidence>.
Root recovery decision: <why this bounded route replaces the failed one>.

Now do only: <single next objective>.
Constraints: <AGENTS rules, CI vs local, deploy route, no invented flags,
deadline, dirty-overlay preservation>.
Before any provider command, verify its actual help/schema. Every wait or network
probe must be non-interactive and deadline-bound.

Do not ask routine questions. Continue autonomously until you have either the
required evidence or a blocker proven by the exact failed probe.
Completion evidence: <SHA, focused checks, exact-SHA CI, runtime/deploy,
worktree cleanup>.
```

## Model/backend switching

Switching is a recovery tool, not a reset. Use only models/backends exposed by Jean. Never assume a backend exists or can handle a tool; inspect the current UI.

Autonomous switching is allowed only within an already-authorized equivalent boundary: same approved provider/account class, no new or higher spend, compatible privacy/data-residency terms, sufficient quota, and equivalent tool/resume semantics. “Already configured” is not itself authorization. Ask before crossing provider, billing, privacy, data-residency, or account boundaries, or when the switch could expose task data to a newly involved service.

Changing a model and changing a backend are different interventions. A model switch can address context, quality, or model quota. Repeated trivial-tool hangs across models on one backend implicate the backend/tool bridge; switch to another backend exposed by the existing session.

After switching:

- keep the same session;
- restate exact state compactly;
- name the failure mode so the new model does not repeat it;
- retain the same completion contract;
- verify the next tool call is materially different when the prior approach failed.

If resume semantics differ, restate exact state and verify the first read-only action before allowing edits. Record provider/model before and after the switch in the ledger.

## Dirty state recovery

Before directing git actions, inspect `git status`, `git worktree list`, current branch, and `git stash list` when applicable. Determine whether dirt is:

- the active agent's intended work;
- a user overlay that must remain uncommitted;
- an earlier session's preserved change;
- generated noise.

Do not stash all, clean all, reset, or restore blindly. Tell the agent exactly which paths belong to its task and which must remain untouched. If it created a stash, require it to restore the intended overlay before closure and verify the final state.

## Rationalizations to reject

| Excuse | Reality |
|---|---|
| “Restarting Jean is quickest” | It destroys orchestration state and repeats the original mistake; recover the session in place |
| “The command may eventually return” | An unbounded command without progress is not a monitoring plan |
| “This flag probably exists” | Plausible syntax is still invented; verify help/schema |
| “A new session will be cleaner” | It loses achieved milestones and invites duplicate work |
| “The agent said it deployed” | Provider/runtime evidence must match the exact SHA |
| “Stash everything to get clean” | Unowned overlays can be lost or forgotten |
| “The MCP call said started” | Fire-and-forget acknowledgment is not visible session ownership or progress |
| “Try another model on this backend again” | Repeated trivial-tool hangs across models call for a backend change, not a third model |

## Troubleshooting

If one bounded retry fails with the same error, do not repeat it unchanged. Reclassify from new evidence and take a different route. After three distinct failed routes, stop changing the project and document the failed probes plus the smallest user-only dependency—while continuing other independent projects.
