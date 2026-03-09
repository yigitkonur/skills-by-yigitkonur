# MCP Inspector API Reference

Complete reference for every endpoint, parameter, and behavior of `@mcp-use/inspector`.

## Starting the Inspector

```bash
MCP_USE_ANONYMIZED_TELEMETRY=false npx @mcp-use/inspector \
  --url "$MCP_URL" \
  --port "$PORT" \
  --no-open &
INSPECTOR_PID=$!
```

### CLI Flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--url <url>` | string | none | MCP server URL to auto-connect (http/https/ws/wss) |
| `--port <port>` | integer | 8080 | Starting port (auto-increments up to +100 if busy) |
| `--no-open` | flag | false | Don't open browser automatically |
| `--help` / `-h` | flag | — | Print help and exit |

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `MCP_USE_ANONYMIZED_TELEMETRY` | `"true"` | Set `"false"` to disable telemetry |
| `PORT` | `8080` | Server port (overridden by `--port`) |
| `HOST` | `0.0.0.0` | Bind address |
| `NODE_ENV` | `production` | `"development"` includes stack traces in errors |
| `DEBUG` | — | Any truthy value enables verbose widget logging |
| `MCP_INSPECTOR_FRAME_ANCESTORS` | — | CSP frame-ancestors for iframe embedding |
| `INSPECTOR_USE_CDN` | `false` | Serve UI from CDN |
| `INSPECTOR_CDN_BASE` | `https://inspector-cdn.mcp-use.com` | CDN base URL |

### Port Selection

The inspector auto-finds the next available port starting from `--port` (default 8080). It tries up to 100 ports. If all are busy, it exits with an error.

To capture the actual port in scripts, parse the startup output:
```bash
ACTUAL_PORT=$(MCP_USE_ANONYMIZED_TELEMETRY=false npx @mcp-use/inspector --port 9000 --no-open 2>&1 | grep -oP 'localhost:\K[0-9]+' | head -1)
```

Or just pick a high port unlikely to conflict:
```bash
PORT=19876
```

### Startup Wait

The inspector needs a moment to boot. Wait for the health endpoint:
```bash
for i in $(seq 1 30); do
  curl -sf "http://localhost:${PORT}/inspector/health" > /dev/null 2>&1 && break
  sleep 1
done
```

---

## API Endpoints

All endpoints are under `http://localhost:<port>/inspector/`.

### Health Check

```
GET /inspector/health
```

Response:
```json
{"status": "ok", "timestamp": "2026-03-02T10:00:00.000Z"}
```

### Config

```
GET /inspector/config.json
```

Response:
```json
{"autoConnectUrl": "http://localhost:3000/mcp"}
```

Returns `null` for `autoConnectUrl` if `--url` was not passed.

---

### MCP Proxy (Core Testing Endpoint)

```
POST /inspector/api/proxy
```

This is the main endpoint for testing. It proxies JSON-RPC requests to your MCP server.

**Required header:** `x-mcp-url` — the target MCP server URL.

**Optional headers:** `Authorization` — forwarded to the MCP server for auth.

**Body:** Any valid MCP JSON-RPC request.

#### Initialize

```bash
curl -sf -X POST "$BASE/api/proxy" \
  -H "Content-Type: application/json" \
  -H "x-mcp-url: $MCP_URL" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-03-26",
      "capabilities": {},
      "clientInfo": {"name": "mcp-test", "version": "1.0.0"}
    }
  }'
```

Response contains: `result.serverInfo`, `result.capabilities`, `result.protocolVersion`

#### List Tools

```bash
curl -sf -X POST "$BASE/api/proxy" \
  -H "Content-Type: application/json" \
  -H "x-mcp-url: $MCP_URL" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

Response: `result.tools[]` — each with `name`, `description`, `inputSchema`

#### Call a Tool

```bash
curl -sf -X POST "$BASE/api/proxy" \
  -H "Content-Type: application/json" \
  -H "x-mcp-url: $MCP_URL" \
  -d '{
    "jsonrpc":"2.0","id":3,"method":"tools/call",
    "params":{"name":"tool_name","arguments":{"key":"value"}}
  }'
