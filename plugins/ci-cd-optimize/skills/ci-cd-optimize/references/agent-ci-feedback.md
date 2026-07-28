# Agent CI Feedback Loops

Optimizing a pipeline is half the job. The other half is receiving its result: an agent that pushes and then blocks, hangs, or claims a green it never verified has un-realized every second you saved. This file is that half.

Provider-neutral. Any CLI or API that can list runs for a commit works — `gh` (GitHub Actions), `avr` (Avrea), `glab` (GitLab), `buildkite-agent`, `curl` against a deploy API. The bundled watcher `scripts/ci-watch.py` implements everything below in two modes; read on to know *why* each rule exists before you trust it.

## Why the obvious approaches fail

Each row below is a distinct, silent failure. "Silent" is the theme: from the outside a hung watch and a slow build look identical.

| Approach | Failure mode |
|---|---|
| `gh run watch` / `avr run watch` in the foreground | **No deadline.** On an *already-finished* run it exits cleanly, so it passes a quick test. On a live run, a stalled API, or a check that never registers, it blocks until something external intervenes. Many also redraw a TTY block off-terminal and suppress their completion summary when stdout is not a TTY, so the finish event never arrives. |
| `until <status> \| grep -q success; do sleep N; done` | **Silent on red.** A failed run and a running run both produce no match, so the loop never exits and never prints. Prove it in one line: `echo failure \| grep -q success && echo exits \|\| echo "runs forever"`. |
| The id-less auto-select watch (`gh run watch` / `avr run watch` with no id, right after a push) | **Registration race → false green.** The run is not indexed yet, so the tool reports "no in-progress runs" and exits **0**. The agent reads success and proceeds unverified. Reproduced on `avr` 0.1.6, 2026-07-28. |
| `<watcher> \| head` and then trusting `$?` | **False green via pipeline status.** A pipeline's exit code is the *last* command's — `head`'s — not the watcher's. A hard failure becomes a passing exit. Capture output first, then read the real code. |
| Re-emitting the run table every poll | **Volume kill.** Three polls of a one-workflow run produce three identical lines; a 15-minute run at 20 s polling emits ~45. Event-stream tools rate-limit or auto-stop noisy producers, so the agent loses the feedback entirely — including the failure. |
| Watching a **branch** instead of a **SHA** | **Stale green.** A branch-tip query returns whatever ran most recently, which may be someone else's newer push or a run from before your change. |

Do not re-litigate these; reproduce them if you doubt them. The commands to force each are in "Verifying the watcher" below.

## The contract a watcher must satisfy

A watcher is trustworthy only if **all** of these hold. Missing one reintroduces a silent hang or a false verdict.

1. **Pinned to an immutable identifier.** A commit SHA, build id, or deployment id, captured *before* arming. Never a moving ref. SHA pinning also catches a *second* workflow that fails after the first passed — a branch-latest watch misses it.
2. **Terminal on every path.** `success`, `failure`, `no-run`, `superseded`, `timeout`, `probe-dead`, `interrupted`. Silence past the deadline must be structurally impossible, not merely unlikely.
3. **A registration deadline, separate from the run deadline.** If no run appears for the identifier within a few minutes, emit `no-run` and stop. Never wait on a run that will never exist.
4. **Diff-gated output.** Emit only on state *change*, plus a low-frequency heartbeat. This is what keeps a long green run to a handful of events instead of dozens of duplicates.
5. **Per-probe timeout + error-streak exit.** Cap each probe call so one wedged request cannot freeze the loop; retry transient errors; warn after ~3 consecutive failures; exit `probe-dead` after ~10 rather than spinning.
6. **A liveness heartbeat.** A compact tick every few minutes distinguishes "still building" from "wedged". Keep the interval under the consuming model's prompt-cache TTL (≈150 s for a 5-minute TTL) so a long queue does not force a cold context re-read.

## Terminal verdicts

Enumerate all seven; a missing one is a hang or a misleading diagnosis waiting to happen. `no-run` and `superseded` are the two most often omitted and the two that most often masquerade as "CI is just slow".

