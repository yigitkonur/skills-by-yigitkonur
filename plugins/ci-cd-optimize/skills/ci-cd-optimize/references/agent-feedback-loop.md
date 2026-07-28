# Agent feedback loop

Use this file when an agent must push and then act on the result: choosing how to wait, arming a watcher, reacting to a red check, or debugging a session that went silent after a push.

This file is provider-neutral. The probe command changes per provider; the contract does not.

## The problem

After an agent pushes, it still needs the answer. The usual waits fail in ways that look like "CI is just slow":

| Attempt | Failure mode |
|---|---|
| Foreground `run watch` command | Re-renders a TTY-oriented table instead of clean line events when stdout is not a terminal; often suppresses its completion summary for the same reason; usually has no deadline of its own. |
| Hand-rolled `while true; do sleep N; …; done` | Burns context, re-prints the same table, and often emits nothing on failure — a crash and a slow run look identical. |
| Success-only filter | Silence on red. The agent waits out the full timeout for a run that died in minute two. |
| No registration deadline | A path-filtered or disabled workflow is watched forever even though no run can ever exist. |

The payoff for solving this is immediate: a failure detected at minute 2 of a 25-minute pipeline gives back 23 minutes of agent time.

## The watcher contract

A watcher is verification infrastructure. Hold it to the same standard as any other gate.

1. **Terminate, always.** Every path ends in an explicit terminal line. Silence past the deadline must be structurally impossible.
2. **Emit on change, not on poll.** A 25-minute green run should cost a handful of notifications, not fifty duplicate job tables.
3. **Cover failure at least as loudly as success.** Ask: if this process crashed right now, would the watcher emit anything? If not, it is broken.
4. **Pin the commit, not the branch.** Query by the SHA you pushed. A green run on the branch tip can be another commit — a classic false green.
5. **Watch every workflow that commit triggered.** A second workflow can fail while the first passes. Completion-triggered follow-up workflows need a settle window before declaring success.
6. **Heartbeat.** Emit a liveness tick every ~2–3 minutes so a quiet watch still proves it is alive.
7. **Bound each probe call.** A single wedged API request must not freeze the whole watch.

## Event vocabulary

Use stable, machine-readable prefixes:

```text
CI-RUN    registered 3: build: queued · lint: queued · test: queued
CI-CHG    test: in_progress -> failure
CI-HB     12/20m
CI-SETTLE all green — holding 90s for completion-triggered follow-ups
CI-WARN   probe failing (3x) — still retrying
CI-DONE   failure — test — <command that prints the failing log>
```

Terminal verdicts worth distinguishing:

| Verdict | Meaning | Default reaction |
|---|---|---|
| `success` | every workflow green on that SHA | proceed |
| `failure` | at least one red | fetch the failing log immediately |
| `cancelled` | terminal but not green (`cancelled`, `skipped`, `stale`, `neutral`) | do not treat as success; decide whether the commit was actually validated |
| `timeout` | deadline hit with work outstanding | read the run; decide whether to keep waiting |
| `no-run` | nothing ever registered | check triggers, path filters, and enabled state |
| `probe-dead` | the provider probe failed repeatedly | check auth/network/tooling |
| `superseded` | the branch moved past the watched SHA | arm a fresh watch on the new SHA |

`timeout` and `no-run` are the two most-misreported outcomes: neither is red, neither is green, both mean you still do not know.

Enumerate **success**, not failure. A watcher that treats "did not fail" as green will eventually call `cancelled`, `skipped`, or an unknown terminal state a pass.

## Watch-shape selection

Pick the wait shape by how many notifications you need:

| Need | Shape |
|---|---|
| One final answer only | background task with an internal `until` loop or equivalent |
| One line per state change until a known end | Monitor tool + diff-gated watcher |
| Raw logs for diagnosis | do **not** watch the raw log stream; pull logs once after a red verdict |

Never arm an unbounded `while true` or `tail -f` for a single answer. It stays armed long after the event and can only end by timeout.

## Reference implementation shape

Bundle an executable watcher in the skill so agents do not rewrite a poll loop every time. The bundled implementation here is [`scripts/ci-watch.py`](../scripts/ci-watch.py).

A minimal control loop:

```text
poll(commit) -> list of {id, workflow, state}
  on error:      retry silently, warn on a streak, then exit probe-dead
  on first data: emit CI-RUN once
  per item:      emit CI-CHG only when state differs from last seen
  all terminal:  emit CI-DONE success|failure|cancelled and exit
  branch moved:  emit CI-DONE superseded and exit
  no data yet and past registration deadline: emit CI-DONE no-run and exit
  past overall deadline: emit CI-DONE timeout and exit
  else: heartbeat if due, sleep interval
```

Provider probes differ only in the `poll(commit)` step:

