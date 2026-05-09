# run-review.sh

Review mode convergence runner. Per branch per round: spawn `codex exec review --base <base> --json -o <findings>`, normalize findings, classify major/minor, and write a terminal manifest state. Round cap defaults to 10. Per-branch parallelism is bounded by `JOBS`.

## Inputs

```bash
bash run-review.sh --manifest <path> [--base main] [--concurrency N] [--max-rounds N] [--only id,id] [--dry-run]
```

| Arg/env | Default | Notes |
|---|---|---|
| `--manifest <path>` | required | Manifest with `mode=review` and per-branch `entries[]` |
| `--base <ref>` | `main` | Base ref passed to `codex exec review --base`. |
| `--concurrency N` / `JOBS=N` | 4 | Per-branch parallel |
| `--max-rounds N` | 10 | Per-branch round cap |
| `--state-dir <dir>` | `dirname(manifest)` | Parent for `rounds/`. Dispatcher passes a run-specific dir. |
| `--only id,id` | unset | Rescue subset replay. |
| `--dry-run` | off | Creates synthetic no-finding review output and reaches `converged` without calling Codex. |

## Outputs

stdout (Monitor-compatible):

```
START feat-auth (round 1 branch=feat/auth base=main)
DONE  feat-auth (converged round=1 findings=/state/rounds/feat-auth.r1.md)
START docs-quickstart (round 1 branch=docs/quickstart base=main)
DONE  docs-quickstart (blocked: 2 major finding(s); see /state/rounds/docs-quickstart.r1.classification.json)
--- all jobs finished ---
```

Per-round findings at `<rounds-dir>/<branch-slug>.r<round>.md` and JSONL at `<rounds-dir>/<branch-slug>.r<round>.jsonl`.
Per-round normalized review JSON at `<rounds-dir>/<branch-slug>.r<round>.review.json`.
Per-round classified output at `<rounds-dir>/<branch-slug>.r<round>.classification.json`.

Manifest mutations: `status`, `round`, `last_findings_path`, `classification_path`, `worktree_path`, `attempts`, timestamps, and `last_error` when blocked/failed.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Runner loop completed; branch failures are recorded in the manifest |
| 1 | Manifest missing |
| 2 | `codex exec review` is not available (binary too old) |
| 3 | Invalid args or invalid concurrency |

## Behavior

- Uses `codex exec review` (not bare `codex review`). Verified against codex-cli 0.130.0: `exec review` accepts full `CODEX_FLAGS`, `--json`, and `-o`.
- Sources `codex-flags.sh` for `CODEX_FLAGS`.
- Round cap = 10. Terminal states: `converged`, `blocked`, `failed`, `cap_reached`.
- Per-branch worktrees created via `setup-worktree.sh` on round 1; reused for subsequent rounds.

## Notes

The runner does not apply code edits. When classification finds major or ambiguous items, it marks the branch `blocked` and records artifact paths. The main agent evaluates items with `do-review` or a local equivalent; external/human/bot feedback consolidation belongs to `evaluate-code-review`; PR handoff belongs to `ask-review`.
