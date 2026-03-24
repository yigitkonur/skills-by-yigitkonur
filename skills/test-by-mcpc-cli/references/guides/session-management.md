# Session Management Deep Dive

Internal architecture and lifecycle of mcpc sessions, covering the two-process model, IPC protocol, session states, auto-recovery, and multi-session patterns.

## Architecture: two-process model

mcpc uses a two-process design:

1. **`mcpc` (CLI process)** — parses commands, exits after each invocation. Stateless by design.
2. **`mcpc-bridge` (persistent daemon)** — maintains the long-lived connection to the MCP server. One bridge per session.

### Request flow

```
User command
    │
    ▼
┌──────────┐     ┌─────────────┐     ┌──────────────────────────────┐     ┌────────────┐
│  mcpc    │────▶│ BridgeClient│────▶│         mcpc-bridge          │────▶│ MCP Server │
│  (CLI)   │ IPC │  (connects  │ sock│  ┌──────────┐ ┌───────────┐ │ HTTP│  (remote)  │
│  parses  │     │  to socket) │     │  │McpClient │→│ Transport │ │     │            │
└──────────┘     └─────────────┘     │  └──────────┘ └───────────┘ │     └────────────┘
   exits                             └──────────────────────────────┘
                                          persists across commands
```

### Bridge spawning

When `mcpc <target> connect @session` runs, the CLI spawns the bridge as a fully detached process:

```javascript
spawn('node', ['dist/bridge/index.js', ...bridgeArgs], {
  detached: true,
  stdio: 'ignore'
})
```

The bridge process is unparented from the CLI — the CLI `unref()`s the child and exits immediately. The bridge continues running as a daemon until explicitly closed, crashed, or cleaned.

### IPC channel

Communication between CLI and bridge uses a Unix domain socket:

```
~/.mcpc/bridges/<session-name>.sock
```

Every CLI command (e.g., `mcpc @session tools-list`) opens a connection to this socket, sends a JSON request, reads the JSON response, then disconnects. The bridge listens on the socket indefinitely.

### Session metadata storage

All session metadata lives in `~/.mcpc/sessions.json`. This file is managed with atomic writes and a file lock to prevent corruption from concurrent CLI invocations:

```json
{
  "my-session": {
    "name": "my-session",
    "target": "https://mcp.example.com",
    "pid": 12345,
    "status": "live",
    "createdAt": "2025-03-20T10:00:00.000Z",
    "lastSeenAt": "2025-03-20T10:05:30.000Z",
    "protocolVersion": "2025-11-25",
    "headers": "<redacted>",
    "profile": "default",
    "proxy": null
  }
}
```

Sensitive values (headers, tokens) are stored as `<redacted>` here. Actual credentials live in the OS keychain or `~/.mcpc/credentials.json` fallback.

## Session states

Every session is in one of five states, derived from bridge health checks:

| State | Icon | PID alive? | lastSeenAt fresh? | Server responding? | Cause |
|---|---|---|---|---|---|
| `live` | green | Yes | Within 65s | Yes | Normal operation |
| `disconnected` | yellow | Yes | Stale (>65s) | No | Server unreachable, bridge retrying |
| `crashed` | yellow | No | N/A | N/A | Bridge process died or OOM-killed |
| `unauthorized` | red | Yes | N/A | 401/403 | Auth credentials rejected |
| `expired` | red | Yes | N/A | 404 | MCP-Session-Id no longer valid on server |

### State determination logic

**`live`**: The bridge PID is alive AND `lastSeenAt` is within 65 seconds of now. The 65-second window is calculated as: 2 x 30-second keepalive interval + 5-second margin.

**`disconnected`**: PID is alive but `lastSeenAt` has gone stale. This means the bridge process is running but the MCP server is not responding to keepalive pings. The bridge continues retrying with exponential backoff.

**`crashed`**: Either `kill(pid, 0)` fails (process dead) or `status` is explicitly set to `crashed` in sessions.json. The `consolidateSessions()` routine marks sessions crashed on startup.

**`unauthorized`**: The bridge received a 401 or 403 response from the server. Detected via regex match against error responses:

```
/invalid_token|unauthorized|missing.*token|401|403/i
```

**`expired`**: The server returned 404 for the MCP session (session-not-found). This is specific to stateful servers using MCP-Session-Id. The server has evicted the session.

## Auto-recovery

### withSessionClient() flow

Every CLI command that targets a session goes through `withSessionClient()`:

1. Load session from sessions.json
2. Check PID liveness with `kill(pid, 0)`
3. If PID dead: auto-restart bridge, wait for socket, retry command
4. If PID alive: connect to socket, call `checkBridgeHealth()` via IPC
5. If health check fails: restart bridge, retry command
6. If health check passes: execute the actual command

### SessionClient.withRetry()

Tool calls and other session operations use `withRetry()` for transient failures:

1. Execute the IPC request
2. If `NetworkError` caught: restart bridge process, wait for socket readiness
3. Retry the original request exactly once
4. If second attempt fails: propagate the error to the user

