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
  command: "ORCHESTRATE_MANIFEST=<manifest-path> ORCHESTRATE_QUIET_AFTER=1 bash <skill-root>/scripts/codex-monitor.sh | grep -E --line-buffered '(streak:[0-9]+x|agent-done-committed|manifest-changed|fleet-quiet|^--- fleet quiet ---)'",
  persistent: true,
  timeout_ms: 300000
})
```

- `description` is shown in every notification. Make it specific so the user can disambiguate when multiple Monitors are armed.
- `command` runs continuously until killed. Stdout lines become notifications. Stderr is logged but does not notify.
- `persistent: true` means the Monitor lives until the session ends or `TaskStop` is called. `timeout_ms` is required by the schema but ignored when `persistent: true` — pass `300000` as convention.
- `persistent: false` for run-single mode (bounded duration), with `timeout_ms` set to the expected wall-clock cap.
- `ORCHESTRATE_QUIET_AFTER=1` (or any value ≥ 1) is required for the script to emit the `--- fleet quiet ---` terminal sentinel; the default (0) means the script never auto-exits. See "Per-mode Monitor commands → exec mode" below.
- The grep filter above is a known-good coverage filter keyed on the script's actual flag vocabulary (`streak:Nx`, `agent-done-committed`, `manifest-changed`, `fleet-quiet`) plus the terminal sentinel. Drop it if you want every per-tick line through; keep it when notification volume must be tight.

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
ORCHESTRATE_MANIFEST=<manifest> ORCHESTRATE_QUIET_AFTER=1 \
    bash <skill-root>/scripts/codex-monitor.sh
```

`codex-monitor.sh` reads the manifest every tick (default 30 s, override with `CODEX_MONITOR_INTERVAL`) and prints exactly one line per tick (one notification each):

```
HH:MM:SSZ procs=codex:N commits=main:M/all:A manifest=[queued=Q running=R done=D failed=F skipped=S reviewed=V total=T] (note) [flag1,flag2,...] :: <worktree-summary>
```

Field-by-field — verified against `scripts/codex-monitor.sh:222`:

- `procs=codex:N` — live `codex exec` parents (`pgrep -f 'codex exec'`). There is **no** `wrap:M` count and there is no `base=<sha7>` field on the tick line.
- `commits=main:M/all:A` — commits since the pinned baseline on `HEAD` (`M`) and across all refs (`A`).
- `manifest=[...]` — full manifest counts (`queued`, `running`, `done`, `failed`, `skipped`, `reviewed`, `total`). When no manifest is set, the field reads `manifest=[manifest=none]`.
- `(note)` — ad-hoc parenthesized note. Possible notes: `(idle)`, `(working/no-commit-yet)`, `(+Ncommit)`. The note is **inline parentheses**, not a `note=<value>` k=v field.
- `[flag1,flag2]` — action signals. Canonical flag vocabulary (verified at `scripts/codex-monitor.sh:196,199,203,208`):
  - `streak:Nx` — N consecutive ticks with the same parenthesized note. Fires when N reaches `CONSEC_WARN_AT` (default 3). The literal `streak:6x` will appear at the sixth identical tick — but `streak:3x`, `streak:4x`, `streak:5x` etc. all fire on their respective ticks. Filter on the prefix `streak:`, not on a specific count.
  - `agent-done-committed` — `procs=codex:0` AND `all_commits` advanced this tick.
  - `manifest-changed` — manifest summary string differs from the prior tick.
  - `fleet-quiet` — manifest is all-terminal AND `procs=codex:0`. When `ORCHESTRATE_QUIET_AFTER>0`, this flag also drives auto-exit (see Stopping a Monitor below).
- `:: <worktree-summary>` — per-worktree `<name>=<commits>c/<dirty>d` pairs (e.g. `myrepo-wt-exec-foo=2c/0d`). Reads `wts=0` when no worktrees exist.

The agent acts on flags:
- `agent-done-committed` → review and (optionally) merge that branch.
- `streak:` (any N≥3 by default) → check the agent's log for rate-limit 503s or rumination.
- `manifest-changed` → re-read the manifest; some entry transitioned status.
- `fleet-quiet` → all entries terminal; consider `TaskStop` and run `audit-fleet-state.py`.

**Flags the doc previously listed but the script does NOT emit:** `silent-edit`, `main-dirty:N`, `size-drift:+Nfiles`. Filters keyed on these will match zero events. They were aspirational and remain unimplemented — do not depend on them.

### batch mode

```bash
ORCHESTRATE_MANIFEST=<manifest> MONITOR_ROOT=<dir> bash <skill-root>/scripts/codex-monitor.sh
```

