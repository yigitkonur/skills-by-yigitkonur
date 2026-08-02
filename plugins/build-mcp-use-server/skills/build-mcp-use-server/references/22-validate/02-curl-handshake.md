# curl Handshake: v2 Protocol Walkthrough

*Read this when you need to verify an MCP server responds correctly to v2 streamable HTTP protocol.*

Copy-paste these exact curl commands against a local `mcp-use dev` server. Default URL: `http://localhost:3000/mcp`.

## 1. Initialize (Handshake)

```bash
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
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

- **HTTP Method**: POST only (no GET/DELETE for tool calls; see references/09-transports/02-streamable-http.md for other methods)
- **Protocol version**: Set `Mcp-Protocol-Version: 2024-11-05` header (MCP spec v2)
- **JSON-RPC 2.0**: All requests use standard JSON-RPC format (id, jsonrpc, method, params)
- **Content-Type**: Always `application/json`
- **Stateless**: Each curl call is independent; no session management
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
| 400 Bad Request | Check JSON syntax; validate header `Content-Type: application/json` |
| `"protocolVersion mismatch"` error | Ensure header `Mcp-Protocol-Version: 2024-11-05` matches server version |
| Tool call returns error | Check tool `name` matches exactly; verify `arguments` match input schema |

## With a Deployed Server

Replace `http://localhost:3000` with your deployment URL:

```bash
curl -X POST https://my-server.deploy.mcp-use.com/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Protocol-Version: 2024-11-05" \
  -d '{ ... }'
```

For tunneled endpoints (via `mcp-use dev --tunnel`):

```bash
curl -X POST https://happy-blue.local.mcp-use.run/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Protocol-Version: 2024-11-05" \
  -d '{ ... }'
```
