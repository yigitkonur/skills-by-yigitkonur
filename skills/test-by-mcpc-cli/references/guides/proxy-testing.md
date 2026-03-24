# Proxy Mode Testing

Test mcpc's built-in MCP proxy server for secure, sandboxed MCP access.

## What proxy mode does

When you add `--proxy` to a connect command, mcpc starts a local HTTP server alongside the normal bridge process. This proxy re-exposes the upstream MCP server as a local HTTP endpoint, using the MCP SDK's `StreamableHTTPServerTransport`.

Key behaviors:

- The bridge holds the original authentication (bearer token, OAuth credentials) and forwards requests upstream
- The proxy accepts unauthenticated connections by default, or enforces its own bearer token via `--proxy-bearer-token`
- Downstream clients never see the original auth tokens — token isolation is enforced at the process boundary
- The proxy speaks standard MCP over HTTP (JSON-RPC via POST, SSE via GET), so any MCP client can connect to it

### Primary use cases

| Scenario | Why proxy helps |
|---|---|
| AI sandbox (E2B, Docker, Codespaces) | Container can't access external auth services; proxy runs on host |
| Multi-tenant testing | One authenticated session shared by multiple test clients |
| Token security | CI runner or shared machine never sees production tokens |
| Local development | Expose a remote server to `localhost` for tools that only accept local URLs |

## Architecture

```
┌──────────┐     ┌──────────────────┐     ┌──────────┐     ┌────────────┐
│ AI Agent │────▶│     Proxy        │────▶│  Bridge  │────▶│ MCP Server │
│(sandbox) │ HTTP│  (:8080)         │ IPC │ (daemon) │ HTTP│  (remote)  │
│          │◀────│ StreamableHTTP   │◀────│          │◀────│            │
└──────────┘     │ ServerTransport  │     └──────────┘     └────────────┘
                 └──────────────────┘

Process boundary: tokens stay inside Bridge.
Proxy ↔ Bridge communication uses the same Unix socket IPC
as all other mcpc commands (~/.mcpc/bridges/<session>.sock).
```

### Data flow for a tool call through proxy

1. AI agent sends `POST /mcp` to proxy with JSON-RPC `tools/call` request
2. Proxy validates optional bearer token (if `--proxy-bearer-token` is set)
3. Proxy forwards the JSON-RPC message to Bridge via IPC socket
4. Bridge injects the original auth headers and forwards to upstream MCP server
5. Upstream responds; Bridge relays response back through proxy to agent

## Setting up a proxy

### Basic proxy (localhost only)

```bash
# Target BEFORE command — correct mcpc syntax
mcpc https://mcp.example.com connect @relay --proxy 8080

# Proxy is now listening on 127.0.0.1:8080
# Bridge is running as daemon with upstream auth
```

### Proxy with explicit bind address

```bash
# Bind to specific interface and port
mcpc https://mcp.example.com connect @relay --proxy 127.0.0.1:8080

# Bind to all interfaces (use with caution — exposes to network)
mcpc https://mcp.example.com connect @relay --proxy 0.0.0.0:8080

# Bind to a specific network interface
mcpc https://mcp.example.com connect @relay --proxy 192.168.1.100:8080
```

### Proxy with authentication

```bash
# Require downstream clients to present a bearer token
mcpc https://mcp.example.com connect @relay \
  --proxy 127.0.0.1:8080 \
  --proxy-bearer-token secret123

# Clients must now include: Authorization: Bearer secret123
```

### Proxy with upstream auth

```bash
# Bearer token upstream + proxy token downstream
mcpc https://mcp.example.com connect @relay \
  --header "Authorization: Bearer $UPSTREAM_TOKEN" \
  --proxy 8080 \
  --proxy-bearer-token $PROXY_TOKEN

# OAuth upstream + proxy token downstream
mcpc login https://mcp.example.com --profile prod
mcpc https://mcp.example.com connect @relay \
  --profile prod \
  --proxy 8080 \
  --proxy-bearer-token $PROXY_TOKEN
```

## Proxy endpoints

The proxy exposes standard MCP-over-HTTP endpoints:

