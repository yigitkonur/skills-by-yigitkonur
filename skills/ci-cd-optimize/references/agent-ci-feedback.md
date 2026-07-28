# Agent CI Feedback Loop

Read this when an agent or unattended process must wait for a CI result without blocking, when a watcher hangs or floods, or when CI is the only verification surface (no trusted local build/test path). In a CI-only repo this loop *is* the development loop — optimizing it is mandatory work, not polish.

A bundled reference implementation lives at `scripts/ci-watch.py` (stdlib-only Python, GitHub mode + generic probe mode). Every design rule below is enforced in that script; validate it against real runs before trusting it (see the validation matrix).

## Fast triage

| Symptom | Likely cause | Read |
|---|---|---|
| Watch returns instantly, reports nothing running | Registration race — the run hasn't been indexed yet | Failure modes, rule 5 |
| Session goes dark after a push | Foreground watch with no deadline | The contract |
| Green reported, commit was actually red | Branch-tip query, single-workflow watch, or stale SHA | Contract rules 3–4 |
| Crashed run indistinguishable from a running one | Success-only filter | Failure modes |
| Watcher killed for flooding, verdict lost | Emitting full state every poll instead of changes | Contract rule 6 |
| "Still running" forever on a run that never existed | No registration deadline (path filter, deleted workflow) | Verdicts: `no-run` |
| Superseded push debugged as a real failure | Cancellation folded into failure | Ordering law |
| Success declared, deploy then failed | `workflow_run` follow-up registered late | Settle window |

## Failure modes worth naming

