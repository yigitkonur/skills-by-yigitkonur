# mcpc Architecture Reference

System overview, source code map, transport layer, configuration system, error hierarchy, and data directory layout for mcpc v0.1.11.

## System overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           User (terminal)                               │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │ CLI command
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  mcpc CLI (short-lived process)                                         │
│  ┌───────────┐  ┌──────────────┐  ┌──────────────────┐                 │
│  │  Parser   │─▶│ Command      │─▶│  BridgeClient    │                 │
│  │ (yargs)   │  │ Router       │  │  (socket IPC)    │                 │
│  └───────────┘  └──────────────┘  └────────┬─────────┘                 │
└────────────────────────────────────────────┬────────────────────────────┘
                                             │ Unix socket
                                             │ ~/.mcpc/bridges/<session>.sock
                                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  mcpc-bridge (persistent daemon, one per session)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────────────┐ │
│  │ IPC Server   │─▶│  McpClient   │─▶│ StreamableHTTPClientTransport │ │
│  │ (socket)     │  │  (MCP SDK)   │  │ or StdioClientTransport       │ │
│  └──────────────┘  └──────────────┘  └──────────────┬───────────────┘ │
│  ┌──────────────┐  ┌──────────────┐                  │                 │
│  │ Keepalive    │  │ OAuthToken   │                  │                 │
│  │ Timer (30s)  │  │ Manager      │                  │                 │
│  └──────────────┘  └──────────────┘                  │                 │
└──────────────────────────────────────────────────────┬─────────────────┘
                                                       │ HTTP / stdio
                                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  MCP Server (remote HTTP or local stdio process)                        │
└─────────────────────────────────────────────────────────────────────────┘
```

Key design principle: the CLI process is stateless and exits after each command. All persistent state (connections, auth tokens, session tracking) lives in the bridge daemon and the filesystem.

## Source code map

```
src/
├── index.ts                    # CLI entry point, yargs setup, command registration
├── commands/                   # One file per CLI command
│   ├── connect.ts              # mcpc <target> connect @session
│   ├── close.ts                # mcpc @session close
│   ├── restart.ts              # mcpc @session restart
│   ├── shell.ts                # mcpc @session shell (interactive REPL)
│   ├── ping.ts                 # mcpc @session ping
│   ├── help.ts                 # mcpc @session help (server info)
│   ├── tools.ts                # tools, tools-list, tools-get, tools-call
│   ├── resources.ts            # resources, resources-list, resources-read, subscribe
│   ├── prompts.ts              # prompts, prompts-list, prompts-get
│   ├── tasks.ts                # tasks-list, tasks-get, tasks-cancel (experimental)
│   ├── login.ts                # mcpc login <server> (OAuth flow)
│   ├── logout.ts               # mcpc logout <server>
│   ├── clean.ts                # mcpc clean [sessions|profiles|logs|all]
│   ├── x402.ts                 # mcpc x402 (payment wallet, experimental)
│   └── logging.ts              # mcpc @session logging-set-level
├── bridge/
│   ├── index.ts                # Bridge daemon entry point
│   ├── bridge-server.ts        # Unix socket IPC server
│   ├── mcp-client.ts           # MCP SDK client wrapper
│   ├── transport.ts            # Transport initialization (HTTP or stdio)
│   ├── keepalive.ts            # 30-second ping timer
│   └── auth/
│       ├── oauth-token-manager.ts  # Token refresh with keychain sync
│       └── credential-store.ts     # Keychain + file fallback abstraction
├── client/
│   ├── bridge-client.ts        # CLI-side IPC: connect to socket, send/receive
│   ├── session-client.ts       # High-level session operations with retry
│   └── session-manager.ts      # sessions.json CRUD with file locking
├── config/
│   ├── config-loader.ts        # Load and parse JSON config files
│   ├── env-substitution.ts     # ${VAR} replacement in config values
│   └── url-resolver.ts         # Bare hostname → full URL resolution
├── auth/
│   ├── keychain.ts             # @napi-rs/keyring wrapper
│   ├── profiles.ts             # profiles.json management
│   └── oauth-flow.ts           # Browser-based OAuth 2.1 flow
├── errors/
│   └── index.ts                # Error class hierarchy (McpError, ClientError, etc.)
├── output/
│   ├── formatter.ts            # Human-readable vs JSON output
│   ├── colors.ts               # Terminal color utilities
│   └── table.ts                # Table formatting for tools/resources lists
├── proxy/
│   ├── proxy-server.ts         # MCP proxy HTTP server
│   └── proxy-auth.ts           # Proxy bearer token validation
└── utils/
    ├── consolidate-sessions.ts # Startup: mark dead PIDs as crashed
    ├── pid.ts                  # Process liveness checks
    ├── file-lock.ts            # Atomic file writes with locking
    └── platform.ts             # OS-specific helpers (open browser, etc.)
