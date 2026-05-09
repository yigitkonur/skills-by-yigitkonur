# run-batch.sh

Batch mode bounded-concurrency runner. Iterates `prompts/*.md`, fans out via `xargs -P "$JOBS"`, per-prompt: spawn codex with stdin-piped prompt → atomic answer move → manifest update. Idempotent skip-existing.

## Inputs

```bash
bash run-batch.sh --manifest <path> [--inputs <file>] [--template <tmpl>] [--answers-dir <dir>] [--concurrency N]
```

| Arg/env | Default | Notes |
|---|---|---|
| `--manifest <path>` | required | Path to orchestrate-codex manifest |
| `--inputs <file>` | n/a | Used only by the dispatcher when seeding the manifest; runtime reads from `prompts/`. |
| `--template <tmpl>` | n/a | Same — used at seed time. |
| `--answers-dir <dir>` | `answers/` (relative to workdir) | Where atomic answer files land |
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
| 2 | Manifest missing or unreadable |

## Behavior

- Skip-existing guard: `[ -s answers/<slug>.md ]` short-circuits before spawn. Re-running the runner is safe.
- Atomic answer move: codex writes to `mktemp -t answers-<slug>.XXXXXX`; only after exit 0 AND non-empty does the runner `mv -f` to the canonical path.
- Pairs `--json` with `-o <tmp>`: the temp is the source of truth for "did codex produce output." JSONL events flow to the `.jsonl` log for forensics.
- No retries; re-run for retries (rescue mode).

## Notes

Two runners over the same workdir would race on the skip-existing guard. The dispatcher refuses concurrent runs — bypass via `--force-new-run` is the user's responsibility.

After `--- all jobs finished ---`, run `audit-sizes.sh` to surface bottom-decile and below-floor entries.
