# codex-json-filter.sh

Reads JSONL on stdin (typically `codex exec --json`), emits one human-readable line per event with a UTC timestamp prefix.

## Inputs

```bash
codex exec --json ... | bash codex-json-filter.sh [--level <minimal|normal|verbose>]
```

| Arg/env | Default | Effect |
|---|---|---|
| `--level <name>` / `LEVEL=<name>` | `normal` | Verbosity tier |
| stdin | required | JSONL stream from codex |

## Verbosity levels

| Level | Includes |
|---|---|
| `minimal` | `[START]`, `[SAID]`, `[ERR]` only |
| `normal` (default) | minimal + `[CMD>]`, `[CMD✓]`, `[CMD✗]`, `[TURN<]` |
| `verbose` | normal + `[THINK]`, `[FILE]`, `[MCP>]`, `[WEB]`, full `aggregated_output` |

## Output line shape

```
<UTC-iso-z> [<TAG>] <one-line summary>
```

Examples:

```
02:08:25Z [START] thread=019e0a7e
02:08:26Z [CMD>] git status
02:08:26Z [CMD✓] git status (exit 0, 0.1s)
02:08:28Z [THINK] Plan: 1) read schema, 2) ...
02:08:29Z [SAID] Done. New migration is at db/migrations/20260508_add_users.sql.
02:08:30Z [TURN<] tokens: in=8234 out=1567 cached=1200
```

## Exit codes

| Code | Meaning |
|---|---|
| 0 | EOF on stdin (codex finished) |
| 1 | Bad input (non-JSONL line; logged to stderr; the bad line is skipped) |

## Behavior

- Uses `awk` with `fflush()` per line so events flow through the pipe as they arrive.
- SIGPIPE-tolerant: when the downstream consumer (e.g. `head`, the Monitor) closes the pipe, the filter exits 0.
- Unrecognized event types pass through as `[?] <type>` lines.
- `[THINK]` lines truncate to first line of `text` (codex reasoning is often multi-paragraph; one line per event keeps the Monitor concise).

## Notes

Verify line buffering with the synthetic stream test in `references/universal/codex-flags.md`. Without proper buffering, the filter holds events for minutes; the Monitor sees nothing.

For post-mortem: the raw JSONL stream is preserved by the runner via `tee <jsonl-log>`. Re-run the filter against the saved log with `--level verbose` to surface details that `normal` hid.
