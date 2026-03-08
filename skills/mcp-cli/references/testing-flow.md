# MCP Server Testing with mcp-cli

Use this flow before reporting any MCP server task as done.

If you built or modified a server and did not test with actual `call` commands, the task is not complete.

## Setup

```bash
# Install if missing
which mcp-cli || curl -fsSL https://raw.githubusercontent.com/philschmid/mcp-cli/main/install.sh | bash
```

Create `mcp_servers.json` in project root.

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

Use `-c <path>` if config is not in current directory.
For testing, hardcode secrets unless you are explicitly testing `${VAR}` substitution.

---

## The testing flow (strict order)

### 1) CONNECT

```bash
# Global smoke check (can hang if any server is broken)
mcp-cli

# Recommended targeted check
mcp-cli info my-server
```

### 2) INVENTORY

```bash
mcp-cli info my-server
```

Verify expected tools are present.

### 3) INSPECT

```bash
mcp-cli info my-server my-tool      # space syntax
mcp-cli info my-server/my-tool      # slash syntax
```

Validate input schema shape, required fields, and types.

### 4) CALL (happy path)

```bash
mcp-cli call my-server my-tool '{"param":"value"}'
```

### 5) BREAK (error path)

```bash
mcp-cli call my-server my-tool '{}'
mcp-cli call my-server my-tool '{"wrong_type":123}'
```

Expect structured failures, not crashes/hangs.

---

## Verification checklist

```bash
# Server connects
mcp-cli info my-server

# Schema is correct
mcp-cli info my-server my-tool

# Happy path
mcp-cli call my-server my-tool '{"valid":"input"}'

# Error path
mcp-cli call my-server my-tool '{}'
mcp-cli call my-server my-tool '{"wrong_type":123}'

# Fresh connection (bypass daemon cache)
MCP_NO_DAEMON=1 mcp-cli call my-server my-tool '{"valid":"input"}'

# Shared-code safety check
mcp-cli call my-server other-tool '{"param":"value"}'
```

If any step fails, keep debugging.
