# Configuration and JSON Arguments

## Config essentials

`mcp-cli` reads `mcp_servers.json` from current directory unless `-c` is provided.

### Stdio server

```json
{
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["./dist/index.js"],
      "env": { "API_KEY": "test-key-123" }
    }
  }
}
```

### HTTP server

```json
{
  "mcpServers": {
    "my-server": {
      "url": "https://mcp.example.com/mcp",
      "headers": { "Authorization": "Bearer token" }
    }
  }
}
```

Use `-c <path>` when config is elsewhere.

## Tool filtering

`disabledTools` wins over `allowedTools`.

```json
{
  "mcpServers": {
    "my-server": {
      "allowedTools": ["read_*"],
      "disabledTools": ["delete_*"]
    }
  }
}
```

## JSON arguments: safe patterns

```bash
# Inline
mcp-cli call server tool '{"key":"value"}'

# Stdin (auto-detected)
echo '{"key":"value"}' | mcp-cli call server tool

# Explicit stdin mode
mcp-cli call server tool -

# Heredoc (best for complex payload)
mcp-cli call server tool <<EOF
{"content":"text with 'quotes' and special chars"}
EOF

# From file
cat args.json | mcp-cli call server tool

# Build with jq
jq -n '{"query":"test","limit":10}' | mcp-cli call server tool
```

Prefer stdin/heredoc for complex JSON.

## Config path precedence

1. `-c` / `--config`
2. `MCP_CONFIG_PATH`
3. `./mcp_servers.json`
4. `~/.mcp_servers.json`
5. `~/.config/mcp/mcp_servers.json`