The dispatcher emits the canonical command via `envelope.monitor.tool_hint`; copy it verbatim. There is no `--tail-runner-log` flag — `codex-monitor.sh` is mode-agnostic and accepts no CLI arguments. The runner emits a state-transition stream (one line per START/DONE/FAIL/SKIP) which the manifest-aware tick line summarizes. To tail the raw runner log directly without ticking, `tail -F "$RUNNER_LOG"` instead. The watcher injects size annotations on DONE/SKIP events:

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
ORCHESTRATE_MANIFEST=<manifest> MONITOR_ROOT=<dir> bash <skill-root>/scripts/codex-monitor.sh
```

The dispatcher emits this verbatim via `envelope.monitor.tool_hint` for review just like exec/batch — `codex-monitor.sh` is mode-agnostic. There is no `--review` flag, no per-tick `branches=converged:C/in-loop:L/...` line shape, and no `round-cap-near` / `oscillation` flag emission; those were aspirational and never wired. The standard manifest-aware tick line carries `mode_state.review.round` per entry; an operator who wants per-round counts can `jq` the manifest separately:

```bash
jq '.entries[] | {id, status, round: .mode_state.review.round}' "$ORCHESTRATE_MANIFEST"
```

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
| `TaskStop` | When the agent decides to release the Monitor (typically after `fleet-quiet` or `--- all jobs finished ---`). |
| Session end | All Monitors die with the Claude session. |
| Command exits naturally | If the watched script exits, the Monitor closes. `tail -F` does NOT exit on its own — the file just stops growing. `codex-monitor.sh` only auto-exits when `ORCHESTRATE_QUIET_AFTER>0` AND the fleet has been quiet (terminal + no codex procs) for that many consecutive ticks; without it the script loops forever. Always `TaskStop` after manifest is terminal. |
| Auto-kill for volume | The system kills Monitors that emit too many events. Tighten the filter and re-arm. Volume budget is hidden but well below 1 line/second sustained. |

### Terminal sentinels per mode

- **exec / review** (`codex-monitor.sh`): `--- fleet quiet ---` is emitted on stdout **only when** `ORCHESTRATE_QUIET_AFTER` is set to a positive integer AND the fleet has been quiet for that many consecutive ticks (see `scripts/codex-monitor.sh:43, 231-233`). Default is `0` = never auto-exit. Set `ORCHESTRATE_QUIET_AFTER=1` (or higher to debounce) when you want a terminal sentinel; otherwise rely on the `fleet-quiet` flag inside per-tick lines and `TaskStop` from the agent.
- **batch** (`codex-monitor.sh`, mode-agnostic, no flags): `--- all jobs finished ---` is emitted by `run-batch.sh` itself when the runner exits. The manifest-aware ticker surfaces it on the same stream the Monitor tails. (No `--tail-runner-log` flag — see L87 above.)
- **single**: `run-single.sh` appends a `{"type":"orchestrate.done","entry_id":"<id>","status":"<status>"}` event to the JSONL log AFTER the terminal manifest write; `codex-json-filter.sh` translates it to the line `--- single done (<id>: <status>) ---`. Live-watch operators (`tail -F <jsonl> | codex-json-filter.sh`) see this final line and TaskStop the Monitor. The sentinel is emitted at every verbosity level. Existing JSONL consumers ignore unknown event types by default (the new event type is additive). Status values: `done` (success), `failed` (codex non-zero or empty `-o`).

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

`codex-json-filter.sh` accepts (verified against `scripts/codex-json-filter.sh:25-32, 162-237`; matches `references/universal/json-streaming.md` §Verbosity levels):

```bash
codex-json-filter.sh --level minimal   # [START] [CMD>] [CMD✓] [CMD✗] [SAID] [TURN<] [ERR]
codex-json-filter.sh --level normal    # minimal + [TURN>] [THINK] [FILE] [ITEM>] [ITEM<]
codex-json-filter.sh --level verbose   # normal + [?] (unknown event types) + [CMD✓] extended form (with output tail)
```

`[CMD>] [CMD✓] [CMD✗] [TURN<]` are emitted at **every** level (no `[[ "$LEVEL" != "minimal" ]]` guard on the `command_execution` arms or the `turn.completed` arm). `[ERR]` is also emitted at every level. The level only gates `[TURN>] [THINK] [FILE] [ITEM>] [ITEM<]` (gated off in `minimal`) and `[?]` plus the verbose `[CMD✓]` output tail (verbose only).

### How to set the level

- **Runner-pipe (per-entry JSONL written to `entry.jsonl_path`):** the bash runners `run-single.sh` and `run-review.sh` read `FILTER_LEVEL` (default `normal`) and forward it to the filter as `CODEX_FILTER_LEVEL`. There is **no `--filter-level` flag on `node orchestrate-codex.mjs`** — set it as an env var on the dispatcher invocation: `FILTER_LEVEL=verbose node scripts/orchestrate-codex.mjs single …`. `run-single.sh` and `run-review.sh` also accept `--filter-level <level>` when invoked directly without the dispatcher.
- **Monitor-pipe (the Monitor command for single mode):** built by `singleMonitorCommand` in `scripts/orchestrate-codex.mjs:418-425`. It pipes `tail -F <jsonl> | bash codex-json-filter.sh` with **no `--level` flag and no `CODEX_FILTER_LEVEL` env**, so the Monitor's filter always runs at the script's default `normal`. `FILTER_LEVEL` does NOT propagate to the Monitor pipe — the runner-pipe verbosity and the Monitor-pipe verbosity are independent. Re-arm the Monitor with a custom command if you need a different Monitor-side level.

`codex-monitor.sh` accepts:
- `CODEX_MONITOR_INTERVAL=N` — seconds between ticks (default 30).
- `CONSEC_WARN_AT=N` — number of identical-note ticks before `streak:Nx` flag fires (default 3).
- `ORCHESTRATE_QUIET_AFTER=N` — fleet-quiet ticks before the loop emits `--- fleet quiet ---` and exits (default 0 = never auto-exit).
- `MONITOR_ROOT=<dir>` — log directory (default `/tmp/orchestrate-codex-monitor`).

For batch mode the `MIN_BYTES` env var controls the `[SMALL]` flag threshold (default 10000 bytes).

## Failure mode: Monitor silent for >2× expected interval

The runner is hung, the disk is full, or the Monitor itself was OOM-killed. Recovery:

1. Check `pgrep -f orchestrate` for live runners.
2. Check `df -h` on the manifest's parent disk.
3. `cat <log-path>` directly to see if events are landing on disk but not flowing through the Monitor.
4. If all of the above are healthy, re-arm the Monitor (it may have been auto-killed for volume).
5. If not healthy, surface and stop. Rescue mode picks up where the manifest left off.
