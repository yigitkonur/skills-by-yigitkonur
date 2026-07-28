# Agent feedback loop — non-blocking CI watching

Read when an autonomous agent (or any long-running session) must learn a CI verdict without blocking, when a watcher hangs or floods, or when CI is the only place verification runs.

The problem this solves: an agent pushes, then stops. It either blocks in the foreground or improvises a polling loop. Both waste the entire pipeline duration, and the improvised loop is usually silent on exactly the outcome that matters. When CI is the only verification surface — no local test runs, several parallel worktrees — this loop *is* the development loop.

## The contract a watcher must satisfy

A watcher is trustworthy only if all of these hold:

1. **Terminates on every path.** Success, failure, timeout, nothing-registered, probe-dead, superseded. Silence past the deadline must be structurally impossible.
2. **Reports failure at least as loudly as success.** A success-only filter is the single most common defect.
3. **Pinned to an immutable identifier** — a commit SHA, build id, or deployment id captured *before* arming. Never a moving ref like a branch tip.
4. **Covers every unit** that can fail for that identifier, not just the first one found.
5. **Emits on change, not on poll.** One notification per state transition; a quiet watcher means "still running," not "stuck."
6. **Bounded.** A deadline shorter than the session, with the deadline reported as its own verdict.

If a proposed watcher fails any of these, it will eventually strand the agent.

## Two patterns that fail — verify before adopting either

**Provider "watch" subcommands are often TTY-shaped.** Many CLIs (`gh run watch` is the common case) redraw a status block on an interval rather than emitting lines. Piped into a line-oriented consumer, every redraw becomes an event; a 20-minute run produces hundreds of duplicate notifications and the watch is rate-limited away. Several also follow a single run, so a second failing workflow for the same commit is never seen.

Check before trusting one:

```bash
timeout 25 <provider-watch-cmd> | cat -A | head -20
```

Repeated identical blocks, or ANSI cursor-movement escapes, mean it is a rendering loop and unsuitable. Some CLIs also suppress their completion summary when stdout is not a terminal, so the finish event never arrives at all.

**Success-only polling is silent on red.** This shape appears constantly:

```bash
until <status-cmd> | grep -q success; do sleep 30; done   # DO NOT USE
```

A failed run and a running run both produce no match, so the loop never exits and never prints. Demonstrate it in one line:

```bash
echo failure | grep -q success && echo exits || echo "no output — loop runs forever"
```

The same defect appears as `--exit-status` flags that return early, and as filters listing only the success marker.

## The shape that works

Poll a pinned identifier on an interval, diff the state against the previous poll, emit only transitions, and guarantee a terminal line.

```
EVENT            MEANING                                   AGENT ACTION
RUN  <n units>   units registered for this identifier      none — keep working
CHG  <unit>      a unit changed state                      act on the first failure
HB   <m/deadline> liveness tick, carries state when stalled acknowledge silently
DONE <verdict>   terminal: success|failure|timeout|no-run|  decide and stop watching
                 superseded|cancelled|probe-dead
```

Rules that make it reliable:

- **Registration deadline.** If nothing registers within a few minutes, exit `DONE no-run` rather than watching a run that will never exist. Causes: path filters excluded the diff, the workflow is disabled, the identifier is wrong, or the push did not land.
- **Heartbeat interval.** Emit liveness on a quiet interval so the caller can distinguish "waiting" from "wedged." Where the consuming model has a prompt-cache TTL, keep the heartbeat comfortably under it so a long queue does not force a cold re-read of context.
- **Per-probe timeout.** Cap each probe call so one wedged request cannot freeze the loop.
- **Error streaks, not error exits.** Transient API failures are normal; retry quietly, warn once after a few consecutive failures, exit `DONE probe-dead` after ~10.
- **Distinguish cancellation from failure.** A superseding push commonly makes a concurrency group auto-cancel the older run. `cancelled` is *not* red. The robust rule: if the only non-green conclusions are `cancelled`, the verdict is `cancelled`/`superseded`, never `failure` — regardless of whether you can prove a newer identifier exists. Report `superseded` when you can confirm the ref moved, `cancelled` otherwise, and reserve `failure` for a genuine non-success/non-cancelled conclusion. Reporting a cancellation as failure sends the agent debugging a phantom break, because it looks exactly like a real red. (A first implementation of the bundled watcher got this wrong by requiring a branch argument to reach the supersession branch; without it, every auto-cancel read as failure.)
- **Aggregate across all runs for the identifier.** After a fast-forward, one commit can carry both a branch run and a default-branch run. A SHA-pinned watch spans both, which is usually correct — the default-branch run is the one that deploys.

## Arming it

Attach the watcher to a background/event-streaming facility rather than the foreground. In Claude Code this is the `Monitor` tool, whose contract is: each stdout line becomes a notification, and process exit ends the watch.

```
Monitor(
  command: "bash scripts/ci-watch.sh <pinned-sha> <branch> 15",
  description: "CI for <branch> <short-sha>",
  timeout_ms: 900000
)
```