| Verdict | Meaning | The reader's next move |
|---|---|---|
| `success` | Every unit for the pinned id finished green | Proceed — and claim only *this* id |
| `failure` | At least one finished non-green | Pull the named log immediately, fix, re-trigger, arm a **fresh** watch |
| `no-run` | Nothing ever registered | Expected for a path-filtered push; otherwise a misconfiguration (wrong branch, disabled workflow, trigger never fired) |
| `superseded` | The ref moved past the pinned id | Yours if you re-pushed; otherwise coordinate with whoever moved it |
| `timeout` | Still unresolved at the deadline | Open the run; it may be stuck or queued behind capacity. Never idle further |
| `probe-dead` | The CLI/API failed repeatedly | Fix auth/connectivity; do **not** claim a result |
| `interrupted` | An operator cancelled the watcher | Treat as unverified; re-arm if a verdict is still needed |

Treat `cancelled` carefully. A run cancelled because a **newer push superseded it** is not a failure. When every non-green conclusion is merely `cancelled` **and** the branch tip has moved, report `superseded` and let the caller re-arm. Reporting that as `failure` sends the agent debugging a phantom break that looks exactly like a real red.

## Event vocabulary

A compact, greppable prefix per line keeps the agent's parsing trivial. Pick one scheme and keep it stable.

```
CI-RUN   3 registered: build:queued · lint:queued · test:queued
CI-CHG   test: in_progress
CI-CHG   test: completed -> failure
CI-HB    6/30m build:success · lint:success · test:in_progress
CI-DONE  failure — test — logs: <exact command to view them>
```

Put the **log-fetch command inside the failure line**. The agent should never have to reconstruct it.

Reaction policy:

| Event | Action |
|---|---|
| `CI-RUN` | none — registration confirmed |
| `CI-CHG … -> failure` | **act now.** Pull the log, start the fix. On a 20-minute pipeline, acting at minute 4 instead of at `CI-DONE` is a ~15-minute head start, and it costs nothing. |
| `CI-CHG` (not red) | none |
| `CI-HB` | acknowledge silently; never narrate a heartbeat to the user |
| `CI-DONE success` | proceed |
| `CI-DONE no-run` | verification did **not** happen — investigate unless a path filter makes zero runs expected |
| `CI-DONE timeout`/`probe-dead`/`superseded`/`interrupted` | the watcher gave up safely — re-check manually, never assume fine |

## Arming it through a background/event tool

Attach the watcher to a background facility rather than the foreground so the session keeps working. In Claude Code this is the **Monitor** tool: each stdout line becomes a notification, and process exit ends the watch.

```
Monitor(
  command: "python3 <skill-dir>/scripts/ci-watch.py --sha <sha> --branch <branch> --deadline-min 20",
  description: "CI for <branch>@<sha8>",
  timeout_ms: 1380000     # (deadline-min + 3) × 60000 — ABOVE the script's own deadline
)
```

Rules that matter more than they look:

- **Give the tool more time than the watcher** (~3 min headroom) so the *script* prints its verdict rather than being killed silently. A killed watcher looks identical to a hung one — the failure you are trying to prevent.
- **Use an absolute or skill-anchored path.** The watcher runs from the session's cwd, which may be a different worktree or repo. In built-in mode pass `--repo owner/name` for the same reason.
- **Choose the tool by notification count.** One notification ("tell me when it's done") is better served by a *backgrounded command that exits on the condition*; per-transition progress needs the streaming tool. Never point an unbounded renderer (`tail -f`, `while true`) at a stream tool — it stays armed long after the event and dies on timeout instead of completing.
- **Every pipe stage must flush per line.** `grep --line-buffered`, `awk '{...; fflush()}'`; `head -N` cannot flush and withholds output until N matches accumulate.
- **One watch per pushed identifier.** A re-push supersedes the old run; the watcher checks the branch tip on every probe and exits `superseded` even if the old SHA still has active runs. Arm a new watcher rather than reasoning about two overlapping streams.
- **Settle before green.** GitHub built-in mode rechecks a fully green run set for 60 seconds by default so a chained deploy or release workflow can register before `success`. Tune `--settle-sec` to the pipeline's registration lag; do not set it to zero unless the workflow set is provably closed.
- **Do not also poll from the main loop while a monitor is armed.** Duplicated polling wastes budget and yields contradictory readings.

