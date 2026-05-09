# Monitor contract

The Claude Code Monitor tool is the skill's observability surface. Each fleet has one Monitor (not one per worker). Each Monitor command tails a single source of truth — typically a runner log — and emits one line per state transition. The agent receives each line as a notification injected into the conversation.

## Contents

- Anatomy of a Monitor invocation
- Load-bearing rules
- Per-mode Monitor commands
- Filter coverage
- Test contract

## Anatomy of a Monitor invocation

```
Monitor({
  description: "<mode> fleet (run_id=<run-id>)",
  command: "ORCHESTRATE_MANIFEST=<manifest-path> bash <skill-root>/scripts/codex-monitor.sh",
  persistent: true,
  timeout_ms: 300000
})
```

- `description` is shown in every notification. Make it specific so the user can disambiguate when multiple Monitors are armed.
- `command` runs continuously until killed. Stdout lines become notifications. Stderr is logged but does not notify.
- `persistent: true` means the Monitor lives until the session ends or `TaskStop` is called. `timeout_ms` is required by the schema but ignored when `persistent: true` — pass `300000` as convention.
- `persistent: false` for run-single mode (bounded duration), with `timeout_ms` set to the expected wall-clock cap.

## The two load-bearing rules

### 1. Arm Monitor BEFORE the runner

The dispatcher emits the Monitor hint in its JSON envelope and exits. The agent surfaces the hint immediately, then the runner is already detached and pumping events. This sequence — envelope → arm Monitor → runner already producing events — guarantees the Monitor sees the first-wave START events.

`tail -F` on a log file misses content written before the tail attaches. When the Monitor command is `tail -F <log>`, late arming silently drops the first wave. Always arm first.

### 2. Coverage: the filter must match every terminal state

A Monitor that filters only success lines is silent on crash, hang, OOM, or rate-limit. Silence is indistinguishable from "still running" — the agent sits, the user waits, no signal arrives. Every terminal state must produce a stdout line.

