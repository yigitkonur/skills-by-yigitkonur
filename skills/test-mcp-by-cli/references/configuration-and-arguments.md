# Configuration and JSON Arguments

Source-verified against `philschmid/mcp-cli` v0.3.0 (`src/config.ts`).

## Config file resolution order

mcp-cli searches these paths in order, using the first one found:

1. Path from `-c`/`--config` flag or `MCP_CONFIG_PATH` env var
2. `./mcp_servers.json` (current working directory)
3. `~/.mcp_servers.json`
4. `~/.config/mcp/mcp_servers.json`

If no config is found: `Error [CONFIG_NOT_FOUND]`.

## Config structure

```json
{
  "mcpServers": {
    "server-name": { ... }
  }
}
```

The top-level `mcpServers` object is required. If missing: `Error [CONFIG_MISSING_FIELD]`.

## Stdio server config

```json
{
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["./dist/index.js"],
      "env": { "API_KEY": "test-key-123" },
      "cwd": "/path/to/workdir",
      "allowedTools": ["read_*", "list_*"],
      "disabledTools": ["delete_*"]
    }
  }
}
```

| Field | Required | Type | Description |
|---|---|---|---|
| `command` | Yes | string | Command to start the server |
| `args` | No | string[] | Arguments passed to the command |
| `env` | No | object | Extra environment variables (merged with process.env) |
| `cwd` | No | string | Working directory for the server process |
| `allowedTools` | No | string[] | Glob patterns — only matching tools visible |
| `disabledTools` | No | string[] | Glob patterns — matching tools hidden |

## HTTP server config

```json
{
  "mcpServers": {
    "my-server": {
      "url": "https://mcp.example.com/mcp",
      "headers": { "Authorization": "Bearer token" },
      "timeout": 30000,
      "allowedTools": ["search_*"],
      "disabledTools": ["admin_*"]
    }
  }
}
```

| Field | Required | Type | Description |
|---|---|---|---|
| `url` | Yes | string | Server URL (StreamableHTTP transport) |
| `headers` | No | object | HTTP headers added to all requests |
| `timeout` | No | number | Per-server timeout override |
| `allowedTools` | No | string[] | Glob patterns — only matching tools visible |
| `disabledTools` | No | string[] | Glob patterns — matching tools hidden |

A server must have EITHER `command` (stdio) OR `url` (HTTP), never both. Both present: `Error [CONFIG_INVALID_SERVER]`.

## Tool filtering rules

1. If `disabledTools` is specified, matching tools are excluded
2. If `allowedTools` is specified, only matching tools are included
3. **`disabledTools` takes precedence over `allowedTools`** — a tool in both lists is disabled
4. If neither is specified, all tools are visible
5. Glob: `*` (any chars), `?` (single char), case-insensitive

```json
"allowedTools": ["read_*", "list_*"],
"disabledTools": ["delete_*", "drop_*"]
```

### Debugging missing tools

If a tool you expect doesn't appear:

1. Check `disabledTools` — it wins over everything
2. Check `allowedTools` — if set, tool must match a pattern
3. Use `mcp-cli info <server> -d` to see what's actually exposed
4. Remove filtering temporarily to confirm the tool exists

## Environment variable substitution

Config values support `${VAR_NAME}` syntax:

```json
{
  "mcpServers": {
    "my-server": {
      "url": "https://api.example.com/mcp",
      "headers": { "Authorization": "Bearer ${API_TOKEN}" }
    }
  }
}
```

### Strict mode (default)

`MCP_STRICT_ENV=true` (default): referencing an unset env var is a hard error:

```
Error [MISSING_ENV_VAR]: Missing environment variable: ${API_TOKEN}
  Suggestion: export API_TOKEN="value" or set MCP_STRICT_ENV=false
```

### Non-strict mode

`MCP_STRICT_ENV=false`: warns instead of erroring. Missing vars resolve to empty strings.

### Testing recommendation

For testing, hardcode secrets directly in the config. Only use `${VAR}` when testing that specific feature or in CI/CD.

---

## JSON arguments: all methods

### 1. Inline (simple cases)

```bash
mcp-cli call server tool '{"key": "value"}'
```

Single quotes outer, double quotes inner.

### 2. Stdin pipe (auto-detected)

```bash
echo '{"key": "value"}' | mcp-cli call server tool
```

No `-` flag needed. Auto-detected when stdin is not a TTY.

### 3. Heredoc (complex payloads)

```bash
mcp-cli call server tool <<EOF
{"content": "text with 'quotes' and special chars"}
EOF
```

Best for complex payloads. Avoids all shell quoting issues.

### 4. From file

```bash
cat args.json | mcp-cli call server tool
```

### 5. Build with jq

```bash
jq -n '{"query": "test", "limit": 10}' | mcp-cli call server tool
```

### 6. No arguments (empty object)

```bash
mcp-cli call server tool
```

When no JSON is provided and stdin is a TTY, an empty object `{}` is passed.

| Method | Best for |
|---|---|
| Inline `'{}'` | Simple key-value pairs, no special characters |
| Stdin pipe | Chaining from other commands |
| Heredoc | Complex payloads with quotes, newlines, special chars |
| File | Reusable test fixtures |
| jq | Dynamic argument construction |

### Common pitfall

```bash
# WRONG — shell interprets the double quotes
mcp-cli call server tool {"key": "value"}

# RIGHT — single quotes protect the JSON
mcp-cli call server tool '{"key": "value"}'
```