Guidance that generalizes to any such facility:

- **Match the tool to the notification count.** One notification ("tell me when it finishes") is better served by a backgrounded command that exits on the condition. Per-transition streaming needs the event-stream tool. Never point an unbounded renderer at a stream tool.
- **Every pipe stage must flush per line.** `grep --line-buffered`, `awk { fflush() }`. `head -N` cannot flush and will withhold output until N matches accumulate.
- **Widen the filter to every terminal state.** If the process crashed right now, would the filter emit anything? If not, it is a success-only filter wearing a disguise.
- **Set the tool timeout above the watcher's own deadline** so the watcher reports its verdict rather than being killed mid-sentence.
- **One watch per pinned identifier.** Re-pushing supersedes; arm a fresh watch rather than reusing the old one.

## Validating a watcher before trusting it

Prove each exit path against real runs. A watcher that has only been observed succeeding is untested.

| Scenario | How to produce it | Expected |
|---|---|---|
| Green lifecycle | ordinary passing push | `RUN` → `CHG` → `DONE success`, few notifications total |
| **Real failure** | push a deliberate compile/type error, then revert | `CHG` red mid-run, `DONE failure` + the log command, non-zero exit |
| Nothing registers | watch a bogus or path-filtered SHA | `DONE no-run` before the deadline |
| Deadline | set the deadline to ~0 against a live run | `DONE timeout`, never silence |
| Superseded | push twice quickly | `DONE superseded`, **not** failure |
| Cancelled without a known newer ref | cancel a run manually, or watch an auto-cancelled SHA without the branch arg | `DONE cancelled`, **not** failure |
| Long queue | watch during contention | periodic `HB` carrying state |

The failure test is the one that matters; run it deliberately rather than waiting for a real break. Confirm the remediation command the watcher prints actually surfaces the error, and confirm the exit code is non-zero (beware `| head` masking it — check `${PIPESTATUS[0]}` or run unpiped).

## Reacting to events

- `RUN` / `HB` — acknowledge silently and keep working. Never restate a heartbeat as progress.
- First `CHG` to a failed state — act immediately. Pull the failed logs, start fixing. On a long pipeline this is the whole benefit: a failure surfaced at minute 3 of a 25-minute run is a ~20-minute head start.
- `DONE failure` — read the logs before changing anything; the verdict names the unit, not the cause.
- `DONE no-run` — decide whether that is expected (docs-only change under a path filter) or a broken trigger. Do not treat it as green by default.
- `DONE timeout` — inspect the run and act; never re-arm blindly into another deadline.

A verdict is evidence only for the identifier it names. Confirm the run's head SHA equals what you pushed, and that your change is in that run's diff, before calling it verified. See `effectiveness-contract.md` for why a green on a stale or empty diff is not proof.

## When CI is the only verification surface

## Choosing the right waiting primitive

| Need | Use |
|---|---|
| Many state changes until a known end (CI progress) | A diff-gated streaming watcher like this one. |
| Exactly one notification ("tell me when it finishes") | A backgrounded command that exits when the condition becomes true. |
| Arbitrary matches in a growing file/log | `tail -f ... | grep --line-buffered`, but only when the filter covers every terminal state. |

**Coverage rule:** a filter that matches only the success marker is silent through a crash, a hang, and an OOM — and silence is indistinguishable from "still running." Always match every terminal state, or widen the alternation. Also ensure every stage in a pipe flushes per line; `head -N` cannot flush and withholds output until N matches accumulate.

## Size the deadline to queue + convergence, not to the happy-path runtime

Two false-red deadline patterns recur:

1. **Queue delay dominates execution.** A job that executes in 20s can still wait minutes for capacity. Deadline to observed p95 wall-clock, not median execution time.
2. **The deploy call returns before the environment converges.** CDN/edge/multi-region platforms frequently serve the previous revision for tens of seconds after the deploy API returned success. A deploy watcher budgeted to the upload/build step rather than to revision convergence reports a false failure and trains the agent to ignore the signal.

A `timeout` verdict is not a red build and not a pass. It means you still do not know. Inspect the run, separate queue from execution, then re-arm with a larger deadline if the workflow is still the right one to watch. If timeouts recur while execution stays flat, the bottleneck is queue capacity, not your watcher — route to `references/capacity-and-contention.md`.


Teams that push heavy work off the developer machine — several agents, several worktrees, limited local RAM — depend on this loop entirely. Additions that pay for themselves:

- **A dispatchable targeted workflow** (typecheck-only, build-only, affected-only) so an agent can ask one narrow question instead of running the whole gate.
- **A separate non-gating suite** for checks that should be visible but must not block shipping. Prefer a separate workflow over a broad `continue-on-error`, which reports green while hiding a real failure.
- **Documented event semantics** in the repository's agent instructions, so every agent reacts the same way rather than improvising.
- **A guard test pinning the watcher's invariants** — that each terminal verdict string exists and the identifier is pinned — so the property is enforced rather than assumed.