```

## Transport layer

### StreamableHTTPClientTransport

mcpc exclusively uses the Streamable HTTP transport for HTTP servers (protocol version `2025-11-25`). Legacy SSE transport is not supported — servers must implement the current MCP spec.

### Connection parameters

| Parameter | Value | Description |
|---|---|---|
| Initial reconnect delay | 1 second | First retry after disconnect |
| Backoff factor | 2x | Exponential growth |
| Max reconnect delay | 30 seconds | Cap on backoff |
| Max retries | 10 | Total reconnection attempts before giving up |
| Request queue max | 100 | Maximum queued requests during reconnection |
| Request timeout | 3 minutes | Per-request timeout for queued requests |

### Session resumption

For stateful servers, the transport maintains the `MCP-Session-Id` header received during initialization. On reconnection:

1. Transport sends the stored `MCP-Session-Id` in the request header
2. If server accepts (200): session resumes, state preserved
3. If server rejects (404): session expired, bridge status set to `expired`, CLI auto-restarts on next command

SSE stream resumption uses `Last-Event-ID` semantics — the client sends the last received event ID to resume from that point, avoiding message loss during reconnection.

### Required HTTP headers

Every request from the bridge to the MCP server includes:

| Header | Value | Purpose |
|---|---|---|
| `MCP-Protocol-Version` | `2025-11-25` | Declares protocol version |
| `MCP-Session-Id` | `<session-id>` | Session tracking (after init) |
| `Accept` | `application/json, text/event-stream` | Accepted response formats |
| `Content-Type` | `application/json` | Request body format |

Plus any custom headers from `--header` flags (e.g., Authorization).

### Proxy-aware fetch

The transport respects standard proxy environment variables:

- `HTTP_PROXY` / `http_proxy`: proxy for HTTP requests
- `HTTPS_PROXY` / `https_proxy`: proxy for HTTPS requests
- `NO_PROXY` / `no_proxy`: comma-separated list of hosts that bypass the proxy

Proxy support is implemented via Node.js native fetch with the `undici` ProxyAgent.

## Config system

### Format

mcpc uses a Claude Desktop / VS Code compatible JSON format for stdio server definitions:

```json
{
  "mcpServers": {
    "entry-name": {
      "command": "node",
      "args": ["./server.js"],
      "env": {
        "API_KEY": "${API_KEY}",
        "BASE_URL": "${BASE_URL}"
      }
    }
  }
}
```

### Referencing config entries

```bash
# Syntax: mcpc <path>:<entry-name> connect @session
mcpc ~/.vscode/mcp.json:my-server connect @test
mcpc ./config.json:filesystem connect @fs
mcpc /absolute/path/config.json:entry connect @session
```

### Environment variable substitution

The `${VAR}` syntax is supported in these fields: `url`, `command`, `args`, `env` values, and `headers` values.

| Input | `$API_KEY=abc123` | `$API_KEY` unset |
|---|---|---|
| `"${API_KEY}"` | `"abc123"` | `""` (empty string) |

Missing variables resolve to an empty string. mcpc logs a warning but does not error. This is intentional — it allows config files to work in environments where some optional vars are not set.

### HTTP server config entries

Config files can also define HTTP servers (not just stdio):

```json
{
  "mcpServers": {
    "remote-server": {
      "url": "https://mcp.example.com",
      "headers": {
        "Authorization": "Bearer ${MCP_TOKEN}"
      }
    }
  }
}
```

```bash
mcpc ./config.json:remote-server connect @remote
```

## Error hierarchy

```
McpError (base class)
├── ClientError     exit code 1    Invalid arguments, unknown command, config errors
├── ServerError     exit code 2    Tool execution failed, resource not found, server bug
├── NetworkError    exit code 3    Connection refused, timeout, DNS failure, socket error
└── AuthError       exit code 4    Invalid credentials, 401, 403, token expired
```

### JSON error output

When `--json` is enabled, errors are output as:

```json
{
  "error": "ClientError",
  "message": "Session 'nonexistent' not found",
  "code": 1,
  "details": {}
}
```

The `details` object may contain additional context depending on the error type:

```json
{
  "error": "ServerError",
  "message": "Tool execution failed",
  "code": 2,
  "details": {
    "toolName": "search",
    "serverMessage": "Rate limit exceeded"
  }
}
```

### No success wrapper

Successful responses return raw MCP data directly — there is no `{"success": true, "data": ...}` wrapper. The exit code (0) indicates success. This makes jq pipelines simpler:

```bash
# Direct access to tool list — no unwrapping needed
mcpc @session tools-list --json | jq '.[0].name'

