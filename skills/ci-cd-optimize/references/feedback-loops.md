# Feedback Loops: Receiving a Pipeline Result Without Stalling

Read this when work is validated *through* CI — an agent or long-running session
pushes, dispatches, re-runs, or deploys, then must learn the outcome before
continuing. Also read it when a wait command hangs, floods the context, or reports
a verdict that turns out to be for the wrong commit.

Making a pipeline fast is only half the job. The other half is consuming the
result. A 60-second pipeline still costs ten minutes of wall-clock if the waiter
blocks on it, and it is *dangerous* if the waiter concludes "green" from a run
that never started. This is a correctness problem, not a convenience one: a
session blocked on CI with no deadline is indistinguishable from a session that
crashed.

The failure is provider-neutral, so the contract here is too. Only the probe
command changes between GitHub Actions, GitLab, Buildkite, CircleCI, or a deploy
API.

## Why the obvious approaches fail

Every naive wait shares one of a few defects. Naming them is what lets an agent
recognize its own stall:

| Attempt | Failure mode |
|---|---|
| A vendor `watch` subcommand piped into a harness (`gh run watch`, `avr run watch`, …) | Off a TTY these redraw the whole run table each interval instead of emitting lines, and many suppress their completion summary entirely when stdout is not a terminal. You get unparseable repetition and no terminal line. None carry a deadline of their own. |
| `while true; do sleep 30; done` with a success-only `grep` | A crashed, cancelled, or never-registered run emits nothing — identical to a healthy one. Silence reads as patience. No deadline. |
| `tail -f log \| grep "BUILD OK"` | Same silence-on-failure defect, plus unflushed pipe buffers hide matches until far too late. |
| A single-condition `until` loop | Correct for "tell me when X exists"; emits nothing if X never happens, and cannot report failure. |
| Polling the branch tip instead of the pushed commit | Returns a newer run from someone else's push, or your own previous one — a false green on a commit that was never tested. |
| Re-printing the full job table each poll | Burns context until the harness rate-limits or kills the monitor, which reintroduces the stall. |
| Blocking the session while waiting | Forfeits the entire point: a failure at minute 3 of a 25-minute pipeline is learned at minute 25. |

The cost is asymmetric, which is why this matters. A failure detected early gives
back most of the pipeline's duration; the same failure detected at the deadline
gives back nothing. On a 25-minute pipeline, reacting to the *first* red lane
rather than the final verdict is roughly a 20-minute head start on the fix.

## The contract a watcher must satisfy

Any wait mechanism armed after a trigger must guarantee all of these. Each maps to
a specific observed failure when missing:

1. **Terminates on every path, with an explicit verdict.** Silence past the
   deadline must be structurally impossible — emit exactly one terminal line, then
   exit. This is the load-bearing property; the rest refine it.
2. **Pins to an immutable identifier**, captured *before* arming — a commit SHA,
   build id, or deploy id. Never a moving ref like a branch tip.
3. **Covers every run the identifier triggered**, not just one workflow by name. A
   second pipeline on the same commit can fail while the watched one passes.
4. **Emits only state changes**, plus a low-frequency heartbeat. A green 20-minute
   run should cost a handful of lines, not fifty identical tables.
5. **Has a registration deadline** distinct from the run deadline. If nothing
   appears for the identifier within a few minutes, say so — a path filter, wrong
   ref, disabled workflow, or failed push must not read as "still running."
6. **Waits for late registration before declaring success.** Runs register seconds
   apart; `workflow_run`-style chains (a deploy triggered on build completion)
   register much later. Require a settle condition before green.
7. **Detects supersession.** If the branch moves past the identifier, retire.
8. **Bounds each probe and survives transient errors.** One wedged API call must
   not freeze the loop; warn on a short streak, exit loudly on a long one.
9. **Heartbeats.** A periodic liveness tick separates "still queued" from "watcher
   died." Keep the interval under the consuming model's prompt-cache TTL (commonly
   ~5 min; ~2–3 min is a safe default) so a long wait stays cheap.

### Verdict vocabulary

A small, stable set of terminal verdicts lets the caller react without parsing
prose. Each implies a different next move — which is the whole reason to
distinguish them:

| Verdict | Meaning | Caller's next move | Exit |
|---|---|---|---|
| `success` | every run for the identifier is green | proceed | 0 |
| `failure` | a run went red | fetch that job's failing log now | 1 |
| `timeout` | not terminal within the deadline | inspect the run; stuck, not slow | 2 |
| `no-run` | nothing registered for the identifier | path filter, wrong ref, disabled workflow, failed push — all actionable, none a hang | 2 |
| `probe-dead` | repeated API/CLI failures | check auth, network, rate limits | 2 |
| `cancelled` | terminal but not green, branch unmoved | usually a manual stop or infra event — decide whether the commit was ever validated | 1 |
| `superseded` | the branch moved past the identifier | retire; arm a fresh watch on the new id | 3 |

Two rules make this vocabulary safe:

