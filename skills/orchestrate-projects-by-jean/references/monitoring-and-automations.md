# Monitoring and Automations

Use this reference for active polling, background command waits, collaboration workers, CI/deploy watchers, heartbeats, recurring schedules, and stopping monitoring.

## Contents

- [Choose one supervision horizon](#choose-one-supervision-horizon)
- [Wait-handle routing](#wait-handle-routing)
- [Jean session watcher](#jean-session-watcher)
- [Adaptive observation](#adaptive-observation)
- [CI and provider watchers](#ci-and-provider-watchers)
- [Discover automation capability](#discover-automation-capability)
- [Heartbeat mission contract](#heartbeat-mission-contract)
- [Wakeup cycle](#wakeup-cycle)
- [Automation lifecycle](#automation-lifecycle)

## Choose one supervision horizon

| Horizon | Use when | Stop condition |
|---|---|---|
| Bounded sweep | “check now,” “one pass,” or an explicit limited cycle | inventory plus immediate safe recovery/verification is handed back |
| Active turn | user says finish/keep working now and useful work can progress in this turn | every in-scope project is terminal, user stops it, or a proven external wait needs a wakeup |
| Thread heartbeat | continue this same task later, especially short recurring follow-up | terminal portfolio or explicit stop; delete/update the heartbeat |
| Standalone scheduled job | user explicitly wants an independent recurring project job | its own declared terminal/expiry condition |

The most specific user horizon wins. Do not let the word “babysit” override “one sweep.” Do not create a recurring automation merely because an active check is slow.

## Wait-handle routing

Inspect the live tool schema and the response shape before waiting.

| Running work | Correct continuation | Rule |
|---|---|---|
| Jean read-only status | `scripts/jean_ops.py watch-session` plus its shell handle/result file | internal MCP polling; refresh UI on transitions or UI-only actions |
| Computer Use / Jean UI | fresh `get_app_state` after a transition or before an action | no stale element indices or blind sleep |
| Unified shell exec returning `session_id` | the matching stdin/poll continuation tool for that session | keep the ID type; poll non-interactively against deadline |
| Yielded orchestration cell returning `cell_id` | the matching cell wait tool | use only for that yielded cell; never pass a shell session ID |
| Collaboration subagent | the collaboration wait/mailbox tool | wait for meaningful update; do not busy-poll or duplicate worker |
| CI/deploy/provider | bounded status/API/CLI polls pinned to exact identity | terminal state or deadline; inspect failure logs |
| Later Codex continuation | verified automation/heartbeat tool | create/update/delete through live schema, never raw directives |

Never mix `session_id`, `cell_id`, thread ID, Jean session ID, worktree ID, run ID, or automation ID. Label IDs in the ledger.

## Jean session watcher

Read `jean-ops-cli.md` before the first use. Start the watcher through unified shell execution without `&`; a returned shell `session_id` is the background handle. Continue it with the matching stdin/poll tool. The Python process performs adaptive Jean MCP polls, so the manager waits on one handle instead of repeatedly spending model turns on unchanged status calls.

Always set a total `--timeout` and a run guard: `--expect-run-id NEW_RUN` after the run ID is known, or `--after-run-id BASELINE_RUN` before a prompt is sent. Without either, the watcher fails safe on an already-terminal first observation and waits for a newly observed run. The watcher creates a collision-safe private result path by default; use `--result-file` only when a new nonexisting path is required for handoff. The atomic checkpoint survives compaction, but it does not wake Codex by itself. A push-style callback is unavailable unless the current runtime exposes a verified notification/automation tool; never claim one exists from the watcher alone.

The watcher uses one-shot mcp2cli calls rather than a persistent helper daemon. This is deliberate: terminal/shell wrappers can disappear without giving a daemon-cleanup path. It acquires a durable per-session lease with watcher/controller IDs, PID, run guard, heartbeat/expiry, and result path. A conflicting live lease exits 14. Before starting a watcher, inspect `jean_ops.py leases`; do not bypass a collision with a second state root.

When the watcher exits 0, fetch fresh Jean UI state if selection, approval, model/mode, prompt history, or UI ownership matters. A terminal target means only that the guarded Jean run ended; route it to `completion-gates.md`. Exit 124 means the deadline—not the task—ended. Exits 10–15 identify config, trust, dependency, MCP, lease, or persistence failure; exit 16 means another run superseded the watched run. Preserve Jean and diagnose in place without restarting it.

## Adaptive observation

- After sending a prompt: immediately prove the prompt appears and the turn started, record the new run marker, then hand read-only observation to the watcher.
- Trivial local read: one short 10–30 second check; inspect immediately if unchanged.
- Normal agent tool: 15–30 seconds based on expected work.
- CI/deploy/provider operation: documented 30–60 second polling with an explicit deadline.
- Two unchanged checks: expand/read the current tool and verify the underlying process/status.
- Three unchanged checks or deadline exceeded: classify with `derailment-recovery.md`.

Expected duration matters more than raw check count. A five-minute `git status` is stalled; a five-minute CI matrix may be healthy.

Keep user commentary less than 60 seconds apart during active work. Report transitions and decisions, not unchanged polls.

## CI and provider watchers

Before watching, capture exact repo, branch, SHA/artifact, run/deployment ID, expected terminal states, poll interval, and deadline. Use non-interactive bounded commands such as limited `gh run list` / `gh run view` status probes when supported. Never use an indefinite `watch`, `gh run watch`, TUI, success-only watcher, or unpinned “latest” run.

If a new commit appears, the old watcher is stale. Pin the new SHA and find its run. On failure, fetch failed logs and steer remediation; on timeout, record the last provider state and exact failed probe.

## Discover automation capability

When the user requests a monitor, wakeup, scheduled babysitter, or later continuation:

1. search the current Codex tool catalog for `automation_update` or the current equivalent;
2. inspect its exact schema—do not invent `loop`, `monitor`, `cron`, `wakeup`, RRULE, model, or destination fields;
3. inspect `$CODEX_HOME/automations/*/automation.toml` or the supported listing route to find an existing mission by ID/name;
4. update the existing automation instead of creating a duplicate;
5. use the tool, never raw automation directives in chat.

Prefer a heartbeat attached to the current thread when continuing this portfolio context, especially below one hour. Use a standalone local scheduled job only when the user explicitly wants independent recurring execution and a valid Codex project mapping exists; resolve its project ID with the live project-list tool.

If the automation record exists but the current worker/tool catalog has no callable mutation schema:

1. inspect the record and recent deliveries read-only;
2. confirm ID, kind, status, cadence, target, prompt, and terminal condition;
3. do not edit `automation.toml` directly and do not create a workaround job;
4. record the exact unavailable tool/schema and the complete desired semantic change;
5. continue any safe bounded supervision in the current turn;
6. let a later manager context with the supported tool apply the update, or mark automation mutation as tool-blocked if it is the only remaining outcome.

This is a terminal fallback, not permission to claim the automation was updated. Do not ask the user merely to copy-edit the file.

## Heartbeat mission contract

The automation prompt must be self-contained enough to survive compaction:

```text
Continue the existing Jean portfolio supervision using
$orchestrate-projects-by-jean, its read-only jean_ops.py watcher, and bundled
Computer Use. Never restart Jean. Re-read the latest user instruction and
ledger; inspect the existing socket and fresh MCP/UI state; process new
completion/failure notifications individually; reconcile exact project/session/
worktree/branch/SHA; preserve dirty state and existing owners/wait handles;
steer only proven stalls in place; verify exact-SHA CI, deploy/runtime,
integration, and cleanup. Stop and delete/update this automation when all
in-scope projects are terminal.
```

Include project-specific prohibitions and the terminal definition when needed. Do not embed secrets or stale volatile SHAs as eternal truth; tell the wakeup to verify them fresh.

## Wakeup cycle

On each heartbeat:

1. re-read the latest user request and prior ledger;
2. verify the supervision horizon and automation ID;
3. confirm Jean is still running without using an action that would relaunch it;
4. fetch fresh UI state when accessible;
5. process new completion/failure notifications first;
6. reconcile owners, branches, SHAs, and active waits;
7. perform only bounded useful work for this wakeup;
8. update the ledger and next check;
9. follow the runtime's exact heartbeat response schema.

Notify the user only for a material decision, verified completion, new terminal blocker, required confirmation, or risk. Use the quiet response when supervision continues safely without user action.

## Automation lifecycle

- **Create** only when the user requests recurrence and no equivalent exists.
- **Update** when the mission, cadence, target thread/project, or terminal condition changes.
- **Keep active** while at least one in-scope project is non-terminal and later observation remains useful.
- **Delete** immediately after all projects are terminal, the user stops monitoring, or the automation is obsolete.
- **Never duplicate** a heartbeat to work around an existing thread heartbeat.

An external wait before its deadline is not a blocker. A terminal external-access blocker may close one project while the automation continues for others. When the last project reaches `verified complete` or `terminal blocked`, delete the automation and make the final portfolio handoff.
