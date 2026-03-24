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
mcpc connect mcp.example.com @test
# Resolves to: https://mcp.example.com

# Explicit HTTPS
mcpc connect https://mcp.example.com @test

# HTTP (only for localhost — auto-detected)
mcpc connect localhost:3000 @local
# Resolves to: http://localhost:3000

# Explicit HTTP for non-localhost
mcpc connect http://192.168.1.100:3000 @lan
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
mcpc connect https://mcp.example.com @test \
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
mcpc connect https://mcp.example.com @test

# Named profiles for multiple accounts
mcpc login https://mcp.example.com --profile work
mcpc login https://mcp.example.com --profile personal
mcpc connect https://mcp.example.com @work-session --profile work

# Custom OAuth scopes
mcpc login https://mcp.example.com --scope "read write admin"

# Custom client credentials
mcpc login https://mcp.example.com \
  --client-id my-app \
  --client-secret $CLIENT_SECRET
```

### Anonymous connection

```bash
# Skip OAuth entirely
mcpc connect https://mcp.example.com @anon --no-profile
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
mcpc connect https://mcp.example.com @sse-1
mcpc @sse-1 ping
mcpc @sse-1 tools

# === Test 2: Connection independence ===
# Session A: create something
mcpc @sse-1 tools-call create-item name:=from-session-A

# Session B: independent connection
mcpc connect https://mcp.example.com @sse-2
mcpc @sse-2 tools-call list-items --json > /tmp/sse-2-items.json

# Close both
mcpc close @sse-1
mcpc close @sse-2

# Session C: fresh connection
mcpc connect https://mcp.example.com @sse-3
mcpc @sse-3 tools-call list-items --json > /tmp/sse-3-items.json

# Compare: if the server is stateless at the session level,
# the list should be based on persistent storage, not session state
diff /tmp/sse-2-items.json /tmp/sse-3-items.json
mcpc close @sse-3

# === Test 3: Reconnection ===
mcpc connect https://mcp.example.com @sse-reconnect
mcpc @sse-reconnect tools-list
mcpc close @sse-reconnect
# Reconnect should work cleanly without "session expired" errors
mcpc connect https://mcp.example.com @sse-reconnect-2
mcpc @sse-reconnect-2 tools-list
mcpc close @sse-reconnect-2
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
mcpc connect https://mcp.example.com @stateful-1
mcpc @stateful-1 help --json | jq '{
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
mcpc connect https://mcp.example.com @stateful-2
mcpc @stateful-2 tools-call list-items --json
# If sessions are isolated, items from stateful-1 should not appear
# (unless backed by shared persistent storage)

# === Test 4: Session restart ===
mcpc restart @stateful-1
mcpc @stateful-1 help --json | jq '.sessionId'
# Should be a DIFFERENT session ID than before restart
mcpc @stateful-1 tools-call list-items --json
# Server decides: session-scoped state is gone, persistent storage may remain

# === Test 5: Keepalive verification ===
mcpc @stateful-1 ping
# Should respond immediately (mcpc auto-pings every 30s)

# === Test 6: Cleanup ===
mcpc close @stateful-1
mcpc close @stateful-2
```

### Session states and recovery

| State | Indicator | Meaning | Recovery |
|---|---|---|---|
| Live | 🟢 | Bridge running, server responding | None needed |
| Disconnected | 🟡 | Bridge alive, server unreachable | Auto-recovers when server returns |
| Crashed | 🟡 | Bridge process died | Auto-restarts on next command |
| Unauthorized | 🔴 | Server rejected auth (401/403) | `mcpc login <server>` then `mcpc restart @session` |
| Expired | 🔴 | Session ID rejected (404) | `mcpc restart @session` (gets new session ID) |

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
mcpc connect https://dev.internal:3000 @dev --insecure

# Never use --insecure in production
```

## Proxy testing

### MCP proxy (expose authenticated server to untrusted clients)

```bash
# Human authenticates and creates proxy
mcpc connect https://mcp.example.com @relay --proxy 8080

# Proxy is now available at localhost:8080
# Connect to it (no auth needed — proxy forwards original auth)
mcpc connect localhost:8080 @sandboxed
mcpc @sandboxed tools-list
mcpc @sandboxed tools-call search query:=test

# With proxy authentication
mcpc connect https://mcp.example.com @relay \
  --proxy 8080 \
  --proxy-bearer-token "secret-token"

# Clients must provide the proxy token
mcpc connect localhost:8080 @client \
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

mcpc connect https://mcp.example.com @through-proxy
```

## Custom headers

```bash
# Single header
mcpc connect https://mcp.example.com @test \
  --header "X-Custom-Header: value"

# Multiple headers
mcpc connect https://mcp.example.com @test \
  --header "Authorization: Bearer $TOKEN" \
  --header "X-Request-Id: test-run-1" \
  --header "X-Tenant-Id: my-org"
```

## Timeout configuration

```bash
# Per-connection timeout (seconds)
mcpc connect https://mcp.example.com @test --timeout 600

# Default: 300 seconds (5 minutes)
# Increase for servers with slow tool calls
```