```

Response: `result.content[]` — each with `type` ("text" or "image") and `text` or `data`.
Error response: `result.isError: true` or `error` object.

#### List Resources

```bash
curl -sf -X POST "$BASE/api/proxy" \
  -H "Content-Type: application/json" \
  -H "x-mcp-url: $MCP_URL" \
  -d '{"jsonrpc":"2.0","id":4,"method":"resources/list","params":{}}'
```

Response: `result.resources[]` — each with `uri`, `name`, `mimeType`, `description`

#### Read a Resource

```bash
curl -sf -X POST "$BASE/api/proxy" \
  -H "Content-Type: application/json" \
  -H "x-mcp-url: $MCP_URL" \
  -d '{
    "jsonrpc":"2.0","id":5,"method":"resources/read",
    "params":{"uri":"resource://example"}
  }'
```

Response: `result.contents[]` — each with `uri`, `mimeType`, and either `text` or `blob`

#### List Resource Templates

```bash
curl -sf -X POST "$BASE/api/proxy" \
  -H "Content-Type: application/json" \
  -H "x-mcp-url: $MCP_URL" \
  -d '{"jsonrpc":"2.0","id":6,"method":"resources/templates/list","params":{}}'
```

#### List Prompts

```bash
curl -sf -X POST "$BASE/api/proxy" \
  -H "Content-Type: application/json" \
  -H "x-mcp-url: $MCP_URL" \
  -d '{"jsonrpc":"2.0","id":7,"method":"prompts/list","params":{}}'
```

Response: `result.prompts[]` — each with `name`, `description`, `arguments[]`

#### Get a Prompt

```bash
curl -sf -X POST "$BASE/api/proxy" \
  -H "Content-Type: application/json" \
  -H "x-mcp-url: $MCP_URL" \
  -d '{
    "jsonrpc":"2.0","id":8,"method":"prompts/get",
    "params":{"name":"prompt_name","arguments":{"arg1":"value"}}
  }'
```

Response: `result.messages[]` — rendered prompt messages

#### Ping

```bash
curl -sf -X POST "$BASE/api/proxy" \
  -H "Content-Type: application/json" \
  -H "x-mcp-url: $MCP_URL" \
  -d '{"jsonrpc":"2.0","id":9,"method":"ping","params":{}}'
```

Response: `result: {}` (empty object = server is alive)

#### Completion

```bash
curl -sf -X POST "$BASE/api/proxy" \
  -H "Content-Type: application/json" \
  -H "x-mcp-url: $MCP_URL" \
  -d '{
    "jsonrpc":"2.0","id":10,"method":"completion/complete",
    "params":{
      "ref":{"type":"ref/resource","uri":"resource://"},
      "argument":{"name":"uri","value":"resource://"}
    }
  }'
```

#### Logging

```bash
curl -sf -X POST "$BASE/api/proxy" \
  -H "Content-Type: application/json" \
  -H "x-mcp-url: $MCP_URL" \
  -d '{
    "jsonrpc":"2.0","id":11,"method":"logging/setLevel",
    "params":{"level":"debug"}
  }'
```

---

### Chat Endpoints (LLM + MCP)

#### Streaming Chat

```
POST /inspector/api/chat/stream
```

Request body:
```json
{
  "mcpServerUrl": "http://localhost:3000/mcp",
  "llmConfig": {
    "provider": "openai",
    "model": "gpt-4o",
    "apiKey": "sk-..."
  },
  "authConfig": {
    "type": "none|basic|bearer|oauth",
    "username": "...",
    "password": "...",
    "token": "...",
    "oauthTokens": {"access_token": "..."}
  },
  "messages": [
    {"role": "user", "content": "...", "attachments": []}
  ]
}
```

Response: Server-Sent Events stream.

Event types:
- `{"type":"message","id":"msg-...","role":"assistant"}` — start
- `{"type":"text","id":"msg-...","content":"chunk"}` — text tokens
- `{"type":"tool-call","id":"msg-...","toolCallId":"...","toolName":"...","args":{}}` — tool invocation
- `{"type":"tool-result","id":"msg-...","toolCallId":"...","toolName":"...","result":{}}` — tool result
- `{"type":"error","data":{"message":"..."}}` — error
- `{"type":"done","id":"msg-..."}` — end

Parse streaming response:
```bash
# Extract text
... | grep -o '"type":"text"[^}]*' | grep -oP '"content":"[^"]*"'

