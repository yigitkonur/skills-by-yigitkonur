# Watching Runs Without Blocking

Read when an agent or script needs the *result* of a pipeline it just triggered: after a push, a
re-run, a dispatch, or a deploy. This is the feedback half of optimization — a 60-second pipeline
still costs ten minutes of wall-clock if the way you wait for it is wrong.

The optimization rules elsewhere in this skill make CI fast. This file makes the *answer* arrive.

## The failure mode

The obvious commands are the wrong ones:

```bash
gh run watch <id>            # no deadline; hangs forever on a check that never resolves
gh pr checks <pr> --watch    # same, plus it waits on third-party checks you do not control
until <done>; do sleep 5; done   # blocks the session; no output until it ends
```

They share three defects:

1. **No deadline.** A queued-forever run, a stuck required check, or a check that is never reported
   at all blocks until something external intervenes. `gh pr checks` has a known gap where expected
   checks are not listed (cli/cli #6448, open as of 2026-07-28) — you cannot wait reliably on a set
   the tool does not fully enumerate.
2. **TTY-shaped output.** They redraw a progress view. Piped into any notification mechanism, each
   redraw becomes an event, so the signal drowns in its own frames.
3. **Foreground occupancy.** While blocking, the agent does nothing else and — in agent harnesses
   with a prompt cache — pays a cache miss when it finally resumes.

Streaming raw logs is the same mistake at higher volume. Logs are pulled *once, on demand, after* a
failure is known — never streamed as a watch.

## The watcher contract

A correct watcher is a **poller that emits state transitions and always terminates**. Five
properties, all load-bearing:

| Property | Why |
|---|---|
| **Pin the identifier before watching** | Resolve the SHA/build id at trigger time. A watcher that re-resolves `HEAD` silently retargets when a teammate or parallel agent pushes. |
| **Diff-gate the output** | Emit only when observed state *changes*. Re-emitting "still running" every poll is noise that trains the reader to ignore it. |
| **Guarantee exactly one terminal line** | Every exit path prints a verdict. Silence past the deadline must be structurally impossible, not merely unlikely. |
| **Cover every terminal state** | `success` is one of five. A watcher that only greps for the happy path is indistinguishable from a hung one when the build breaks. |
| **Carry the next action** | On failure, print the exact log command. The reader should not have to reconstruct it. |

### The five verdicts

Enumerate them explicitly; a missing one is a hang waiting to happen.

| Verdict | Meaning | Reader's next move |
|---|---|---|
| `success` | Every run for the pinned id finished green | Proceed; claim only this SHA |
| `failure` | At least one finished non-green | Pull the named log, fix, re-trigger, arm a **new** watch |
| `no-run` | Nothing ever registered | Path filter skipped it, wrong branch, or the trigger never fired — all actionable, none a hang |
| `superseded` | The ref moved past the pinned id | Yours if you re-pushed; otherwise coordinate with whoever moved it |
| `timeout` | Still unresolved at the deadline | Open the run; never idle further |

`no-run` and `superseded` are the two most often omitted, and the two that most often masquerade as
"CI is just slow."

## Reference implementation

Provider-agnostic in shape; the probe is the only part that changes. This one targets GitHub
Actions and needs `gh` + `jq`.

```bash
#!/usr/bin/env bash
# watch-ci.sh <pinned-sha> [branch] [deadline-min]
set -uo pipefail
SHA="${1:?need a pinned sha}"; BRANCH="${2:-}"; DEADLINE_MIN="${3:-20}"

INTERVAL="${CI_WATCH_INTERVAL:-15}"
HEARTBEAT="${CI_WATCH_HEARTBEAT:-150}"
GRACE="${CI_WATCH_REGISTER_GRACE:-240}"       # no-run cutoff
max=$(( DEADLINE_MIN * 60 / 2 ))              # keep no-run reachable before timeout
[ "$GRACE" -gt "$max" ] && GRACE=$max

short="${SHA:0:8}"; deadline=$(( SECONDS + DEADLINE_MIN * 60 ))
last=""; last_runs_error=""; last_branch_error=""; beat=$SECONDS; seen=false

while :; do
  if ! runs=$(gh run list --commit "$SHA" --limit 20 \
          --json databaseId,workflowName,status,conclusion 2>&1); then
    error="runs: ${runs//$'\n'/ }"
    [ "$error" != "$last_runs_error" ] && { echo "CI-ERR $short $error"; last_runs_error="$error"; beat=$SECONDS; }
  else
    last_runs_error=""
    if [ -z "$runs" ] || [ "$runs" = "[]" ]; then
      if [ "$seen" = false ] && [ $SECONDS -gt $GRACE ]; then
        echo "CI-DONE no-run — nothing triggered for $short"; exit 0
      fi
    else
      seen=true
      state=$(jq -r 'sort_by(.workflowName)[] | "\(.workflowName)=\(.status)\(if .conclusion != "" then "/"+.conclusion else "" end)"' <<<"$runs" | paste -sd' ' -)
      [ "$state" != "$last" ] && { echo "CI-CHG $short $state"; last="$state"; beat=$SECONDS; }

      if jq -e 'length > 0 and all(.status == "completed")' <<<"$runs" >/dev/null 2>&1; then
        bad=$(jq -r '[.[] | select(.conclusion | IN("success","skipped","neutral") | not) | .workflowName] | join(", ")' <<<"$runs")
        if [ -z "$bad" ]; then echo "CI-DONE success — $short"; exit 0; fi
        id=$(jq -r '[.[] | select(.conclusion=="failure")][0].databaseId // empty' <<<"$runs")
        echo "CI-DONE failure — $short — $bad${id:+ — gh run view $id --log-failed}"; exit 1
      fi
    fi
  fi

  if [ -n "$BRANCH" ] && [ "$seen" = false ]; then
    if ! head=$(gh run list --branch "$BRANCH" --limit 1 --json headSha --jq '.[0].headSha // empty' 2>&1); then
      error="branch: ${head//$'\n'/ }"
      [ "$error" != "$last_branch_error" ] && { echo "CI-ERR $short $error"; last_branch_error="$error"; beat=$SECONDS; }
    else
      last_branch_error=""
      [ -n "$head" ] && [ "$head" != "$SHA" ] && { echo "CI-DONE superseded — $short → ${head:0:8}"; exit 0; }
    fi
  fi

  [ $SECONDS -ge $deadline ] && { echo "CI-DONE timeout — $short still ${last:-unregistered}"; exit 1; }
  [ $HEARTBEAT -gt 0 ] && [ $(( SECONDS - beat )) -ge $HEARTBEAT ] && { echo "CI-HB $short $(( SECONDS/60 ))m/${DEADLINE_MIN}m"; beat=$SECONDS; }
  sleep "$INTERVAL"
done
```

Two details worth keeping when you adapt it:

- **The grace clamp.** If the no-run cutoff exceeds the deadline, `no-run` becomes unreachable and
  every skipped pipeline reports as `timeout` — a strictly less useful verdict.
- **An already-finished id terminates on the first poll**, in well under a second. Watching a
  completed SHA should never cost a full interval.

## Arming it from an agent harness

In Claude Code the Monitor tool turns each stdout line into a notification while the agent keeps
working:

```
Monitor({
  command: "cd <repo> && bash scripts/ci/watch-ci.sh <sha> <branch> 15",
  description: "CI <branch>@<sha7>",
  persistent: false,
  timeout_ms: 1080000        // (deadline-min + 3) * 60000
})
```

`timeout_ms` **must exceed the script's own deadline** by a few minutes. Inverted, the harness kills
the watcher before it can print its verdict — reintroducing the silence the design exists to
prevent.

Choose the mechanism by how many notifications you want:

| Need | Mechanism |
|---|---|
| Progress while you work | Monitor (one event per state change) |
| Only the final verdict | Background task running the same script — one completion notification |
| A blocking gate in a script | Run it in the foreground and check the exit code |

The script is identical in all three; only the invocation differs. That is the point of putting the
logic in a script rather than in tool arguments.

### One watch per trigger

Re-pushing invalidates the previous watch. Arm a new one on the new id; do not reuse the old.
A watch is scoped to an immutable identifier, and the SHA changed.

## Adapting the probe

Keep the loop, replace the query:

| Platform | Probe | Terminal test |
|---|---|---|
| GitHub Actions | `gh run list --commit <sha> --json status,conclusion` | all `completed`; non-green ⇒ failure |
| GitHub PR gate | `gh pr checks <pr> --json name,bucket` | any `bucket=="fail"` ⇒ failure; no `pending` ⇒ terminal |
| GitLab CI | `glab ci status --live` is TTY-shaped — use the pipelines API and read `status` | `success` / `failed` / `canceled` |
| Buildkite | `buildkite-agent` or the REST build endpoint | `state` in `passed`/`failed`/`canceled` |
| Avrea | `avr run watch <run-id> --ndjson --exit-status` already emits line-per-event JSON with a non-zero exit on failure — wrap it only to add a deadline | exit code |
| Anything else | Any command printing `<name>: <state>` per unit | your own `TERMINAL:` line |

When a provider ships a machine-readable stream with an exit code, prefer it over re-implementing
polling — but confirm it has a deadline. Most do not, and that is the property you cannot skip.

**PR mergeability is a different question from branch CI.** Required checks include third-party
services you do not control; a branch can be green while the PR is not mergeable. Watch whichever
one actually gates you.

## Anti-patterns

| Anti-pattern | Why it fails |
|---|---|
| Watching `HEAD` instead of a pinned SHA | Silently retargets when anyone pushes |
| Emitting every poll | Noise; the reader stops reading |
| Grepping only for success | Crash, cancel, and hang all look identical to silence |
| Streaming job logs as events | Enormous volume; the interesting lines are only interesting after a verdict |
| `timeout_ms` ≤ the script's deadline | Harness kills the watcher before it can report |
| Reusing a watch after re-pushing | Reports on a SHA nobody cares about |
| Treating a relayed "it's green" as proof | A claim, not evidence — verify the run's head SHA yourself |

## Sources

- `gh pr checks` omits expected checks: https://github.com/cli/cli/issues/6448 (open, accessed 2026-07-28)
- `gh run watch` timeout behavior: https://github.com/cli/cli/issues/6560 (closed, accessed 2026-07-28) — historical context for why an external deadline is worth owning rather than delegating
- `gh run watch` / `gh pr checks` reference: https://cli.github.com/manual/gh_run_watch (accessed 2026-07-28)
- The reference implementation above was executed against a live GitHub Actions repository on Avrea runners (2026-07-28): a completed SHA terminated in 0.68s, an unknown SHA produced `no-run` in 7s, and a deliberately broken build produced `failure` with exit code 1 and a log command that resolved to the exact failing assertion.
