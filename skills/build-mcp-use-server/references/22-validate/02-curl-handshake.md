# Legacy Compatibility curl Handshake

*Read this when verifying the legacy initialize/tools-list/tools-call compatibility path. For the native modern `2026-07-28` wire (which has no `initialize`), start with `references/09-transports/02-streamable-http.md`.*

Copy these commands against a local `mcp-use dev` server. Default URL: `http://localhost:3000/mcp`.

**Legacy-only required header:** every legacy POST in this walkthrough must send `Accept: application/json, text/event-stream`; omitting either media type returns `406 Not Acceptable`. Modern-wire POSTs do not have this requirement.

## 1. Initialize (Handshake)

```bash
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Protocol-Version: 2024-11-05" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": { },
      "clientInfo": {
        "name": "curl-test",
        "version": "1.0"
      }
    }
  }'
```

Expected response (HTTP 200):
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": { },
      "resources": { },
      "prompts": { }
    },
    "serverInfo": {
      "name": "my-server",
      "version": "1.0.0"
    }
  }
}
```

## 2. List Tools

```bash
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": { }
  }'
```

Expected response (HTTP 200):
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "get-weather",
        "description": "Get weather for a location",
        "inputSchema": {
          "type": "object",
          "properties": {
            "location": {
              "type": "string",
              "description": "City name"
            }
          },
          "required": ["location"]
        }
      }
    ]
  }
}
```

## 3. Call a Tool

```bash
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "get-weather",
      "arguments": {
        "location": "San Francisco"
      }
    }
  }'
```

Expected response (HTTP 200):
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Sunny, 72°F"
      }
    ]
  }
}
```

## Key v2 Details

- **HTTP Method**: POST only for JSON-RPC calls (no GET/DELETE for tool calls; see references/09-transports/02-streamable-http.md for other methods)
- **Accept header required**: `Accept: application/json, text/event-stream` on every POST — the server returns `406 Not Acceptable` without it, regardless of any other header
- **Protocol version header is optional**: `Mcp-Protocol-Version` is only validated when present. If sent, it must be one of the server's supported versions (`2025-11-25`, `2025-06-18`, `2025-03-26`, `2024-11-05`, `2024-10-07` as of this SDK build) or the server responds `400 Bad Request: Unsupported protocol version`. Omitting it is fine — the `initialize` call's `params.protocolVersion` is what actually negotiates the session.
- **JSON-RPC 2.0**: All requests use standard JSON-RPC format (id, jsonrpc, method, params)
- **Content-Type**: Always `application/json`
- **Stateless**: Each curl call is independent; no session management, and no `notifications/initialized` call is required between them — every POST builds a fresh server instance from the tool/resource/prompt registry
- **Error response** (HTTP 200 with error envelope):
  ```json
  {
    "jsonrpc": "2.0",
    "id": 3,
    "error": {
      "code": -32602,
      "message": "Invalid params: missing 'location'"
    }
  }
  ```

## Troubleshooting

| Symptom | Check |
| --- | --- |
| 404 or 405 | Verify server running at correct URL + `/mcp` suffix |
| `406 Not Acceptable` | Missing `Accept` header — must include both `application/json` and `text/event-stream` |
| 400 Bad Request | Check JSON syntax; validate header `Content-Type: application/json`; if you sent `Mcp-Protocol-Version`, confirm it's a supported version string |
| `Bad Request: Unsupported protocol version` | The optional `Mcp-Protocol-Version` header was sent but isn't recognized — drop it or match a supported version |
| Tool call returns error | Check tool `name` matches exactly; verify `arguments` match input schema |

## With a Deployed Server

Replace `http://localhost:3000/mcp` with the exact MCP endpoint supplied by the platform/dashboard — never infer a Manufact hostname from a slug:

```bash
export MCP_URL="PASTE_THE_EXACT_DEPLOYED_MCP_URL"
curl -X POST "${MCP_URL}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Protocol-Version: 2024-11-05" \
  -d '{ ... }'
```

For tunneled endpoints (via `mcp-use dev --tunnel`):

```bash
curl -X POST https://happy-blue.local.mcp-use.run/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Protocol-Version: 2024-11-05" \
  -d '{ ... }'
```
