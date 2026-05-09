# codex-monitor.sh

Manifest-aware fleet ticker. Emits one stdout line per tick (default every 60 s) summarizing manifest counts, live codex procs, baseline drift, and action flags.

## Inputs

```bash
ORCHESTRATE_MANIFEST=<path> bash codex-monitor.sh [--review] [--auto-exit]
```

| Arg/env | Default | Notes |
|---|---|---|
| `ORCHESTRATE_MANIFEST` (env) | required | Path to the orchestrate-codex manifest |
| `INTERVAL=N` (env) | 60 | Seconds between ticks |
| `--review` | off | Switch to per-branch round-counting line format |
| `--auto-exit` | off | Exit when manifest is fully terminal |
| `--tail-runner-log` | off | For batch mode: tail `<monitor-root>/_runner.log` instead of computing manifest summary |

## Outputs

stdout (one line per tick; tail-friendly for the Monitor tool):

For exec / single / rescue:
```
2026-05-08T18:30:11Z procs=codex:6/wrap:5 m=q:0/r:5/d:8/f:0 base=abc1234 note=- flags=- :: 5 entries running
```

For review (`--review` flag):
```
2026-05-08T18:30:11Z branches=converged:2/in-loop:3/blocked:0/cap:0/failed:0 rounds=12 flags=round-cap-near
```

For batch (`--tail-runner-log` flag):
```
START 01-foo
DONE 01-foo (12345 bytes)
DONE 02-bar (4231 bytes) [SMALL]
--- all jobs finished ---
```

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Loop exited cleanly (TERM/INT or auto-exit) |
| 1 | Manifest path missing or unreadable |

## Action flags

The tick line's `flags=` field surfaces actionable signals:

| Flag | Meaning | Action |
|---|---|---|
| `silent-edit` | Codex started writing but no commit yet | Normal; no action |
| `agent-done-committed` | Wrapper exited; commits landed | Time to review and merge that branch |
| `streak:Nx` (N≥6) | Six+ consecutive ticks with no commit advance | Check the agent's log for rate-limit 503s or rumination |
| `main-dirty:N` | Main branch has uncommitted changes | Fix immediately; nothing should touch main during exec |
| `size-drift:+Nfiles` | File count changed without a commit | Could be generated files; usually benign |
| `round-cap-near` (review only) | Branch ≥ round 8 of 10 | Decide if cap should extend or branch should be split |
| `oscillation` (review only) | 3 consecutive all-rejected rounds | Branch will mark `three_all_rejected` next round |

## Behavior

- Reads the manifest every tick; counts entries by status.
- Runs `pgrep -f 'codex exec'` to count live procs (filters by current user when possible).
- Runs `git -C <workspace> rev-parse HEAD` and compares to `BASELINE_SHA` for drift detection.
- Uses `--line-buffered` and `fflush()` discipline so the Monitor tool sees events as they happen.

## Notes

`tail -F` does NOT exit when the watched file stops growing. Always `TaskStop` the Monitor when `manifest.entries[].status` is fully terminal (or pass `--auto-exit` for the same effect).

The Monitor tool batches lines arriving within 200 ms into one notification. Multi-line bursts group naturally.
