---
name: herdr
description: Use if explicitly asked to orchestrate or control Herdr agents, panes, tabs, or worktrees.
---

# Herdr

Own each assigned outcome until its evidence and next owner are recorded. Herdr
supplies terminal controls and lifecycle signals; it does not decide whether a
mission succeeded. Use direct CLI commands and the host's resumable sessions.

## Enter and route

Use this skill for an explicit Herdr request. Editing this skill does not start
or resume unrelated project work. Before controlling a live session:

```bash
test "${HERDR_ENV:-}" = 1
```

If this fails, explain that control must run inside a Herdr-managed pane. Do
not attach to whichever session happens to be focused. Bare `herdr` launches
the interactive TUI; use `herdr --version` and relevant group/subcommand help
for discovery. The installed CLI wins over examples here. Never probe a
mutating command by omitting arguments: some execute with defaults.

Read only the branch that applies. These files own their respective rules:

| Branch | Read before acting |
|---|---|
| Task submission, WAIT, READ, observer failures, PR discovery | [event-monitoring.md](references/event-monitoring.md) |
| Parallel issues, worktree capacity, mission briefs, PR review or integration | [parallel-capacity.md](references/parallel-capacity.md) |
| Writing standalone delegated assignments | [mission-briefs.md](references/mission-briefs.md) |
| Confirmed unfinished worker stopped or lost its conversation | [stopped-agent-recovery.md](references/stopped-agent-recovery.md) |

This skill works as a single-skill install. If the project or installed skill
catalog provides `dispatch`, read it for mission decomposition; Herdr owns
terminal supervision. For issue implementation, also read the project's or
installed `implement` skill when available. Carry its bounded spec → code →
focused checks → review → commit philosophy into PR handoffs. When companions
are absent, use the mission and delivery references here; do not assume sibling
directories exist. Repository testing restrictions override generic full-suite
advice. Ordinary terminal inspection does not activate implementation.

## 1. Ground and record the mission

Resolve the caller and assigned targets without changing focus:

```bash
printf '%s\n' "$HERDR_WORKSPACE_ID" "$HERDR_TAB_ID" "$HERDR_PANE_ID"
herdr pane current --current
herdr pane layout --pane "$HERDR_PANE_ID"
herdr agent list
```

Add broader inventories only when scope requires them. Use returned opaque
IDs, never sidebar positions, "latest pane," or another client's focused
target. Record actual checkout/foreground cwd and conversation identity.

**Create the task table before dispatch.** Reuse the existing run ledger and
show the initial table to the user. Keep one current table at its top, with
short dated history below; appended old status rows are not current state.
For a single task, use one row.

| Task / attempt / outcome | Dependencies; checkout / writer | Workspace / tab / pane / terminal / conversation | Worker; observer / typed handle; delivery | PR / base / head; evidence / gap | Last observed / result; next action / owner |
|---|---|---|---|---|---|
| A / 1 / bounded outcome | none; checkout and owned paths | caller workspace; returned IDs pending | not started; none; implementation | required artifact/check | timestamp; launch / controller |

Keep three independent axes; never compress them into a single "done":

- **Worker:** not started, working, needs input, stopped, handed off, terminal closed.
- **Observer:** none, waiting, settled, timed out, disconnected. Store the host
  tool type and handle, target identity/attempt, and last consumed result.
- **Delivery:** implementation, verification, ready for review, changes requested,
  merge pending, merged with acceptance reconciled; or a named blocker.

An idle worker may have an incomplete draft. A broken observer may be watching
a healthy worker. A ready PR still needs review/integration. Every unfinished
delivery has one next owner and action, including drafts whose author exited.
Store resource grants, recovery attempts and pending user decisions with the
row. Use links to long evidence instead of copying transcripts into the table.

Before resuming after compaction, reconcile the table against live inventory,
Git/PR state and available host sessions. Old handles and mergeability are
historical evidence. Recover the observer before restarting a worker.

When the user explicitly requests a tracked goal and goal tools exist, inspect
and reuse the applicable goal before creating one. Follow that tool's lifecycle
rules; ordinary tasks do not create goals. Neither a goal nor a ledger wakes
the controller after its turn ends.

## 2. Create only the needed containers

Stay in the caller's workspace unless the user explicitly overrides this.

- **Independent outcome:** a new tab in that workspace.
- **Related subtask/review:** a new pane in the owning task's live tab.
- **Concurrent writers:** isolated checkouts and explicit contract ownership;
  a shared tab does not authorize concurrent writes to one tree.

Use `--no-focus`. Record creation responses immediately. `agent start` needs an
available shell pane; it does not create layout. Use the user's requested agent
kind/model through installed, supported options.

**Worker agents run interactively in their visible pane by default.** The user
must be able to watch progress, inspect the conversation and take over. Prefer
`agent start` plus `agent prompt`; for an unrecognized CLI, launch its documented
interactive mode through `pane run`. Keep its live output in the terminal and
save a separate final report when needed. The controller's short-yield WAIT
session is separate from the worker's interactive session.

