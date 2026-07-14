# Project Control Loop

Use this reference to inventory several Jean projects, prioritize like a startup manager, assign future workers, and maintain active monitoring.

## Contents

- [The manager's job](#the-managers-job)
- [Ledger schema](#ledger-schema)
- [State transitions](#state-transitions)
- [Startup decision filter](#startup-decision-filter)
- [Inventory sweep](#inventory-sweep)
- [Progress signals](#progress-signals)
- [Monitoring cadence](#monitoring-cadence)
- [Per-project workers](#per-project-workers)
- [Wakeup routing](#wakeup-routing)
- [Autonomous decision boundary](#autonomous-decision-boundary)
- [Troubleshooting](#troubleshooting)

## The manager's job

The manager owns portfolio truth, not implementation detail. For each project, know:

- what product outcome is being shipped;
- which exact session and worktree own it;
- what has been verified already;
- what is currently preventing the next useful milestone;
- which autonomous decision will move it forward;
- what proof closes it.

Do not let a technically interesting side issue replace the product objective. Do not let the easiest project monopolize attention while a release blocker waits.

## Ledger schema

Maintain a compact ledger in conversation or a user-approved durable file:

| Field | Required content |
|---|---|
| Project | Jean-visible name plus repo path |
| Purpose | One sentence naming user/business value |
| Definition of done | Observable terminal outcome |
| Horizon | bounded sweep, active-until-terminal, or recurring automation |
| Owner | durable Jean session lease plus manager, worker, existing external supervisor/process, or none |
| Session | Session title/id and backend/model if visible |
| Git state | Worktree, branch, HEAD, dirty/stash state |
| State | one canonical state from the transition table below |
| Last progress | Timestamp or check count plus concrete evidence |
| Blocker | Exact failure, missing proof, or `none` |
| Next action | One bounded action with an owner |
| Proof | Exact SHA, checks, deploy/runtime, cleanup |

Refresh fields from live state. Old chat summaries are hints, not current truth.

## State transitions

Use states as evidence-bearing transitions, not labels of convenience:

| From | To | Required evidence |
|---|---|---|
| `active` | `waiting` | a named external operation or dependency, its identity, deadline, and next observation route |
| `active` or `waiting` | `stuck` | bounded stall criteria from `derailment-recovery.md` |
| any running state | `failed` | a terminal agent/tool/provider failure with its error, operation identity, and preserved repo state |
| `stuck`, `failed`, or `verification-failed` | `recovering` | one classified failure and a materially different bounded recovery started in the same session |
| any non-terminal state | `claims-complete` | a session completion claim tied to an identified repo/worktree/branch |
| `claims-complete` | `verification-failed` | a completion gate fails, with the exact missing/failing evidence routed back to the same session |
| `claims-complete` | `verified-ready` | implementation and all currently authorized verification gates pass, but closure disposition has not been decided |
| `verified-ready` | `awaiting-authorization` | the only remaining action is an authorization-gated merge, deploy, delete, publish, or cleanup |
| `verified-ready` or `awaiting-authorization` | `verified-complete` | every applicable gate passes and every authorized integration/cleanup action is terminal for the exact final state |
| any state | `inconsistent` | UI, MCP, repository, provider, or ledger identities conflict; mutations stop until reconciled |
| any owned state | `orphaned/superseded` | the owner vanished, its lease expired, or a different Jean run replaced the watched run; exact surviving state is inventoried before reassignment |
| any non-terminal state | `terminal-blocked` | the blocker ladder is exhausted, the failed probes are recorded, and no useful in-scope action remains |

`failed` is recoverable when a different bounded route exists; it reaches `terminal-blocked` only after the blocker ladder is exhausted. `verification-failed` returns to `recovering`, then `claims-complete`, after remediation. `inconsistent` returns to the last proven state after identity reconciliation. `orphaned/superseded` requires lease/process/run reconciliation before a new owner is assigned.

Do not move directly from `active` to `verified-complete`, infer `stuck` from elapsed time alone, or leave a project in `recovering` without a deadline and next check. Do not call an authorization wait blocked. A bounded sweep may end with `observed-active`; that describes the handoff horizon, not a terminal project state.

## Startup decision filter

Before assigning work, ask four questions:

1. Does this directly unblock a customer, release, revenue path, or critical learning?
2. Is failure expensive or reversible?
3. Can a smaller action prove the assumption?
4. Will this work still matter after the current blocker clears?

Use the smallest adequate process:

- copy/presentation polish: direct fix and visual check;
- isolated behavior bug: reproduce, narrow fix, regression proof;
- normal startup feature: thin end-to-end slice, focused tests, deploy proof;
- auth/payment/data/security: threat and failure-mode review plus stronger gates;
- multi-repo release: explicit dependency order and exact-SHA gates.

Avoid heavyweight architecture exercises, speculative abstractions, exhaustive matrices, or question rounds unless the cost of a wrong decision justifies them.

## Inventory sweep

Run the read-only `jean_ops.py` explicit-ID chain first, then inspect Jean's visible projects, notification list, and active/completed sessions where UI state matters. For each candidate:

1. resolve project → worktree → session IDs and paths through `projects`, `worktrees`, and `sessions`;
2. read bounded `status`, `messages`, and `changes` for plausible active or completed sessions;
3. verify the current visible project/session header before any UI mutation;
4. note whether the agent is thinking, running a tool, awaiting input, failed, or complete;
5. compare the claim with current repository state rather than cached Jean counts alone;
6. choose the next bounded action and one owner.

Do not prompt every session merely because it exists. Verified-complete sessions are closed; waiting sessions may need no action; active sessions need observation; stuck or failed sessions need recovery.

## Progress signals

Count these as progress:

- a meaningful diff or commit aligned with the objective;
- a previously failing focused test now passing;
- CI moving to a terminal result for the correct SHA;
- a deployment reaching ready/failed with inspectable evidence;
- runtime/browser proof of the intended behavior;
- a blocker narrowed to a concrete external dependency;
- safe branch/worktree integration or cleanup.

Do not count these alone:

- increasing tool-call count;
- repeated status prose;
- an unchanged spinner;
- another broad scan of the same files;
- “looks good,” “should work,” or “done” without new evidence.

## Monitoring cadence

Use `monitoring-and-automations.md` for cadence, wait handles, CI watchers, heartbeats, schedules, and stop conditions. This control loop decides *what matters*; that reference decides *how and when to observe it*.

## Per-project workers

When delegation is allowed and projects are independent, one worker per active project can preserve context and reduce manager thrash. The worker observes and verifies one project; the manager owns Jean UI, steering, portfolio decisions, and final approval.

Spawn only when all are true:

- the user/runtime permits subagents;
- at least two active projects are independently actionable;
- the worker has a concrete bounded mission;
- workers will not mutate the same files, index, deployment, or provider resource;
- the manager can independently verify the handback.

Before spawning, inspect current supervisors/processes, `jean_ops.py leases`, and the ledger owner field. Keep one owner per project, reserve manager capacity, and queue excess projects by startup priority. Reuse an existing worker with a precise follow-up instead of replacing it.

Do not spawn for an unknown failure. Localize first. Do not spawn multiple workers for one project unless independent domains are proven and file/state ownership is explicit. While a Jean agent run is active, its worktree is exclusively implementation-owned by Jean: workers may inspect it read-only but must not edit, stage, commit, stash, merge, deploy, or invoke implementation agents there. Direct worker implementation requires the Jean turn to be stopped/idle, a durable ownership handoff in the ledger/lease, and exclusive worktree ownership.

### Worker mission template

```text
Role: Observer/verifier for <project>; do not implement while Jean owns the worktree.
Purpose: <customer/business outcome>.
Ground truth: <repo, AGENTS/plan paths, branch, worktree, HEAD>.
Already verified: <milestones and evidence>.
Own only: <bounded observation/verification objective and read-only evidence surfaces>.
Do not: restart Jean, redo milestones, invent commands, run unbounded probes,
touch unrelated dirt, or claim completion without the evidence contract.
Return on: meaningful progress, terminal proof, or a blocker proven by a failed probe.
Evidence contract: <exact tests, CI SHA, deploy/runtime, cleanup>.
```

Workers may report status; they do not approve themselves. The manager spot-checks their state and runs completion gates.

## Wakeup routing

On each wakeup, follow the exact cycle in `monitoring-and-automations.md`, then use this ledger and priority filter to select work. Do not inherit liveness, selected-session identity, or exact SHA from the previous wakeup without a fresh check.

## Autonomous decision boundary

Take routine, reversible project actions without asking. Examples include switching to an equivalent already-authorized backend after a quota error, asking for a focused test, cancelling one frozen turn after non-idempotent-operation reconciliation, using a bounded provider API instead of a hanging CLI, or selecting the next project by critical path.

Ask only after probes and alternatives fail, and only for user-owned intent, unavailable credentials, new cost, data loss/history rewrite, or outward impact outside the authorized result.

## Troubleshooting

| Pattern | Manager response |
|---|---|
| Many projects appear active | Prioritize release blockers and near-terminal work; do not prompt all at once |
| Worker reports completion | Verify independently, then update ledger |
| Two workers need same repo state | Serialize or split ownership; do not race |
| Monitoring consumes the work | Lengthen cadence and require meaningful progress markers |
| Agent over-engineers | Restate startup outcome, smallest adequate solution, and proof required |
| Agent asks routine questions | Answer from evidence in the steering prompt and require autonomous execution |
| All worker slots are occupied | Keep a priority queue; attach the next project when one owner returns terminal evidence |
| Another supervisor already owns a project | Record it and observe its handback; do not create a competing manager |
