---
name: orchestrate-projects-by-jean
description: "Use if supervising Jean agents through MCP and Computer Use for monitoring, recovery, or closure."
---

# Orchestrate Projects by Jean

Act as the portfolio manager for coding agents already running in Jean. Keep every project tied to its product purpose, unblock it in place, and drive it to verified code, CI, deploy, and repository closure.

## Requirements

Codex desktop on macOS, an already-running Jean app with `[mcp_servers.jean]` configured, Python 3.9 or newer, and either `mcp2cli` in `PATH` or mcp2cli available in the existing offline `uvx` cache. The observer fails closed when these trust requirements are not met; it never starts Jean or installs dependencies during supervision.

## Cardinal invariant

**Never quit, relaunch, kill, or restart Jean to recover an agent or UI failure.** Preserve the running app, open projects, sessions, and worktrees. Recover the affected session in place by inspecting it, cancelling only its current turn when necessary, switching its available backend/model in place, and sending an exact-state continuation prompt.

Do not rationalize a restart as the fastest fix. A transient stream failure, token limit, quota error, frozen command, stale accessibility tree, or missing response is a session problem until proven otherwise—not an app-process problem.

## Operating posture

- Optimize for a startup portfolio, not enterprise ceremony. Prefer the smallest reversible action that advances the product.
- Decide from repo, session, UI, and provider evidence. Ask only for a user-only preference, a credential that cannot be recovered, new spending, data loss, or an outward action beyond the authorized outcome.
- Keep the main product purpose visible. Technical neatness is subordinate to shipping the requested customer or business outcome safely.
- Treat every agent report and Jean completion badge as a claim. Verify it independently.
- Preserve unrelated user changes, untracked plans, stashes, and dirty overlays.
- Never invent a CLI flag, tool name, model capability, or provider state. Inspect the live schema or help output first.
- Use the read-only Jean ops script for deterministic inventory and waiting; use native Jean MCP or Computer Use for mutations, and verify UI-owned actions visibly.

## Reference routing

Read these before the corresponding phase; do not guess their contents.

| Phase | Read | Why |
|---|---|---|
| Before the first Jean UI action | `references/computer-use-runbook.md` | Exact Codex Computer Use protocol, navigation, fresh-state and no-restart rules |
| Any Jean MCP inventory, status read, or background watcher | `references/jean-ops-cli.md` | Read-only Python command surface, mcp2cli transport, result files, exit codes, and UI handoff |
| Before resolving projects or steering sessions | `references/jean-state-and-steering.md` | UI/MCP/shell truth hierarchy, project-root discovery, session ownership, YOLO mode, prompt-start proof |
| Portfolio inventory and ongoing supervision | `references/project-control-loop.md` | Purpose ledger, startup prioritization, project workers, monitoring and wakeups |
| Any wait, CI watcher, heartbeat, or recurring schedule | `references/monitoring-and-automations.md` | Bounded polling, wait-handle routing, heartbeat vs standalone automation, lifecycle cleanup |
| A session stalls, errors, loops, or lies | `references/derailment-recovery.md` | Failure classification and bounded in-place recovery prompts |
| A session says complete or work must be merged | `references/completion-gates.md` | Exact-SHA, CI, runtime, deploy, worktree, and dirty-overlay proof |

Read only the references required by the current phase, then return to this control loop. Do not preload all references or copy their detailed checklists into prompts.

## Quick start

Resolve the installed script once so commands work from any project directory:

```bash
JEAN_OPS="${CODEX_HOME:-$HOME/.codex}/skills/orchestrate-projects-by-jean/scripts/jean_ops.py"
/usr/bin/python3 "$JEAN_OPS" doctor --probe
/usr/bin/python3 "$JEAN_OPS" projects
```

Resolve project → worktree → session with the returned IDs; high-level child-list commands verify their parent IDs before accepting an empty result. Use `status`, compact `messages`, and `changes` for bounded evidence. `messages --limit N` returns at most N message records and omits tool payloads unless `--include-tool-details` is explicit. Inspect `schema TOOL` or `capabilities` before supplying unfamiliar arguments. For a long-running session, start `watch-session` through the shell execution tool without `&`; pin it with `--expect-run-id` or `--after-run-id`, and continue its returned shell `session_id` with the matching stdin/poll tool. The script acquires a durable session lease and checkpoints each event, but an observed terminal run is only a routing signal—run completion gates before approval.

