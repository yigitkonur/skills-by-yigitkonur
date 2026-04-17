# Observability Rules

Every tick, `codex-monitor.sh` emits one line. The format is stable:

```
HH:MM:SSZ procs=codex:N/wrap:M commits=main:X/all:Y (note) [flags] :: per-worktree-breakdown
```

Reading the line quickly is half the skill. Here's what each field means and what to do about it.

## procs field

`codex:N/wrap:M`

- `codex` is the count of `codex exec` processes system-wide.
- `wrap` is the count of `codex-wrapper.sh` processes.
- Relationship: every wrapper launches one `codex exec`, which spawns one child. Expect `codex = 2 × wrap` while agents are running code.
- `codex:0/wrap:N` with `N > 0` means wrappers are in post-verify phase (running tsc/vitest). They'll exit soon.
- `codex:N/wrap:0` means orphaned codex procs. Likely from stale interactive `codex` sessions (different from `codex exec`). Not dangerous, but eats memory — `pkill -f "codex resume"` cleans them up.

## commits field

`main:X/all:Y`

- `main` counts commits on `main` past the baseline SHA in `baseline.sha`.
- `all` counts unique commits across ALL branches (including in-flight worktree branches) past baseline.
- `Y > X` means there are in-flight commits on worktree branches not yet merged. That's the expected state during a wave.
- `Y == X` after an `agent-done-committed` flag means everything merged.

## note field

Exactly one note per tick, in parentheses. This is the narrative summary.

| Note | Meaning | Action |
|---|---|---|
| `(idle)` | No codex procs, no new commits since last tick | OK — either everyone's done or nothing is dispatched |
| `(working/no-commit-yet)` | Codex procs running, no new commits | Normal while agents are editing; becomes concerning if streak gets long |
| `(+Ncommit)` | N new commits landed since last tick | Something finished committing — go inspect |

## flags field

Zero or more flags in brackets, comma-separated. Flags ADD information to the note.

| Flag | Triggered when | What to do |
|---|---|---|
| `streak:Nx` | Same note fired N consecutive ticks (default N≥3) | Check the specific agent's log if N≥6 with no `silent-edit` — ruminating |
| `silent-edit` | Worktree state hash changed but no new commit | Normal — agent is writing. No action. |
| `main-dirty:N` | Main branch has N uncommitted files | Stop everything. You or a tool accidentally wrote to main. Figure out what and undo. |
| `agent-done-committed` | `codex:0` + commit count advanced in the same tick | **A wrapper just finished and committed. Go inspect + merge.** |
| `size-drift:±Nfiles` | File count changed but no new commit | Usually generated files or caches slipping out of git. Benign most of the time. Investigate if large. |

## per-worktree breakdown

The tail `:: name1=ActiveC/DirtyD name2=...`

- `name` = worktree directory name (e.g. `wave1-reports`)
- `A` = commits this branch has past baseline
- `D` = dirty file count (uncommitted changes)

State transitions to watch:

- `0c/0d` → `0c/5d` → `1c/0d` — the happy path: wrote code, committed, cleaned up.
- `0c/Nd` static for 5+ ticks — agent writing slowly (big plan) OR stuck. Check the log.
- `0c/0d` for the whole run — agent never edited. Bailout. Re-dispatch or give up.
- `Nc/Md` where M > 0 after `agent-done-committed` fired — something uncommitted is left after post-verify. Inspect manually.

## Frequency

Default `CODEX_MONITOR_INTERVAL=60` seconds. Two reasons to change it:

- **Shorter (30s)** — during early-stage development where you want rapid feedback. Produces 2× the notification volume.
- **Longer (300s)** — for multi-hour background runs where you don't want per-minute notifications. Dramatically cuts the notification firehose.

Don't go below 10 seconds — the `git log --all` + `find` + `pgrep` loop has a non-trivial cost; under 10s you start competing with the agents for IO.

## How to watch without drowning in events

- Skim the note + flag columns; ignore the rest on most ticks.
- `(working/no-commit-yet)` with `silent-edit`: agents making progress, no action.
- `(+Ncommit) [agent-done-committed]`: stop scrolling, go look.
- `streak:6x+` without `silent-edit`: the agent's stuck or bailed. Check its log file.

## Log files

All in `$MONITOR_ROOT/logs/`:

- `monitor.log` — accumulates every tick line
- `<worktree-name>.log` — per-agent stdout + codex output + post-verify results. Grep for `post-verify`, `exit=`, `no changes`, or `503`.
