# Testing Flow

Grounded in the installed `philschmid/mcp-cli v0.3.0` binary and checked with real commands.

Use this flow before reporting any MCP server task as done.
If you built or modified a server and did not test with actual `call` commands, the task is not complete.

## Setup

```bash
# Install if missing
which mcp-cli || curl -fsSL https://raw.githubusercontent.com/philschmid/mcp-cli/main/install.sh | bash
```

Create `mcp_servers.json` in project root. See `references/configuration-and-arguments.md` for config format.

---

## The 8-phase testing flow (strict order)

### Phase 1 — Config setup

Create the config file. Hardcode secrets for testing. Do not use `${VAR}` substitution unless testing that specifically (strict mode errors on missing vars by default).

Stdio server:
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

HTTP server:
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

### Phase 2 — Connect

```bash
mcp-cli info my-server
```

If this fails, nothing else matters. Check the error type in `references/errors-and-recovery.md`:
- `CONFIG_NOT_FOUND` → config file missing or wrong path
- `CONFIG_INVALID_JSON` → broken JSON syntax
- `SERVER_CONNECTION_FAILED` → server can't start or respond
- `SERVER_NOT_FOUND` → server name not in config (error lists available servers)

### Phase 3 — Inventory

```bash
# List all tools with parameters
mcp-cli info my-server

# With descriptions for discovery
mcp-cli info my-server -d
```

Verify the server exposes expected tools. If a tool is missing, check `allowedTools`/`disabledTools` filtering in `references/configuration-and-arguments.md`.

### Phase 4 — Inspect each tool

```bash
# Space syntax
mcp-cli info my-server my-tool

# Slash syntax (equivalent)
mcp-cli info my-server/my-tool
```

Verify the input schema matches your implementation: required vs optional parameters, types, descriptions.

### Phase 5 — Call with valid input

```bash
mcp-cli call my-server my-tool '{"param": "value"}'
```

`call` outputs the raw MCP JSON envelope to stdout. Errors and server startup noise go to stderr.

For JSON responses that need further parsing:
```bash
mcp-cli call my-server my-tool '{"param": "value"}'

# Extract text content
mcp-cli call my-server my-tool '{"param": "value"}' | jq -r '.content[0].text'

# Parse JSON returned inside text content
mcp-cli call my-server my-tool '{"param": "value"}' | jq -r '.content[0].text' | jq '.some_field'
```

### Phase 6 — Break with bad input

```bash
# Missing required fields
mcp-cli call my-server my-tool '{}'

# Wrong types
mcp-cli call my-server my-tool '{"count": "not-a-number"}'

# Extra unknown fields
mcp-cli call my-server my-tool '{"valid": "input", "garbage": true}'
```

The server should return meaningful errors, not crash. Check exit code: `2` = server error (expected), `3` = network error (server crashed).

### Phase 7 — Verify without daemon cache

```bash
MCP_NO_DAEMON=1 mcp-cli call my-server my-tool '{"param": "value"}'
```

The daemon caches connections for 60 seconds. After rebuilding your server, always test with `MCP_NO_DAEMON=1` to prove the new build works.

### Phase 8 — Cross-tool regression

If you changed shared server code, verify other tools still work:
```bash
mcp-cli call my-server other-tool '{"param": "value"}'
```

---

## Verification checklist

Before reporting an MCP server task as done, every item must pass:

```
[ ] mcp-cli info my-server                              → server connects, tools listed
[ ] mcp-cli info my-server my-tool                      → schema correct for each tool
[ ] mcp-cli call my-server my-tool '{"valid": "input"}' → happy path returns expected data
[ ] mcp-cli call my-server my-tool '{}'                  → bad input returns error, not crash
[ ] MCP_NO_DAEMON=1 mcp-cli call my-server my-tool ...  → works without daemon cache
[ ] Other tools on the server still work                 → no cross-tool regression
```

If any item fails, the task is not done.
