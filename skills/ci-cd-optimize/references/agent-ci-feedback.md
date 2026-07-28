# Agent CI Feedback Loops

An agent that pushes and then blocks on CI is an agent that stops working. An agent that pushes and never checks is one that reports success it did not verify. This file covers the third option: a watcher that reports state changes as they happen and always terminates with a verdict.

Provider-neutral. Any CLI that can list runs for a commit works — `gh` (GitHub Actions), `avr` (Avrea), `glab` (GitLab), `buildkite-agent`, or a plain `curl` against a REST API.

## Why the obvious approaches fail

| Approach | Failure mode |
|---|---|
| `gh run watch` / `avr run watch` in the foreground | Blocks the agent for the whole run. In a non-TTY harness it may emit redraw blocks instead of lines and suppress its own completion summary. No deadline: a check that never registers hangs forever. |
| `while true; do sleep 30; ... done` | Emits an event per poll, so one run produces dozens of duplicate notifications and burns context. Line-buffering swallows matches. Naming a shell variable `status` is fatal in zsh (readonly). |
| Grep for the success marker only | A crashed, cancelled, or never-registered run looks identical to a still-running one. **Silence is not success.** |
| Polling in a loop inside the agent turn | Wastes turns, and many harnesses block bare `sleep`. |

The fix is a small watcher process whose stdout is the event stream.

## The invariants

Any watcher worth arming satisfies all of these. Freeze them in code, not in instructions — instructions are advisory and agents improvise under pressure.

1. **Pin the exact SHA.** Query by commit, not "latest run on branch". A stale branch tip yields a false green; a second failing workflow on the same commit gets missed.
2. **Diff-gate the output.** Emit only on state change. A 20-minute green run should cost a handful of lines, not 40.
3. **Terminate on every path.** Success, failure, no-run, superseded, probe-dead, timeout. Silence past the deadline must be structurally impossible.
4. **Registration deadline.** If no run appears for the SHA within a few minutes, say so and exit — a typo'd branch or a disabled trigger should not read as "still running".
5. **Detect supersession.** On re-push, the older watcher must retire rather than report the concurrency-cancelled run as a failure.
6. **Survive transient errors.** Per-call timeouts; warn on a short streak, exit loudly on a long one. One 502 must not kill the watch, and a wedged request must not freeze it.
7. **Heartbeat.** A compact tick every few minutes proves liveness. Keep the interval under the assistant prompt-cache TTL where that matters.

## Event vocabulary

A compact, greppable prefix per line keeps the agent's parsing trivial:

```
CI-RUN  registered 3: build: queued · lint: queued · test: queued
CI-CHG  test: in_progress
CI-CHG  test: failure
CI-HB   6/25m build:success · lint:success · test:failure
CI-DONE failure — test — <command to fetch the failing log>
```

Put the **exact log command in the terminal line**. The agent should never have to reconstruct it.

## Terminal verdicts

| Verdict | Meaning | Agent's next move |
|---|---|---|
| `success` | every workflow for the SHA finished green | proceed |
| `failure` | at least one terminal failure | fetch failed-step logs, fix, push a new SHA |
| `no-run` | nothing registered before the deadline | check the trigger, path filters, branch name |
| `superseded` | branch tip moved past this SHA | discard; arm a watcher on the new SHA |
| `probe-dead` | the CLI/API failed repeatedly | check auth/network; do not claim a result |
| `timeout` | no terminal state before the deadline | inspect the run; it may be stuck or queued behind capacity |

Treat `cancelled` carefully: a run cancelled because a **newer push superseded it** is not a failure. Check whether the branch tip moved before reporting red — otherwise agents chase logs for a run that was retired on purpose.

## Wiring it to a notification tool

