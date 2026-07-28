# Agent Feedback Loops: Waiting on CI Without Stalling

Read when an autonomous agent must push work and then *learn the result* — or
when an agent has been observed sitting idle after a push, reporting a stale
green, or burning its context on duplicate status tables.

This is a distinct failure domain from pipeline speed. A 90-second pipeline is
worthless to an agent that waits 20 minutes to notice it finished, and actively
dangerous if the agent concludes "green" from a run that never started.

## The contract a CI watcher must satisfy

Any wait mechanism an agent arms after a push must guarantee all six. Missing
one produces a specific, observed failure:

| Property | Failure when missing |
|---|---|
| **Terminates on every path** | The agent waits forever on a crashed, cancelled, or never-registered run |
| **Emits on failure, not just success** | Silence is indistinguishable from "still running" — a crashloop looks like patience |
| **Diff-gated output** | A 25-minute run re-prints the same job table 50 times and evicts the agent's working context |
| **Non-silent while healthy** | Long queues become ambiguous; the agent cannot tell "queued" from "watcher died" |
| **Bound to an exact commit** | A branch-tip query returns someone else's newer run — a false green |
| **Bounded per-probe latency** | One wedged API call freezes the loop with no deadline |

### Terminal verdicts

Emit exactly one terminal line, then exit. A useful verdict set:

| Verdict | Meaning | Agent's next move |
|---|---|---|
| `success` | All runs for the commit finished green | Continue |
| `failure` | A run failed | Fetch failing logs, fix |
| `cancelled` | Everything terminal ended cancelled, and the branch did not move | Inspect; usually a concurrency cancel or an operator stop, not a code defect |
| `timeout` | Hard deadline hit | Inspect the run; do not assume either outcome |
| `no-run` | Nothing registered within the registration deadline | Usually correct — path filters excluded the change. Not a failure |
| `superseded` | A newer commit landed on the branch | Retire; arm a fresh watch on the new SHA |
| `probe-dead` | The status API failed repeatedly | Escalate; the result is unknown |

`no-run` deserves emphasis: with path-filtered triggers, a docs-only commit
*correctly* starts nothing. A watcher without a registration deadline hangs
forever on exactly the commits that are safest.

`superseded` must be evaluated **before** any run is called a failure. Under
the `cancel-in-progress: true` concurrency pattern that this skill recommends
elsewhere, pushing a fix cancels the previous commit's run — and a watcher that
checks failure first reports `failure` for a run nobody should act on.

## Anti-patterns

| Approach | Why it stalls an agent |
|---|---|
| `gh run watch` / any vendor `watch` piped into an agent harness | Emits TTY redraw blocks rather than lines, and several CLIs suppress their completion summary when stdout is not a terminal. No deadline of its own |
| `while true; do sleep 30; done` with a success-only `grep` | A crashed run emits nothing — identical to a healthy one. No deadline |
| `tail -f log \| grep "BUILD OK"` | Same silence-on-failure defect, plus unflushed pipe buffers hide matches |
| Single-condition `until` loop | Correct for "tell me when X exists"; emits nothing if X never happens and cannot report failure |
| Polling the branch tip instead of the commit | Returns a newer run from another push — a false green on a commit that was never tested |
| Re-printing full job state each poll | Burns context until the harness rate-limits or kills the monitor |

A blocking foreground wait is its own anti-pattern: the agent could have been
working. Arm the watch in the background and continue.

## Reference implementation

`scripts/ci-watch.py` (stdlib-only Python, no dependencies) implements the
contract. Two modes:

```bash
# GitHub Actions, zero config
python3 scripts/ci-watch.py --sha "$(git rev-parse HEAD)" --branch main

# Any other provider: supply a probe that prints "<name>: <state>" lines
python3 scripts/ci-watch.py --sha "$SHA" --cmd './ci/probe.sh'
```

The probe contract is deliberately small so the same harness works for GitLab,
Buildkite, a deploy API, or a `curl`:

- print one `name: state` line per unit of work
- print `TERMINAL: <verdict>` when everything reached a terminal state
- exit non-zero only for probe failure, not for pipeline failure

The harness exports the watched commit to the probe as `$CI_WATCH_SHA`; a probe
that reports on anything other than that commit breaks the "bound to an exact
commit" guarantee, and the harness cannot catch that for you. A minimal probe:

