# Feedback Loops: Waiting on CI Without Stalling

Read when an agent or non-interactive process must learn the result of a
pipeline it triggered — after a push, a re-run, a dispatch, or a deploy — or
when a watch command "returns nothing", a monitor stays armed after a run
finished, or CI is the only surface where verification runs.

This is a distinct failure domain from pipeline speed, and a correctness
problem rather than a convenience one. A 90-second pipeline is worthless to an
agent that waits 20 minutes to notice it finished, and actively dangerous if
the agent concludes "green" from a run that never started. A session blocked on
CI with no deadline is indistinguishable from a session that has crashed.

## Fast triage

| Symptom | Most likely cause | Section |
|---|---|---|
| Watch returns instantly, reports nothing running | Registration race — armed before the run was indexed | Failure modes |
| Watch prints a garbled blob or nothing, then exits 0 | Non-TTY redraw output; suppressed completion summary | Failure modes |
| Watch never returns; the harness timeout kills it | No deadline of its own | Failure modes |
| Run failed but the agent proceeded as green | Success-only filter; silence read as success | Failure modes |
| Green reported for a commit you did not push | Branch-tip watch instead of SHA-pinned | The contract |
| Old run reports failure right after you re-push | Concurrency cancellation, not a real failure | `superseded` |
| Monitor stays armed long after the run ended | Unbounded command (`tail -f`, `while true`) | Wiring to a harness |
| Monitor auto-stopped mid-run | Output volume; every poll became a notification | The contract (diff-gating) |

## The failure modes

Each is common, each has been observed in practice, and each is silent — which
is what makes them dangerous rather than merely annoying.

**1. Registration race.** Push, immediately ask the provider "what is running?",
get nothing — the run is not created or indexed yet. Auto-selecting watchers
(`gh run watch` with no id, `avr run watch` with no id) exit 0 with "no
in-progress runs". The agent reads success; nothing was verified. The same
shape hides in `until [ pending -eq 0 ]` loops: a commit with *zero* runs also
has zero pending runs, so the loop exits "done" immediately.

**2. Non-TTY output.** Interactive watchers redraw with ANSI cursor control
instead of emitting lines, and several suppress the completion summary entirely
when stdout is not a terminal. A line-oriented consumer sees a redraw blob, or
nothing, then no finish event. Confirm before trusting any `watch` subcommand:

```bash
timeout 25 <provider-watch-cmd> | cat -A | head -20
```

Repeated identical blocks or `^[[` cursor escapes mean it is a rendering loop,
unsuitable as an event source.

**3. No deadline of its own.** A watch inherits no timeout. A run that never
registers, a required check that never resolves, or a 5xx streak blocks forever.
`--exit-status` gives a pass/fail code but no time bound.

**4. Success-only filters.** `grep "passed"` looks identical whether the run is
still going, crashed, was cancelled, or never started. **Silence is not
success.** Demonstrable in one line:

```bash
echo failure | grep -q success && echo exits || echo "no output — loops forever"
```

The same defect hides in filters listing only the success marker, and in
`watcher | head` pipelines, where the pipeline's exit code is `head`'s — a hard
failure converted into exit 0. Capture output first, then read the real code.

## The contract

Any watcher an agent arms must satisfy all of these; missing one reintroduces a
stall.

| Property | Why |
|---|---|
| **Terminates on every path** | Emit exactly one terminal line, then exit. Silence past the deadline must be structurally impossible. |
| **Pinned to a commit, not a workflow** | A branch-tip query returns someone else's newer run — a false green. Pinning to the SHA also catches a *second* workflow that fails after the first passed. |
| **Diff-gated output** | Emit only on state change. A 20-minute green run should cost a handful of lines; harnesses auto-stop noisy monitors, and a stopped monitor is silence. |
| **Registration deadline** | If nothing appears for the SHA within a few minutes, say `no-run` and exit. A path filter, wrong ref, or failed push must not read as "still running". |
| **Settles before declaring success** | Runs register seconds apart; `workflow_run`-style chains register much later. Hold a short all-green window and re-probe. |
| **Detects supersession** | If the branch moves past the watched SHA, retire rather than report the concurrency-cancelled run as a failure. |
| **Bounded per-probe latency + error streak** | One wedged request cannot freeze the loop; retry transient errors, warn on a short streak, exit loudly on a long one. |
| **Heartbeats** | A periodic tick separates "still working" from "wedged", and on cache-based model APIs keeps the prompt cache warm — keep it under the TTL (~150s for a 5-minute TTL). |