# Direct access to tool call result
mcpc @session tools-call search query:=test --json | jq '.content[0].text'
```

### Error detection in scripts

```bash
# Exit code approach (recommended)
if mcpc @session tools-call my-tool arg:=val --json > /tmp/result.json 2>/dev/null; then
  jq '.content' /tmp/result.json
else
  echo "Failed with exit code $?"
fi

# JSON error field approach
RESULT=$(mcpc @session tools-call my-tool arg:=val --json 2>&1)
if echo "$RESULT" | jq -e '.error' > /dev/null 2>&1; then
  echo "Error: $(echo "$RESULT" | jq -r '.message')"
else
  echo "Success: $(echo "$RESULT" | jq -r '.content[0].text')"
fi
```

## Data directory

Default location: `~/.mcpc/` (override with `MCPC_HOME_DIR` environment variable).

```
~/.mcpc/
├── sessions.json              # Session metadata (atomic writes, file-locked)
│                              #   name, target, pid, status, createdAt, lastSeenAt,
│                              #   protocolVersion, headers (redacted), profile, proxy
│
├── profiles.json              # OAuth profile metadata (mode 0600)
│                              #   host → profileName → {clientId, scopes, userInfo, timestamps}
│                              #   No tokens or secrets — those are in keychain
│
├── credentials.json           # Fallback credential storage (mode 0600)
│                              #   Only created when OS keychain is unavailable
│                              #   Contains actual tokens — protect this file
│
├── history                    # Interactive shell (mcpc @s shell) command history
│                              #   readline-compatible format
│
├── bridges/                   # Unix domain sockets for bridge IPC
│   ├── my-session.sock        # One socket per active session
│   ├── prod.sock              #   Created by bridge on startup
│   └── staging.sock           #   Removed on graceful close or by clean command
│
└── logs/                      # Bridge process logs
    ├── bridge-my-session.log  # One log file per session
    ├── bridge-prod.log        #   Contains transport-level debug info
    └── bridge-staging.log     #   Useful for diagnosing connection issues
```

### File permissions

| File | Mode | Reason |
|---|---|---|
| `profiles.json` | `0600` | Contains OAuth metadata (host, scopes, user info) |
| `credentials.json` | `0600` | Contains actual tokens (fallback storage) |
| `sessions.json` | `0644` | No secrets (headers redacted) |
| `bridges/*.sock` | `0600` | IPC channel — should only be accessible by owner |

### Disk usage

- `sessions.json`: typically < 10 KB (even with many sessions)
- `profiles.json`: typically < 5 KB
- `credentials.json`: typically < 10 KB
- Each bridge socket: 0 bytes on disk (Unix domain socket, kernel-managed)
- Each bridge log: grows unbounded in verbose mode, typically < 1 MB in normal operation
- Use `mcpc clean logs` to reclaim log space

### Custom home directory

```bash
# Isolated test environment
export MCPC_HOME_DIR=/tmp/mcpc-test-run-42

# All files created under the custom directory
# /tmp/mcpc-test-run-42/sessions.json
# /tmp/mcpc-test-run-42/bridges/
# /tmp/mcpc-test-run-42/logs/
# etc.

mcpc mcp.example.com connect @isolated
mcpc @isolated tools-list
mcpc @isolated close

# Clean up
rm -rf /tmp/mcpc-test-run-42
```

This is essential for:
- CI pipelines (prevent cross-job interference)
- Parallel test runs (each run gets its own directory)
- Testing mcpc itself (e2e tests use isolated home dirs)
