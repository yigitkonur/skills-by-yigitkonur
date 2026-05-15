# run-single.sh

Single mission wrapper. One `codex exec` invocation, JSONL stream piped through `codex-json-filter.sh` for live Monitor consumption.

## Inputs

```bash
bash run-single.sh --manifest <path> --out <answer-file> --jsonl <jsonl-log> \
    [--prompt-file <file> | --prompt <text>] [--cwd <dir>]
```

| Arg | Notes |
|---|---|
| `--manifest <path>` | One-entry manifest written by the dispatcher |
| `--out <file>` | Answer file (`-o` argument to codex) |
| `--jsonl <file>` | Where the raw JSONL stream is `tee`'d for forensics |
| `--prompt-file <file>` OR `--prompt <text>` | The prompt; one of the two required |
| `--cwd <dir>` | The worktree (or current cwd if reused). Defaults to `$PWD`. |
| `--entry-id <id>` | Manifest entry to update. Dispatcher uses `single`. |
| `--reuse-worktree` | Records that the selected cwd is an existing worktree; no new worktree is created. |
| `--dry-run` | Writes a synthetic answer/JSONL and marks the entry `done` without calling Codex. |

## Outputs

stdout (Monitor-compatible filtered events):

```
[START] thread=019e0a7e
[CMD>] git status
[CMD✓] git status (exit 0, 0.1s)
[THINK] Plan: 1) read schema, 2) ...
[SAID] Done. New migration is at db/migrations/...
[TURN<] tokens: in=8234 out=1567 cached=1200
DONE single (runtime=42s; answer=2841B)
--- all jobs finished ---
```

Side effects:
- `<answer-file>` written by codex (`-o`).
- `<jsonl-log>` populated by `tee`.
- Manifest entry transitions: `running` → `done | failed`.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Codex exited 0 AND `<answer-file>` non-empty |
| 1 | Codex exited non-zero |
| 2 | Codex exited 0 but `<answer-file>` is empty |

## Behavior

- Sources `codex-flags.sh` for `CODEX_FLAGS`.
- Runs roughly:
  ```
  codex exec "${CODEX_FLAGS[@]}" --json -o <out> -C <cwd> < <prompt> \
      2> <err.log> | tee <jsonl> | codex-json-filter.sh
  ```
  stderr is redirected to a separate `<err.log>` (NOT merged via `2>&1`)
  because codex deprecation warnings on stderr would otherwise corrupt the
  JSONL pipe. The runner's manifest entry sets `log_path=<err.log>`,
  `jsonl_path=<jsonl>`, `answer_path=<out>` per `manifest-contract.md`.
- Pipefail-safe: codex's exit code is captured via `${PIPESTATUS[1]}` despite the pipe.
- Manifest writes via `manifest-update.sh` for atomicity.

## Notes

The pipe is the Monitor: events arrive line-buffered as codex emits them. Use `LEVEL=verbose` env to surface `[THINK]`, `[FILE]`, full command output via `codex-json-filter.sh`.

If codex's JSONL stream loses the terminal `agent_message phase=final_answer` event (MCP-active dropout, see `references/universal/json-streaming.md`), the runner uses the `<answer-file>` content as the source of truth. Mark `done` with advisory `last_error="json_event_dropped"` when this happens.
