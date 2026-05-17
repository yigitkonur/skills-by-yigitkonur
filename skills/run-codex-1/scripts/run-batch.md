# run-batch.sh

Batch mode bounded-concurrency runner. Iterates `prompts/*.md`, fans out via `xargs -P "$JOBS"`, per-prompt: spawn codex with stdin-piped prompt → atomic answer move → manifest update. Idempotent skip-existing.

## Inputs

Both flag-style and env-style invocations work; flags win when both are given.

```bash
# Flag-style (preferred for one-off invocations)
bash run-batch.sh --manifest <path> --prompts-dir <p> --answers-dir <a> \
                  [--logs-dir <l>] [--concurrency N] [--min-bytes N] [--dry-run]

# Env-style (preferred when the dispatcher spawns the runner)
PROMPTS=p ANSWERS=a LOGS=l JOBS=N MIN_BYTES=N \
  ORCHESTRATE_MANIFEST=<path> bash run-batch.sh
```

| Flag | Env | Default | Notes |
|---|---|---|---|
| `--manifest <path>` | `ORCHESTRATE_MANIFEST` | unset | Path to run-codex-1 manifest. Required for manifest writes; absent is a valid no-manifest mode. |
| `--prompts-dir <p>` | `PROMPTS` | `./prompts` | Source of `*.md` prompt files |
| `--answers-dir <a>` | `ANSWERS` | `./answers` | Where atomic answer files land |
| `--logs-dir <l>` | `LOGS` | `./logs` | Per-job `<slug>.log` and `<slug>.jsonl` |
| `--concurrency N` | `JOBS` | `10` | Soft warn above 20 |
| `--min-bytes N` | `MIN_BYTES` | `10000` | Floor for `[SMALL]` flag and `mode_state.below_floor` |
| `--dry-run` | `DRY_RUN=1` | off | Print planned commands; do not invoke codex |
| `--inputs <file>` | n/a | accepted-and-ignored | Used only at seed time (the dispatcher renders prompts before invoking the runner). |
| `--template <tmpl>` | n/a | accepted-and-ignored | Same — used at seed time. |

## Outputs

stdout (one line per state transition; Monitor-compatible):

```
START 01-foo
DONE 01-foo (12345 bytes)
DONE 02-bar (4231 bytes) [SMALL]
FAIL 03-baz (codex_exit=1, see logs/03-baz.log)
SKIP 04-qux (already done)
--- all jobs finished ---
```

Per-prompt log file at `logs/<slug>.log`.
Per-prompt JSONL at `logs/<slug>.jsonl`.
Per-prompt answer at `<answers-dir>/<slug>.md` (atomic move from temp).

Manifest mutations: same shape as run-fleet.sh; `mode_state.answer_size_bytes` and `mode_state.below_floor` populated.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | All prompts processed |
| 1 | `prompts/` directory missing or empty |
| 2 | `codex` missing on non-dry-run path |
| 3 | Invalid concurrency or args |

## Behavior

- Skip-existing guard: `[ -s answers/<slug>.md ]` short-circuits before spawn. Re-running the runner is safe.
- **SKIP preserves `done`**: when the answer already exists, the runner only
  flips manifest status to `skipped` if the prior status was `queued` (or
  empty / unset). A pre-existing `done` entry is left as `done` — this avoids
  silently demoting completed work on a re-run.
- Atomic answer move: codex writes to `<answers-dir>/<slug>.partial`; only
  after exit 0 AND non-empty does the runner `mv -f` to `<slug>.md`. Crashes
  leave no `<slug>.md`, so the next run retries. (Filename uses **no leading
  dot** so `find` and `ls` show partial files plainly.)
- Pairs `--json` with `-o <tmp>`: the temp is the source of truth for "did codex produce output." JSONL events flow to `<logs-dir>/<slug>.jsonl`; stderr (auth errors, deprecation warnings) goes to `<logs-dir>/<slug>.log` so the JSONL pipeline stays parseable.
- **Per-entry path fields**: `log_path`, `jsonl_path`, `answer_path` are
  populated on every entry on the same write that flips status to `running`
  (per `manifest-contract.md`). `mode_state.answer_size_bytes` and
  `mode_state.below_floor` are populated when the answer lands cleanly.
- **Signal handling**: `trap 'kill 0' TERM INT EXIT` runs near the top so SIGTERM
  on the runner propagates to xargs and every codex child. No orphan codex
  processes survive a runner kill.
- No retries; re-run for retries (rescue mode).

## Notes

Two runners over the same workdir would race on the skip-existing guard. The dispatcher refuses concurrent runs; use separate workdirs for independent batches.

When `--audit-report` is supplied, the runner executes `audit-sizes.sh` after all jobs finish and writes the report. Without that flag, run the auditor manually.