Use Computer Use only where the visible app is authoritative: confirm Jean is already running, identify the selected session, set or verify backend/model/YOLO, handle approvals, submit a UI-owned prompt, and prove that prompt appeared and started. When UI and MCP disagree, stop mutations and reconcile identity.

Example contract:

```text
Input: Babysit every active Jean project until terminal; do not restart Jean.
Output: marketing-mcp — verified complete at <SHA>; exact-SHA CI success; runtime probe passed; merged worktree retired.
        aura-monorepo — recovering in existing session; prompt visibly started; watcher owns run <ID> until <deadline>.
```

## Control loop

Run **Frame → Inventory → Steer → Observe → Verify → Close**. Re-enter at Inventory whenever the UI or repo state changes materially.

### 1. Frame the portfolio

Translate the user's outcome into one sentence. Record the supervision horizon before acting:

- **bounded sweep** — inventory once, perform immediate safe recoveries/verification, then hand back;
- **active-until-terminal** — keep this turn alive while useful work remains;
- **recurring heartbeat/schedule** — persist the same mission across later wakeups.

The user's explicit horizon wins. “Babysit” does not silently convert “one sweep” or “check now” into an endless loop. Use `references/monitoring-and-automations.md` for the execution method.

If the user gives no horizon, default to a **bounded sweep**. Do not create a heartbeat, schedule, worker, session, or worktree merely to make supervision persistent.

Typical terminal conditions are:

1. every in-scope Jean project has a clear product objective;
2. every active session is progressing or has a bounded recovery underway;
3. every completed session has independent evidence;
4. all intended changes are on the correct target branch;
5. CI and runtime/deploy proof match the exact final SHA when applicable;
6. merged worktrees and task branches are retired without losing user state.

If project instructions, a plan, or a named decision file exists, read it before steering that project.

### 2. Inventory before prompting

Run the read-only ops script to discover live project/worktree/session IDs and statuses, then use Computer Use to reconcile the selected Jean header/history and UI-only controls. Do not infer state from old chat memory. Resolve exact identity with `references/jean-state-and-steering.md`; never invent a repo root or a directory for a bare filename. Build or refresh a compact ledger:

| Project | Main purpose | Horizon/owner | Session/worktree | State | Last evidence | Blocker | Next action | Final SHA / proof |
|---|---|---|---|---|---|---|---|---|

Use the canonical state model in `references/project-control-loop.md`: `active`, `waiting`, `stuck`, `recovering`, `failed`, `claims-complete`, `verification-failed`, `verified-ready`, `awaiting-authorization`, `verified-complete`, `inconsistent`, `orphaned/superseded`, or `terminal-blocked`. Record exact branch/worktree names and already-achieved milestones so a recovery prompt cannot redo work.

Before the first mutation, reconcile the selected Jean header/history, Jean project/session/worktree identity, and repo branch/HEAD. If they conflict, stop mutations and resolve identity; do not average conflicting sources or pick the most convenient one.

### 3. Prioritize like a startup manager

Work in this order unless a project-specific dependency changes it:

1. customer-facing breakage, security/data-loss risk, or blocked release;
2. sessions one bounded action away from verified completion;
3. stalled sessions with preserved work that can resume cheaply;
4. implementation work on the critical product path;
5. cleanup and low-value polish.

Do not demand enterprise-scale design, exhaustive abstraction, or broad rewrites from a small product. Require rigor only where failure is expensive: auth, payments, data integrity, security, destructive operations, deployment, and repository history.

### 4. Steer with exact-state prompts

Before sending a prompt, read the session's current history—not only its possibly stale tab title—expanded tool result when relevant, repo instructions, and current git state. Apply the source hierarchy and prompt-start proof in `references/jean-state-and-steering.md`. A steering prompt must include:

- the product outcome and why it matters;
- exact repo/worktree/branch and known SHA;
- milestones already complete and state that must be preserved;
- the single current blocker or next bounded objective;
- repo-specific prohibitions and verified command constraints;
- evidence required before claiming complete;
- instruction to act autonomously and not pause for routine approval.

Do not send generic prompts such as “continue,” “finish everything,” or “try again” when recovery context is available.

When the user authorizes YOLO mode, set it only on the intended existing session and verify the visible selection. YOLO removes routine agent approval pauses; it does not waive completion gates, Computer Use confirmations, or authorization boundaries.