| Provider | Probe |
|---|---|
| GitHub Actions | `gh run list --commit <sha> --json databaseId,workflowName,status,conclusion` |
| GitLab CI | pipelines API filtered by revision |
| Buildkite | builds API filtered by commit |
| CircleCI | pipeline → workflow state by revision |
| Anything else | any command printing `<name>: <state>` lines |

### Hard requirements for the implementation

- Key state by **run id** (or an equivalent stable identifier), not workflow name. One commit can carry multiple runs of the same workflow.
- Collapse retries/attempts correctly **per provider**. Some APIs already do; some do not. Verify it.
- If expanding GitHub runs to job level for faster failure notice, expand only **active** runs so the extra API cost is bounded.
- Keep only the newest run per workflow **and event** when deciding the final verdict. A dispatch-only rerun and the original push run are different validation surfaces.
- Require the run set to be stable across two polls (or hold a settle window) before calling success. A fast workflow can finish before a slower sibling is even created.
- For completion-triggered follow-ups (`workflow_run`, deploy-after-build, etc.), hold a grace period after all-green and re-probe before declaring success.
- Keep the registration deadline below the overall deadline. If they cross, `no-run` becomes unreachable and every skipped pipeline misreports as `timeout`.
- Distinguish exit codes. `watch && deploy` must not ship on `failure`, `cancelled`, `timeout`, or `superseded`.

## Wiring to a streaming monitor

A monitor tool that turns each stdout line into a notification is the best host for this pattern. Use it when you need feedback while still working.

Rules:
- Arm the watch in the same turn as the push.
- One watch per pushed SHA. Re-push ⇒ old watch retires, arm a fresh one.
- Every pipe stage must flush per line (`grep --line-buffered`, `awk { fflush() }`). `head -N` cannot flush; it withholds output until N matches accumulate.
- Keep the monitor timeout **above** the watcher's own deadline so the script can emit its own `timeout` verdict instead of being killed silently.
- A heartbeat is not a result. Acknowledge it silently; never treat it as user input.

## Verifying the watcher itself

Do not trust a watcher that has only been observed succeeding. Rehearse it like any other piece of verification infrastructure.

Run each of these deliberately:

1. **Known green** — a historical SHA where every workflow succeeded.
2. **Known red** — a historical SHA with a real failing run.
3. **No-run** — a SHA that will never register, or a path-filtered push declared with `--expect-none`.
4. **Timeout** — a probe that reports a running state forever under a tiny deadline.
5. **Probe-dead** — a broken or unauthenticated provider CLI.
6. **Superseded** — arm on one SHA, then move the branch tip.

Check the real process exit code after each, not the exit of a pipeline you piped it through. `watch | tail` or `watch | head` can hide the watcher's own status behind the last command's `$?`.

## Reacting to a red check

1. Run the exact log command the failure verdict printed. Do not re-derive it.
2. Reproduce with the narrowest local command. If the failure is CI-only, reproduce the CI condition — job-wide environment variables, a clean checkout, a different working directory, absent secrets.
3. Fix the cause. Never add a retry, widen a threshold, mock the failure away, or `skip` to reach green; the check measures reality.
4. Verify red-first: confirm the test fails without the fix and passes with it.
5. Push and arm a fresh watch on the new SHA.

## Common traps

- `gh run watch` (or equivalent) piped into another command: the pipe can hide the real exit code, and the watcher often emits table redraws instead of line events.
- Looking only for a success marker: silence then looks identical to "still running".
- Using `run list --branch --limit 1` as a branch-tip check: the newest **run** can lag the newest **commit**, so a fresh push is falsely reported as superseded by its own ancestor.
- Reusing a large static monitor timeout for every provider: the deadline should be tied to measured p95 plus headroom.
- Assuming a watcher bug is harmless because the CI itself is correct. A false green in the watcher is the exact defect class this file exists to prevent.

## Related references

- `references/measurement.md` — queue versus execution, sample size, and evidence rungs
- `references/github-actions.md` — trigger duplication, concurrency, required checks, and when a PR gate differs from a branch gate
- `references/testing-and-flakiness.md` — deciding whether a red check is a real regression or a flake
- `references/effectiveness-contract.md` — why retries and weakened assertions are not valid fixes for a red pipeline

## Sources

- GitHub CLI watch source (`watchRun`, TTY-gated output paths): https://github.com/cli/cli/blob/trunk/pkg/cmd/run/watch/watch.go (accessed 2026-07-28)
- GitHub CLI iostreams TTY detection: https://github.com/cli/cli/blob/trunk/pkg/iostreams/iostreams.go (accessed 2026-07-28)
- POSIX shell pipeline exit status: https://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html#tag_18_09_02 (accessed 2026-07-28)
