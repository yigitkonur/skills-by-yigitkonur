# Async Work Boundary

Use this page to avoid inventing task commands that `mcpc 0.1.11` does not expose.

## Current CLI surface

`mcpc 0.1.11` does **not** support these commands or flags:

```bash
mcpc @session tools-call slow-tool --task
mcpc @session tools-call slow-tool --task --detach
mcpc @session tasks-list
mcpc @session tasks-get <taskId>
mcpc @session tasks-cancel <taskId>
```

If you run them, Commander exits with a client error such as:

- `Unknown option: --task`
- `unknown command 'tasks-list'`

## What to do instead

### Long-running tool calls

Use a longer timeout and treat the call as synchronous:

```bash
mcpc @session tools-call slow-tool arg:=value --timeout 900
```

If the call returns JSON, still check `.isError` because tool-level failures keep exit code `0`:

```bash
mcpc --json @session tools-call slow-tool arg:=value --timeout 900 | jq '.isError // false'
```

### Background work

If the server itself exposes job IDs through a normal tool, use that server-specific workflow rather than generic `tasks-*` commands. Example pattern:

```bash
JOB=$(mcpc --json @session tools-call start-export format:=csv | jq -r '.content[0].text')
```

Then poll through whatever server-specific tool the schema exposes.

### Progress and notifications

`progress` notifications may still exist inside the MCP protocol, but `mcpc 0.1.11` does not provide a generic task runner, detach flow, or polling surface for them.

## Operator rule

Before writing any async testing instructions, check `mcpc --help`. If the command is not listed there, do not assume the CLI can drive it.
