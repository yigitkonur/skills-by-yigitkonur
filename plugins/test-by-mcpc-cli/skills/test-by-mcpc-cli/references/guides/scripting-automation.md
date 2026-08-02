# Scripting and Automation

Verified against mcpc 0.6.0.

Use `--json` for commands that support machine-readable output.
Do not assume it applies to interactive flows such as `login`.
(The interactive `shell` command was removed in 0.4.0 — it no longer exists in any form.)

## Core pattern

```bash
set -euo pipefail
RESULT=$(mcpc --json @research-test tools-call web-search '{"queries":["OpenAI MCP"]}')
printf '%s' "$RESULT" | jq -e '.isError != true' >/dev/null
```

## Exit-code contract (since 0.5.0)

`tools-call` and `tasks-result` exit **2** whenever the MCP round-trip produced
`isError: true` (schema rejection, unknown tool, runtime tool failure — all land
here uniformly), so `$? -eq 2` is a reliable signal for those two commands
specifically. Pure CLI usage errors that never reach the server (missing argument,
`restart` on a nonexistent session) exit **1**; `0` otherwise, including truncated
(`--max-chars`) output and empty-result states. Other command families don't model
"found nothing" as `isError` — for those, keep checking the JSON payload, not the
exit code.

## Rules

- for `tools-call`/`tasks-result`, the exit code alone is sufficient (contract above)
- for other commands, check `isError` inside the JSON payload, not just exit status
- prefer `mcpc @session --help` or `mcpc grep <pattern>` before bespoke parsing logic
- keep session names stable when you want cache or reconnect behavior
- use temporary session names for destructive or isolated tests
- errors that fail before a normal JSON payload forms are typically emitted on `stderr`

## Good automation targets

- `mcpc --json`
- `mcpc --json @session`
- `mcpc --json @session tools-list`
- `mcpc --json @session tools-call ...`
- `mcpc --json @session tasks-result <taskId>`
- `mcpc --json grep <pattern>`
- `mcpc --json @session tasks-list`