**Enumerate success, not failure.** The most dangerous watcher bug is treating
"did not fail" as green. A run that ends `cancelled`, `skipped`, `stale`, or
`neutral` is terminal but *not* validated. Match an explicit success set and treat
every other terminal conclusion — including ones never seen before — as not-green.

**Evaluate supersession before calling anything a failure.** The
`cancel-in-progress: true` concurrency pattern this skill recommends elsewhere
(see `references/github-actions.md`) cancels the previous commit's run when a fix
lands. A watcher that checks failure first reports `failure` for a run nobody
should act on, and the agent chases a phantom break. `no-run` and `superseded` are
the two verdicts hand-rolled loops almost always omit, and the two that waste the
most wall-clock.

Distinct exit codes matter for chaining: `watch && deploy` must not proceed on a
`superseded` watch that never reached a real verdict. Put the failing run's log
command *inside* the `failure` line so the caller never has to reconstruct it.

## Reference implementation shape

Provider-agnostic; swap `probe()` for the platform's CLI or API. The bundled
`scripts/ci-watch.py` implements this exactly, with a built-in GitHub Actions probe
and a custom-probe mode for everything else.

```python
def watch(sha, branch, deadline, register_by, settle, interval, heartbeat) -> int:
    start = last_beat = all_green_since = now()
    seen, errors, registered = {}, 0, False

    while True:
        if now() - start > deadline:
            emit("CI-DONE timeout"); return 2

        try:
            runs = probe(sha)                # ALL runs for this id, never "latest"
            errors = 0
        except Exception:
            errors += 1
            if errors == 3:  emit("CI-WARN probe failing (3x)")
            if errors >= 10: emit("CI-DONE probe-dead"); return 2
            sleep(interval); continue

        if runs and not registered:
            registered = True; emit(f"CI-RUN registered {len(runs)}")
        if not registered and now() - start > register_by:
            emit("CI-DONE no-run"); return 2

        for r in runs:                       # diff-gated: emit only on change
            if seen.get(r.id) != r.state:
                if r.id in seen: emit(f"CI-CHG {r.name}: {seen[r.id]} -> {r.state}")
                seen[r.id] = r.state

        if registered and runs and all(r.terminal for r in runs):
            superseded = branch and head_of(branch) != sha   # a lookup error is NOT supersession
            bad = [r for r in runs if r.conclusion not in SUCCESS_SET]
            if superseded and not any(r.conclusion in FAILURE_SET for r in runs):
                emit("CI-DONE superseded"); return 3
            if bad:
                emit(f"CI-DONE failure — {bad[0].name} — logs: <log-cmd {bad[0].id}>"); return 1
            if now() - all_green_since >= settle:            # hold for late workflow_run chains
                emit("CI-DONE success"); return 0
        else:
            all_green_since = now()

        if now() - last_beat >= heartbeat:
            last_beat = now(); emit(f"CI-HB {int((now()-start)/60)}m")   # MUST reset, or it fires every poll
        sleep(interval)
```

Three judgement calls to make explicit for the target setup:

- **`SUCCESS_SET`.** `{success, skipped, neutral}` is a reasonable default — a
  skipped job is usually an intentional route. Verify against the repo's own gating
  rules before trusting it.
- **`settle`.** How long to hold an all-green state before declaring success. One
  poll interval (~15s) covers workflows that register seconds apart;
  `workflow_run` chains register *after* their trigger completes, so give those
  60–120s or watch the downstream workflow explicitly.
- **`FAILURE_SET` vs `cancelled`.** A *completed red* run reports `failure` even if
  the branch later moved — "did this SHA pass" matters more than "did the branch
  move." A `cancelled` run on an *unmoved* branch is a distinct signal (manual
  cancel or infra), not a test failure, so it is not silently folded into success.

## Per-provider probes

Only the poll step changes. Everything above is identical.

| Provider | Poll for one commit |
|---|---|
| GitHub Actions | `gh run list --commit <sha> --json databaseId,workflowName,status,conclusion` |
| GitLab CI | pipelines API filtered by `sha` |
| Buildkite | builds API filtered by commit |
| CircleCI | pipeline → workflow status by revision |
| A deploy / anything else | any command printing `<name>: <state>` lines and a terminal marker |

A provider CLI that emits a structured event stream and a nonzero exit on failure
(NDJSON, `--json`) already satisfies most of the contract — prefer wrapping it over
hand-rolling. What such CLIs typically still lack is a self-imposed deadline, a
registration timeout, and coverage of *every* run for the commit. Wrap, do not
replace.

## Run granularity: run-level status hides an early failing job

A run-level status stays `in_progress` until *every* job finishes, and its
conclusion is unset until then. If a pipeline is one workflow with several jobs,
polling run status alone cannot tell you a lane already failed — which defeats the
"react to the first red" payoff. Either split genuinely independent lanes into
separate workflows (they then appear as separate runs for the commit), or expand
in-flight runs to job level when polling (`gh run view <id> --json jobs`). Expand
only *in-flight* runs; completed ones already carry a conclusion, so the extra call
is bounded to work that is still moving.

## Wiring it to an agent harness

