# Feedback Loops — Observing CI Without Stalling

Use this file when an agent or human must **wait for a pipeline result**: after a
push, a re-run, a dispatch, or a deploy trigger. Optimizing a pipeline is only
half the job; if the result never arrives, or arrives wrong, the speedup is
unrealized.

This is provider-neutral. The probe changes; the contract does not.

## The failure modes

Watching CI naively fails in ways that are quiet and expensive.

| Failure | Why it happens |
|---|---|
| **Blocked session** | A foreground watch consumes the whole turn producing nothing. |
| **False green** | `gh run watch <id> --exit-status \| head` reports exit 0. `head` closes the pipe, and the pipeline's exit status is `head`'s, not the watcher's. Measured directly: a run that never started still yielded `exit 0`. |
| **Never terminates** | A check that never registers — deleted workflow, path filter, protected branch, wrong SHA — has no natural end. Naive loops wait forever. |
| **Silent on crash** | A success-only filter (`grep "succeeded"`) cannot distinguish "still running" from "crashed"; both are silence. |
| **Notification flood** | Re-printing the whole job table each poll gets the watcher rate-limited or killed. |
| **Stale green** | Watching a *branch* instead of a *SHA* accepts a green from a commit that is not yours. |
| **TTY-shaped output** | Interactive watchers emit redraw escapes off-TTY and suppress their completion summary; some refuse to run non-interactively at all. |

The `head` trap deserves emphasis: it converts a hard failure into a passing
exit code. An agent that trusts `$?` there will merge a broken build.

## The contract

Any watcher used for CI feedback must satisfy all six:

1. **SHA-pinned.** Resolve the SHA once, before arming. Never re-resolve a moving
   ref inside the probe.
2. **Terminal-guaranteed.** Every exit path prints exactly one terminal line.
   Silence past the deadline must be structurally impossible.
3. **Deadline-bounded.** A wall-clock deadline that fires even if the provider
   never answers.
4. **Registration-bounded.** If nothing registers within a few minutes, say so
   and exit — do not wait on something that will never exist.
5. **Diff-gated.** Emit only state *changes* plus a low-frequency heartbeat.
6. **Failure-inclusive.** Match every terminal state, not just success. Ask: *if
   this pipeline crashed right now, would my filter emit anything?*

### Terminal verdicts

A complete watcher distinguishes at least these. Collapsing them costs
diagnosis time:

| Verdict | Meaning | Typical response |
|---|---|---|
| `success` | All required checks green for the pinned SHA | Proceed |
| `failure` | At least one check failed | Pull that job's log; fix |
| `no-run` | Nothing registered | Expected for path-filtered/docs-only pushes; otherwise a misconfiguration |
| `superseded` | The ref moved and nothing of yours resolved | Re-arm on the new SHA, or coordinate |
| `timeout` | Deadline hit while still in flight | Read the run page; never idle |
| `probe-dead` | Repeated probe errors (auth, API 5xx) | Fix credentials/connectivity |

Distinguishing **`no-run` from `failure`** matters most in repositories with path
filters or per-package workflows, where zero runs is often the *correct* outcome.
Give the caller a way to declare that expectation.

## Arming it (agent harnesses)

With a background-event tool such as Claude Code's **Monitor**, each stdout line
becomes a notification. Pin the SHA immediately after pushing:

```bash
sha=$(git rev-parse HEAD); branch=$(git branch --show-current)
```

```
Monitor({
  command: "python3 references/scripts/ci-watch.py --sha <sha> --branch <branch> --deadline-min 20",
  description: "CI <branch>@<sha7>",
  persistent: false,
  timeout_ms: 1380000        // (deadline-min + 3) * 60000
})
```

Rules that prevent the common breakages:

- **Give the tool more time than the watcher.** Set `timeout_ms` above the
  watcher's own deadline (~3 min of headroom) so the watcher prints its own
  `timeout` verdict instead of being killed silently. A killed watcher is
  indistinguishable from a hung one.
- **Never point it at a TUI watcher or a raw log stream.** Pull failed logs once,
  on demand — do not stream them.
- **Every pipe stage must flush per line.** `grep` needs `--line-buffered`; `awk`
  needs `fflush()`. `head` cannot flush and truncates the stream.
- **One watch per pushed SHA.** A re-push supersedes the old watch; arm a new one.
- **Only need the final verdict?** Run the same command as a background task for
  a single completion notification instead of a stream.

Set the heartbeat below the model's prompt-cache TTL (~150 s for a 5-minute TTL)
so a long quiet run keeps the cache warm instead of paying a cold re-read.

## Reacting

| Event | Action |
|---|---|
| Registered | Note the count. Keep working. |
| State change → failure | **Act immediately.** Pull that job's log and start fixing; do not wait for siblings. On a 20-minute pipeline this is a ~15-minute head start. |
| Heartbeat | Liveness. Acknowledge silently. |
| Probe error | Investigate if it repeats. |
| Terminal | Respond per the table above. |

Acting on the *first* red check rather than the final verdict is the largest
practical latency win in the whole loop — it costs nothing and needs no
infrastructure.

## Verifying the watcher itself

A watcher is infrastructure; test it like infrastructure. Drive each verdict
deliberately and assert the **real** exit code:

```bash
out=$(python3 ci-watch.py --sha <sha> ...); code=$?   # NOT `| tail`, which masks it
```

| Verdict | How to force it |
|---|---|
| success | A known-green historical SHA |
| failure | A known-red historical SHA, or push a deliberate type error |
| no-run | A SHA that never existed |
| superseded | An unregistered SHA on a branch that has moved |
| timeout | A stuck SHA with a tiny deadline |

Offline probes are necessary but not sufficient — rehearse against live CI too.
A real rehearsal caught a false `superseded` that every offline test missed: the
provider's "latest run for this branch" is **not** the branch tip. When the newest
push has not registered a run yet, the previous commit's run looks like the tip,
and the newest commit gets reported as superseded by its own ancestor. Resolve
the tip from the ref itself (`git ls-remote origin refs/heads/<branch>`).

## Adapting to any provider

Keep the harness and swap the probe. A probe prints one `name: state` line per
watched unit and a terminal line when done:

```
build: running
test: running
TERMINAL: failure — test
```

That contract fits GitLab pipelines, Buildkite builds, CircleCI workflows, EAS
builds, and plain deploy APIs polled with `curl`. For **PR mergeability**
(including third-party required checks) rather than branch CI, build the probe
from the provider's checks API and treat "all non-pending" as terminal.

## Sources

- GitHub CLI non-interactive `run watch` limitations: https://github.com/cli/cli/issues/6448 (accessed 2026-07-28)
- POSIX pipeline exit status is the last command's: https://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html (accessed 2026-07-28)