| Method | Path | Purpose | Content-Type |
|---|---|---|---|
| `POST` | `/mcp` | MCP JSON-RPC requests (tool calls, resource reads, etc.) | `application/json` |
| `GET` | `/mcp` | SSE event stream (server-initiated notifications) | `text/event-stream` |
| `DELETE` | `/mcp` | Session termination | — |
| `GET` | `/health` | Health check (no auth required) | `application/json` |

### Health endpoint response

```json
{"status": "ok"}
```

The `/health` endpoint bypasses bearer token authentication, so monitoring systems can probe it without credentials.

## Testing the proxy

### Step 1: Verify proxy is running

```bash
# Health check — should return {"status":"ok"}
curl -s http://127.0.0.1:8080/health
curl -s http://127.0.0.1:8080/health | jq .

# If proxy requires bearer token, health still works without it
curl -s http://127.0.0.1:8080/health
```

### Step 2: Connect a second mcpc instance to the proxy

```bash
# Second mcpc client connects to the proxy
mcpc localhost:8080 connect @sandboxed

# If proxy requires bearer token
mcpc localhost:8080 connect @sandboxed \
  --header "Authorization: Bearer secret123"

# Test through the proxy
mcpc @sandboxed ping
mcpc @sandboxed tools-list
mcpc @sandboxed tools-call search query:=test
mcpc @sandboxed close
```

### Step 3: Test with raw curl

```bash
# Direct MCP JSON-RPC via curl (initialize request)
curl -X POST http://127.0.0.1:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"curl-test","version":"1.0"}}}'

# With proxy bearer token
curl -X POST http://127.0.0.1:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer secret123" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"curl-test","version":"1.0"}}}'
```

### Step 4: Test bearer token enforcement

```bash
# Without token when token is required — should fail
curl -s -o /dev/null -w "%{http_code}" \
  -X POST http://127.0.0.1:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"ping"}'
# Expected: 401

# With wrong token — should fail
curl -s -o /dev/null -w "%{http_code}" \
  -X POST http://127.0.0.1:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer wrong-token" \
  -d '{"jsonrpc":"2.0","id":1,"method":"ping"}'
# Expected: 401

# With correct token — should succeed
curl -s -o /dev/null -w "%{http_code}" \
  -X POST http://127.0.0.1:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer secret123" \
  -d '{"jsonrpc":"2.0","id":1,"method":"ping"}'
# Expected: 200
```

## Port conflict detection

If the specified port is already in use, mcpc reports a `ClientError` (exit code 1) during connect:

```bash
# Start first proxy
mcpc https://mcp.example.com connect @relay1 --proxy 8080

# Attempt second proxy on same port — fails with EADDRINUSE
mcpc https://mcp.example.com connect @relay2 --proxy 8080
# Error: Port 8080 is already in use (EADDRINUSE)
# Exit code: 1 (ClientError)

# Use a different port instead
mcpc https://mcp.example.com connect @relay2 --proxy 8081
```

## Proxy with Docker containers

### Host proxy, container client

```bash
# On host: start proxy bound to all interfaces
mcpc https://mcp.example.com connect @relay \
  --proxy 0.0.0.0:8080 \
  --proxy-bearer-token $PROXY_TOKEN

# In container: connect to host
docker run --rm -it node:22 bash -c '
  npm install -g @apify/mcpc
  mcpc host.docker.internal:8080 connect @sandbox \
    --header "Authorization: Bearer '"$PROXY_TOKEN"'"
  mcpc @sandbox tools-list
  mcpc @sandbox close
'
```

### Docker Compose setup

```yaml
services:
  mcp-proxy:
    image: node:22
    command: >
      bash -c "npm install -g @apify/mcpc &&
      mcpc https://mcp.example.com connect @relay
        --header 'Authorization: Bearer $${MCP_TOKEN}'
        --proxy 0.0.0.0:8080
        --proxy-bearer-token $${PROXY_TOKEN}"
    ports:
      - "8080:8080"
    environment:
      - MCP_TOKEN=${MCP_TOKEN}
      - PROXY_TOKEN=${PROXY_TOKEN}

  ai-agent:
    image: my-ai-agent:latest
    environment:
      - MCP_URL=http://mcp-proxy:8080
      - MCP_TOKEN=${PROXY_TOKEN}
    depends_on:
      - mcp-proxy
```

