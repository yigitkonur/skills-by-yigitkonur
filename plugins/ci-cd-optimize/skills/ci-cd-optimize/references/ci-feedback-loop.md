# CI feedback loop: watching a run without hanging

Read when an agent (or a human in a non-interactive shell) needs to learn a CI
result, when a watch command "returns nothing", when a monitor stays armed after
a run finished, or when a pipeline is CI-only so every verification round-trips
through the provider.

Optimizing pipeline seconds is wasted if the agent then blocks for twenty
minutes on a broken watch, or worse, silently concludes "no news, must be fine."
The feedback loop is part of the critical path.

## Fast triage

| Symptom | Most likely cause | Go to |
|---|---|---|
| Watch returns instantly, reports nothing running | Registration race — armed before the run was indexed | Failure mode 1 |
| Watch prints a garbled blob, or nothing, then exits 0 | Non-TTY redraw output | Failure mode 2 |
| Watch never returns; harness timeout kills it | No deadline of its own | Failure mode 3 |
| Run failed but the agent proceeded as if green | Success-only filter; silence read as success | Failure mode 4 |
| Monitor stays armed long after the run ended | Unbounded command (`tail -f`, `while true`) | Wiring it to an agent monitor |
| Monitor auto-stopped mid-run | Output volume; every line became a notification | Wiring it to an agent monitor |
| Green reported for someone else's commit | Branch-tip watch instead of SHA-pinned | The contract |
| Old run reports failure right after you re-push | Concurrency cancellation, not a real failure | `superseded` verdict |

## The four failure modes

Each is common, each has been observed in practice, and each is silent.

**1. Registration race.** You push, immediately ask the provider "what is
running?", and get nothing — the run has not been created or indexed yet.
Auto-selecting watchers (`gh run watch` with no id, `avr run watch` with no id)
exit successfully with "no in-progress runs". The agent reads success. Nothing
was verified. *Fix: poll for a run matching your exact SHA, with its own
registration deadline, before watching anything.*

**2. Non-TTY output.** Interactive watchers redraw with ANSI cursor control
instead of emitting lines, and some suppress the completion summary entirely
when stdout is not a terminal. A line-oriented consumer sees a blob, or nothing.
*Fix: prefer a line/NDJSON mode when the CLI has one; otherwise poll an API and
print your own lines.*

**3. No deadline of its own.** A watch inherits no timeout. If a run never
registers, a check never reports, or the API returns 5xx in a streak, the
watcher waits forever. Harness-level timeouts eventually fire, but you have
burned the budget and learned nothing. *Fix: a hard ceiling that exits with an
explicit `timeout` verdict.*

**4. Success-only filters.** `grep "passed"` looks identical whether the run is
still going, crashed, was cancelled, or never started. **Silence is not
success.** *Fix: emit a terminal verdict on every path, including failure,
cancellation, timeout, and never-registered.*

## The contract a watcher must satisfy

Anything you build or adopt should guarantee:

| Property | Why |
|---|---|
| **SHA-pinned** | A branch-tip watch can report a green from someone else's newer push, or a stale run from before your change. Verification must bind to the commit you pushed. |
| **Terminal on every path** | `success`, `failure`, `cancelled`, `timeout`, `no-run`, `superseded`. Silence must be structurally impossible. |
| **Registration window** | Bounded wait for the run to appear, separate from the run's own deadline. |
| **Change-gated output** | Emit on state transitions, not every poll. Repeated identical lines flood the transcript and get monitors auto-killed. |
| **Per-probe timeout** | One wedged HTTP request must not freeze the loop. |
| **Error tolerance** | Transient 5xx happens; retry quietly, exit loudly after a streak. |
| **Heartbeat** | A periodic progress line proves liveness during long queues without flooding. |
| **Actionable failure** | The failure line should carry the command that shows the logs. |

## Event vocabulary

A compact, greppable stream. Prefixes matter more than exact words — pick one
scheme and keep it stable so filters and humans can both read it.

