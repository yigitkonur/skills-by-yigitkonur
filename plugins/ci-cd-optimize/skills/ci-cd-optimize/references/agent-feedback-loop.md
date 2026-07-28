# Agent feedback loop — waiting for CI without stalling

Read when an agent must push and then act on the result: choosing how to wait,
arming a watcher, reacting to a red check, or debugging a session that went
silent after a push.

This is provider-neutral. The probe command changes per provider; the contract
does not.

## The problem

An agent pushes, then blocks. The usual attempts all fail in ways that look
like "CI is just slow":

| Attempt | Failure mode |
|---|---|
| `gh run watch` (or equivalent) in the foreground | Emits TTY redraw frames, not lines, when stdout is not a terminal; suppresses its completion summary for the same reason; has no deadline of its own. |
| `sleep N` polling loop | Burns turns, re-prints the same table, and produces no event when the run *crashes* — a dead run and a slow run look identical. |
| A watcher that greps only for success | Silence on failure. The agent waits out the full timeout for a run that died in minute two. |
| No deadline | A run that never registers — path filter excluded it, workflow disabled, wrong branch — waits forever for something that will never exist. |

The cost is asymmetric: a failure detected at minute 2 of a 25-minute pipeline
gives back 23 minutes of agent time; the same failure detected at the timeout
gives back nothing.

## The contract a watcher must satisfy

1. **Terminate, always.** Every path ends in an explicit verdict line. Silence
   past the deadline must be structurally impossible, not merely unlikely.
2. **Emit on state change only.** Diff-gate the output. A 25-minute green run
   should cost a handful of events, not fifty identical job tables. Watchers
   that flood get rate-limited or killed, which reintroduces the stall.
3. **Cover failure, not just success.** If the process crashed right now, the
   filter must emit something. Widen the match rather than narrow it.
4. **Pin the commit, not the branch.** Query by the SHA you pushed. "Latest run
   on the branch" can be someone else's commit, or your own previous one — a
   classic false green.
5. **Watch every workflow that commit triggered**, not just the one you care
   about. A second workflow can fail while the first goes green.
6. **Heartbeat.** A periodic liveness tick proves the watcher is alive and, on
   agents with a prompt cache, keeps that cache warm so waiting stays cheap.
   Roughly every 2–3 minutes is a reasonable default.
7. **Bound the probe itself.** Give each API call its own timeout; a wedged
   request must not freeze the loop. Retry transient errors, but exit loudly on
   a sustained streak.

## Event vocabulary

A small, stable set of prefixes lets the agent react without parsing prose:

```
CI-RUN   registered 3: build: queued · lint: queued · test: queued
CI-CHG   test: in_progress -> failure
CI-HB    12/30m
CI-WARN  probe failing (3x) — still retrying
CI-DONE  failure — test — <command that prints the failing log>
```

Terminal verdicts worth distinguishing, because each implies a different next
action:

| Verdict | Meaning | Reaction |
|---|---|---|
| `success` | every workflow green on that SHA | proceed |
| `failure` | at least one red | fetch the failing log immediately |
| `cancelled` | ended `cancelled`/`skipped`/`stale`/`neutral` | **not green** — usually a concurrency cancel or a filtered job; decide whether the commit was ever validated |
| `timeout` | deadline hit with work outstanding | read the run; decide to wait or cancel |
| `no-run` | nothing ever registered | check triggers, path filters, enabled state |
| `probe-dead` | the API was unreachable repeatedly | check auth/network |
| `superseded` | the branch moved on | this verdict is moot; arm a watch on the new SHA |

`no-run` and `superseded` are the two that hand-rolled loops almost always
miss, and they are the two that waste the most wall-clock.

**Enumerate success, not failure.** The most dangerous bug in a watcher is
treating "did not fail" as green. A run that ends `cancelled`, `skipped`,
`stale`, or `neutral` is terminal but *not* validated — and `cancel-in-progress`
concurrency, which this skill recommends elsewhere, manufactures exactly that
state. Match an explicit success set and treat every other terminal conclusion,
including ones you have never seen, as not-green.

