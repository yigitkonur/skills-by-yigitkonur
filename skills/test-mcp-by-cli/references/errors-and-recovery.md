# Errors and Recovery

Ground this file in installed `mcp-cli v0.3.0` behavior first. Use repo-source internals as implementation notes, not as a replacement for real command output.

## Exit codes

| Code | Constant | Category |
|---|---|---|
| 0 | — | Success |
| 1 | CLIENT_ERROR | Invalid arguments, config issues, user mistakes |
| 2 | SERVER_ERROR | Tool execution failed (server-side bug) |
| 3 | NETWORK_ERROR | Connection failed, timeout |
| 4 | AUTH_ERROR | Authentication failed (401/403) |
| 130 | — | SIGINT (Ctrl+C) |
| 143 | — | SIGTERM |

---

## Common error types

All errors follow the format:
```
Error [TYPE]: Message
  Details: Additional context
  Suggestion: How to fix it
```

### Config errors (exit 1)

| Error | Cause | Fix |
|---|---|---|
| `CONFIG_NOT_FOUND` | No config file in search paths | Create `mcp_servers.json` or use `-c` flag |
| `CONFIG_INVALID_JSON` | Broken JSON syntax | Fix: missing commas, unquoted keys, trailing commas |
| `CONFIG_MISSING_FIELD` | No `mcpServers` key | Add `{ "mcpServers": { ... } }` wrapper |
| `CONFIG_INVALID_SERVER` | Bad server config | Needs `command` (stdio) OR `url` (HTTP), not both, not neither |
| `MISSING_ENV_VAR` | `${VAR}` in config not set | Export the var or `MCP_STRICT_ENV=false` |

### Server errors

| Error | Exit | Cause | Fix |
|---|---|---|---|
| `SERVER_NOT_FOUND` | 1 | Server name not in config | Check spelling. Error lists all available servers |
| `SERVER_CONNECTION_FAILED` | 3 | Can't connect to server | See connection failure details below |

**Connection failure details depend on the error message:**
- `ENOENT` / `not found` → server binary not installed
- `ECONNREFUSED` → server not running or wrong URL
- `ETIMEDOUT` → network issue or slow server startup
- `Connection closed` → server crashed during startup (check stderr)
- `401` / `Unauthorized` → add auth headers to config
- `403` / `Forbidden` → check credentials and permissions

### Tool errors

| Error | Exit | Cause | Fix |
|---|---|---|---|
| `TOOL_NOT_FOUND` | 1 | Tool name doesn't exist | Check spelling. Error shows first 5 available tools |
| `TOOL_EXECUTION_FAILED` | 2 | Server-side execution error | Check arguments vs schema. See details for specific cause |
| `TOOL_DISABLED` | 1 | Tool blocked by config filtering | Remove from `disabledTools` or add to `allowedTools` |

### Argument errors (exit 1)

| Error | Cause | Fix |
|---|---|---|
| `INVALID_JSON_ARGUMENTS` | Malformed JSON input | Use single quotes: `'{"key": "value"}'` or heredoc |
| `MISSING_ARGUMENT` | Required arg not provided | Check command syntax in error suggestion |
| `AMBIGUOUS_COMMAND` | No subcommand (`mcp-cli server tool`) | Add `call` or `info` before server name |
| `UNKNOWN_SUBCOMMAND` | Wrong subcommand (`run`, `exec`) | Use `call`, `info`, or `grep` |
| `UNKNOWN_OPTION` | Unknown CLI flag | Server/tool are positional, not flags |
| `TOO_MANY_ARGUMENTS` | Extra positional args | `grep` takes exactly 1 pattern |
| `INVALID_TARGET` | Bad server/tool format | Use `server/tool` or `server tool` format |

### Smart subcommand suggestions

If you use a common alias, the error suggests the correct subcommand:
- `run`/`execute`/`exec`/`invoke` → suggests `call`
- `list`/`ls`/`get`/`show`/`describe` → suggests `info`
- `search`/`find`/`query` → suggests `grep`

---

## Common failure scenarios

### Stale daemon after rebuild

You changed server code, rebuilt, but calls hit the old process. The daemon caches connections for 60s.

```bash
MCP_NO_DAEMON=1 mcp-cli call server tool '{"param": "value"}'
```

Always use `MCP_NO_DAEMON=1` after rebuilds.

### `mcp-cli` with no args hangs

It connects ALL servers. One broken server blocks everything.

```bash
# Test one server at a time
mcp-cli info my-server
```

### Missing tool

Check tool filtering in config:
```json
"allowedTools": ["read_*"],
"disabledTools": ["delete_*"]
```

`disabledTools` wins over `allowedTools`. Glob: `*` (any chars), `?` (single char).

### Ambiguous command

```bash
mcp-cli server tool           # AMBIGUOUS_COMMAND
mcp-cli call server tool '{}' # correct
mcp-cli info server tool      # correct
```

Always use a subcommand: `call`, `info`, or `grep`.

---

## Daemon architecture

The daemon caches persistent MCP connections via Unix sockets to avoid reconnection overhead.

### How it works

1. First CLI call spawns a daemon process for the target server
2. Daemon creates a Unix socket at `/tmp/mcp-cli-<uid>/<server>.sock`
3. Subsequent calls reuse the socket instead of starting a new server process
4. After idle timeout (default 60s), daemon shuts down and cleans up

### Stale detection

On every call, the client validates:
1. PID file exists → process is actually running → config hash matches → socket exists
2. If any check fails: kill old daemon, spawn new one
3. Config hash is SHA-256 of the server config — changing ANY config field triggers a new daemon

### When stale connections happen

You rebuild server code but the daemon still holds the OLD process. Config hash didn't change (code changes don't affect config), so the daemon thinks everything is fine.

**Fix:** `MCP_NO_DAEMON=1` bypasses the daemon entirely.

### Debugging daemon state

```bash
# Check for running daemons
ls /tmp/mcp-cli-$(id -u)/*.pid 2>/dev/null

# See daemon interactions
MCP_DEBUG=1 mcp-cli call my-server my-tool '{}'

# Force kill a stuck daemon
kill $(cat /tmp/mcp-cli-$(id -u)/my-server.pid | jq -r .pid 2>/dev/null)
```

### Orphan cleanup

mcp-cli runs `cleanupOrphanedDaemons()` on every CLI startup — scans the socket directory and removes PID/socket files for processes that are no longer running.

---

## Release inconsistencies to know

These are worth knowing because they affect trust and troubleshooting:

- `mcp-cli --help` says `call` writes raw JSON to stdout. Real local calls match that.
- Some repo-source snapshots show extracted-text formatting for `call`, but that is not what the installed `v0.3.0` binary does.
- `UNKNOWN_OPTION` suggestions mention `-j/--json` and `-r/--raw`, but the installed `v0.3.0` binary rejects both flags.

When these conflict, trust the installed binary and real command output.

---

## Debugging commands

```bash
# Full protocol traffic
MCP_DEBUG=1 mcp-cli call server tool '{"param": "value"}'

# Lower timeout to catch hangs
MCP_TIMEOUT=30 mcp-cli call server tool '{"param": "value"}'

# Fresh connection (bypass daemon)
MCP_NO_DAEMON=1 mcp-cli call server tool '{"param": "value"}'

# All three for maximum visibility
MCP_DEBUG=1 MCP_NO_DAEMON=1 MCP_TIMEOUT=30 mcp-cli info my-server
```