## Security model

### Token isolation

| Layer | Who holds token | Exposure |
|---|---|---|
| Upstream auth (bearer/OAuth) | Bridge process only | Never sent to proxy clients |
| Proxy bearer token | Proxy + downstream clients | Shared secret for proxy access |
| MCP-Session-Id | Proxy ↔ Bridge IPC | Internal transport detail |

The upstream authentication tokens exist only in the bridge process memory and in the OS keychain. They never traverse the proxy HTTP connection. Downstream clients authenticate with the proxy bearer token only.

### Session storage

Proxy configuration is persisted in `~/.mcpc/sessions.json` alongside normal session data:

```json
{
  "relay": {
    "server": { "url": "https://mcp.example.com" },
    "status": "live",
    "proxy": {
      "host": "127.0.0.1",
      "port": 8080
    }
  }
}
```

### Binding recommendations

| Binding | Security | Use case |
|---|---|---|
| `127.0.0.1:PORT` (default) | Localhost only | Same-machine containers, local dev |
| `0.0.0.0:PORT` | All interfaces | Docker bridge network, LAN testing |
| `SPECIFIC_IP:PORT` | One interface | Targeted access to specific network |

Always use `--proxy-bearer-token` when binding to non-localhost addresses. Without it, anyone on the network can access the proxy and, by extension, the upstream MCP server.

## Troubleshooting proxy issues

| Symptom | Cause | Fix |
|---|---|---|
| `EADDRINUSE` on connect | Port already in use | Use a different port or close the other process |
| `curl` to `/mcp` returns 401 | Missing or wrong bearer token | Include `Authorization: Bearer <token>` header |
| Container can't reach proxy | Proxy bound to 127.0.0.1 | Bind to `0.0.0.0` or specific interface |
| Proxy health OK but tools fail | Upstream server is down | Check `mcpc @relay ping` from host |
| Slow proxy responses | Upstream latency | Increase `--timeout`; proxy adds minimal overhead |
| Proxy stops after terminal close | Bridge process terminated | Run in background: `nohup mcpc ... &` or use tmux |

## Complete proxy test script

```bash
#!/bin/bash
set -euo pipefail

SERVER="${1:?Usage: $0 <server-url>}"
PROXY_PORT="${2:-8080}"
PROXY_TOKEN="test-token-$(date +%s)"
SESSION="proxy-test-$$"

cleanup() {
  mcpc "@$SESSION" close 2>/dev/null || true
  mcpc "@${SESSION}-client" close 2>/dev/null || true
}
trap cleanup EXIT

echo "=== Proxy Mode Test ==="

# Step 1: Start proxy
echo "Starting proxy on port $PROXY_PORT..."
mcpc "$SERVER" connect "@$SESSION" \
  --proxy "$PROXY_PORT" \
  --proxy-bearer-token "$PROXY_TOKEN"

# Step 2: Health check
HEALTH=$(curl -sf "http://127.0.0.1:$PROXY_PORT/health")
if [ "$HEALTH" = '{"status":"ok"}' ]; then
  echo "  OK: Health check passed"
else
  echo "  FAIL: Health check returned: $HEALTH"
  exit 1
fi

# Step 3: Auth enforcement
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "http://127.0.0.1:$PROXY_PORT/mcp" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"ping"}')
if [ "$STATUS" = "401" ]; then
  echo "  OK: Unauthenticated request rejected (401)"
else
  echo "  FAIL: Expected 401, got $STATUS"
fi

# Step 4: Connect client through proxy
mcpc "localhost:$PROXY_PORT" connect "@${SESSION}-client" \
  --header "Authorization: Bearer $PROXY_TOKEN"

# Step 5: Test through proxy
mcpc "@${SESSION}-client" ping && echo "  OK: Ping through proxy"
TOOLS=$(mcpc --json "@${SESSION}-client" tools-list | jq 'length')
echo "  OK: $TOOLS tool(s) visible through proxy"

echo "=== Proxy test complete ==="
```