```
CI-RUN  <sha> registered: build:queued · test:queued
CI-CHG  test: in_progress
CI-CHG  test: completed -> failure
CI-HB   6/30m — build=completed/success test=in_progress/-
CI-DONE failure — test — logs: <exact command to view them>
```

Reaction policy: act on the first `CI-CHG … -> failure` immediately rather than
waiting for `CI-DONE`; on a long pipeline that is a large head start on the fix.
Acknowledge `CI-HB` silently. Treat `CI-DONE no-run` as "verification did not
happen", never as success.

## Reference implementation

Provider-neutral shape. Substitute the provider query; the control flow is the
point.

```bash
#!/usr/bin/env bash
set -uo pipefail
SHA="${1:-$(git rev-parse HEAD)}"
DEADLINE="${DEADLINE:-1800}"; REGISTER="${REGISTER:-300}"
HEARTBEAT="${HEARTBEAT:-150}"; POLL="${POLL:-10}"

# One probe, individually timed out, returning JSON for this SHA only.
probe() { timeout 25 <provider-cli> list --json ... ; }
done_with() {
  verdict="$1"
  echo "CI-DONE $verdict${2:+ — $2}"
  case "$verdict" in
    success) exit 0 ;;
    failure) exit 1 ;;
    no-run) exit 2 ;;
    superseded|cancelled) exit 3 ;;
    timeout) exit 124 ;;
    *) exit 2 ;;
  esac
}

start=$SECONDS
# Phase 1 — registration, with its own deadline.
while [ $((SECONDS-start)) -lt "$REGISTER" ]; do
  runs="$(probe | jq -c --arg s "$SHA" '[.[]|select(.head_sha==$s)]')"
  [ "$(jq length <<<"$runs")" -gt 0 ] && break
  sleep "$POLL"
done
[ "$(jq length <<<"${runs:-[]}")" -gt 0 ] || done_with no-run "nothing registered for ${SHA:0:7}"
echo "CI-RUN ${SHA:0:7} registered"

# Phase 2 — change-gated polling until every run is terminal.
prev=""; errors=0; beat=$SECONDS
while [ $((SECONDS-start)) -lt "$DEADLINE" ]; do
  snap="$(probe | jq -c --arg s "$SHA" '[.[]|select(.head_sha==$s)]')"
  if [ -z "$snap" ]; then
    errors=$((errors+1))
    [ "$errors" -ge 10 ] && done_with failure "provider unreachable for 10 probes"
    sleep "$POLL"; continue
  fi
  errors=0
  cur="$(jq -r 'sort_by(.id)|map("\(.name)=\(.status)/\(.conclusion//"-")")|join(" ")' <<<"$snap")"
  if [ "$cur" != "$prev" ]; then
    jq -r '.[]|"CI-CHG \(.name): \(.status)\(if .conclusion then " -> \(.conclusion)" else "" end)"' <<<"$snap"
    prev="$cur"; beat=$SECONDS
  elif [ $((SECONDS-beat)) -ge "$HEARTBEAT" ]; then
    echo "CI-HB $(((SECONDS-start)/60))/$((DEADLINE/60))m — $cur"; beat=$SECONDS
  fi
  if [ "$(jq '[.[]|select(.status!="completed")]|length' <<<"$snap")" -eq 0 ]; then
    bad="$(jq -r '[.[]|select(.conclusion=="failure" or .conclusion=="timed_out")][0].name // empty' <<<"$snap")"
    [ -n "$bad" ] && done_with failure "$bad — logs: <cli> view <id> --log-failed"
    [ "$(jq '[.[]|select(.conclusion=="cancelled")]|length' <<<"$snap")" -gt 0 ] \
      && done_with superseded "a newer push replaced ${SHA:0:7}"
    done_with success "${SHA:0:7}"
  fi
  sleep "$POLL"
done
done_with timeout "still running after $((DEADLINE/60))m"
```

Shell notes that cost real debugging time: in `zsh`, `status` is a **readonly**
builtin variable — assigning it aborts the script, so name your variables
`state`/`verdict`. Every pipe stage must flush per line (`grep --line-buffered`,
`awk '{...; fflush()}'`); `| head -N` buffers until N matches and can strand the
stream entirely.

