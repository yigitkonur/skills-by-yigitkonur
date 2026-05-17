# Scripting and Automation

Use `--json` for commands that support machine-readable output.
Do not assume it applies to interactive flows such as `login` or `shell`.

## Core pattern

```bash
set -euo pipefail
RESULT=$(mcpc --json @research-test tools-call search-reddit '{"queries":["OpenAI MCP"]}')
printf '%s' "$RESULT" | jq -e '.isError != true' >/dev/null
```

## Rules

- check shell exit status for CLI or transport failures
- also check `isError` inside JSON payloads for MCP-level failures
- prefer `mcpc @session help` or `mcpc grep` before bespoke parsing logic
- keep session names stable when you want cache or reconnect behavior
- use temporary session names for destructive or isolated tests

## Error channel detail

When a command fails before it returns a normal JSON payload, the structured error object is typically emitted on `stderr`.
That matters for Python wrappers and CI harnesses because a nonzero failure is not the same thing as an MCP payload with `isError: true`.

## Good automation targets

- `mcpc --json`
- `mcpc --json @session`
- `mcpc --json @session tools-list`
- `mcpc --json @session tools-call ...`
- `mcpc --json grep <pattern>`
- `mcpc --json @session tasks-list`
