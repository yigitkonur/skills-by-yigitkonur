# Agent CI Feedback Loop

Use this file when an automated agent (or any unattended process) must **wait for a CI result** without blocking a session or hanging forever. Optimizing the pipeline is worthless if the thing that consumes the result stalls for 20 minutes or, worse, reports a false verdict.

This is provider-neutral. The reference implementation below is GitHub Actions, but the contract holds for any CI that exposes run state over an API.

## The failure modes this prevents

| Symptom | Root cause |
|---|---|
| Session goes dark after a push, agent "waits" indefinitely | Blocking foreground watch with no deadline. |
| Agent reports green, the commit was actually red | Watched the branch tip, or a stale/second workflow, instead of the exact SHA. |
| A crashed run looks identical to a running one | Filter matched only success lines; failure produced no output. |
| Watcher killed for flooding, no result at all | Emitted the full job table every poll instead of state changes. |
| "Still running" forever on a run that never existed | Push matched no trigger (path filter, deleted workflow, wrong branch); nothing was ever going to appear. |
| Watch survives, but the answer is for the wrong commit | Re-push superseded the run; the old watcher kept reporting. |

## Do not use the CLI's built-in "watch" subcommand

Most CI CLIs ship a `watch` command intended for a human terminal. Under an agent harness they commonly:

- redraw with ANSI cursor control instead of emitting append-only lines,
- suppress the final summary when stdout is not a TTY,
- exit 0 on states that are not a real success.