### Terminal verdicts

Distinct exit codes matter: `watch && deploy` must not proceed on a
`superseded` watch that never reached a real verdict.

| Verdict | Meaning | Caller's move | Exit |
|---|---|---|---|
| `success` | every run for the SHA is green | proceed; claim only this SHA | 0 |
| `failure` | a run went red | fetch that job's failing logs now, fix, re-push, arm a fresh watch | 1 |
| `timeout` | not terminal within the deadline | inspect; stuck, not slow. Re-arm with a larger deadline | 2 |
| `no-run` | nothing registered for the SHA | wrong ref, path filter, failed push — actionable, not a hang | 2 |
| `probe-dead` | repeated API/CLI failures | check auth, network, rate limits; the result is unknown | 2 |
| `superseded` | branch moved past the SHA | re-arm on the new SHA | 3 |

The two most often omitted are `no-run` and `superseded`, and they are the two
that most often masquerade as "CI is just slow". `timeout`, `no-run`, and
`probe-dead` all mean *you still do not know* — never record any of them as a
pass. Put the failing run's log command inside the `failure` line so the caller
never has to reconstruct it.

Evaluate supersession **before** calling a cancelled run a failure: under the
`cancel-in-progress` concurrency pattern this skill recommends elsewhere,
pushing a fix cancels the previous commit's run, and "cancelled because a newer
push landed" is not a bug to go fix. A completed *red* run still reports
`failure` even if the branch moved — "did this SHA pass" matters more than "did
the branch move".

## Event vocabulary

A compact, greppable prefix per line. Prefixes matter more than exact words —
pick one scheme and keep it stable so filters and humans can both read it.

```
CI-RUN    registered 3: build: queued · lint: queued · test: queued
CI-CHG    test: in_progress -> failure
CI-HB     6/25m — build:success lint:success test:failure
CI-SETTLE all green; holding 90s for late-registering workflows
CI-DONE   failure — test — logs: gh run view 123 --log-failed
```

**Reaction policy: act on the first `CI-CHG … -> failure`, not on `CI-DONE`.**
On a 25-minute pipeline, a failure at minute 6 gives a ~19-minute head start on
the fix. Acknowledge `CI-HB` silently; a heartbeat is liveness, not news, and
events arrive asynchronously — an event is never a reply from the user. A
verdict is about one SHA only; after pushing a fix, the previous verdict is
void.

## Two correctness traps when reading run state

**1. Re-run attempts — provider-specific.** Verified 2026-07-28:
`gh run list --commit <sha> --json databaseId,attempt` returns **one row per run
id, already reflecting the latest attempt**, so no de-duplication is needed
there. Other status APIs do not all behave that way — Avrea's `avr run list`
returns a separate record per attempt sharing one `platform_run_id`, so a query
after a re-run yields both `attempt 1 (failure)` and `attempt 2 (in_progress)`.
Reading those naively reports the stale failure, and a watcher keyed on the run
id oscillates between the records. Before trusting any status query, check
whether it collapses attempts; if not, keep the highest attempt per id.
(Attempt semantics also affect *measurement* — see the rerun sampling trap in
`references/measurement.md`.)

**2. `workflow_run`-style follow-ups register late.** When one workflow triggers
another on completion (deploy after build), the follow-up does not exist yet
when the first turns green. Exiting on first-green reports a success that
structurally cannot include the deploy. Size the settle window from the observed
gap between "first workflow concludes" and "follow-up appears" in your own run
history — tens of seconds for pipelines that register seconds apart;
`workflow_run` chains register *after* their trigger completes, so give those
60–120s or watch the downstream workflow explicitly.

## Granularity: run-level status hides an early failing job

A run-level status stays `in_progress` until *every* job finishes, and its
conclusion is unset until then. If a pipeline is one workflow with several jobs,
polling run status alone cannot tell you one lane already failed — which defeats
the "react to the first red check" payoff. Either split genuinely independent
lanes into separate workflows, or expand in-flight runs to job level when
polling (`gh run view <id> --json jobs`). `scripts/ci-watch.py` expands
in-progress runs automatically and falls back to run-level state for completed
ones, so the extra call is bounded to runs still moving.

## Reference implementation

`scripts/ci-watch.py` (stdlib-only Python, no dependencies) implements the
contract. Two modes:

