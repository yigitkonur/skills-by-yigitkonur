# Agent Feedback Loop — receiving CI results without stalling

Read this when an autonomous agent (or any non-interactive automation) has to wait for a
pipeline it just triggered. This is a *reliability* problem, not a speed problem: a session
blocked on a run that never terminates costs more wall-clock than any optimization returns.

The failure is silent. The agent pushes, waits, and produces nothing — no output, no
deadline, no verdict. From outside it is indistinguishable from a slow build.

## Rule

**Never block the session on CI.** Arm an out-of-band watcher that emits events and always
terminates. In Claude Code that is the **Monitor** tool; elsewhere it is a background
process whose stdout the agent can read.

## Three approaches that fail, and why

Verified empirically against a real GitHub Actions repository (2026-07-28). Do not
re-litigate these — reproduce them if you doubt them.

| Approach | Observed failure |
|---|---|
| `gh run watch <id> --exit-status` (or any provider's blocking watch) | **No deadline.** On an *already-completed* run it exits cleanly, so it looks fine in testing. On a live run, a stalled API, or a check that never registers, it blocks forever. Also exits non-zero on a bad run id, which a naive wrapper treats as failure. |
| `until [ pending -eq 0 ]; do sleep N; done` | **False green.** A commit with *zero* runs also has zero *pending* runs, so the loop exits "success" immediately. This is not exotic: any `paths-ignore`/`paths` filter, a deleted workflow, or branch protection produces it. Measured: a docs-only commit returned `[]` from the API and the loop reported done. |
| Re-emitting the run table every poll | **Volume kill.** Three polls of a one-workflow run produced three identical lines; a 15-minute run at 20 s polling emits ~45. Event-stream tools rate-limit or auto-stop noisy producers, so the agent loses the feedback entirely — including the failure. |

## Required properties of a watcher

Any watcher you write or adopt must have all six. Missing one reintroduces the hang.

1. **Guaranteed terminal event.** Every code path — success, failure, timeout, no-run,
   probe-dead — ends with one parseable line. If the agent can reach a state with no
   output, the design is wrong.
2. **Registration deadline.** Allow N minutes (4 is a reasonable default) for every run
   on the pinned commit to register before emitting a terminal verdict. If none appears,
   emit `no-run` and exit; if an early run finishes, keep watching for late registrations.
3. **Commit pinning, not branch.** Query by the exact SHA. A branch-tip query returns a
   *newer* run and reports a false green for code you did not push. Pinning also catches a
   second failing workflow hiding behind a passing one.
4. **Diff-gating.** Emit only on state *change*. This is what keeps a long run to a handful
   of events instead of dozens of duplicates.
5. **Liveness heartbeat.** A compact tick every ~2.5 minutes proves the watcher is alive
   and distinguishes "still building" from "wedged". On LLM agents this also lands inside
   a typical 5-minute prompt-cache TTL, so the conversation stays warm.
6. **Bounded error handling.** Per-probe timeout so one wedged request cannot freeze the
   loop; retry transient errors; warn after a few consecutive failures; exit loudly after
   ~10 rather than spinning.

## Event contract

Emit a small, greppable vocabulary. The agent reacts to the prefix, not to prose.

```
CI-RUN   3 registered: build:queued · lint:queued · test:queued
CI-CHG   test: in_progress -> completed/failure
CI-HB    12/30m build:in_progress
CI-DONE  failure test — <command to fetch the failing log>
```

Reaction policy the agent should follow:

| Event | Action |
|---|---|
| `CI-RUN` | none — registration confirmed |
| `CI-CHG` | none unless it went red |
| `CI-HB` | acknowledge silently; never narrate a heartbeat to the user |
| `CI-DONE success` | proceed |
| `CI-DONE failure` | fetch the failing log immediately, fix, re-push, arm a **fresh** watcher |
| `CI-DONE no-run` | expected for filtered paths; otherwise investigate why nothing registered |
| `CI-DONE timeout`/`probe-dead` | the watcher gave up safely — re-check manually |

Put the log-fetch command *inside* the failure line. The agent should not have to
reconstruct it.

## Wiring it to the Monitor tool

```
Monitor(
  command: "<repo>/scripts/ci-watch.sh $(git rev-parse HEAD) 25",
  description: "CI for <sha8>",
  timeout_ms: 1800000
)
```

Set `timeout_ms` above the watcher's own deadline so the watcher — which produces a proper
verdict — wins the race against the harness timeout, which produces none.

Two rules that matter more than they look:

- **One watch per pushed SHA.** After a fix-and-re-push, arm a new watcher. The old one is
  watching the old commit and its verdict is meaningless for the new one.
- **A heartbeat is not a reply.** Events arrive asynchronously, including while the agent
  is waiting on the user. Do not treat an event as user input.

## Provider-native shortcuts

Some platforms ship a watch that already has a deadline and a machine-readable exit. Prefer
it when it exists, but verify the anti-stall properties above before trusting it:

- Avrea: `avr run watch --exit-status` / `avr workflow run ... --watch --exit-status`
  (see `avrea/cli-evidence.md`).
- Anything else: wrap the provider CLI in the loop described here.

For a non-GitHub provider, keep the same contract and swap only the probe: the script needs
one command that prints `<name>: <state>` lines and a terminal verdict.

## When *not* to use a watcher

If the pipeline finishes in well under a minute and the agent has nothing else to do,
polling twice inline is simpler and cheaper. The watcher earns its complexity when runs are
long, when several workflows fire per commit, or when the agent should keep working while
CI runs.

## Sources

- Anti-stall mechanism set adapted from `yigitkonur/plugin-ci-watch-unstall` (accessed
  2026-07-28), which documents the hook/skill/harness split and the diff-gating,
  registration, and heartbeat behaviors.
- Failure modes in the table above were reproduced directly against GitHub Actions on
  2026-07-28; the short-SHA and zero-run cases were found that way, not from documentation.