## The bundled watcher

`scripts/ci-watch.py` (Python 3 stdlib only) implements the full contract in two modes:

- **Built-in (GitHub Actions):** `ci-watch.py --sha <sha> --branch <branch> [--repo owner/name]`. Queries by SHA, so one watch survives "push, then open a PR".
- **Generic (any provider):** `ci-watch.py --cmd '<probe>'`. The probe prints one `name: state` line per unit and a `TERMINAL: <verdict>` line when done. This fits GitLab pipelines, Buildkite builds, CircleCI workflows, Jenkins, EAS builds, and deploy APIs polled with `curl`.

Commit a watcher to the repository rather than expecting an agent to retype a poll loop each time — hand-rolled loops are exactly where the failure modes above reappear. Document the one-line invocation in `AGENTS.md`/`CONTRIBUTING.md` next to the push instruction, with the expected duration so an agent can tell "slow" from "stuck".

If a platform ships a machine-readable stream with an exit code (`--ndjson`, `--json`, `--exit-status`), prefer it *inside* the streaming phase — but keep your own registration window, deadline, and SHA pinning around it. Native watches fix output shape; they generally do not fix registration, deadline, or pinning.

### Adapting the probe

Keep the loop, replace the query:

| Platform | Probe | Terminal test |
|---|---|---|
| GitHub Actions | `gh run list --commit <sha> --json status,conclusion` | all `completed`; any non-`{success,skipped,neutral}` ⇒ failure |
| GitHub PR gate | `gh pr checks <pr> --json name,bucket` | any `bucket=="fail"` ⇒ failure; no `pending` ⇒ terminal |
| GitLab CI | pipelines API `status` (`glab ci status --live` is TTY-shaped — avoid) | `success` / `failed` / `canceled` |
| Buildkite | `buildkite-agent` or the REST build endpoint | `state` in `passed`/`failed`/`canceled` |
| Avrea | `avr run watch <run-id> --ndjson --exit-status` already emits line-per-event JSON with a non-zero exit — wrap it only to add a registration wait and deadline | exit code |
| Anything else | any command printing `<name>: <state>` per unit | your own `TERMINAL:` line |

**PR mergeability is a different question from branch CI.** Required checks include third-party services you do not control, so a branch can be green while the PR is not mergeable. Watch whichever one actually gates you.

## Verifying the watcher itself

A watcher is verification infrastructure — test its failure paths before trusting it, the same standard applied to any other gate. A watcher observed only succeeding is untested. Drive each verdict and assert the **real** exit code (capture output first, since `| tail` masks it):

```bash
out=$(python3 scripts/ci-watch.py --sha <sha> ...); code=$?
```

| Scenario | How to force it | Expected |
|---|---|---|
| Green lifecycle | an ordinary passing push | `RUN` → `CHG` → `DONE success`, few events total |
| **Real failure** | push a deliberate type error, revert immediately | `CHG` red mid-run, `DONE failure` + a working log command, non-zero exit |
| Nothing registers | a bogus or path-filtered SHA | `DONE no-run` before the deadline, not a hang |
| Deadline | a tiny `--deadline-min` against a live run | `DONE timeout`, never silence |
| Superseded (if your pipeline cancels stale runs) | push twice quickly | `DONE superseded`, **not** failure |
| Long queue | watch during contention | periodic `CI-HB` carrying state |

Offline probes are necessary but insufficient — rehearse against live CI. A real rehearsal caught a false `superseded` that every offline test missed: some providers' "latest run for this branch" is **not** the branch tip. When the newest push has not registered yet, the previous commit's run looks like the tip and the newest commit is reported as superseded by its own ancestor. Resolve the tip from the ref (`git ls-remote origin refs/heads/<branch>`), which is what the bundled script does.

