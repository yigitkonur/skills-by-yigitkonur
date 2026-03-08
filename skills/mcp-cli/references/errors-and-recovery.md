# What Can Go Wrong (and Fixes)

## Stale daemon after rebuild

```bash
MCP_NO_DAEMON=1 mcp-cli call server tool '{"param":"value"}'
```

Always use `MCP_NO_DAEMON=1` after rebuilds.

## `mcp-cli` with no args hangs

It connects all servers, so one broken server can block everything.

```bash
mcp-cli info my-server
```

## Missing tool

Check filtering:

```json
"allowedTools": ["read_*"],
"disabledTools": ["delete_*"]
```

`disabledTools` overrides `allowedTools`.

## Ambiguous command

```bash
mcp-cli server tool           # ❌ AMBIGUOUS_COMMAND
mcp-cli call server tool '{}' # ✅
mcp-cli info server tool      # ✅
```

Always use `call`, `info`, or `grep`.

## Structured errors to recognize

| Code | Meaning | Fix |
|---|---|---|
| `AMBIGUOUS_COMMAND` | Missing subcommand | Add `call` or `info` |
| `UNKNOWN_SUBCOMMAND` | Wrong subcommand | Use `call`, `info`, or `grep` |
| `SERVER_NOT_FOUND` | Server not in config | Check config path/name |
| `TOOL_NOT_FOUND` | Tool missing | `mcp-cli info <server>` |
| `INVALID_JSON_ARGUMENTS` | Malformed JSON | Fix quoting/JSON |

## Retry behavior

Auto-retry transient failures (3x exponential backoff):

- `ECONNREFUSED`, `ETIMEDOUT`, etc.
- HTTP `429`, `502`, `503`, `504`

Fail fast:

- HTTP `401`, `403`
- validation/schema errors

## Debugging commands

```bash
MCP_DEBUG=1 mcp-cli call server tool '{"param":"value"}'
MCP_TIMEOUT=30 mcp-cli call server tool '{"param":"value"}'
MCP_NO_DAEMON=1 mcp-cli call server tool '{"param":"value"}'
```
