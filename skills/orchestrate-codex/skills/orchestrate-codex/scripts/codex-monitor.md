# codex-monitor.sh

Manifest-aware fleet ticker. Emits one stdout line per tick (default every 30s) summarizing manifest counts, live codex procs, baseline drift, action flags, and per-worktree commit/dirty counts.

## Inputs

```bash
ORCHESTRATE_MANIFEST=<path> bash codex-monitor.sh
```

The script has no CLI flags. All knobs are env vars.

| Env var | Default | Notes |
|---|---|---|
| `PROJECT_DIR` | `$(pwd)` | Repo root the monitor watches |
| `ORCHESTRATE_MANIFEST` | none | Path to the orchestrate-codex manifest. Without it, the monitor only reports git/process counts (no manifest summary). |
| `MONITOR_ROOT` | `/tmp/orchestrate-codex-monitor` | Logs dir; `monitor.log` and `baseline.sha` land here |
| `CODEX_MONITOR_INTERVAL` | `30` | Seconds between ticks |
| `CONSEC_WARN_AT` | `3` | Consecutive identical-note ticks before `streak:Nx` flag fires |
| `NOTIFY_TITLE` | `Orchestrate Codex` | osascript title |
| `CODEX_MONITOR_NO_OSASCRIPT` | unset | Set to `1` to disable native macOS notifications |
| `WORKTREE_DIR_NAME` | `.worktrees` | Legacy in-repo worktree subdir name (only used when git is unavailable) |
| `AUTOSTOP_GRACE_SEC` | `60` | Seconds the manifest must remain fully terminal AND no codex procs alive before the monitor self-terminates with `--- all jobs finished ---` and exits 0. Set to `0` to disable. |
| `ORCHESTRATE_QUIET_AFTER` | `0` | Legacy: ticks of consecutive `fleet-quiet` before emitting `--- fleet quiet ---` and exiting. Kept for backward compatibility; superseded by `AUTOSTOP_GRACE_SEC`. |

## Output

stdout (one line per tick; tail-friendly for the Monitor tool).

### Tick-line shape (canonical)

```
<UTC-iso-z> procs=codex:N commits=main:M/all:A manifest=[<summary>](<note>) [<flag>,<flag>...] :: <wt-summary>
```

Fields:

- `procs=codex:N` — count of live `codex exec` parents (via `pgrep -f 'codex exec'`).
- `commits=main:M/all:A` — `M` = commits on `HEAD` since baseline; `A` = commits across all refs since baseline. Both are 0 if no git baseline is pinned.
- `manifest=[<summary>]` — `summary` is `queued=N running=N done=N failed=N skipped=N reviewed=N total=N`, or the literal `manifest=none` when no manifest is configured.
- `(<note>)` — optional. One of `idle`, `working/no-commit-yet`, `+Ncommit`. Empty if no note applies.
- `[<flags>]` — optional. Any of:
  - `streak:Nx` — N consecutive ticks with identical note (N ≥ `CONSEC_WARN_AT`, default 3).
  - `agent-done-committed` — codex procs hit zero AND new commits landed since the previous tick.
  - `manifest-changed` — manifest summary differs from the previous tick.
  - `fleet-quiet` — manifest fully terminal AND no codex procs (precursor to auto-stop).
- `:: <wt-summary>` — per-worktree summary. Either `wts=0` (no worktrees) or space-separated `<name>=<commits>c/<dirty>d` entries (e.g. `wt-feat-1=2c/0d wt-feat-2=0c/3d`). Worktrees are enumerated via `git worktree list --porcelain`; the legacy in-repo glob is the fallback when git is unavailable.

### Sentinels (terminal lines)

- `--- all jobs finished ---` — manifest stayed fully terminal for `AUTOSTOP_GRACE_SEC` seconds. Emitted exactly once before exit 0. This is the universal terminator; consumers should match this line as their stop signal.
- `--- fleet quiet ---` — legacy sentinel emitted when `ORCHESTRATE_QUIET_AFTER>0` and that many consecutive `fleet-quiet` ticks have elapsed.

### Examples

```
04:47:27Z procs=codex:6 commits=main:0/all:8 manifest=[queued=0 running=5 done=8 failed=0 skipped=0 reviewed=0 total=13] (working/no-commit-yet) [manifest-changed] :: wt-feat-1=1c/0d wt-feat-2=2c/3d
04:47:57Z procs=codex:0 commits=main:0/all:13 manifest=[queued=0 running=0 done=13 failed=0 skipped=0 reviewed=0 total=13] (+5commit) [agent-done-committed,manifest-changed,fleet-quiet] :: wt-feat-1=2c/0d wt-feat-2=3c/0d
--- all jobs finished ---
```

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Auto-stop (`--- all jobs finished ---` or `--- fleet quiet ---`) or TERM/INT |
| 1 | Cannot `cd` into `PROJECT_DIR` |

## Action flags

| Flag | Meaning | Action |
|---|---|---|
| `streak:Nx` | N consecutive identical-note ticks (N ≥ `CONSEC_WARN_AT`) | Check the agent's log for rate-limit 503s or rumination |
| `agent-done-committed` | Codex procs hit zero AND new commits landed | Time to review and merge that branch |
| `manifest-changed` | Manifest summary string changed since the previous tick | Status transitioned (queued → running → done/failed) |
| `fleet-quiet` | Manifest fully terminal AND no codex procs | Auto-stop will fire after `AUTOSTOP_GRACE_SEC` |

## Behavior

- Tick cadence is fixed by `CODEX_MONITOR_INTERVAL`; the monitor `sleep`s between ticks.
- One stdout line per tick, line-buffered. Each line is also appended to `$MONITOR_ROOT/monitor.log`.
- `pgrep -f 'codex exec'` counts live parent procs.
- `git rev-list --count $BASELINE..HEAD` (in `PROJECT_DIR`) gives `commits=main`; `git log --all` gives `commits=all`.
- Worktree enumeration uses `git -C $PROJECT_DIR worktree list --porcelain`. The main worktree is dropped from the count; siblings (whether under `<project>/.worktrees/` or `../<project>-wt-*`) are reported uniformly.
- Auto-stop ends the loop cleanly when the manifest stays fully terminal for `AUTOSTOP_GRACE_SEC` seconds; the operator does not need to call `TaskStop` for finished fleets.

## Notes

`tail -F` does NOT exit when its source file stops growing. Auto-stop replaces that pattern: the monitor itself terminates with `--- all jobs finished ---` once the manifest is settled, and the Monitor tool reads that line as its stop signal.

The Monitor tool batches lines arriving within 200 ms into one notification. Multi-line bursts group naturally.
