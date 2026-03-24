# Stdio Transport Testing

Test MCP servers that run as local processes communicating over stdin/stdout.

## When to use stdio

- The MCP server is an npm package, Python script, or compiled binary
- The server runs locally on your machine
- No HTTP endpoint exists — communication is via process pipes
- Examples: `@modelcontextprotocol/server-filesystem`, `@modelcontextprotocol/server-github`

## Config file format

Stdio servers are defined in JSON config files compatible with Claude Desktop and VS Code.

### Minimal config

```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-filesystem", "/path/to/dir"]
    }
  }
}
```

### Full config with all options

```json
{
  "mcpServers": {
    "server-name": {
      "command": "node",
      "args": ["./dist/index.js", "--port", "3000"],
      "env": {
        "API_KEY": "${API_KEY}",
        "DEBUG": "true",
        "NODE_ENV": "development"
      },
      "timeout": 60
    }
  }
}
```

### Config fields

| Field | Required | Type | Description |
|---|---|---|---|
| `command` | Yes | string | Executable to run (e.g., `npx`, `node`, `python`, `./binary`) |
| `args` | No | string[] | Arguments passed to the command |
| `env` | No | object | Environment variables for the process |
| `timeout` | No | number | Timeout in seconds |

### Environment variable substitution

Config files support `${VAR_NAME}` syntax for environment variable substitution:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}",
        "WORKING_DIR": "${PWD}"
      }
    }
  }
}
```

Variables are resolved at connect time. Missing variables resolve to empty string.

### Config file locations

mcpc accepts any file path. Common locations:

```bash
# VS Code MCP config (standard)
~/.vscode/mcp.json

# Custom test config
/tmp/mcp-test-config.json

# Project-local config
./mcp-servers.json
```

## Connecting to stdio servers

```bash
# Connect using config file:entry-name format
mcpc /path/to/config.json:server-name connect @session-name

# Examples
mcpc ~/.vscode/mcp.json:filesystem connect @fs-test
mcpc ./test-config.json:my-server connect @dev-test
```

### Multiple servers from same config

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-filesystem", "/tmp"]
    },
    "github": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-github"],
      "env": { "GITHUB_TOKEN": "${GITHUB_TOKEN}" }
    }
  }
}
```

```bash
# Connect to each independently
mcpc ./config.json:filesystem connect @fs
mcpc ./config.json:github connect @gh
```

## Testing stdio servers step by step

### 1. Verify the command works standalone

Before using mcpc, run the server command directly to check for errors:

```bash
# Run the server command directly
npx @modelcontextprotocol/server-filesystem /tmp/test-dir

# Expected: server starts and waits for JSON-RPC on stdin
# If you see errors here, fix them before using mcpc
# Press Ctrl+C to stop
```

### 2. Connect via mcpc

```bash
mcpc ./config.json:my-server connect @test
```

### 3. Check server health

```bash
mcpc @test ping
# Expected: "pong" or similar success response

mcpc @test help
# Shows server name, version, and capabilities
```

### 4. Discover capabilities

```bash
# List all tools
mcpc @test tools --full

# List resources
mcpc @test resources

# List prompts
mcpc @test prompts
```

### 5. Test tool calls

```bash
# Call a tool
mcpc @test tools-call read_file path:=/tmp/test-dir/test.txt

# With JSON output for verification
mcpc @test tools-call read_file path:=/tmp/test-dir/test.txt --json
```

### 6. Cleanup

```bash
mcpc @test close
# This kills the child process
```

## Debugging stdio issues

### Server stderr

By default, server stderr is suppressed. Enable verbose mode to see it:

```bash
mcpc ./config.json:my-server connect @debug --verbose
mcpc @debug tools-list --verbose
```

Or check bridge logs:

```bash
cat ~/.mcpc/logs/bridge-test.log
```

### Common stdio problems

| Symptom | Cause | Fix |
|---|---|---|
| "Failed to connect" on connect | Command not found or fails to start | Run command manually: `npx @package/name` |
| Hangs on connect | Server not sending init response | Check server implements MCP handshake correctly |
| "Not connected" errors | Bridge process crashed | `mcpc @session restart` or reconnect |
| Tool call timeout | Server processing slowly | `--timeout 600` or check server logs |
| Empty tool list | Server not registering tools | Check server code, verify with `--verbose` |
| Wrong Node.js version | Server requires specific Node | Use `nvm use 20` before connecting |
| Missing env vars | `${VAR}` resolves to empty | Export vars before connecting: `export API_KEY=xxx` |

### Process inspection

```bash
# Check if bridge process is running
mcpc
# Shows session list with status indicators:
# 🟢 live — running and responding
# 🟡 disconnected — bridge alive but server not responding
# 🟡 crashed — bridge process died
# 🔴 unauthorized / expired — auth issue

# Check bridge PID
cat ~/.mcpc/sessions.json | jq '.[] | {name, pid, status}'

# Check bridge socket exists
ls -la ~/.mcpc/bridges/
```

## Example: Testing the filesystem server

```bash
# 1. Create test directory with test files
mkdir -p /tmp/mcp-test && echo "hello world" > /tmp/mcp-test/test.txt

# 2. Create config
cat > /tmp/fs-config.json << 'EOF'
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-filesystem", "/tmp/mcp-test"]
    }
  }
}
EOF

# 3. Connect
mcpc /tmp/fs-config.json:filesystem connect @fs-test

# 4. Discover
mcpc @fs-test tools
mcpc @fs-test resources

# 5. Test reading a file
mcpc @fs-test tools-call read_file path:=/tmp/mcp-test/test.txt

# 6. Test with JSON output
mcpc @fs-test tools-call read_file path:=/tmp/mcp-test/test.txt --json | jq '.content'

# 7. Cleanup
mcpc @fs-test close
```

## Example: Testing a Python MCP server

```json
{
  "mcpServers": {
    "my-python-server": {
      "command": "python",
      "args": ["-m", "my_mcp_server"],
      "env": {
        "PYTHONPATH": "${PWD}/src"
      }
    }
  }
}
```

```bash
# Verify Python server starts
python -m my_mcp_server
# Ctrl+C to stop

# Connect via mcpc
mcpc ./config.json:my-python-server connect @py-test
mcpc @py-test tools --full
mcpc @py-test tools-call my-tool arg:=value
mcpc @py-test close
```