**Provider `watch` subcommands are TTY-shaped.** `gh run watch` and its cousins redraw a status block, suppress the completion summary when stdout is not a terminal, and can exit 0 on states that are not a real pass (cli/cli #6448, #6560, #8194). Piped into a line consumer, every redraw becomes an event and the watch gets rate-limited away. Test before trusting any of them: `timeout 25 <watch-cmd> | cat -A | head -20` — repeated blocks or cursor-movement escapes mean it is a renderer, not an event stream.

**Success-only filters are silent on red.** `until <status> | grep -q success; do sleep 30; done` never exits on a failed run — failure produces no match, so the loop looks identical to "still running." One line proves it: `echo failure | grep -q success || echo "no output — loop runs forever"`.

**The `| head` pipe trap.** A shell pipeline's exit status is the *last* command's. `watch-cmd --exit-status | head` reports 0 even when the run failed — a run that never started still "passed." Check `${PIPESTATUS[0]}` (bash) or run unpiped before trusting `$?`.

**Enumerate success, not failure.** The most dangerous watcher bug is treating "did not fail" as green. Match an explicit success set (`success`, plus deliberate neutrals like `skipped`) and treat every other terminal conclusion — including ones never seen before — as not-green.

## The contract

A watcher is trustworthy only if all seven hold:

1. **Every exit path prints a terminal verdict.** Silence past the deadline must be structurally impossible — including when the watcher itself crashes (wrap the whole loop; a traceback with no verdict strands the caller).
2. **Reports failure at least as loudly as success**, with the exact log-retrieval command in the verdict line so the caller acts without re-deriving anything.
3. **Pinned to an immutable identifier captured before arming** — a full commit SHA, build id, or deployment id. Never a branch tip: a branch-tip query returns a newer run and reports a green for code you did not push. (Short SHAs can silently match zero runs — guard the length.)
4. **Covers every unit the identifier triggered**, not just the named workflow. A second workflow can fail after the first passes; after a fast-forward, one commit can carry both a branch run and a default-branch run — the second is usually the one that deploys.
5. **A registration deadline separate from the run deadline**, clamped below half the overall deadline. If nothing registers in a few minutes, exit `no-run` — otherwise a skipped pipeline misreports as `timeout`, a strictly less useful verdict. In path-filtered repos zero runs is often *correct*; give callers an explicit expect-none mode rather than making them ignore `no-run`.
6. **Diff-gated, with heartbeats.** Emit only state transitions — a green 20-minute run should cost a handful of notifications, not 60 duplicate tables (harnesses auto-stop flooding watchers, and a stopped watcher is silence). Heartbeat every ~2.5 minutes so "waiting" is distinguishable from "wedged"; where the consuming model has a prompt-cache TTL, keep the heartbeat under it so a long queue does not force a cold context re-read.
7. **Per-probe timeouts and streak-bounded errors.** Cap each probe call so one wedged request cannot freeze the loop; retry transient errors quietly, warn once after ~3 consecutive, exit `probe-dead` after ~10.

Two state-keying rules from bugs found only under live testing: key state by **run id**, not workflow name (one commit can run the same workflow twice; keyed by name the states overwrite each other and the watcher flaps forever), and compute the verdict from the **newest run per workflow** so a concurrency-cancelled older sibling does not turn a green commit red.

## Ordering law: supersession before failure

Under `cancel-in-progress` concurrency, pushing a fix cancels the previous commit's run. A watcher that checks failure first reports `failure` for a run nobody should act on — and the agent goes off debugging a phantom break that looks exactly like a real red. Evaluate in this order:

1. Real failure conclusions → `failure`.
2. All conclusions in `{success, skipped, neutral, cancelled}` **and** a newer identifier exists → `superseded`.
3. Cancelled with the branch *unmoved* → `cancelled` (manual cancel or infrastructure — a distinct signal, still not a test failure).

Resolve the branch tip with `git ls-remote origin refs/heads/<branch>`, not "latest run for the branch": the newest push may not have registered a run yet, and the previous commit's run masquerades as the tip — misreporting the new commit as superseded by its own ancestor.

## Settle window

When one workflow triggers another on completion (`workflow_run`: deploy-after-build), the follow-up does not exist at the moment the first turns green. Exiting on first-green reports a success that structurally cannot include the deploy. Hold an all-green state for a short settle window (~90s) and re-probe before declaring `success`.

## Verdicts and the agent's next move

| Verdict | Meaning | Next move |
|---|---|---|
| `success` | Explicit success/neutral set across every unit, settled | Proceed; confirm the run's head SHA equals what was pushed |
| `failure` | ≥1 unit concluded non-success | Run the printed log command **immediately** — a failure at minute 6 of a 25-minute pipeline is a ~19-minute head start |
| `cancelled` | Cancelled, branch unmoved | Investigate who/what cancelled; not red, not green |
| `superseded` | Newer identifier landed | Retire this watch; arm a fresh one for the new identifier |
| `no-run` | Nothing registered in time | Check triggers/path filters/branch rules; expected under path filters — never silently treat as green |
| `timeout` | Deadline hit, no verdict | **Not a pass and not a build failure** — frequently queue starvation. Inspect the run, then re-arm with a larger deadline |
| `probe-dead` | API unreachable or watcher crashed | Infrastructure problem; escalate rather than blind-retry |

The two most misreported are `timeout` and `no-run`; both mean *you still do not know*. A verdict is evidence only for the identifier it names — a green on a stale or empty diff proves nothing (`effectiveness-contract.md`).

Distinct exit codes matter because callers chain on them: `watch && deploy` must not proceed on `superseded` or `timeout`. The bundled script uses 0 for success, 124 for timeout (the GNU `timeout` convention), 1 otherwise.

Watch run-level status for cost, but expand in-flight runs to **job level** when early reaction matters: run status stays `in_progress` until every job finishes, so an already-failed lane is invisible at run granularity.

## Provider probes

The contract is provider-neutral; only the probe changes. The generic mode of `scripts/ci-watch.py` accepts any command that prints `<name>: <state>` lines and one `TERMINAL: <verdict>` line when finished — the watcher never guesses a verdict for a custom probe.

| Provider | Probe | Notes |
|---|---|---|
| GitHub Actions | `gh run list --commit <sha> --json …` | All workflows for the exact commit. `gh run list` collapses re-run attempts — check the attempt counter before treating a rerun as a new sample |
| GitHub PR gate | `gh pr checks` | Mergeability ≠ branch CI: required checks include third-party services; a branch can be green while the PR is not mergeable. Watch whichever one actually gates you (also cli/cli #6448: expected-but-unreported checks) |
| GitLab CI | `glab pipeline list --sha …` / pipelines API | Poll pipeline + bridges for the SHA |
| CircleCI | pipelines-for-commit API → workflows per pipeline | Two-level: pipeline → workflows |
| Buildkite | builds API filtered by commit | One build may fan out to triggered builds |
| Anything else | your status command as a `--cmd` probe | Deploy APIs, EAS, self-hosted — anything that can print `name: state` |

## Choosing the waiting primitive

| Need | Use |
|---|---|
| Progress events until a known end | Streaming watcher (this contract) on the harness's event-stream facility |
| Exactly one notification ("tell me when done") | Backgrounded command that exits on the condition: `until <cond>; do sleep 5; done` — with a deadline |
| A blocking gate inside a script | The same watcher, foreground, branching on its exit code |

The watcher is identical in all three; only the invocation differs. Never arm an unbounded `while true` for a single answer, and never point a TTY renderer at an event-stream tool.

Arming rules that generalize to any harness facility:

- Every pipe stage must flush per line (`grep --line-buffered`, `awk '{...; fflush()}'`); `head -N` cannot flush and withholds output until N matches accumulate.
- If the process crashed right now, would the filter emit anything? If not, it is a success-only filter in disguise — widen it to every terminal state.
- Set the facility's own timeout **above** the watcher's deadline (~3 min headroom) so the watcher prints its verdict instead of being killed mid-sentence. A killed watcher looks identical to a hung one.
- One watch per pinned identifier; re-pushing supersedes — arm a fresh watch.
- Shell traps: in zsh, `status` is a readonly builtin (`status=$(…)` is fatal and the watcher emits nothing at all); command substitution strips trailing newlines, so diff-gate on parsed fields, not raw blobs; pass configuration as explicit arguments rather than inheriting ambient environment.

## Validate the watcher before trusting it

A watcher only ever observed succeeding is untested. Produce each path deliberately:

| Scenario | How | Expected |
|---|---|---|
| Green lifecycle | ordinary passing push | `RUN` → `CHG` → `DONE success`, few notifications |
| **Real failure** | push a deliberate compile/type error, revert after | red `CHG` mid-run, `DONE failure` + working log command, non-zero exit |
| Nothing registers | bogus or path-filtered SHA | `DONE no-run` well before the deadline |
| Deadline | near-zero deadline against a live run | `DONE timeout`, exit 124, never silence |
| Superseded | two pushes in quick succession | `DONE superseded`, **not** failure |
| Long queue | watch during runner contention | periodic heartbeats carrying state |
| Probe garbage | probe emitting invalid bytes | degraded probe error, not a crash |

Confirm the printed remediation command actually surfaces the error, and that the exit code survives your invocation (`${PIPESTATUS[0]}`, unpiped run).

## Reacting to a red check

1. Run the exact log command the verdict printed — do not re-derive it.
2. Reproduce with the narrowest command available; if it only fails in CI, reproduce the CI-specific condition (env, OS, service) rather than guessing.
3. Fix the root cause. Never reach green by adding a retry, widening a threshold, mocking away the failure, or skipping the check — that corrupts the measurement instead of fixing the pipeline (`effectiveness-contract.md`).
4. For a suspected flake: re-run the *identical* commit first. A pass on the unchanged tree is evidence of flake (route to `testing-and-flakiness.md`); a second failure is a real break. Provider flake counters undercount — they typically only catch a step that succeeded elsewhere.
5. Push the fix and arm a fresh watch for the new SHA.

Heartbeats are acknowledged silently — never restated as progress, never treated as a reply from anyone.

## Shrinking the loop itself

- **Narrow dispatchable lanes**: a `workflow_dispatch` input selecting typecheck-only / lint-only / test-only / affected-only lets an agent ask one question in seconds instead of re-running the whole gate. Guard dispatch by refusing unless the remote ref's SHA equals local HEAD, and correlate the resulting run by head SHA + dispatch time window — display-title matching silently attaches to the wrong run.
- **Deadline sizing**: set the watch deadline above the workflow's observed p95 *including queue* (`measurement.md`); a 40s pipeline can sit 15 minutes in a runner shortage, and a deadline tuned to execution time trains the caller to ignore verdicts. Recurring timeouts with flat execution are a capacity story — `capacity-and-contention.md`.
- **Deploy self-verification**: when the pipeline ends in a deploy, the revision-convergence assertion has its own sizing trap — `deployment.md`.
- Commit the watcher script to the repo and document the exact arming invocation next to the push instructions in the contributor/agent docs, so every agent can tell "slow" from "stuck" without reinventing the loop.

## Sources

- GitHub Actions REST — workflow runs: https://docs.github.com/en/rest/actions/workflow-runs (accessed 2026-07-28)
- `gh run watch` / checks limitations: cli/cli #6448 (open as of 2026-07-28), #6560 (closed; historical context for owning your own deadline), #8194 (accessed 2026-07-28)
- POSIX shell pipeline exit status (the `| head` trap): https://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html#tag_18_09_02 (accessed 2026-07-28)
- Design lineage: yigitkonur/plugin-ci-watch-unstall (diff-gating, SHA pinning, guaranteed terminal verdict)
- Contract validated end-to-end on live GitHub Actions runs (2026-07-28): green, red, timeout under 867s queue starvation, no-run, superseded, multi-workflow registration, and crash-to-verdict each observed.
