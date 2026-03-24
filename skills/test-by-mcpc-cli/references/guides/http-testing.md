# HTTP Transport Testing

Test MCP servers over HTTP — both stateless (SSE) and stateful (streamable HTTP) transports.

## Transport detection

mcpc auto-detects the transport during the initialization handshake. You do not need to specify stateless vs stateful — mcpc handles this based on the server's protocol version response.

| Server behavior | Protocol | mcpc behavior |
|---|---|---|
| No `MCP-Session-Id` in response | SSE (stateless) | Independent connections |
| Returns `MCP-Session-Id` | Streamable HTTP (stateful) | Session tracking + auto-resume |
| Protocol version 2025-11-25+ | Streamable HTTP | Full session management |

## Connecting to HTTP servers

### Basic connection (no auth)

```bash
# HTTPS (default for bare hostnames)
mcpc mcp.example.com connect @test
# Resolves to: https://mcp.example.com

# Explicit HTTPS
mcpc https://mcp.example.com connect @test

# HTTP (only for localhost — auto-detected)
mcpc localhost:3000 connect @local
# Resolves to: http://localhost:3000

# Explicit HTTP for non-localhost
mcpc http://192.168.1.100:3000 connect @lan
```

### URL resolution rules

| Input | Resolved URL |
|---|---|
| `mcp.example.com` | `https://mcp.example.com` |
| `mcp.example.com:8080` | `https://mcp.example.com:8080` |
| `localhost:3000` | `http://localhost:3000` |
| `127.0.0.1:3000` | `http://127.0.0.1:3000` |
| `https://mcp.example.com/mcp` | `https://mcp.example.com/mcp` (as-is) |
| `http://staging.internal:3000` | `http://staging.internal:3000` (as-is) |

## Authentication

### Bearer token (most common)

```bash
# Via --header flag
mcpc https://mcp.example.com connect @test \
  --header "Authorization: Bearer $MCP_TOKEN"

# Token is stored in OS keychain for the session duration
# Subsequent commands auto-include the token:
mcpc @test tools-list
```

### OAuth 2.1 (interactive)

```bash
# Step 1: Login (opens browser)
mcpc login https://mcp.example.com

# Step 2: Connect using saved profile
mcpc https://mcp.example.com connect @test

# Named profiles for multiple accounts
mcpc login https://mcp.example.com --profile work
mcpc login https://mcp.example.com --profile personal
mcpc https://mcp.example.com connect @work-session --profile work

# Custom OAuth scopes
mcpc login https://mcp.example.com --scope "read write admin"

# Custom client credentials
mcpc login https://mcp.example.com \
  --client-id my-app \
  --client-secret $CLIENT_SECRET
```

### Anonymous connection

```bash
# Anonymous connection — simply omit --profile and --header flags
mcpc https://mcp.example.com connect @anon
```

### Auth priority order

1. `--header` flags (highest priority)
2. Saved OAuth profiles
3. Config file headers
4. Anonymous (no auth)

### Managing OAuth profiles

```bash
# List saved profiles
mcpc
# Shows sessions with associated profiles

# Delete a profile
mcpc logout https://mcp.example.com
mcpc logout https://mcp.example.com --profile work
```

## Testing stateless servers (SSE)

Stateless SSE servers have no server-side session state. Each connection is independent.

### What to test

1. **Connection independence**: Two separate sessions should not share state
2. **Idempotent reads**: Same query returns same result regardless of prior calls
3. **No session leakage**: Data created in one session is not visible through server session state in another

### Test procedure

```bash
# === Test 1: Basic connectivity ===
mcpc https://mcp.example.com connect @sse-1
mcpc @sse-1 ping
mcpc @sse-1 tools

# === Test 2: Connection independence ===
# Session A: create something
mcpc @sse-1 tools-call create-item name:=from-session-A

# Session B: independent connection
mcpc https://mcp.example.com connect @sse-2
mcpc @sse-2 tools-call list-items --json > /tmp/sse-2-items.json

# Close both
mcpc @sse-1 close
mcpc @sse-2 close

# Session C: fresh connection
mcpc https://mcp.example.com connect @sse-3
mcpc @sse-3 tools-call list-items --json > /tmp/sse-3-items.json

# Compare: if the server is stateless at the session level,
# the list should be based on persistent storage, not session state
diff /tmp/sse-2-items.json /tmp/sse-3-items.json
mcpc @sse-3 close

# === Test 3: Reconnection ===
mcpc https://mcp.example.com connect @sse-reconnect
mcpc @sse-reconnect tools-list
mcpc @sse-reconnect close
# Reconnect should work cleanly without "session expired" errors
mcpc https://mcp.example.com connect @sse-reconnect-2
mcpc @sse-reconnect-2 tools-list
mcpc @sse-reconnect-2 close
```