## Wiring it to an agent monitor

Two different tools for two different needs. Choosing wrong is the usual cause
of a stuck agent.

**One notification, when a condition becomes true** — use a backgrounded
command that *exits* when the condition holds:

```
Bash(run_in_background: true,
     command: "until <condition>; do sleep 5; done")
```

**A stream of events as they occur** — use the streaming monitor, with a command
that terminates on its own:

```
Monitor(command: "DEADLINE=1500 scripts/ci-watch.sh <sha>",
        description: "CI for <branch>",
        timeout_ms: 1560000)
```

Rules that keep this reliable:

- **Never arm an unbounded command for a one-shot answer.** `tail -f`,
  `while true`, and `inotifywait -m` never exit, so the monitor stays armed long
  after the event fired and eventually dies on timeout instead of completing.
- **Set the monitor timeout above the watcher's own deadline**, so the *script*
  decides the outcome and reports a verdict, rather than the harness killing it
  with no explanation.
- **Filter to lines you would act on.** Piping raw CI logs generates a
  notification per line; high-volume monitors get stopped automatically.
- **One watch per pushed SHA.** Re-pushing supersedes the old run — let the old
  watcher exit `superseded` and arm a new one rather than reasoning about two
  overlapping streams.
- **Do not poll from the main loop while a monitor is armed.** Duplicated
  polling wastes budget and produces contradictory readings.

## Making the watch cheap to arm

The loop is only followed if it is one command. Commit the watcher to the
repository (`scripts/ci-watch.sh`) rather than expecting an agent to retype a
poll loop each time — hand-rolled loops are where the four failure modes above
reappear. Document the exact invocation in `AGENTS.md`/`CONTRIBUTING.md` next to
the push instruction, and state the expected duration so an agent can tell
"slow" from "stuck".

If the platform offers a native line-oriented watch (`--ndjson`, `--json`,
`--exit-status`), prefer it *inside* the script for the streaming phase, but
keep your own registration window and deadline around it. Native watches solve
output shape; they generally do not solve registration, deadline, or SHA
pinning.

## Verifying the watcher itself

A watcher is verification infrastructure, so test its failure paths before
trusting it — the same standard applied to any other gate:

1. **no-run** — invoke against a SHA that has no runs; it must exit with
   `no-run` inside the registration window, not hang.
2. **failure** — push a deliberately broken commit (a type error is cheap and
   unambiguous); it must report `failure` and print a working logs command.
   Revert immediately afterward.
3. **success** — a normal green push produces `CI-DONE success`.
4. **superseded** (if your pipeline cancels stale runs) — push twice quickly;
   the first watch should end `superseded`, not `failure`.

Until those paths are exercised, "the watcher works" is a config-review claim,
not a verified one.

## Distinguishing "slow" from "stuck"

Long waits are not automatically a defect. Before treating a slow run as a
problem, split the wall clock:

- **Queue time** (created → started) is provider capacity. On a measured
  repository it ranged 10s–193s within a single hour on identical config, while
  execution held steady at 11–13s. Nothing in the workflow file changes that.
- **Execution time** (started → completed) is yours to optimize.

A watcher that heartbeats with elapsed time lets an agent tell the difference
without polling. Report the two separately; presenting a queue-dominated wall
clock as a regression sends the next optimization round after the wrong target.

## Sources

- Failure taxonomy and the diff-gated / guaranteed-exit design are modeled on
  `yigitkonur/plugin-ci-watch-unstall` (README, accessed 2026-07-28), which
  documents the same `gh run watch` non-TTY and no-deadline problems.
- Registration-race behavior, `--ndjson` output shape, and the queue-vs-execution
  spread were observed directly against `avr` 0.1.6 on a live repository
  (2026-07-28); the id-less watch exiting 0 with "No in-progress workflow runs
  found" is a reproduced observation, not a vendor-documented behavior.
- `zsh` readonly `status` and pipe-buffering pitfalls were hit and fixed while
  building the reference implementation above.
