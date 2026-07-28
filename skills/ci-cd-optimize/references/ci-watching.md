# Watching CI Without Stalling

Use this file when an agent or script must wait for a pipeline result — after a push, a dispatch,
or a deploy — and the wait must be bounded, observable, and impossible to hang.

This is a correctness problem, not a convenience one. A session blocked on CI with no deadline is
indistinguishable from a session that has crashed.

## What actually goes wrong

| Anti-pattern | Failure |
|---|---|
| A TTY-oriented watcher with no machine-readable stream | Off-TTY, `gh run watch` appends the whole run table every interval (its `RefreshScreen`/alternate-buffer paths are TTY-gated) and its final `✓ Run … completed` summary is suppressed entirely. You get unparseable repetition and no completion line. |
| Any watcher without its own deadline | A run that never registers, or a hung job, waits forever. `--exit-status` gives a pass/fail code but no time bound. |
| `while true; do sleep 30; done` | No deadline, no registration timeout, usually no failure path. |
| Filtering only for success | A crashed, cancelled, or never-registered run looks identical to a running one: silence. |
| Watching one workflow by name | A second pipeline on the same commit can fail while the watched one passes — a false green. |
| Echoing the full job table each poll | Burns context; most harnesses rate-limit or kill noisy monitors. |
| Blocking the session while waiting | Forfeits the point: you learn about a minute-3 failure at minute 25. |

A provider CLI that emits a structured event stream and a nonzero exit on failure (for example
`avr run watch --ndjson`, or any `--json`/NDJSON mode) already satisfies most of the contract
below — prefer it over hand-rolling. What such CLIs typically still lack is a self-imposed
deadline, registration timeout, and coverage of *every* run for the commit. Wrap rather than
replace.

## The contract

1. **Always terminates with an explicit verdict.** Silence past the deadline must be structurally
   impossible: emit exactly one terminal line, then exit.
2. **Pins to a commit, not a workflow.** Watch every run for the SHA so a second pipeline failing
   is visible.
3. **Emits only state changes.** Diff-gate output; a green 20-minute run should produce a handful
   of lines.
4. **Has a registration deadline.** If nothing appears for the SHA within a few minutes, say so —
   a path filter, wrong ref, or failed push must not read as "still running."
5. **Waits for late registration before declaring success.** Runs can register seconds apart, and
   `workflow_run`-style pipelines register much later. Require a settle condition.
6. **Detects supersession.** If the branch moves past the watched SHA, retire.
7. **Survives transient errors.** Per-probe timeout, quiet retry, warn on a short streak, exit on
   a long one.
8. **Heartbeats.** A periodic liveness tick separates "still working" from "wedged."

### Verdict vocabulary

| Verdict | Meaning | Caller's move | Suggested exit |
|---|---|---|---|
| `success` | every run for the SHA is green | proceed | 0 |
| `failure` | a run went red | fetch that job's failing logs now | 1 |
| `timeout` | not terminal within the deadline | inspect; stuck, not slow | 2 |
| `no-run` | nothing registered for the SHA | wrong ref, path filter, failed push | 2 |
| `probe-dead` | repeated API/CLI failures | check auth, network, rate limits | 2 |
| `superseded` | branch moved past the SHA | re-arm on the new SHA | 3 |

Distinct exit codes matter: `watch && deploy` must not proceed on a `superseded` watch that never
reached a real verdict. Put the failing run's log command inside the `failure` line so the caller
never has to work out how to see the cause.

## Reference implementation shape

Provider-agnostic; swap `probe()` for your platform's CLI or API.

```python
def watch(repo, sha, branch, deadline, register_by, settle_secs, interval, heartbeat) -> int:
    start = last_beat = all_done_since = monotonic()
    seen, errors, registered = {}, 0, False

    while True:
        elapsed = monotonic() - start
        if elapsed > deadline:
            emit("CI-DONE timeout"); return 2

        try:
            runs = list(probe(repo, sha))    # ALL runs for this commit; safely reusable
            errors = 0
        except Exception:
            errors += 1
            if errors == WARN_AFTER: emit(f"CI-WARN probe failing ({errors}x)")
            if errors >= DIE_AFTER:  emit("CI-DONE probe-dead"); return 2
            sleep(interval); continue

        if runs and not registered:
            registered = True
            emit(f"CI-RUN registered {len(runs)}: ...")
        if not registered and elapsed > register_by:
            emit("CI-DONE no-run"); return 2

        for r in runs:                       # diff-gated; announce new runs too
            if r.id not in seen:
                if registered: emit(f"CI-CHG {r.name}: registered ({r.state})")
            elif seen[r.id] != r.state:
                emit(f"CI-CHG {r.name}: {seen[r.id]} -> {r.state}")
            seen[r.id] = r.state

        if registered and runs and all(r.done for r in runs):
            bad = [r for r in runs if r.conclusion not in OK]
            genuine_failures = [r for r in bad if r.conclusion != "cancelled"]
            try:
                superseded = branch and head_of(branch) != sha
            except Exception:
                superseded = False         # a lookup failure is not supersession
            if superseded and not genuine_failures:
                emit("CI-DONE superseded"); return 3
            if bad:
                emit(f"CI-DONE failure — {bad[0].name} — logs: <log-cmd {bad[0].id}>")
                return 1
            # Hold all-green for a settle window so late-registering workflows
            # (e.g. workflow_run chains) are observed before declaring success.
            if monotonic() - all_done_since >= settle_secs:
                emit("CI-DONE success"); return 0
        else:
            all_done_since = monotonic()

        now = monotonic()
        if now - last_beat >= heartbeat:
            last_beat = now                  # must reset, or it fires every poll
            emit(f"CI-HB {int((now - start) / 60)}m")

        sleep(interval)
```

