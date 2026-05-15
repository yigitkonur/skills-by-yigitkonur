# codex-json-filter.sh

Reads JSONL on stdin (typically `codex exec --json`), emits one human-readable line per event with a UTC timestamp prefix.

## Inputs

```bash
codex exec --json ... | bash codex-json-filter.sh [--level <minimal|normal|verbose>]
```

| Arg/env | Default | Effect |
|---|---|---|
| `--level <name>` (CLI flag) | (env wins if unset) | Verbosity tier; same values as `CODEX_FILTER_LEVEL`. CLI flag takes precedence over the env var when both are set. |
| `CODEX_FILTER_LEVEL` (env) | `normal` | Verbosity tier |
| `CODEX_FILTER_MAXLEN` (env) | `200` | Max chars per emitted line |
| stdin | required | JSONL stream from codex |

## Verbosity levels

Strict subset relation: `minimal ⊂ normal ⊂ verbose`. Tags emitted at each level:

| Level | Tags |
|---|---|
| `minimal` | `[START]`, `[CMD>]`, `[CMD✓]`, `[CMD✗]`, `[SAID]`, `[TURN<]`, `[ERR]` |
| `normal` (default) | minimal **+** `[TURN>]`, `[THINK]`, `[FILE]`, `[ITEM>]`, `[ITEM<]` |
| `verbose` | normal **+** `[?]` (unknown event types) and command-output tail on `[CMD✓]` |

`[ITEM>]` is `item.started` for non-command items; `[ITEM<]` is `item.completed` for items without a dedicated tag (mcp_tool_call, dynamic_tool_call, web_search, plan_update, todo_list — and any unknown item type at `verbose`). The `<`/`>` distinction marks start vs. complete.

`[ERR]` is emitted for both top-level `error` events AND `item.completed{type:error}` items (e.g. codex deprecation warnings) — the latter is surfaced at every verbosity level so the Monitor sees real failures per the coverage rule.

## Output line shape

```
<UTC-iso-z> [<TAG>] <one-line summary>
```

Examples:

```
02:08:25Z [START] thread=019e0a7e
02:08:26Z [CMD>] git status
02:08:26Z [CMD✓] exit=0 git status
02:08:28Z [THINK] Plan: 1) read schema, 2) ...
02:08:29Z [SAID] Done. New migration is at db/migrations/20260508_add_users.sql.
02:08:30Z [TURN<] tokens: in=8234 out=1567 cached=1200
02:08:31Z [ERR] `[features].codex_hooks` is deprecated. Use `[features].hooks` instead.
```

## Exit codes

| Code | Meaning |
|---|---|
| 0 | EOF on stdin (codex finished) **or** SIGPIPE (downstream closed pipe) |
| 1 | Internal error (rare) |
| 2 | Bad CLI flag |

## Behavior

- Pure bash `while IFS= read -r` loop with `jq` invoked per line. No `awk`, no `fflush()` — `printf` to a pipe is line-buffered when the downstream reads line-by-line, which is the Monitor case.
- SIGPIPE-tolerant: `trap 'exit 0' PIPE` plus per-emit `printf … 2>/dev/null || exit 0` means a downstream `head -1` (or any short-tailed consumer) closes the filter cleanly with exit 0, even under callers using `set -o pipefail`.
- Unrecognized event types appear as `[?] <type>` lines at `verbose` only.
- `[THINK]` lines truncate to first non-empty line of the reasoning text (codex reasoning is often multi-paragraph; one line per event keeps the Monitor concise).

## Notes

Verify SIGPIPE handling end-to-end:

```bash
printf '{"type":"thread.started","thread_id":"t1"}\n%.0s' {1..1000} \
  | bash codex-json-filter.sh \
  | head -1
echo "${PIPESTATUS[1]}"   # → 0
```

For post-mortem: the raw JSONL stream is preserved by the runner via `tee <jsonl-log>`. Re-run the filter against the saved log with `--level verbose` to surface details that `normal` hid.
