# diagnose-agent-stuck.sh

Read-only diagnostics for an `MCPAgent` that is not progressing.

## Usage

```bash
bash scripts/diagnose-agent-stuck.sh --target /path/to/project
```

Optionally check one explicit server command:

```bash
bash scripts/diagnose-agent-stuck.sh --target /path/to/project --server-command "npx -y @modelcontextprotocol/server-filesystem ."
```

## What it checks

- Node.js version
- Installed/latest `mcp-use` and latest npm engine range
- Provider environment variable presence by name only
- `maxSteps`, `autoInitialize`, and `manageConnector` mentions
- Cleanup API patterns
- MCP server command reachability by first command name
- Plain-string `run()` calls
- `streamEvents()` structured-output handling
- `step.observation` reliance

The script never prints environment variable values and does not execute MCP server commands.