**Blacklisted shortcuts:** headless/print-mode workers (such as `agy --print`
or `-p`), redirecting all worker output to files, and backgrounding/detaching a
worker to make monitoring easier. Use these only when the user explicitly asks
for a noninteractive/batch worker; an ordinary shell command or a controller
WAIT is not a worker. A report file supplements visible progress, never replaces
it. If an accidental headless worker is already running, preserve its session
and artifacts, stop only that owned process, confirm it exited, then resume
interactively; never launch a second writer alongside it.

```bash
# Independent task, using an already prepared checkout:
herdr tab create --workspace "$HERDR_WORKSPACE_ID" \
  --cwd /absolute/path/to/task-checkout --label "Task name" --no-focus

# Related work; use the recorded owner, not the focused pane:
herdr pane split --pane <owning-task-pane-id> --direction down \
  --cwd /absolute/path/to/task-checkout --no-focus
```

Choose split direction from the current rectangle: wide → right, narrow/tall →
down. When the installed `worktree create/open` creates another workspace,
prepare isolation with Git, then open the checkout as a tab above:

```bash
git -C /absolute/path/to/repo worktree add \
  -b feature/task-name /absolute/path/to/task-checkout <verified-base-ref>
```

## 3. Dispatch, observe, consume, advance

1. Dispatch ready independent rows within the capacity plan. Preserve any
   existing composer text. Prefer `agent prompt` for recognized agents; use
   `pane run` only for intentional raw input. A submitted/queued message is not
   proof of pickup; confirm current-turn activity before relying on it.
2. Attach one bounded WAIT per active target attempt through a separate
   controller tool session. Record its handle immediately. Keep the worker's
   input terminal available. The exact commands and result decision table live
   in [event-monitoring.md](references/event-monitoring.md).
3. Between host yields, process user steering, ready dispatches, finished waits
   and PR candidates. Writing a plan or editing a skill does not suspend
   already-owned work. Reconcile settled observers before claiming a worker is
   still active; keep status statements dated when a fresh check is unavailable.
4. **Every settled WAIT → explicit short READ → classify → next action.**
   An embedded WAIT snapshot or idle footer is insufficient. Renew normal
   timeouts after reading; diagnose observer errors separately. Release a
   dependent lane only from the evidence its prerequisite requires.
5. Preserve a completed worker's handback and the next delivery owner, then
   close its terminal immediately under the rule below. Advance other ready
   work without waiting for unrelated siblings.

Use native CLI/tools, static mission files and finite metadata queries. Do not
write Python/Node/custom socket clients or shell loops to schedule agents, poll
panes, renew waits or decide completion. Product scripts and finite validation
tools are unaffected. A missing native capability is a limitation to report,
not a reason to invent a detached daemon.

Continue until the authorized outcome is complete, remaining work has specific
blockers, or the user pauses/cancels/requests handoff. Do not end an active
orchestration with only "WAIT is running." Do not invent busywork to keep an
agent active. User stops, real limits and host execution boundaries outrank
"never stop" wording. If the host cannot sustain supervision, save exact
handoff state and say so; no skill text can guarantee autonomous wakeups.

## 4. Close finished terminals; preserve integration work

Mandatory sequence for a task-owned terminal:

**WAIT → READ → verify its assigned handback → record remaining ownership →
preserve artifacts → close the smallest finished container → read inventory.**

Do this as soon as that worker's assignment is complete. A pending PR review or
merge alone does not justify keeping its finished terminal open. A draft with
unowned work does not qualify for closure as a completed mission.

```bash
# Sibling work continues:
herdr pane close <completed-subtask-pane-id>
# All work in the independent task tab is finished:
herdr tab close <completed-task-tab-id>
```

Verify the ID is gone. Check for active background jobs and unrelated panes
before closing a larger container. Never close the parent orchestration tab or
caller workspace. An existing task-owned auxiliary workspace may be closed
once all its work is finished; this does not authorize creating new workspaces.
If related work arrives after the owning tab closed, recreate a task tab and
update its IDs; do not target stale panes or retain idle shells as spare slots.

Terminal close, worktree removal, merge and issue closure are separate actions.
Never infer auto-merge from close/remove. Retain the checkout for unfinished
review/integration and record why. Before removal, inspect unique commits,
dirty/untracked/valuable ignored files and active processes; preserve what is
needed. A branch does not back up uncommitted files. Investigate removal refusal
rather than forcing it. Use the integration procedure for PR/issue settlement.

Close only task-owned or explicitly authorized resources. Never stop the Herdr
server to recover one worker. After an authorized pane move, use the returned
pane identity rather than assuming the old ID survived.

## Handoff

Report delivered outcomes and evidence, current draft/ready/merged counts when
relevant, retained blockers with owners, and resources closed or still active.
Record the latest successful observation and next action before compaction.
An unconsumed observer or ownerless candidate is unfinished orchestration.