```bash
# GitHub Actions, zero config
python3 scripts/ci-watch.py --sha "$(git rev-parse HEAD)" --branch main

# Any other provider: a probe that prints "<name>: <state>" lines, and
# "TERMINAL: <verdict>" once everything is terminal
python3 scripts/ci-watch.py --sha "$SHA" --cmd './ci/probe.sh'
```

The probe contract is deliberately small so the same harness works for GitLab,
Buildkite, CircleCI, an EAS build, or a deploy API polled with `curl`:

- print one `name: state` line per unit of work
- print `TERMINAL: <verdict>` when everything reached a terminal state
- exit non-zero only for probe failure, not for pipeline failure

The harness exports the watched commit to the probe as `$CI_WATCH_SHA`; a probe
reporting on anything other than that commit breaks the "bound to an exact
commit" guarantee, and the harness cannot catch that for you. A minimal probe:

```sh
#!/bin/sh
# Answers "did the deploy for THIS commit reach the app?"
if ! response=$(curl -sf "https://api.example.com/deploys?sha=$CI_WATCH_SHA"); then
  echo "probe: deploy API request failed"
  exit 1
fi
if ! state=$(printf '%s' "$response" \
        | python3 -c 'import sys,json;print(json.load(sys.stdin).get("state","pending"))'); then
  echo "probe: deploy API returned invalid JSON"
  exit 1
fi
echo "deploy: ${state:-pending}"
[ "$state" = "live" ] && echo "TERMINAL: success"
```

For provider CLIs, keep the loop and swap the probe: GitHub PR-gate checks via
`gh pr checks <pr> --json name,bucket` (terminal when nothing is `pending`;
note PR mergeability includes third-party required checks and is a different
question from branch CI — watch whichever actually gates you), GitLab via the
pipelines API (`glab ci status --live` is TTY-shaped), Buildkite via the REST
build endpoint, Avrea via `avr run list`/`avr run watch --ndjson` wrapped with
your own deadline.

Details that only surface in live testing, worth keeping in any
re-implementation:

- **Normalize to a full SHA before querying.** `gh run list --commit` silently
  returns zero results for a short SHA — which a registration deadline then
  reports as `no-run`.
- **Key diff-gate state by run id, not workflow name** — one commit can carry
  several runs of the same workflow; keyed by name they overwrite and the
  watcher flaps forever.
- **Guard the empty list.** `all([])` is `True` in most languages, so
  `all(completed)` over zero runs reports success having observed nothing.
  Require a non-empty run set before concluding.
- **Clamp the registration deadline below the overall deadline**, or a SHA with
  no runs reports the far less useful `timeout` instead of `no-run`.
- **Resolve the branch tip from the ref** (`git ls-remote origin refs/heads/<b>`),
  not from "latest run on branch" — the provider's latest run is *not* the
  branch tip when the newest push has not registered, and a naive check reports
  the new commit as superseded by its own ancestor.
- **Bound the lookback window consciously.** Providers that list runs by time
  window silently return nothing for an older SHA, which reads as `no-run` when
  the runs merely aged out.

## Wiring it to an agent harness

Run the watcher as a background process whose **stdout lines become
notifications**, so the agent keeps working and reacts on arrival. With Claude
Code's `Monitor` (the same shape applies to any streaming background-task tool):

```
Monitor(
  command: "python3 scripts/ci-watch.py --sha <sha> --branch <branch> --deadline 1500",
  description: "CI for <sha>",
  timeout_ms: 1800000,        # comfortably longer than the watcher's own deadline
)
```

Rules that matter in practice:

- **Set the harness timeout above the watcher's own deadline** (a few minutes'
  headroom), so the *watcher* ends the watch and prints a verdict rather than
  the harness killing it. A killed watcher looks identical to a hung one.
- **Arm it last.** Any commit after arming moves the branch and the watcher
  retires as `superseded` — correct, but you lose the watch. Finish committing,
  then arm.
- **Never hand-type the SHA.** Use `$(git rev-parse HEAD)`; a wrong SHA reports
  `superseded` or `no-run` against the real head and teaches you nothing.
- **One watch per pushed SHA.** After a re-push, arm a fresh one; do not reason
  about two overlapping streams.
- **Do not also poll from the main loop while a monitor is armed** — duplicated
  polling wastes budget and produces contradictory readings.
- **If any stage is a shell pipeline, flush per line** — `grep --line-buffered`,
  `awk` + `fflush()`; `head -N` cannot flush and withholds output until N
  matches accumulate. (In `zsh`, also avoid a variable named `status`; it is
  readonly and the loop dies instantly.)
