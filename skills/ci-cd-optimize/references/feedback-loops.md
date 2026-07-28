# Feedback Loops — Observing CI Without Stalling

Use this file when an agent or human must **wait for a pipeline result**: after a
push, re-run, dispatch, or deploy trigger. Optimizing a pipeline is half the job;
if the result never arrives, or arrives wrong, the speedup is unrealized.

Provider-neutral. The probe changes; the contract does not.

## Failure modes

| Failure | Cause |
|---|---|
| **Blocked session** | A foreground watch consumes the turn producing nothing. |
| **False green** | `gh run watch <id> --exit-status \| head` exits 0 — a pipeline's status is the *last* command's, not the watcher's. Measured: a run that never started still yielded exit 0. |
| **Never terminates** | A check that never registers (deleted workflow, path filter, wrong SHA) has no natural end. |
| **Silent on crash** | A success-only filter cannot tell "still running" from "crashed"; both are silence. |
| **Notification flood** | Re-printing the job table each poll gets the watcher rate-limited or killed. |
| **Stale green** | Watching a *branch* rather than a *SHA* accepts a green from someone else's commit. |
| **TTY-shaped output** | Interactive watchers emit redraw escapes off-TTY, suppress their completion summary, or refuse to run non-interactively. |

The `head` trap matters most: it converts a hard failure into a passing exit
code. An agent trusting `$?` there merges a broken build.

## The contract

A watcher used for CI feedback must satisfy all six:

1. **SHA-pinned** — resolve once before arming; never re-resolve a moving ref inside the probe.
2. **Terminal-guaranteed** — every exit path prints exactly one terminal line; silence past the deadline is structurally impossible.
3. **Deadline-bounded** — fires even if the provider never answers.
4. **Registration-bounded** — if nothing registers in a few minutes, say so and exit.
5. **Diff-gated** — emit state *changes* plus a low-frequency heartbeat, nothing else.
6. **Failure-inclusive** — match every terminal state. Ask: *if this crashed now, would my filter emit anything?*

### Terminal verdicts

| Verdict | Meaning | Response |
|---|---|---|
| `success` | All required checks green for the pinned SHA | Proceed |
| `failure` | A check failed | Pull that job's log; fix |
| `no-run` | Nothing registered | Expected for path-filtered pushes; otherwise a misconfiguration |
| `superseded` | Ref moved, nothing of yours resolved | Re-arm on the new SHA, or coordinate |
| `timeout` | Deadline hit in flight | Read the run page; never idle |
| `probe-dead` | Repeated probe errors | Fix auth/connectivity |

Separating **`no-run` from `failure`** matters in any repo with path filters,
where zero runs is often correct. Give the caller a way to declare that
expectation (`--expect-none` in the bundled script).

## Arming it

With a background-event tool such as Claude Code's **Monitor**, each stdout line
becomes a notification. Pin the SHA immediately after pushing:

```bash
sha=$(git rev-parse HEAD); branch=$(git branch --show-current)
```

```
Monitor({
  command: "python3 <skill-dir>/references/scripts/ci-watch.py --sha <sha> --branch <branch> --deadline-min 20",
  description: "CI <branch>@<sha7>",
  persistent: false,
  timeout_ms: 1380000        // (deadline-min + 3) * 60000
})
```

Use an absolute path or one anchored to the skill directory — the watcher runs
from the session's cwd, which may be a different worktree or repo. In the
built-in mode pass `--repo owner/name` for the same reason.

Rules that prevent the common breakages:

- **Give the tool more time than the watcher** (~3 min headroom) so it prints its own `timeout` verdict instead of being killed silently. A killed watcher looks identical to a hung one.
- **Keep the heartbeat under the model's prompt-cache TTL** (~150 s for a 5-minute TTL) so a quiet run keeps the cache warm.
- **Never point it at a TUI watcher or a raw log stream.** Pull failed logs once, on demand.
- **Every pipe stage must flush per line** — `grep` needs `--line-buffered`, `awk` needs `fflush()`, `head` cannot flush at all.
- **One watch per pushed SHA.** A re-push supersedes the old one; arm a new one.
- **Only need the final verdict?** Run the same command as a background task for a single completion notification.

## Reacting

Act on the **first** red check rather than the final verdict — on a 20-minute
pipeline that is a ~15-minute head start, and it costs nothing. Acknowledge
heartbeats silently; investigate probe errors only if they repeat.

## Verifying the watcher

A watcher is infrastructure; test it like infrastructure. Drive each verdict and
assert the **real** exit code — capture output first, since `| tail` masks it:

```bash
out=$(python3 ci-watch.py --sha <sha> ...); code=$?
```

Force verdicts with: a known-green SHA, a known-red SHA, a SHA that never
existed, an unregistered SHA on a moved branch, and a stuck SHA with a tiny
deadline.

Offline probes are necessary but insufficient — rehearse against live CI. A real
rehearsal caught a false `superseded` that every offline test missed: the
provider's "latest run for this branch" is **not** the branch tip. When the newest
push has not registered yet, the previous commit's run looks like the tip and the
newest commit is reported as superseded by its own ancestor. Resolve the tip from
the ref (`git ls-remote origin refs/heads/<branch>`).

## Any provider

Keep the harness, swap the probe. A probe prints one `name: state` line per unit
and a terminal line when done:

```
build: running
test: running
TERMINAL: failure — test
```

That fits GitLab pipelines, Buildkite builds, CircleCI workflows, EAS builds, and
deploy APIs polled with `curl`. For **PR mergeability** (including third-party
required checks) rather than branch CI, build the probe from the provider's
checks API and treat "all non-pending" as terminal.

`references/scripts/ci-watch.py` implements this contract in both modes.

## Sources

- GitHub CLI non-interactive `run watch` limitations: https://github.com/cli/cli/issues/6448 (accessed 2026-07-28)
- POSIX: a pipeline's exit status is the last command's: https://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html (accessed 2026-07-28)