# Extract tool calls
... | grep '"type":"tool-call"'

# Extract tool results
... | grep '"type":"tool-result"'
```

#### Non-streaming Chat

```
POST /inspector/api/chat
```

Same request body as streaming. Returns:
```json
{"content": "assistant response text", "toolCalls": []}
```

#### Agent Configuration (hardcoded in inspector)

The chat endpoints create an MCPAgent with these fixed settings:
- `maxSteps: 10` — maximum 10 tool invocations per turn
- `memoryEnabled: false` — no built-in memory (uses externalHistory)
- `exposeResourcesAsTools: false`
- `exposePromptsAsTools: false`
- System prompt: "You are a helpful assistant with access to MCP tools..."

---

### RPC Event Stream

#### Subscribe to RPC events (SSE)

```
GET /inspector/api/rpc/stream?replay=3&serverIds=http://localhost:3000/mcp
```

Query params:
- `replay` (number, default 3) — how many recent events to replay on connect. Set 0 for none.
- `serverIds` (comma-separated string) — filter by server IDs. Empty = all servers.

Events:
```json
{"type":"rpc","serverId":"...","direction":"send|receive","timestamp":"...","message":{...}}
```

Keepalive comments sent every 15 seconds: `: keepalive <timestamp>`

#### Post RPC event

```
POST /inspector/api/rpc/log
```

Body: `{"serverId":"...","direction":"send|receive","timestamp":"...","message":{...}}`

#### Clear RPC log

```
DELETE /inspector/api/rpc/log
DELETE /inspector/api/rpc/log?serverIds=http://localhost:3000/mcp
```

Buffer limit: 1000 events per server (FIFO).

---

### Authentication through proxy

Pass auth headers and they get forwarded to the MCP server:

```bash
# Bearer token
-H "Authorization: Bearer $TOKEN"

# Basic auth
-H "Authorization: Basic $(echo -n 'user:pass' | base64)"

# URL-embedded auth (fallback)
# If URL is http://user:pass@host/mcp, inspector extracts and sends Basic auth
```

For OAuth, the inspector has a built-in proxy at `/inspector/api/oauth/*` that handles redirect flows. This is browser-only — not usable from curl.

---

### Widget Endpoints

```
POST /inspector/api/resources/widget/store    # Store widget data
GET  /inspector/api/resources/widget/:toolId  # Render widget container
GET  /inspector/api/resources/widget-content/:toolId  # Render widget content HTML
```

Widget data expires after 1 hour. 5-minute cleanup sweep. In-memory only.

---

### Telemetry (disabled for testing)

```
POST /inspector/api/tel/posthog
POST /inspector/api/tel/scarf
```

Both are silenced when `MCP_USE_ANONYMIZED_TELEMETRY=false` or `NODE_ENV=test`.

---

## JSON-RPC Helper Pattern

To reduce repetition in test scripts, define a helper function:

```bash
BASE="http://localhost:${PORT}/inspector"

rpc() {
  local method="$1"
  local params="${2:-{}}"
  local id="${3:-1}"
  curl -sf -X POST "${BASE}/api/proxy" \
    -H "Content-Type: application/json" \
    -H "x-mcp-url: ${MCP_URL}" \
    ${AUTH_HEADER:+-H "$AUTH_HEADER"} \
    -d "{\"jsonrpc\":\"2.0\",\"id\":${id},\"method\":\"${method}\",\"params\":${params}}"
}

# Usage:
rpc "tools/list"
rpc "tools/call" '{"name":"my_tool","arguments":{"q":"test"}}'
rpc "resources/read" '{"uri":"resource://data"}'
```
