# Output Formatting

## Human mode vs JSON mode

Use human mode for exploration and JSON mode for assertions.

```bash
mcpc @research-test help
mcpc --json @research-test help
```

## What JSON mode gives you

- `mcpc --json` returns `sessions` and `profiles`
- `mcpc --json @session` returns session info, capabilities, and discovered tools
- `mcpc --json @session tools-list` returns tool arrays
- `mcpc --json @session grep search` returns per-session matches plus totals
- `mcpc --json @session tasks-list` returns a `tasks` array

## Error channel behavior

When a command fails before producing a normal JSON payload, the structured error output is typically emitted on `stderr`.
That matters for wrappers and CI harnesses.

## Exit-code rule

A zero exit code does not prove the MCP operation succeeded.
MCP-level failures can still arrive as payloads with `isError: true`.

## `--full` note

`tools-list --full` matters in human mode.
When you are already in JSON mode, you often have enough schema detail without extra formatting flags.