Three judgement calls to make explicit for your setup:

- **`OK` set.** `{success, skipped, neutral}` is a reasonable default — a skipped job is usually an
  intentional route. Verify against your own gating rules.
- **`settle_secs`.** How long to hold an all-green state before declaring success, to catch
  late-registering workflows. A single poll interval (~15s) covers pipelines that register seconds
  apart; `workflow_run` chains register *after* their trigger completes, so give those 60–120s or
  watch the downstream workflow explicitly.
- **`cancelled` and supersession.** Check supersession only when a run was cancelled or nothing
  failed; a completed red run must report `failure` even if the branch moved, because the question
  "did this SHA pass" matters more than "did the branch move." A `cancelled` run on an *unmoved*
  branch is a distinct signal — manual cancel or infrastructure — not a test failure, so it is not
  silently treated as `OK`.
  Check supersession *before* concluding failure (as above) so a correctly retired run is not
  reported red.

## Wiring it to an agent harness

Run the watcher as a background process whose **stdout lines become notifications**, so the agent
keeps working and reacts on arrival. If your harness exposes a streaming background-process tool
(for example Claude Code's `Monitor`), wire it like this:

```
Monitor(
  command: "python3 <your-watcher>.py --repo <owner/repo> --sha <full-sha> \
            --branch <branch> --deadline-min 25 --register-min 4",
  description: "CI for <short-sha>",
  timeout_ms: 1800000        # comfortably longer than --deadline-min
)
```

Rules that matter in practice:

- **Set the harness timeout longer than the watcher's own deadline**, so the watcher is what ends
  the watch and you get a verdict instead of a truncated stream.
- **Arm it last.** Any commit after arming moves the branch and the watcher retires as
  `superseded` — correct, but you lose the watch. Finish committing, then arm.
- **Never hand-type the SHA.** Use `$(git rev-parse HEAD)`; a wrong SHA reports `superseded` or
  `no-run` against the real head and teaches you nothing.
- **One watch per SHA.** After a re-push, arm a fresh one.
- **If any stage is a shell pipeline, flush per line** — `grep --line-buffered`, `awk` +
  `fflush()`. A buffered stage silently withholds events, and `| head -N` cannot flush at all.
  (In `zsh`, also avoid a variable named `status`; it is readonly and the loop dies instantly.)

### When one notification is enough

For "tell me when it is done", a bounded background command that exits on the condition is
simpler than a streaming watcher:

```bash
until <terminal-state-check>; do sleep 20; done
```

Use the streaming watcher when you want to react to the *first* red check while other jobs still
run — on a 25-minute pipeline that is roughly a 20-minute head start.

## Reacting to events

| Event | Response |
|---|---|
| `CI-RUN` / `CI-CHG … registered` | Note the count. Fewer runs than expected means a routing problem. |
| `CI-CHG … -> failure` | Act now; pull that job's failing step logs without waiting for the rest. |
| `CI-CHG in_progress -> queued` | Normal on platforms that reclaim runners. Not a fault. |
| `CI-HB` | Acknowledge silently. |
| `CI-DONE` | The only line that is a verdict. |

State is **not** monotonic on every platform. Only a terminal line means terminal.

## Verify the watcher before trusting it

Exercise the paths that would otherwise hang:

| Path | How to force it |
|---|---|
| `no-run` | Watch an all-zeros or unpushed SHA with a short `--register-min`. |
| `failure` | Watch a known-red historical SHA. |
| `success` | Watch a known-green historical SHA. |
| `superseded` | Watch a SHA, then push one more commit to the branch. |

A watcher you have not seen fail correctly is not yet a safety mechanism.

## Sources

- `gh run watch` TTY gating of screen refresh and of the completion summary: `cli/cli`
  `pkg/cmd/run/watch/watch.go`, `pkg/iostreams/iostreams.go` (read 2026-07-28)
- `gh run watch` flags (`--exit-status`, `--interval`, `--compact`):
  https://cli.github.com/manual/gh_run_watch (accessed 2026-07-28)
- Implementation example of the same contract (not a source for the claims above):
  https://github.com/yigitkonur/plugin-ci-watch-unstall (accessed 2026-07-28)