Run the watcher as a background process whose **stdout lines become
notifications**, so the agent keeps working and reacts on arrival. With a streaming
background-process tool (for example Claude Code's `Monitor`):

```
Monitor(
  command: "python3 scripts/ci-watch.py --sha <full-sha> --branch <branch> --deadline-min 25",
  description: "CI for <short-sha>",
  timeout_ms: 1800000        # comfortably longer than the watcher's own deadline
)
```

Rules that matter in practice:

- **Set the harness timeout longer than the watcher's deadline**, so the watcher is
  what ends the watch and you get a verdict instead of a truncated stream.
- **Arm it last, in the same turn as the push.** Any commit after arming moves the
  branch and the watcher correctly retires as `superseded` — but you lose the
  watch. Finish committing, then arm, then keep working.
- **Never hand-type the identifier.** Use `$(git rev-parse HEAD)`; a wrong SHA
  reports `no-run` or `superseded` against the real head and teaches nothing.
- **One watch per identifier.** After a re-push, arm a fresh one.
- **A heartbeat is not a result.** Acknowledge it silently; never report it as
  progress or treat it as a user message.
- **If any stage is a shell pipeline, flush per line** — `grep --line-buffered`,
  `awk` with `fflush()`. A buffered stage silently withholds events, and `| head -N`
  cannot flush at all. In `zsh`, avoid a variable named `status`; it is a readonly
  builtin and the loop dies instantly, emitting nothing.

### When one notification is enough

For plain "tell me when it is done," a bounded background command that exits on the
condition is simpler than a streaming watcher:

```bash
until <terminal-state-check>; do sleep 20; done
```

Reach for the streaming watcher when you want to react to the *first* red lane while
others still run — the head-start described above.

## Reacting to events

| Event | Response |
|---|---|
| `CI-RUN` / `CI-CHG … registered` | Note the count. Fewer runs than expected is a routing problem — see `references/change-based-ci.md`. |
| `CI-CHG … -> failure` | Act now; pull that job's failing step log without waiting for the rest. |
| `CI-CHG in_progress -> queued` | Normal on platforms that reclaim runners mid-run. Not a fault. |
| `CI-HB` | Acknowledge silently. |
| `CI-DONE` | The only line that is a verdict. |

State is **not** monotonic on every platform. Only a terminal line means terminal.

## Reacting to a red check without corrupting the measurement

A red check is a real finding, not an obstacle to route around. Deciding *whether
it is your failure* comes before changing code:

1. Run the exact log command the verdict printed. Do not re-derive it.
2. Diff the failing commit against the last green one: `git diff --stat <green>..<red>`.
   If nothing in that diff can plausibly reach the failing test, re-run the
   **identical commit** rather than pushing a speculative fix.
3. A pass on the unchanged commit demonstrates a flaky test — a separate defect to
   own, never "fixed" by relaxing the assertion, adding a retry, mocking the failure
   away, or `skip`ping to green. Each of those corrupts the measurement instead of
   fixing the pipeline (`references/effectiveness-contract.md`). Quarantine and
   ownership belong in `references/testing-and-flakiness.md`.
4. If the failure is genuine, reproduce it with the narrowest local command. If it
   is CI-only, reproduce the *CI condition* — job-wide environment variables, a
   clean checkout, a different working directory, absent secrets — not the whole
   pipeline.
5. Verify red-first: confirm the test fails without the fix and passes with it. A
   fix never seen to fail is a fix you cannot vouch for.

A provider flake counter, where one exists, is a useful prior but not a substitute:
it typically only catches a step that succeeded on retry, so a
consistently-failing-then-passing test can read as zero flakes. The identical-commit
re-run is the reliable test.

## A collateral benefit: automatic CI surfaces hidden defects

Moving from a manual, hand-dispatched pipeline to one that runs on every push
surfaces defects the manual flow hid — environment leakage between jobs, assertions
that drifted from the contract they check, pre-existing flakes. Treat each as a real
finding and root-cause it red-first. Reaching green by weakening the check trades a
slow local loop for a silent remote one that lies.

## Verify the watcher before trusting it

A watcher never seen to fail correctly is not yet a safety mechanism. Exercise the
paths that would otherwise hang:

| Path | How to force it |
|---|---|
| `no-run` | Watch an all-zeros or unpushed SHA with a short registration deadline. |
| `failure` | Watch a known-red historical SHA. |
| `success` | Watch a known-green historical SHA. |
| `superseded` | Watch a SHA, then push one more commit to the branch. |

## Sources

- `gh run watch` TTY-gating of screen refresh and of the completion summary: `cli/cli` `pkg/cmd/run/watch/watch.go`, `pkg/iostreams/iostreams.go` (read 2026-07-28)
- `gh run watch` flags (`--exit-status`, `--interval`, `--compact`): https://cli.github.com/manual/gh_run_watch (accessed 2026-07-28)
- GitHub Actions `workflow_run` trigger semantics (late follow-up registration): https://docs.github.com/actions/reference/events-that-trigger-workflows (accessed 2026-07-28)
