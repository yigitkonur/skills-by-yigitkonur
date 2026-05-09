# run-batch.sh

Batch mode bounded-concurrency runner. Iterates `prompts/*.md`, fans out via `xargs -P "$JOBS"`, per-prompt: spawn codex with stdin-piped prompt → atomic answer move → manifest update. Idempotent skip-existing.

## Inputs

```bash
bash run-batch.sh --manifest <path> --prompts-dir <dir> --answers-dir <dir> --logs-dir <dir> [--concurrency N] [--only id,id] [--dry-run]
```

| Arg/env | Default | Notes |
|---|---|---|
| `--manifest <path>` | required | Path to orchestrate-codex manifest |
| `--inputs <file>` | n/a | Accepted for dispatcher compatibility; render already happened before runner start. |
| `--template <tmpl>` | n/a | Accepted for dispatcher compatibility; runtime reads from `--prompts-dir`. |
| `--prompts-dir <dir>` | `prompts/` | Rendered prompt files. |
| `--answers-dir <dir>` | `answers/` (relative to workdir) | Where atomic answer files land |
| `--logs-dir <dir>` | `logs/` | Per-input JSONL/log files. |
| `--runner-log <file>` | unset | Optional combined runner log for `audit-sizes.sh`. |
| `--audit-report <file>` | unset | If set, `audit-sizes.sh` runs after all jobs finish and writes here. |
| `--only id,id` | unset | Rescue subset replay. |
| `JOBS=N` / `--concurrency N` | 10 | Soft gate above 20 |
| `MIN_BYTES=N` | 10000 | Floor for `[SMALL]` flag in stdout |

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

- Skip-existing guard: `[ -s answers/<slug>.md ]` short-circuits only when the manifest entry is already `done`. Rescue can replay a failed id even if an old answer file exists.
- Atomic answer move: codex writes to `mktemp -t answers-<slug>.XXXXXX`; only after exit 0 AND non-empty does the runner `mv -f` to the canonical path.
- Pairs `--json` with `-o <tmp>`: the temp is the source of truth for "did codex produce output." JSONL events flow to the `.jsonl` log for forensics.
- No retries; re-run for retries (rescue mode).

## Notes

Two runners over the same workdir would race on the skip-existing guard. The dispatcher refuses concurrent runs; use separate workdirs for independent batches.

When `--audit-report` is supplied, the runner executes `audit-sizes.sh` after all jobs finish and writes the report. Without that flag, run the auditor manually.