`gh run watch` exhibits all three (see cli/cli issues #6448, #6560, #8194). Poll a JSON API and derive state yourself.

## The watcher contract

Any watcher an agent arms must satisfy all six:

1. **One line per event, append-only.** The harness turns each stdout line into a notification.
2. **Diff-gated.** Emit only *state changes*. A green 3-minute run should cost ~4 notifications, not 12 duplicate job tables. Harnesses auto-stop noisy watchers, and a stopped watcher is silence.
3. **Pinned to the exact commit, across every workflow.** Query by commit SHA, not branch. This kills false greens from a stale tip *and* catches a second workflow that fails after the first passed.
4. **Every exit path prints a terminal verdict.** `success`, `failure`, `timeout`, `no-run`, `superseded`, `probe-dead`. Silence past the deadline must be structurally impossible.
5. **A registration deadline, separate from the run deadline.** If no run appears for the SHA within a few minutes, say `no-run` and stop.
6. **Per-probe timeouts and an error-streak exit.** One wedged HTTP call must not freeze the loop; N consecutive failures is a verdict, not a retry-forever.

Add **heartbeats** (~2–3 min). They are the only thing distinguishing "slow" from "wedged", and on cache-based model APIs they keep the prompt cache warm.

## Reference implementation (GitHub Actions)

```bash
#!/usr/bin/env bash
# ci-watch.sh <sha> [deadline_min] — one line per state change, always ends in CI-DONE.
set -uo pipefail
SHA="$1"; DEADLINE=$(( ${2:-20} * 60 )); REPO="${REPO:?set REPO=org/name}"
START=$(date +%s); REGISTERED=0; declare -A SEEN; STREAK=0; BEAT=$START

while :; do
  NOW=$(date +%s); ELAPSED=$(( NOW - START ))

  if ! RAW=$(timeout 30 gh api "repos/$REPO/actions/runs?head_sha=$SHA&per_page=50" \
        --jq '.workflow_runs[] | [.name, .status, (.conclusion // ""), .id] | @tsv' 2>/dev/null); then
    STREAK=$(( STREAK + 1 ))
    [ "$STREAK" -ge 10 ] && { echo "CI-DONE probe-dead — 10 consecutive probe errors"; exit 1; }
  else
    STREAK=0
    [ -n "$RAW" ] && [ "$REGISTERED" -eq 0 ] && { REGISTERED=1; echo "CI-RUN registered"; }
    DONE=1; BAD=""
    while IFS=$'\t' read -r name status conclusion id; do
      [ -z "$name" ] && continue
      state="${conclusion:-$status}"
      [ "${SEEN[$name]:-}" != "$state" ] && { [ -n "${SEEN[$name]:-}" ] && echo "CI-CHG $name: $state"; SEEN[$name]="$state"; }
      [ "$status" != "completed" ] && DONE=0
      [ "$status" = "completed" ] && [ "$conclusion" != "success" ] && BAD="$name:$conclusion (gh run view $id --log-failed)"
    done <<< "$RAW"

    if [ "$REGISTERED" -eq 1 ] && [ "$DONE" -eq 1 ]; then
      [ -z "$BAD" ] && { echo "CI-DONE success — $SHA"; exit 0; }
      echo "CI-DONE failure — $BAD"; exit 1
    fi
    [ "$REGISTERED" -eq 0 ] && [ "$ELAPSED" -gt 240 ] && { echo "CI-DONE no-run — nothing registered for $SHA"; exit 1; }
  fi

  [ "$ELAPSED" -gt "$DEADLINE" ] && { echo "CI-DONE timeout — last state: ${SEEN[*]:-none}"; exit 1; }
  [ $(( NOW - BEAT )) -ge 150 ] && { BEAT=$NOW; echo "CI-HB $(( ELAPSED / 60 ))/$(( DEADLINE / 60 ))m"; }
  sleep 20
done
```

Arm it with the harness's streaming-watch facility (in Claude Code, the `Monitor` tool) and **keep working**:

```
Monitor(command: "REPO=org/app ./ci-watch.sh $(git rev-parse HEAD) 12",
        description: "CI for feature-branch", timeout_ms: 840000)
```

Set the harness timeout comfortably above the script's own deadline so the script — not the harness — produces the verdict.

## Choosing the right waiting primitive

| Need | Use |
|---|---|
| Many events until a known end (CI progress) | A streaming watcher like the above. |
| Exactly one notification ("tell me when it's done") | A backgrounded command that exits when true: `until <cond>; do sleep 5; done`. |
| Watch a file/log for arbitrary matches | `tail -f … \| grep --line-buffered` — but see the coverage rule below. |

**Coverage rule:** a filter that matches only the success marker is silent through a crash, a hang, and an OOM — and silence is indistinguishable from "still running". Always match every terminal state, or widen the alternation:

```bash
# wrong — silent on crash
tail -f run.log | grep --line-buffered "BUILD SUCCESS"
# right
tail -f run.log | grep -E --line-buffered "BUILD SUCCESS|FAILED|ERROR|Killed|OOM"
```

Every stage in a pipe must flush per line (`grep --line-buffered`, `awk … fflush()`); `head -N` cannot flush and will withhold output until N matches accumulate.

## Interpreting verdicts

| Verdict | Meaning | Correct reaction |
|---|---|---|
| `success` | Every workflow for that SHA passed | Proceed. |
| `failure` | At least one concluded non-success | Pull the failed log **immediately** — a failure at minute 2 of a 20-minute pipeline is an 18-minute head start. |
| `timeout` | **No verdict yet.** Not a pass, not a build failure | Inspect the run. Frequently queue starvation, not your code. Re-arm with a larger deadline. |
| `no-run` | Nothing was triggered | Check triggers/path filters/branch rules before assuming the pipeline is broken. |
| `superseded` | A newer commit landed | Retire this watch, arm one for the new SHA. |
| `probe-dead` | The API is unreachable | Infrastructure problem; escalate rather than retry blindly. |

The two that get misreported most often are **`timeout`** and **`no-run`**. Neither is a red build and neither is a green one; both mean *you still do not know*. Never let either be recorded as a pass.

## Sizing the deadline

Set it above the workflow's observed **p95**, not its median, and remember p95 includes queue time. A pipeline that executes in 40s can still sit 15 minutes in a runner shortage; a deadline tuned to execution time will fire spuriously and train the agent to ignore verdicts.

If timeouts recur while execution stays flat, the bottleneck is queue/capacity — route to `references/runners-and-autoscaling.md`, not to the build.

## Do not measure during your own burst

Arming several validation runs back-to-back inflates queue time for all of them. Wall-clock measured under self-inflicted contention is not a regression signal. Separate queue from execution before concluding anything, and take timing samples from ordinary pushes — see `references/measurement.md`.

## Sources

- GitHub Actions REST — workflow runs: https://docs.github.com/en/rest/actions/workflow-runs (accessed 2026-07-28)
- `gh run watch` non-TTY/false-green issues: cli/cli #6448, #6560, #8194 (accessed 2026-07-28)
- Contract validated end-to-end on a live GitHub Actions repository (2026-07-28): green, red, timeout (867s runner-queue starvation), no-run, and multi-workflow registration each observed and handled.