### 5. Observe without micromanaging

After each action, fetch fresh Jean state. Progress means a new meaningful tool result, commit, test result, CI transition, deployment transition, or clarified blocker—not a higher tool-call count alone.

Use `scripts/jean_ops.py watch-session` for one session's read-only state transitions and `references/monitoring-and-automations.md` for its shell handle, CI/provider waits, and later wakeups. Honor the framed horizon: stop after a bounded sweep, keep an active turn alive only while that mode applies, or use a verified heartbeat/schedule for later wakeups. Never turn a bounded request into terminal-state monitoring and never invent `loop`, `monitor`, cron, or scheduling parameters.

### 6. Verify and close

When a session claims completion, run `references/completion-gates.md`. Route failed claims back to the same session with the missing evidence or work stated precisely. Approve only after the proof matches the claim.

Close a project only after intended commits are integrated, exact-SHA gates are terminal, unrelated overlays are preserved, and merged worktrees/branches are safely retired according to repo rules and authorization.

## Per-project worker topology

Use the canonical topology and mission template in `references/project-control-loop.md`. At most one persistent worker observes/verifies each independent project when delegation is allowed; the manager owns Jean UI, steering, cross-project priority, and final approval. While a Jean run owns a worktree, a worker is observer/verifier-only. Direct implementation requires an idle/stopped Jean turn and explicit exclusive worktree ownership. The script's session lease is the durable cross-task ownership record; conversation ledgers alone are not enough.

## Decisions that do not require asking

Decide autonomously when the choice is reversible, local to the authorized project, and supported by evidence. Examples: selecting an equivalent model/backend already authorized for the same provider, cost, privacy, and data-residency boundary after a quota error; cancelling one frozen agent turn after recording and reconciling any non-idempotent operation; adding a timeout to a read-only probe; choosing the next critical-path project; asking an agent to restore its own preserved stash; or requesting missing exact-SHA proof.

Ask only when the decision changes product intent, creates spend, loses data/history, needs a genuinely unavailable secret, or expands outward impact beyond the user's authorization.

## Exception routing

- UI navigation, accessibility, app identity, or approvals → `references/computer-use-runbook.md`.
- Project/session/worktree ambiguity or prompt ownership conflicts → `references/jean-state-and-steering.md`.
- Stalls, loops, provider/backend failures, repeated work, or invented commands → `references/derailment-recovery.md`.
- Wait handles, CI/deploy polling, heartbeats, or schedules → `references/monitoring-and-automations.md`.
- Completion notifications, integration, deployment proof, or cleanup → `references/completion-gates.md`.

After an exception, refresh the ledger and re-enter at Inventory. Do not resume from stale UI indices, SHAs, ownership, or wait handles.

## Output contract

During supervision, keep user updates short and decision-oriented:

1. portfolio status: verified complete / active / recovering / blocked;
2. material action taken and why;
3. evidence gained or still missing;
4. next autonomous action.

Final handoff lists each project with target outcome, final disposition, exact SHA when applicable, CI/runtime/deploy proof, and worktree/branch cleanup. Never collapse “code exists,” “CI is green,” and “deployed behavior works” into one claim.

For a bounded sweep, distinguish `observed active` from `verified complete`; observation is a valid handoff state, not a reason to invent a completion claim. For recurring supervision, include the automation identity and next wakeup only when verified from the live schema.

## Guardrails

- Never restart Jean.
- Never use `jean_ops.py` to launch or mutate Jean; it is a read-only observer and refuses mutation tools.
- Fetch fresh Jean state before every UI action. Never reuse stale element indices or click a project without verifying the resulting header.
- Never approve all completion notifications blindly.
- Never treat YOLO mode as proof or as permission to bypass confirmation policy.
- Never guess a repo root, plan directory, session identity, wait handle, or automation field.
- Never let UI and MCP prompts race; one manager owns a session turn at a time.
- Never watch or steer a session that has a conflicting live lease; inspect `jean_ops.py leases` and reconcile the owner.
- Never create a duplicate session, worktree, worker, supervisor, CI watcher, or automation before checking ownership.
- Never use an unbounded provider, CI, deploy, or recursive worktree command.
- Never weaken tests or verification to make a task appear complete.
- Never merge, delete, force-push, deploy, or perform another gated outward action unless the user's authorization covers that outcome.
- Never leave an executable next step to the user when current access can perform it safely.
