# curl Handshake — initialize → list → call

The Inspector is the primary validation tool, but `curl` is faster for scripted smoke tests, CI, and reproducing client bugs in a known-good shell. Every JSON-RPC call after `initialize` MUST carry the session ID and protocol version headers.

---

## Required headers

| Header | Required when | Value |
|---|---|---|
| `Content-Type` | Always | `application/json` |
| `Accept` | Always | `application/json, text/event-stream` |
| `Mcp-Session-Id` | After `initialize` | Captured from `initialize` response headers |
| `MCP-Protocol-Version` | After `initialize` | `2025-11-25` (current) |

Skip any of these and you'll get a 400 or a JSON-RPC error.

---

## Step 1 — Initialize and capture the session ID

```bash
BASE=http://localhost:3000/mcp

curl -s -D - -X POST "$BASE" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-11-25",
      "capabilities": {},
      "clientInfo": { "name": "curl-test", "version": "1.0.0" }
    },
    "id": 1
  }'
```

The `-D -` flag prints response headers; pluck `Mcp-Session-Id` from there.

**One-liner to capture into a shell var:**

```bash
SESSION=$(curl -s -D - -X POST "$BASE" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"curl","version":"1.0.0"}},"id":1}' \
  | grep -i "mcp-session-id" | awk '{print $2}' | tr -d '\r')
echo "SESSION=$SESSION"
```

---

## Step 2 — List tools

```bash
curl -s -X POST "$BASE" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: $SESSION" \
  -H "MCP-Protocol-Version: 2025-11-25" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":2}' | jq
```

---

## Step 3 — Call a tool

```bash
curl -s -X POST "$BASE" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: $SESSION" \
  -H "MCP-Protocol-Version: 2025-11-25" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": { "name": "greet", "arguments": { "name": "World" } },
    "id": 3
  }' | jq
```

For tools that declare `outputSchema` or return `structuredContent`, verify both surfaces. The text surface should be readable; the structured surface should mirror the essential body, not just metadata. Secrets belong in `_meta`, not `structuredContent`.

```bash
curl -s -X POST "$BASE" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: $SESSION" \
  -H "MCP-Protocol-Version: 2025-11-25" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"greet","arguments":{"name":"World"}},"id":4}' \
  | jq '.result | {text: .content[0].text, structuredContent, metaKeys: (._meta // {} | keys)}'
```

---

## Resources and prompts

```bash
# Read a resource
curl -s -X POST "$BASE" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: $SESSION" \
  -H "MCP-Protocol-Version: 2025-11-25" \
  -d '{"jsonrpc":"2.0","method":"resources/read","params":{"uri":"config://app"},"id":5}' | jq

# Get a prompt
curl -s -X POST "$BASE" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: $SESSION" \
  -H "MCP-Protocol-Version: 2025-11-25" \
  -d '{"jsonrpc":"2.0","method":"prompts/get","params":{"name":"summarize","arguments":{"topic":"MCP"}},"id":6}' | jq
```

---

## End-to-end smoke script

Drop into `scripts/smoke.sh`. Exits non-zero on any curl failure thanks to `set -e`.

```bash
#!/bin/bash
set -e
BASE="${BASE:-http://localhost:3000/mcp}"

SESSION=$(curl -s -D - -X POST "$BASE" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"smoke","version":"1.0.0"}},"id":1}' \
  | grep -i "mcp-session-id" | awk '{print $2}' | tr -d '\r')

[ -z "$SESSION" ] && { echo "No session ID returned"; exit 1; }
echo "Session: $SESSION"

COUNT=$(curl -s -X POST "$BASE" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: $SESSION" \
  -H "MCP-Protocol-Version: 2025-11-25" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":2}' | jq '.result.tools | length')

echo "Tools: $COUNT"
[ "$COUNT" -gt 0 ] || { echo "No tools advertised"; exit 1; }
```

---

## Common curl failures

| Symptom | Cause | Fix |
|---|---|---|
| 400 with `Missing session ID` | Forgot `Mcp-Session-Id` after init | Capture from initialize response and pass on every request |
| 400 with `Unsupported protocol version` | Old `MCP-Protocol-Version` value | Use `2025-11-25` |
| 406 Not Acceptable | Missing `Accept` header | Send `application/json, text/event-stream` |
| Empty body, hangs | Server is streaming (SSE) but client used POST | Add `Accept: text/event-stream` |

---

## Legacy `/sse` alias

Older clients use the `/sse` endpoint. Modern clients should target `/mcp`.

```bash
curl -N -H "Accept: text/event-stream" http://localhost:3000/sse
```
