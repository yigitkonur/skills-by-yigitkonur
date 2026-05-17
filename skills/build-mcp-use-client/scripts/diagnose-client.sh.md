# diagnose-client.sh

Read-only diagnostic for stuck, disconnected, or suspicious `mcp-use` client projects.

## Usage

```bash
bash scripts/diagnose-client.sh
bash scripts/diagnose-client.sh /path/to/project
```

The script scans common TypeScript/JavaScript/JSON files while skipping `node_modules`, `.git`, `dist`, `build`, and `coverage`.

## What It Reports

| Area | Signals |
|---|---|
| package state | package manager lockfiles, `mcp-use` dependency, useful package scripts |
| imports | `mcp-use`, `mcp-use/browser`, `mcp-use/react`, direct `@modelcontextprotocol/sdk` |
| config | `mcp.json`, `mcp.config.*`, `.vscode/mcp.json` |
| React mistakes | `mcp.status`, `persistenceProvider`, hooks without `McpClientProvider` |
| cleanup | `closeAllSessions`, `client.close`, `SIGINT`/`SIGTERM` handlers |
| auth | files containing auth/header patterns without printing secret values |
| transport | WebSocket references that should not be used for MCP clients |
| resilience | `autoReconnect`, `reconnectionOptions`, timeouts, progress resets, aborts |

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | Diagnostic completed |
| `2` | Project root not found or inaccessible |
| `3` | `package.json` exists but is not parseable JSON |

## Security Boundary

The script prints auth-related file paths only. It does not print matching source lines, bearer tokens, custom header values, or environment variable values.

## Follow-Up

Use the suggested references at the bottom of the output. The script is an index into the skill, not a proof that the client works at runtime.
