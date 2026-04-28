# loop-status.py

Live read-only table of branch round status. Used by the main agent during Phase 3 to monitor parallel subagents without entering their worktrees.

## Usage

```bash
python3 scripts/loop-status.py                 # one-shot snapshot
python3 scripts/loop-status.py --watch         # redraw every 10s
python3 scripts/loop-status.py --watch --refresh 5
python3 scripts/loop-status.py --json          # machine-readable
```

## What it shows

```
# loop-status @ 2026-04-26 10:14:32Z

Branch              Worktree                    Rounds  Last      State     Age
--------------------------------------------------------------------------------
feat/onboarding     myrepo-wt-feat-onboarding        4  no-major  DONE       2m
fix/auth-bug        myrepo-wt-fix-auth-bug           7  2+1u      in-loop    1m
docs/contributors   myrepo-wt-docs-contributors      3  1+0u      in-loop    8m
chore/cleanup       myrepo-wt-chore-cleanup         20  3+2u      CAP-REACHED 1m

total: 4  (DONE: 1, in-loop: 2, CAP-REACHED: 1)
```

Columns:

- **Branch** — branch name
- **Worktree** — basename of the worktree path
- **Rounds** — number of rounds completed
- **Last** — `no-major` / `cap` / `Mn+Uu` (M majors, U unclassified-as-major)
- **State** — `spawned` / `in-loop` / `STALE` / `DONE` / `CAP-REACHED` / `BLOCKED` / `FAILED`
- **Age** — minutes since the latest round-log was written (heartbeat)

`STALE` means `state == in-loop` but the heartbeat is older than `--stale-minutes`. The subagent is presumed crashed; main agent should triage per `references/failure-recovery.md`.

## Flags

| Flag | Default | Effect |
|---|---|---|
| `--manifest <path>` | `<repo-root>/.codex-review-manifest.json` (repo-local default) | Source-of-truth manifest. |
| `--rounds-dir <path>` | `<repo-root>/.codex-review-rounds/` | Per-branch round-log directory. |
| `--stale-minutes <n>` | `60` | Heartbeat threshold for `STALE` flagging. |
| `--watch` | off | Redraw on a timer. |
| `--refresh <n>` | `10` | Seconds between redraws (only with `--watch`). |
| `--json` | off | Emit the raw manifest JSON instead of the table. |

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Always, regardless of state. Read-only. |
| `2` | Manifest missing or unreadable (printed to stdout, not stderr — caller decides). |

## When to run

- **Phase 3**: main agent runs `--watch` while subagents are looping. This is the primary monitor.
- **Phase 4**: one-shot `loop-status.py --json` to consume the manifest programmatically.
- **Anytime debugging**: peek at parallel state without touching anything.

## Safety

Pure read-only. Never opens the manifest for write. Never enters worktrees. Never invokes git or codex.

## Reading the table

- `in-loop` with monotonically-increasing `Rounds` → healthy convergence.
- `in-loop` with `Last` showing the same `Mn+Uu` over multiple checks → possible oscillation. If 3+ rounds with the same major count, subagent should mark BLOCKED (per `references/per-branch-fix-loop.md`).
- `STALE` → subagent crashed or stuck. Read the most recent round log; decide redispatch or FAILED.
- `CAP-REACHED` after rounds=20 → expected terminal state; surface for human decision.

## Integration with `audit-review-state.py`

Phase 0's `audit-review-state.py` queries the same manifest and round-log directory. If `loop-status.py` shows STALE branches, `audit-review-state.py`'s "stale round logs" section will list them — the two views agree by design.

## Watch-mode semantics

`--watch` uses ANSI clear-screen (`\033[2J\033[H`) and redraws every `--refresh` seconds. Press Ctrl+C to exit; the script returns 0 on KeyboardInterrupt. Suitable for `tmux` pane or a dedicated terminal during long Phase-3 runs.

## Extending

- Add a `--filter <state>` flag to show only branches in a given state.
- Add a `--per-branch <branch>` flag to show round_history for a single branch.
- Add a `--csv` mode for spreadsheet ingestion.