Test before shipping: feed your filter a synthetic stream that crashes mid-stream (no closing line). The filter must surface SOMETHING (a `[CRASHED]` or `[TIMEOUT]` event from the watcher's own logic). Use the test pattern in `references/universal/codex-flags.md` §JSONL.

## Per-mode Monitor commands

### exec mode

```bash
ORCHESTRATE_MANIFEST=<manifest> bash <skill-root>/scripts/codex-monitor.sh
```

`codex-monitor.sh` reads the manifest every tick (default 60 s) and prints:

```
<UTC-iso>  procs=codex:N/wrap:M  m=q:Q/r:R/d:D/f:F  base=<sha7> note=<note>  flags=<flags>  :: <per-entry summary>
```

- `procs` = live `codex exec` parents and `run-fleet.sh` per-task wrappers.
- `m=` = manifest counts (queued / running / done / failed).
- `base=` = baseline SHA tail.
- `note=` = ad-hoc note (e.g. "main-dirty:N", "size-drift:+Nfiles").
- `flags=` = action signals: `silent-edit`, `agent-done-committed`, `streak:6x`, `main-dirty:N`, `size-drift:+Nfiles`.

The agent acts on flags:
- `agent-done-committed` → review and (optionally) merge that branch.
- `streak:6x` → check the agent's log for rate-limit 503s or rumination.
- `main-dirty:N` → fix immediately; nothing else should touch main during parallel exec.

### batch mode

```bash
bash <skill-root>/scripts/codex-monitor.sh --tail-runner-log
```

Tails the runner's `_runner.log` (one line per state transition emitted by `run-batch.sh`). The watcher injects size annotations on DONE/SKIP events:

```
START 01-foo
DONE 01-foo (12345 bytes)
DONE 02-bar (4231 bytes) [SMALL]
FAIL 03-baz (see logs/03-baz.log)
SKIP 04-qux (already done)
--- all jobs finished ---
```

`[SMALL]` flag triggers when the answer file is under `MIN_BYTES` (default 10000). After `--- all jobs finished ---`, run `audit-sizes.sh` to inspect the bottom decile.

### single mode

`run-single.sh` pipes `codex exec --json` through `codex-json-filter.sh` directly to stdout. The Monitor command tails this output:

```bash
tail -F <jsonl-log> | bash <skill-root>/scripts/codex-json-filter.sh
```

`codex-json-filter.sh` emits one line per JSONL event:

```
[START] thread=t-1234
[CMD>] pnpm install
[CMD✓] pnpm install (exit 0, 2.3s)
[THINK] Plan: 1) read schema, 2) add migration, 3) ...
[SAID] Done. New migration is at db/migrations/20260508_add_users.sql.
[TURN<] tokens=in:1234/out:567/cached:200
```

Verbosity is configurable: `minimal | normal | verbose`. Default is `normal`.

### review mode

```bash
ORCHESTRATE_MANIFEST=<manifest> bash <skill-root>/scripts/codex-monitor.sh --review
```

The `--review` flag changes the per-tick line to:

```
<UTC-iso>  branches=converged:C/in-loop:L/blocked:B/cap:K/failed:X  rounds=<sum>  flags=<flags>
```

Per-branch round counts are logged. `flags=` includes `round-cap-near` (round ≥ 8 of 10) and `oscillation` (3-consecutive-all-rejected).

### rescue mode

Rescue does not arm its own Monitor — it inherits from the original mode. The dispatcher emits a Monitor hint with the original mode's command, parameterized to the same manifest.

## Line-buffering rules

Pipes to grep / awk lose buffer flushing by default. The skill enforces:

- `grep --line-buffered` whenever grep is in a pipe.
- `awk '{...; fflush();}'` whenever awk is in a pipe.
- `stdbuf -oL` for any other pipe stage that needs forced line-buffering.

Without these, a 4 KB pipe buffer means events arrive in batches separated by minutes. The Monitor sees nothing until the buffer flushes or the source closes — by which point the agent has already paused and asked the user.

## Stopping a Monitor

| Method | When |
|---|---|
| `TaskStop` | When the agent decides to release the Monitor (typically after `--- all jobs finished ---`). |
| Session end | All Monitors die with the Claude session. |
| Command exits naturally | If the watched script exits, the Monitor closes. `tail -F` does NOT exit on its own — the file just stops growing. Always `TaskStop` after manifest is terminal. |
| Auto-kill for volume | The system kills Monitors that emit too many events. Tighten the filter and re-arm. Volume budget is hidden but well below 1 line/second sustained. |

## Forbidden patterns

- **`tail -f` without `-F`.** `tail -f` follows the original inode; if log rotation moves the file, the tail dies silently. `tail -F` re-opens.
- **`grep` without `--line-buffered`.** Events delayed by minutes.
- **`awk` without `fflush()`.** Same.
- **One Monitor per worker.** Use one Monitor for the whole fleet. Per-worker Monitors flood notifications and miss cross-worker patterns.
- **Filtering only success.** Coverage rule violation. Surface failures.
- **Re-arming the same Monitor in a loop.** A Monitor that re-arms on its own confuses the agent and the user. Arm once; let it run; TaskStop when terminal.

## Why one Monitor, not one per worker

The agent receives every Monitor line as a notification injected into the conversation. With N workers and N Monitors, every event from every worker fights for context. A single Monitor with a structured per-tick summary line lets the agent see the whole fleet in one notification batch. Per-worker logs still exist on disk (one per entry); the agent reads them on demand for forensics.

## Tuning verbosity

`codex-json-filter.sh` accepts:

```bash
codex-json-filter.sh --level minimal   # only [START], [SAID], [ERR]
codex-json-filter.sh --level normal    # add [CMD>], [CMD✓], [TURN<]
codex-json-filter.sh --level verbose   # add [THINK], [FILE], full command output
```

`codex-monitor.sh` accepts `INTERVAL=N` (seconds between ticks; default 60).

For batch mode the `MIN_BYTES` env var controls the `[SMALL]` flag threshold (default 10000 bytes).

## Failure mode: Monitor silent for >2× expected interval

The runner is hung, the disk is full, or the Monitor itself was OOM-killed. Recovery:

1. Check `pgrep -f orchestrate` for live runners.
2. Check `df -h` on the manifest's parent disk.
3. `cat <log-path>` directly to see if events are landing on disk but not flowing through the Monitor.
4. If all of the above are healthy, re-arm the Monitor (it may have been auto-killed for volume).
5. If not healthy, surface and stop. Rescue mode picks up where the manifest left off.