## Testing stateful servers (streamable HTTP)

Stateful servers maintain session state via the `MCP-Session-Id` header.

### What to test

1. **Session creation**: Server returns `MCP-Session-Id` in init response
2. **State persistence**: Data created in a session is visible in subsequent requests within the same session
3. **Session isolation**: Different sessions should not share in-session state
4. **Session restart**: `mcpc restart` creates a new session
5. **Session expiry**: How the server handles expired sessions (should return 404, mcpc auto-recovers)
6. **Keepalive**: mcpc sends pings every 30s; server should respond

### Test procedure

```bash
# === Test 1: Session creation and protocol check ===
mcpc https://mcp.example.com connect @stateful-1
mcpc --json @stateful-1 | jq '{
  protocolVersion: .protocolVersion,
  sessionId: .sessionId
}'
# protocolVersion should be "2025-11-25" or later
# sessionId should be non-null for stateful servers

# === Test 2: State persistence within session ===
mcpc @stateful-1 tools-call create-item name:=test-1
mcpc @stateful-1 tools-call create-item name:=test-2
mcpc @stateful-1 tools-call list-items --json
# Should show both test-1 and test-2

# === Test 3: Session isolation ===
mcpc https://mcp.example.com connect @stateful-2
mcpc @stateful-2 tools-call list-items --json
# If sessions are isolated, items from stateful-1 should not appear
# (unless backed by shared persistent storage)

# === Test 4: Session restart ===
mcpc @stateful-1 restart
mcpc --json @stateful-1 | jq '.sessionId'
# Should be a DIFFERENT session ID than before restart
mcpc @stateful-1 tools-call list-items --json
# Server decides: session-scoped state is gone, persistent storage may remain

# === Test 5: Keepalive verification ===
mcpc @stateful-1 ping
# Should respond immediately (mcpc auto-pings every 30s)

# === Test 6: Cleanup ===
mcpc @stateful-1 close
mcpc @stateful-2 close
```

### Session states and recovery

| State | Indicator | Meaning | Recovery |
|---|---|---|---|
| Live | 🟢 | Bridge running, server responding | None needed |
| Disconnected | 🟡 | Bridge alive, server unreachable | Auto-recovers when server returns |
| Crashed | 🟡 | Bridge process died | Auto-restarts on next command |
| Unauthorized | 🔴 | Server rejected auth (401/403) | `mcpc login <server>` then `mcpc @session restart` |
| Expired | 🔴 | Session ID rejected (404) | `mcpc @session restart` (gets new session ID) |

### Reconnection behavior

mcpc uses exponential backoff for reconnection:

- Initial delay: 1 second
- Max delay: 30 seconds
- Growth factor: 2x
- Max retries: 10
- Max queue wait: 3 minutes (fails after)

## TLS and self-signed certificates

```bash
# Skip TLS verification (development only!)
mcpc https://dev.internal:3000 connect @dev --insecure

# Never use --insecure in production
```

## Proxy testing

### MCP proxy (expose authenticated server to untrusted clients)

```bash
# Human authenticates and creates proxy
mcpc https://mcp.example.com connect @relay --proxy 8080

# Proxy is now available at localhost:8080
# Connect to it (no auth needed — proxy forwards original auth)
mcpc localhost:8080 connect @sandboxed
mcpc @sandboxed tools-list
mcpc @sandboxed tools-call search query:=test

# With proxy authentication
mcpc https://mcp.example.com connect @relay \
  --proxy 8080 \
  --proxy-bearer-token "secret-token"

# Clients must provide the proxy token
mcpc localhost:8080 connect @client \
  --header "Authorization: Bearer secret-token"
```

### Proxy binding options

| Flag | Binds to | Security |
|---|---|---|
| `--proxy 8080` | `127.0.0.1:8080` | Localhost only (safe) |
| `--proxy 0.0.0.0:8080` | All interfaces | Exposed to network (use with caution) |
| `--proxy 192.168.1.100:8080` | Specific interface | Targeted binding |

### HTTP/HTTPS proxy (outbound)

```bash
# Set proxy for outbound connections
export HTTPS_PROXY=http://corporate-proxy:8080
export NO_PROXY=localhost,127.0.0.1

mcpc https://mcp.example.com connect @through-proxy
```

## Custom headers

```bash
# Single header
mcpc https://mcp.example.com connect @test \
  --header "X-Custom-Header: value"

# Multiple headers
mcpc https://mcp.example.com connect @test \
  --header "Authorization: Bearer $TOKEN" \
  --header "X-Request-Id: test-run-1" \
  --header "X-Tenant-Id: my-org"
```

## Timeout configuration

```bash
# Per-connection timeout (seconds)
mcpc https://mcp.example.com connect @test --timeout 600

# Default: 300 seconds (5 minutes)
# Increase for servers with slow tool calls
```