```sh
#!/bin/sh
# Answers "did the deploy for THIS commit reach the app?"
code=$(curl -sf "https://api.example.com/deploys?sha=$CI_WATCH_SHA" \
       | python3 -c 'import sys,json;d=json.load(sys.stdin);print(d.get("state","pending"))')
echo "deploy: ${code:-pending}"
[ "$code" = "live" ] && echo "TERMINAL: success"
```

### Arming it from an agent

With Claude Code's `Monitor` tool (the same shape applies to any
background-task mechanism):

```
Monitor(
  command: "python3 scripts/ci-watch.py --sha <sha> --branch <branch>",
  description: "CI for <sha>",
  timeout_ms: 1800000,
)
```

Arm it **immediately after** `git push`, a workflow dispatch, or a re-run —
then keep working. Do not block.

### Event stream

```
CI-RUN     registered 2: build: queued · test: queued
CI-CHG     build: queued -> in_progress
CI-HB      160s/1500s — 2 run(s) tracked
CI-CHG     test: in_progress -> failure
CI-DONE    failure — test — logs: gh run view 123 --log-failed
```

**React to the first `CI-CHG … -> failure`, not to `CI-DONE`.** In a pipeline
whose slowest lane runs 25 minutes, a lane that fails at minute 6 gives a
19-minute head start on the fix. Acknowledge heartbeats silently.

### Heartbeat interval

Pick an interval shorter than your model's prompt-cache TTL (commonly 5
minutes) so a long wait keeps the conversation cache warm; ~2–3 minutes works.
The heartbeat is also the liveness proof that distinguishes a long queue from a
dead watcher.

## Two correctness traps when reading run state

**1. Re-run attempts — provider-specific.** Verified 2026-07-28: `gh run list
--commit <sha> --json databaseId,attempt,status,conclusion` returns **one row
per run id, already reflecting the latest attempt**, so no de-duplication is
needed there. Other status APIs do not all behave that way — Avrea's
`avr run list` returns a separate record per attempt sharing one
`platform_run_id`, so a query after a re-run yields both
`attempt: 1 (failure)` and `attempt: 2 (in_progress)`. Reading those naively
reports the stale failure, and a watcher keyed on the run id oscillates between
the two records. Before trusting any status query, check whether it collapses
attempts; if it does not, keep the highest attempt per id.

**2. `workflow_run`-style follow-ups register late.** When one workflow
triggers another on completion (deploy after build), the follow-up does not
exist yet at the moment the first turns green. Exiting on first-green reports a
success that structurally cannot include the deploy. Hold a settle window after
everything known is green and re-probe before declaring success. Size it from
the observed gap between "first workflow concludes" and "follow-up appears" in
your own run history — tens of seconds is typical; the bundled script defaults
to 90s and exposes `--settle`.

## Granularity: run-level status hides an early failing job

A run-level status stays `in_progress` until *every* job finishes, and its
conclusion is unset until then. If a pipeline is one workflow containing
several jobs, polling run status alone cannot tell you that one lane already
failed — which defeats the "react to the first red check" payoff.

Either split genuinely independent lanes into separate workflows, or expand
in-flight runs to job level when polling (`gh run view <id> --json jobs`).
`scripts/ci-watch.py` does the latter automatically for in-progress runs and
falls back to run-level state for completed ones, so the extra API call is
bounded to runs that are still moving.

## Flake triage without weakening the test

When CI fails, decide *whether it is your failure* before changing code:

1. Diff the failing commit against the last green one:
   `git diff --stat <green>..<red>`.
2. If nothing in that diff can plausibly reach the failing test, re-run the
   **identical commit** rather than pushing a speculative fix.
3. A pass on the unchanged commit demonstrates a flaky test. That is a separate
   defect to report and own — never "fix" it by relaxing the assertion, adding
   a retry, or re-running until green.

A provider flake counter (where one exists) is a useful prior but not a
substitute: it typically only catches a step that succeeded elsewhere, so a
consistently-failing-then-passing test can read as zero flakes. The
identical-commit re-run is the reliable test. See
`references/testing-and-flakiness.md` for quarantine and ownership once a flake
is confirmed.

## Sources

- GitHub Actions `workflow_run` trigger semantics: https://docs.github.com/actions/reference/events-that-trigger-workflows (accessed 2026-07-28)
- Prior art on agent CI stalling, including the TTY-redraw and success-only-grep failure modes: https://github.com/yigitkonur/plugin-ci-watch-unstall (accessed 2026-07-28)
