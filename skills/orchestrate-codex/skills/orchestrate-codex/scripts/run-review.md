# run-review.sh

Review mode driver. Per branch per round: spawn `codex exec review --base <base> --json -o <findings>`. Round cap 10. Per-branch parallelism bounded by `JOBS`.

## Inputs

```bash
bash run-review.sh --manifest <path> [--concurrency N] [--max-rounds N]
```

| Arg/env | Default | Notes |
|---|---|---|
| `--manifest <path>` | required | Manifest with `mode=review` and per-branch `entries[]` |
| `--concurrency N` / `JOBS=N` | 4 | Per-branch parallel |
| `--max-rounds N` | 10 | Per-branch round cap |

## Outputs

stdout (Monitor-compatible):

```
START feat-auth round=1
MAJOR feat-auth round=1 count=3 needs-decision
APPLY feat-auth round=1 count=2 (main agent in own context)
START feat-auth round=2
DONE feat-auth round=2 (no major)
CONVERGED feat-auth (rounds=2, total_pushed=2)
START docs-quickstart round=1
NO-MAJOR docs-quickstart round=1
CONVERGED docs-quickstart (rounds=1, total_pushed=0)
--- all jobs finished ---
```

Per-round findings JSON at `<rounds-dir>/<branch-slug>.<round>.md` and `<rounds-dir>/<branch-slug>.<round>.jsonl`.
Per-round classified output at `<rounds-dir>/<branch-slug>.<round>.classified.json`.
Per-round apply queue at `<rounds-dir>/<branch-slug>.<round>.apply-queue.json` (written by main agent's evaluation).

Manifest mutations: per-round entries appended to `mode_state.rounds[]`; terminal state in `mode_state.terminal_state`.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | All branches reached terminal state |
| 1 | Manifest missing |
| 2 | `codex exec review` is not available (binary too old) |

## Behavior

- Uses `codex exec review` (not bare `codex review`). The live binary supports the full `CODEX_FLAGS` only on the `exec review` subcommand; bare `review` has a narrower flag set.
- Sources `codex-flags.sh` for `CODEX_FLAGS`.
- Round cap = 10. Terminal states: `converged`, `cap_reached_with_progress`, `cap_reached_no_progress`, `three_all_rejected`, `blocked`, `failed`.
- 3-consecutive-all-rejected detection: per branch, if 3 rounds in a row produce major items where the main agent rejects every one, the runner marks `done` with `terminal_state="three_all_rejected"` and `terminal_reason="codex stuck"`.
- Per-branch worktrees created via `setup-worktree.sh` on round 1; reused for subsequent rounds.

## Notes

The runner emits `MAJOR <branch> round=N count=K needs-decision` and **stops the per-branch round** until the main agent writes the apply queue. The main agent reads `<rounds-dir>/<branch-slug>.<round>.classified.json`, evaluates each item via `Skill(do-review)`, and writes `<rounds-dir>/<branch-slug>.<round>.apply-queue.json`. The runner watches for the queue file; once present, it proceeds.

This handoff is the role split: classifier is mechanical (script); evaluator is contextual (main agent); applier is contextual (main agent). Per the plan, no Applier sub-agent.