## Reference implementation shape

Stdlib only, no dependencies. The loop:

```
poll(sha) -> list of {id, workflow, status, conclusion}
  on error:      streak++; warn once at 3; exit `probe-dead` at 10
  on first data: emit CI-RUN once
  per item:      emit CI-CHG only when state differs from last seen
  all terminal:  emit CI-DONE success|failure (+ the log command) and exit
  branch moved:  emit CI-DONE superseded and exit
  no data yet and past registration deadline: emit CI-DONE no-run and exit
  past overall deadline: emit CI-DONE timeout and exit
  else: heartbeat if due, sleep interval
```

Two deadlines matter and they are different: a short **registration** deadline
(a few minutes — did any run appear at all?) and a longer **overall** deadline
(the pipeline's p95 plus headroom).

Provider probes differ only in the poll step:

| Provider | Poll |
|---|---|
| GitHub Actions | `gh run list --commit <sha> --json databaseId,workflowName,status,conclusion` |
| GitLab CI | pipelines API filtered by `sha` |
| Buildkite | builds API filtered by commit |
| CircleCI | pipeline → workflow status by revision |
| Anything else | any command printing `<name>: <state>` lines and a terminal marker |

## Wiring it to a streaming-notification tool

Agent harnesses that expose a background monitor (each stdout line becomes a
notification) are the right host for this. Rules that matter in practice:

- **Every pipe stage must flush per line**, or matches sit in a buffer unseen:
  `grep --line-buffered`, `awk { ...; fflush() }`. `head -N` cannot flush at
  all — it delivers nothing until N matches accumulate.
- **Prefer one bounded process over an unbounded tail.** `tail -f`, `while
  true`, and `inotifywait -m` never exit on their own, so the watch stays armed
  long after the event fired.
- **`tail -f log | grep -m1 …` does not fix that.** If the log goes quiet after
  the match, `tail` never receives SIGPIPE and the pipeline hangs.
- **Arm the watch in the same turn as the push**, then keep working. Do not add
  a `sleep` loop beside an armed watcher; the events come to you.
- **One watch per pushed SHA.** A re-push supersedes the old watch; retire it
  and arm a fresh one.
- **A heartbeat is not a result.** Acknowledge it silently; never report it as
  progress or treat it as a user message.

### Shell gotchas that produce silent watchers

- In `zsh`, `status` is a readonly builtin variable — `status=$(...)` is a fatal
  error inside the watcher, which then emits nothing at all. Name it anything
  else.
- Command substitution strips trailing newlines; compare parsed fields, not raw
  blobs, when diff-gating.
- A watcher that inherits the harness's environment can pick up variables that
  change CI behavior. Prefer explicit arguments over ambient state.

## Reacting to a red check

1. Run the exact log command the verdict printed. Do not re-derive it.
2. Reproduce with the narrowest local command. If the failure is CI-only,
   reproduce the *CI condition* — job-wide environment variables, a clean
   checkout, a different working directory, absent secrets.
3. Fix the cause. Never add a retry, widen a threshold, mock the failure away,
   or `skip` to reach green; the check measures reality.
4. Verify red-first: confirm the test fails without the fix and passes with it.
   A fix you never saw fail is a fix you cannot vouch for.
5. Push and arm a fresh watch on the new SHA.

## Failure-only diagnostics

Upload the diagnostic bundle on failure only, with short retention and exact
paths — logs, screenshots, server output. A successful run does not need them,
and uploading a whole workspace turns every green run into a transfer cost.
Never include generated credentials or a provisioning directory in the bundle.

## Why this is worth the file

The measurable win is not a faster pipeline; it is the agent noticing. A team
that adopts automatic CI without a reliable feedback loop trades a slow local
loop for a silent remote one, and the first red check that goes unnoticed for
twenty minutes erases the migration's entire gain.