This means a single bridge crash during a tool call is silently recovered. Two consecutive failures surface the error.

### Credential re-injection on restart

When a bridge is auto-restarted:

1. CLI reads credentials from keychain (or credentials.json fallback)
2. After socket connects, CLI sends `set-auth-credentials` IPC message
3. Bridge configures OAuthTokenManager or injects bearer headers
4. MCP connection is re-established with credentials

This allows recovery without user interaction, as long as tokens have not expired.

## IPC protocol

### Wire format

Newline-delimited JSON (NDJSON) over Unix domain socket. Each message is a single JSON object terminated by `\n`. Maximum buffer size: 10 MB per message.

### Message types

| Type | Direction | Purpose |
|---|---|---|
| `request` | CLI -> Bridge | Execute a command (tools-call, resources-read, etc.) |
| `response` | Bridge -> CLI | Command result or error |
| `shutdown` | CLI -> Bridge | Graceful bridge termination |
| `notification` | Bridge -> CLI | Server-initiated notification forwarding |
| `task-update` | Bridge -> CLI | Task progress updates (experimental) |
| `set-auth-credentials` | CLI -> Bridge | Inject OAuth tokens or bearer headers |
| `set-x402-wallet` | CLI -> Bridge | Inject x402 payment wallet config |

### Timing

- **Request timeout**: 3 minutes (180,000 ms). If the bridge does not respond within this window, the CLI throws a `NetworkError`.
- **Keepalive ping**: Every 30 seconds, the bridge pings the MCP server. Updates `lastSeenAt` in sessions.json on success.

### Example IPC exchange

CLI sends:
```json
{"type":"request","id":"req-1","command":"tools-list","args":{}}
```

Bridge responds:
```json
{"type":"response","id":"req-1","result":[{"name":"search","description":"Search docs","inputSchema":{...}}]}
```

## consolidateSessions()

This function runs at every CLI startup (before any command executes):

1. Reads sessions.json
2. For each session entry, checks if `pid` is alive via `kill(pid, 0)`
3. If PID is dead:
   - Sets `status` to `crashed`
   - Clears the PID field
   - Removes the stale socket file from `~/.mcpc/bridges/`
4. Writes updated sessions.json atomically

This ensures that `mcpc` (bare command, list sessions) always shows accurate state, even after system reboots or OOM kills.

## Session lifecycle commands

### Create a session

```bash
# HTTP server
mcpc mcp.example.com connect @prod

# Stdio server from config
mcpc ~/.vscode/mcp.json:my-server connect @local

# With authentication
mcpc https://mcp.example.com connect @authed \
  --header "Authorization: Bearer $TOKEN"

# With OAuth profile
mcpc https://mcp.example.com connect @oauth --profile myprofile

# With proxy enabled
mcpc https://mcp.example.com connect @relay --proxy 8080
```

### Inspect sessions

```bash
# List all sessions with human-readable status
mcpc

# JSON output with full metadata
mcpc --json | jq '.sessions[]'

# Single session metadata
mcpc --json @prod | jq '._mcpc'

# Extract specific fields
mcpc --json @prod | jq '{
  status: ._mcpc.status,
  pid: ._mcpc.pid,
  target: ._mcpc.target,
  uptime: (now - (._mcpc.createdAt | fromdateiso8601))
}'
```

### Health check

```bash
# Ping measures round-trip time (CLI -> Bridge -> Server -> Bridge -> CLI)
mcpc @prod ping
```

### Restart a session

```bash
# Kill bridge, respawn, reconnect to server (new MCP-Session-Id)
mcpc @prod restart
```

This is useful after:
- Auth token refresh (forces credential re-injection)
- Server-side session expiry (gets a fresh session ID)
- Suspected bridge corruption

### Close a session

```bash
# Graceful shutdown: sends shutdown IPC, waits for bridge exit, removes socket
mcpc @prod close
```

### Bulk cleanup

```bash
# Remove all sessions with dead bridges
mcpc clean sessions

# Remove everything (sessions + profiles + logs + credentials)
mcpc clean all
```

## Multi-session patterns

### Independent bridge processes

Each session runs its own bridge process. Typical memory: 30-50 MB per bridge (Node.js baseline + MCP client state).

```bash
# Three concurrent sessions to different servers
mcpc mcp-prod.example.com connect @prod
mcpc mcp-staging.example.com connect @staging
mcpc localhost:3000 connect @local-dev
```

### Shared OAuth profiles

OAuth profiles are per-server, not per-session. Multiple sessions to the same server share the same profile and token set:

```bash
# Both sessions use the same OAuth tokens for mcp.example.com
mcpc mcp.example.com connect @session-a --profile work
mcpc mcp.example.com connect @session-b --profile work
```

Token refresh in one bridge is picked up by the other via keychain re-read (onBeforeRefresh callback).

### Naming conventions

Use a `@server-environment` pattern for clarity:

```bash
mcpc mcp.apify.com connect @apify-prod
mcpc mcp-staging.apify.com connect @apify-staging
mcpc localhost:3000 connect @apify-dev
```

### Comparing tools across servers

```bash
# Diff tool lists between production and staging
PROD_TOOLS=$(mcpc @apify-prod tools-list --json | jq -r '.[].name' | sort)
STAGING_TOOLS=$(mcpc @apify-staging tools-list --json | jq -r '.[].name' | sort)
diff <(echo "$PROD_TOOLS") <(echo "$STAGING_TOOLS")
```

## Monitoring scripts

### Session health watchdog

```bash
#!/bin/bash
# session-watchdog.sh — restart unhealthy sessions automatically
set -euo pipefail

SESSIONS=$(mcpc --json | jq -r '.sessions[].name')

for session in $SESSIONS; do
  STATUS=$(mcpc --json "@$session" | jq -r '._mcpc.status')

  case "$STATUS" in
    live)
      echo "[$session] healthy"
      ;;
    disconnected)
      echo "[$session] disconnected — server may be down, bridge retrying"
      ;;
    crashed)
      echo "[$session] crashed — restarting bridge"
      mcpc "@$session" restart 2>/dev/null || echo "[$session] restart failed"
      ;;
    unauthorized)
      echo "[$session] unauthorized — re-authentication required"
      ;;
    expired)
      echo "[$session] expired — restarting to get new session ID"
      mcpc "@$session" restart 2>/dev/null || echo "[$session] restart failed"
      ;;
    *)
      echo "[$session] unknown status: $STATUS"
      ;;
  esac
done
```

### Multi-session dashboard

```bash
#!/bin/bash
# session-dashboard.sh — live session overview
set -euo pipefail

printf "%-20s %-15s %-8s %-30s %-20s\n" "SESSION" "STATUS" "PID" "TARGET" "LAST SEEN"
printf "%-20s %-15s %-8s %-30s %-20s\n" "-------" "------" "---" "------" "---------"

mcpc --json | jq -r '.sessions[] |
  [.name, .status, (.pid // "dead" | tostring), .target, .lastSeenAt] |
  @tsv' | while IFS=$'\t' read -r name status pid target lastseen; do
    printf "%-20s %-15s %-8s %-30s %-20s\n" "$name" "$status" "$pid" "$target" "$lastseen"
done
```

### Continuous health monitor

```bash
#!/bin/bash
# health-monitor.sh — poll all sessions every 60 seconds, log results
set -euo pipefail

LOG_FILE="${1:-/tmp/mcpc-health.log}"

while true; do
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  SESSIONS=$(mcpc --json 2>/dev/null | jq -r '.sessions[].name' 2>/dev/null || echo "")

  if [ -z "$SESSIONS" ]; then
    echo "$TIMESTAMP no-sessions" >> "$LOG_FILE"
  else
    for session in $SESSIONS; do
      STATUS=$(mcpc --json "@$session" 2>/dev/null | jq -r '._mcpc.status' 2>/dev/null || echo "unreachable")
      RTT=""
      if [ "$STATUS" = "live" ]; then
        RTT=$(mcpc "@$session" ping --json 2>/dev/null | jq -r '.rtt // "unknown"' 2>/dev/null || echo "timeout")
      fi
      echo "$TIMESTAMP $session status=$STATUS rtt=$RTT" >> "$LOG_FILE"
    done
  fi

  sleep 60
done
```

## Advanced: bridge internals

### Bridge startup sequence

1. Parse command-line arguments (target, session name, options)
2. Create Unix domain socket at `~/.mcpc/bridges/<session>.sock`
3. Initialize `McpClient` with `StreamableHTTPClientTransport`
4. Perform MCP handshake (`initialize` request)
5. Record session in sessions.json with status `live`
6. Start keepalive timer (30-second interval)
7. Begin listening for IPC connections on socket

### Bridge shutdown sequence (graceful)

1. Receive `shutdown` IPC message from CLI
2. Send MCP `close` notification to server (if connected)
3. Close all pending IPC connections
4. Remove socket file
5. Update sessions.json (remove entry)
6. `process.exit(0)`

### Keepalive mechanism

Every 30 seconds the bridge:

1. Sends MCP `ping` to the server
2. On success: updates `lastSeenAt` in sessions.json
3. On failure: logs the error, increments failure counter, continues retrying
4. After prolonged failure: status transitions to `disconnected` (detected by CLI via stale `lastSeenAt`)

The CLI determines `live` vs `disconnected` by checking whether `lastSeenAt` is within 65 seconds (2 x 30s interval + 5s margin) of the current time.

### Session file locking

Multiple CLI processes may access sessions.json concurrently (e.g., parallel test runs). mcpc uses file-based locking:

1. Acquire lock on `~/.mcpc/sessions.json.lock`
2. Read sessions.json
3. Modify in memory
4. Write to temporary file
5. Atomic rename to sessions.json
6. Release lock

This prevents partial writes and race conditions even under heavy parallel usage.