- **Size the deadline above the workflow's observed p95, including queue.** A
  pipeline that executes in 40s can still sit many minutes in a runner
  shortage; a deadline tuned to execution time fires spuriously and trains the
  agent to ignore verdicts. Recurring timeouts with flat execution mean the
  bottleneck is capacity — route to `references/capacity-and-contention.md`.

### When one notification is enough

For "tell me when it is done", a bounded background command that exits on the
condition is simpler than a streaming watcher, and produces a single completion
notification:

```bash
until <terminal-state-check>; do sleep 20; done
```

Use the streaming watcher when you want to react to the *first* red check while
other jobs still run. Never arm an unbounded command (`tail -f`, `while true`,
`inotifywait -m`) for a one-shot answer — it stays armed long after the event
and can only end by timeout. And never use a bare `until`-loop as the CI gate:
it emits nothing on failure and cannot distinguish "condition will never
happen" from "still waiting".

## Flake triage without weakening the test

When CI fails, decide *whether it is your failure* before changing code:

1. Diff the failing commit against the last green one:
   `git diff --stat <green>..<red>`.
2. If nothing in that diff can plausibly reach the failing test, re-run the
   **identical commit** rather than pushing a speculative fix.
3. A pass on the unchanged commit demonstrates a flaky test — a separate defect
   to report and own, never "fixed" by relaxing the assertion, adding a retry,
   or re-running until green.

A provider flake counter (where one exists) is a useful prior but not a
substitute: it typically only catches a step that succeeded elsewhere, so a
consistently-failing-then-passing test can read as zero flakes. The
identical-commit re-run is the reliable test. See
`references/testing-and-flakiness.md` for quarantine and ownership once a flake
is confirmed.

## Verify the watcher before trusting it

A watcher is verification infrastructure, so test its failure paths before
relying on it — the same standard applied to any other gate. Capture output
first, since `| tail` masks the real exit code (`out=$(...); code=$?`).

| Path | How to force it |
|---|---|
| `no-run` | Watch an unpushed or all-zeros SHA with a short registration deadline. |
| `failure` | Watch a known-red historical SHA. |
| `success` | Watch a known-green historical SHA. |
| `superseded` | Watch a SHA, then push one more commit to the branch. |
| `timeout` | Watch an in-progress SHA with a tiny deadline. |

A live rehearsal is not optional: offline probes miss the branch-tip trap
above, which every offline test passes and live CI fails. A watcher you have
not seen fail correctly is not yet a safety mechanism.

## Making the watch cheap to arm

The loop is only followed if it is one command. Commit the watcher to the
repository rather than expecting an agent to retype a poll loop each time —
hand-rolled loops are where the failure modes above reappear. Document the
exact invocation in `AGENTS.md`/`CONTRIBUTING.md` next to the push instruction,
with the expected run duration so an agent can tell "slow" from "stuck". If the
platform ships a machine-readable line/NDJSON watch, prefer it *inside* the
streaming phase but keep your own registration window, deadline, and SHA
pinning around it — native watches solve output shape, not registration or
deadline.

For repositories agents work on routinely, also expose **narrow feedback
lanes**: a dispatchable workflow with a mode input (`typecheck`, `lint`,
`build`, `affected`) returns a targeted answer in a fraction of the full gate's
time. Correlate the resulting run by head SHA plus a dispatch-time window, not
by run title — title templates do not reliably populate the API's display-title
field.

## Sources

- GitHub Actions `workflow_run` trigger semantics: https://docs.github.com/actions/reference/events-that-trigger-workflows (accessed 2026-07-28)
- `gh run watch` TTY gating of screen refresh and completion summary: `cli/cli` `pkg/cmd/run/watch/watch.go`, `pkg/iostreams/iostreams.go` (read 2026-07-28); flag reference https://cli.github.com/manual/gh_run_watch (accessed 2026-07-28)
- `gh pr checks` omits expected checks (why a branch watch is not a PR-mergeability watch): https://github.com/cli/cli/issues/6448 (open, accessed 2026-07-28); `gh run watch` deadline gap: https://github.com/cli/cli/issues/6560 (accessed 2026-07-28)
- Prior art on agent CI stalling, including the TTY-redraw, no-deadline, and success-only-grep failure modes: https://github.com/yigitkonur/plugin-ci-watch-unstall (accessed 2026-07-28)
- The `gh` attempt-collapsing behavior, the auto-select registration-race exit-0, the short-SHA zero-result behavior, and every watcher exit path above were reproduced against live repositories on 2026-07-28.