When the harness provides a background watch primitive (Claude Code's `Monitor`, a job runner, a webhook), arm the watcher there so events arrive asynchronously:

```
Monitor(
  command: 'python3 scripts/ci-watch.py --sha <sha> --branch <branch> --interval 15 --deadline 900',
  description: 'CI for <sha8>',
  timeout_ms: 960000,     # slightly ABOVE --deadline
)
```

Set the harness timeout **above** the script deadline so the script produces the verdict. If the harness kills the process first, you lose the structured outcome and get an ambiguous timeout instead.

**One watcher per pushed SHA.** Re-push means the old watcher retires and a new one is armed. Two watchers on the same SHA duplicate every notification.

### Choosing the shape of the watch

| Need | Shape |
|---|---|
| Per-occurrence updates until CI ends | the diff-gated watcher above |
| One notification when a condition becomes true | a bounded `until <check>; do sleep N; done` that exits on its own |
| "Tell me when this long command finishes" | run it in the background; the harness notifies on exit |

Never arm an unbounded `while true` for a single answer: it stays armed long after the event and can only end by timeout.

## Reference implementation sketch

Stdlib-only, roughly 150 lines. The shape matters more than the language.

```python
seen, registered, err_streak = {}, False, 0
while True:
    if elapsed() > deadline:
        done("timeout")

    runs, err = probe(repo, sha)              # per-call timeout
    if err:
        err_streak += 1
        if err_streak == 3:  emit("CI-WARN " + err)
        if err_streak >= 10: done("probe-dead", err)
        sleep(interval); continue
    err_streak = 0

    if not runs:
        if not registered and elapsed() > register_deadline:
            done("no-run")
        if branch_tip_moved():                 # superseded
            done("superseded")
    elif not registered:
        registered = True
        emit("CI-RUN " + summary(runs))

    for r in runs:                             # diff-gate: key by RUN ID
        state = r.conclusion or r.status
        if seen.get(r.id) != state:
            if r.id in seen: emit(f"CI-CHG {r.name}: {state}")
            seen[r.id] = state

    if registered and runs and all(r.status == "completed" for r in runs):
        bad = [r for r in runs if r.conclusion in BAD]
        if bad: done(bad[0].conclusion, f"{bad[0].name} — {log_cmd(bad[0])}")
        done("success")

    heartbeat_if_due()
    sleep(interval)
```

Details that only surface in live testing:

- **Key state by run ID, not workflow name.** One commit can have several runs of the same workflow (a push superseding an earlier one). Keyed by name, they overwrite each other and the watcher flaps between states forever.
- **Keep only the newest run per workflow** when deciding the overall verdict, so a concurrency-cancelled sibling does not turn a green commit red.
- **Guard the empty list.** `all([])` is `True` in most languages, so `all(completed)` over an empty run list reports success having observed nothing. Require `runs` to be non-empty, as above.
- **Clamp the registration deadline below the overall deadline.** If `register_deadline >= deadline`, a SHA with no runs reports `timeout` instead of the far more useful `no-run`.
- **Bound the lookback window.** Providers that list runs by time window (`--since 2h`) silently return nothing for an older SHA, which reads as `no-run` when the runs simply aged out. Make the window an argument and widen it when re-checking an older commit.

## Reacting to events

- **Act on the first `CI-CHG … failure`.** Do not wait for `CI-DONE`. On a 20-minute pipeline, a failure at minute 4 buys a 16-minute head start.
- **Acknowledge heartbeats silently.** They are liveness, not news.
- **A verdict is about one SHA.** After pushing a fix, the previous verdict is void.
- **Green counts only when the run's head SHA equals the local HEAD.** Re-running an unchanged tree proves nothing about the change you just made.
- **A watcher only knows about workflows that have registered.** When deploy or release workflows are *chained* off a completed run, a watcher armed at push time reports success for the first stage and exits before the dependent ones exist. To confirm what follows, re-check after the first stage completes, or arm a bounded settle-watch scoped to the SHA.
- **Never claim a result the watcher did not produce.** `probe-dead` and `timeout` are "unknown", not "fine".

## Local-vs-CI division of labor

When CI is fast and the workstation is contended (parallel worktrees, limited RAM), push work to CI and keep local checks to what is instant:

- Local: formatting, a whitespace/EOL guard (`git diff --check`), lint on changed files, targeted unit tests.
- CI: full typecheck, full test suite, builds, container images, integration environments.

Document the split so agents do not "pre-check" locally by running the whole suite — that is the exact contention CI was meant to remove. A cheap local guard for whatever the repo's CI checks first (often whitespace or formatting) prevents the most common self-inflicted red.

## Narrow feedback lanes

A full gate is the wrong tool when only one signal is needed. Expose a dispatchable workflow with a mode input (`typecheck`, `build`, `lint`, `test`, `affected`) so an agent gets a targeted answer in well under a minute.

Guard the lane so it cannot lie:

- Refuse to dispatch unless the remote branch SHA equals local HEAD.
- Correlate the resulting run by **head SHA plus a dispatch timestamp window**, not by run title. A `run-name:` template does not always populate the API's display-title field, so title matching silently attaches to the wrong run.
- Print failed-step logs automatically on failure.

## Common mistakes

| Mistake | Fix |
|---|---|
| Foreground `watch` in an agent turn | Arm a background watcher; keep working. |
| Success-only filter | Emit on every terminal state, including crash and cancel. |
| Keying state by workflow name | Key by run ID; multiple runs share a name. |
| Reporting a superseded run as failure | Check whether the branch tip moved first. |
| Harness timeout below script deadline | Set it above so the script yields the verdict. |
| Trusting a green on the branch's latest run | Pin the SHA and compare to local HEAD. |
| Watcher with no registration deadline | A never-registered run hangs the loop forever. |
| Reporting "still running" after a probe failure | `probe-dead` is unknown; say so. |