## Distinguishing "slow" from "stuck"

A long wait is not automatically a defect. Before treating a slow run as a problem, split the wall clock — a watcher that heartbeats elapsed time lets an agent do this without polling:

- **Queue time** (created → started) is provider capacity, not your workflow. Measured on one repository it ranged 10 s–193 s within a single hour on identical config, while execution held at 11–13 s. Nothing in the YAML changes that.
- **Execution time** (started → completed) is yours to optimize.

Report the two separately. Presenting a queue-dominated wall clock as a regression sends the next optimization round after the wrong target. See `references/measurement.md` for the decomposition and `references/runners-and-autoscaling.md` for when queue share means the whole topology question is moot.

## Local-vs-CI division of labor

When CI is fast and the workstation is contended (parallel worktrees, limited RAM), push work to CI and keep local checks to what is instant:

- Local: formatting, a whitespace/EOL guard (`git diff --check`), lint on changed files, a targeted unit test.
- CI: full typecheck, full suite, builds, container images, integration environments.

Document the split so agents do not "pre-check" locally by running the whole suite — that reintroduces the exact contention CI was meant to remove. A cheap local guard for whatever the repo's CI checks *first* (often whitespace or formatting) prevents the most common self-inflicted red.

## Narrow feedback lanes

A full gate is the wrong tool when only one signal is needed. Expose a dispatchable workflow with a mode input (`typecheck`, `build`, `lint`, `test`, `affected`) so an agent gets a targeted answer in well under a minute. Guard the lane so it cannot lie:

- Refuse to dispatch unless the remote branch SHA equals local HEAD.
- Correlate the resulting run by **head SHA plus a dispatch timestamp window**, not by run title. A `run-name:` template does not always populate the API's display-title field, so title matching silently attaches to the wrong run.
- Print failed-step logs automatically on failure.

## Common mistakes

| Mistake | Fix |
|---|---|
| Foreground `watch` in an agent turn | Arm a background watcher; keep working. |
| Success-only filter | Emit on every terminal state, including crash and cancel. |
| `<watcher> \| head` then trusting `$?` | Capture output first; a pipeline's status is `head`'s. |
| Keying state by workflow name | Key by run id; one commit can have several runs of one workflow, and name-keying makes them flap forever. |
| Reporting a concurrency-cancelled run as failure | Check whether the branch tip moved first → `superseded`. |
| Harness timeout below the script deadline | Set it above so the script yields the verdict. |
| Watcher with no registration deadline | A never-registered run hangs the loop forever. |
| Registration deadline ≥ overall deadline | `no-run` becomes unreachable; every skipped pipeline reports `timeout`. |
| Time-windowed query missing an older SHA | Widen the lookback window when re-checking an older commit. |
| Success concluded from an empty run list | `all([])` is true; require a non-empty list before concluding. |
| Assuming a green first stage ends the chain | Chained deploy/release runs register later; re-check or settle-watch. |
| Reporting "still running" after a probe failure | `probe-dead` is unknown, not fine — say so. |

## Sources

- Failure taxonomy and the diff-gated / guaranteed-exit design follow `yigitkonur/plugin-ci-watch-unstall` (README, accessed 2026-07-28), which documents the same `gh run watch` non-TTY and no-deadline problems.
- `gh run watch` / `gh pr checks` non-interactive limitations: https://github.com/cli/cli/issues/6448 and https://github.com/cli/cli/issues/6560 (accessed 2026-07-28).
- POSIX pipeline exit status is the last command's: https://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html (accessed 2026-07-28).
- The id-less watch exiting 0 with "No in-progress workflow runs found", the branch-tip vs latest-run distinction, and the queue-vs-execution spread were observed directly against a live GitHub Actions repository on Avrea runners and `avr` 0.1.6 (2026-07-28); the bundled `scripts/ci-watch.py` was exercised across every verdict path there.
