# run-fleet.sh

Exec mode bounded-concurrency runner. Reads the manifest, fans out queued/failed entries via `xargs -P "$JOBS"`, per-task: setup-worktree → spawn `codex exec` → auto-commit → post-verify → manifest update.

## Inputs

```bash
bash run-fleet.sh --manifest <manifest-path> [--concurrency N] [--only id,id] [--dry-run]
```

| Arg/env | Default | Notes |
|---|---|---|
| `--manifest <path>` | required | Path to the orchestrate-codex manifest |
| `--concurrency N` / `JOBS=N` | 5 | Per-mode default; soft gate above 20 |
| `--only id,id` | unset | Rescue subset replay. |
| `--i-have-measured <why>` | unset | Required above concurrency 20; refused above 100. |
| `--dry-run` / `DRY_RUN=1` | off | Print planned `codex exec` command per task; do NOT spawn |
| `COMMIT_LEVEL=<1|2|3>` | 2 | 1=subject only / 2=subject+body / 3=subject+body+diffstat |

## Outputs

stdout (one line per state transition; Monitor-compatible):

```
START 01-search-rewrite
DONE 01-search-rewrite (commits=3, post_verify=0)
FAIL 02-cache-eviction (codex_exit=1, see logs/02-cache-eviction.log)
SKIP 03-already-done
--- all jobs finished ---
```

Per-task log file at `<monitor-root>/<entry-id>.log`.
Per-task JSONL events at `<monitor-root>/<entry-id>.jsonl`.

Manifest mutations:
- On task start: `entries[i].status=running`, `started_at`, `attempts++`.
- On `thread.started` event: `entries[i].codex_thread_id`.
- On task finish: `status` → `done` or `failed`; `exit_code`; `finished_at`; `mode_state.post_verify_exit`.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | All entries reached terminal state (any mix of done/failed/skipped) |
| 1 | Manifest missing or unreadable |
| 2 | `codex` or `jq` missing |
| 3 | Invalid concurrency, missing entries, or cap above 20 without `--i-have-measured` |

## Behavior

- Idempotent: skips entries with `status=done`. Re-running picks up `queued` and `failed`; rescue can limit that replay with `--only`.
- Auto-commit: if codex didn't commit (no commits past baseline) but worktree has changes, the wrapper commits them with a generated `<emoji> <type>(<scope>): <task-id> auto-commit` message.
- Post-verify: auto-detects `tsc --noEmit` (if `tsconfig.json`), `mypy .` (if `pyproject.toml` with mypy), `cargo check` (if `Cargo.toml`), `go vet ./...` (if `go.mod`). Override per-task via `tasks.json` `post_verify_cmd`.
- Failure surfaces: codex exit non-zero / no commits despite exit 0 / dirty worktree post-run / post-verify failed → `status=failed` with descriptive `last_error`.

## Notes

The runner does NOT push or auto-merge. Each task's branch is committed locally; the user pushes and merges using their normal flow.

Auto-commit is advisory: the commit lands even if post-verify fails (the marker `mode_state.post_verify_exit` records the failure). The user reviews the commit and decides whether to fix manually or rescue redo.

`--dry-run` prints the exact `codex exec` command line per task without spawning. Use this to verify flags before a long-running fleet.
