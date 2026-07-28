# Feedback Loops — Observing CI Without Stalling

Read when an agent or human must wait for a pipeline result after a push, re-run, dispatch, or deploy trigger. A fast pipeline still wastes wall-clock if the waiting strategy is wrong.

## The contract

A watcher used for CI feedback must satisfy all six:

1. **SHA-pinned** — resolve once before arming; never watch a moving ref.
2. **Terminal-guaranteed** — every exit path emits exactly one verdict.
3. **Deadline-bounded** — fire even if the provider never answers.
4. **Registration-bounded** — if nothing registers in a few minutes, say so and exit.
5. **Diff-gated** — emit state changes and a low-frequency heartbeat, nothing else.
6. **Failure-inclusive** — every terminal state is explicit. Silence is never success.

## The five verdicts

| Verdict | Meaning | Next move |
|---|---|---|
| `success` | Every run for the pinned id finished green | Proceed |
| `failure` | At least one finished non-green | Pull that job's log, fix, re-trigger |
| `no-run` | Nothing ever registered | Path filter skipped it, wrong branch, or the trigger never fired |
| `superseded` | The ref moved past the pinned id | Re-arm on the new SHA or coordinate |
| `timeout` | Still unresolved at the deadline | Open the run; never idle further |

## Why not use the obvious watch command?

Common failure modes:

| Failure | Cause |
|---|---|
| Blocked session | A foreground watch consumes the turn and produces nothing useful |
| False green | A success-only pipe or auto-select watch returns 0 before your run exists |
| Never terminates | The run never registers, or a check never reports |
| Silent on crash | A success-only filter makes crash, cancel, and hang all look identical |
| Notification flood | Printing the full job table every poll becomes spam |
| Stale green | Watching a branch instead of a SHA accepts someone else's run |

A correct watcher is a **poller that emits state transitions and always terminates**.

## Wiring to an agent / monitor

Use the mechanism that matches how many notifications are needed:

| Need | Mechanism |
|---|---|
| Progress while other work continues | A monitor / background event stream |
| Only the final verdict | A background task that exits when done |
| A blocking gate in a shell script | The same watcher script in the foreground |

Rules that keep it reliable:

- Set the outer timeout **above** the watcher's own deadline so the script reports `timeout` itself.
- One watch per pushed SHA. Re-pushing invalidates the old watch.
- Do not stream raw logs as events; fetch logs once after a failure is known.
- Treat any relayed "CI is green" as a claim, not evidence, until you verify the head SHA.

## Avrea-specific guidance

When the repository runs on Avrea and `avr` is available, use it as the evidence source:

- `avr run view <run-id>` for jobs and timings
- `avr run watch <run-id> --exit-status` when a line-oriented watch is sufficient
- `avr job metrics <job-id>` for CPU/memory/IO after the run
- `avr log search` for recurring failure signatures across runs

Check the org/repo context first (`avr auth status`, `avr config list`). A wrong org is a silent footgun.

## Implementation guidance

Prefer checking the provider for a run matching the **exact SHA** before watching anything. If a provider offers a machine-readable watch (`--ndjson`, `--json`, or similar), wrap it in your own registration window and deadline rather than delegating everything to the provider.

## Sources

- GitHub CLI `run watch`: https://cli.github.com/manual/gh_run_watch (accessed 2026-07-28)
- GitHub CLI issue on incomplete PR checks: https://github.com/cli/cli/issues/6448 (accessed 2026-07-28)
- Avrea CLI reference (`run`, `job`, `log`): https://docs.avrea.com/cli/reference/ (accessed 2026-07-28)
