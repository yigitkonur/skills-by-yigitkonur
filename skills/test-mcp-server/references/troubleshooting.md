# MCP Inspector Troubleshooting

Quick reference for common failures during testing.

## Inspector Won't Start

### Port in use
```
Error: No available port found after trying 100 ports starting from 8080
```
**Fix:** Use a higher starting port:
```bash
npx @mcp-use/inspector --port 19000 --no-open
```

### npx download fails
```
npm ERR! code ETARGET
```
**Fix:** Clear npm cache and retry:
```bash
npm cache clean --force
npx @mcp-use/inspector@latest --no-open
```

### Node version too old
Inspector requires Node.js ^20.19.0 or >=22.12.0.
```bash
node --version  # Check your version
```

## Can't Connect to MCP Server

### Server not running
```bash
# Check if anything is listening on the expected port
lsof -i :3000
# Or
curl -sf http://localhost:3000/mcp -o /dev/null && echo "reachable" || echo "unreachable"
```

### Wrong URL format
The proxy requires `x-mcp-url` header with a valid URL. Common mistakes:
- Missing protocol: `localhost:3000/mcp` → should be `http://localhost:3000/mcp`
- Trailing slash issues: Try both `http://localhost:3000/mcp` and `http://localhost:3000/mcp/`
- Wrong path: The MCP endpoint might be at `/mcp`, `/api/mcp`, or just `/`

### CORS issues
The inspector adds `cors({ origin: "*" })` so this shouldn't be an issue. If you see CORS errors in the browser, you're probably hitting the MCP server directly instead of going through the inspector proxy.

### SSL/TLS errors
For `https://` servers with self-signed certs:
```bash
NODE_TLS_REJECT_UNAUTHORIZED=0 npx @mcp-use/inspector --url https://... --no-open
```

## Proxy Returns Errors

### "Method not found" (-32601)
The server doesn't implement the requested MCP method. This is expected for optional methods like `completion/complete` or `logging/setLevel` if the server doesn't advertise those capabilities.

**Check capabilities first:**
```bash
rpc "initialize" '...' | jq '.result.capabilities'
```

Only test methods the server advertises.

### "Invalid params" (-32602)
Your JSON-RPC params are malformed. Double-check:
- `tools/call` needs `{"name":"...","arguments":{...}}`
- `resources/read` needs `{"uri":"..."}`
- `prompts/get` needs `{"name":"...","arguments":{...}}`

### "Internal error" (-32603)
The server threw an unhandled exception. This is a bug in the server, not the inspector. Check the server's stderr for stack traces.

### Connection reset / timeout
The server might be crashing on certain requests. Check:
```bash
# Is the server still running after the failed request?
rpc "ping"
```

If ping fails after a tool call, the server crashed. That's a critical bug.

## Chat Endpoint Failures

### "Unsupported LLM provider: xyz"
Only `"openai"`, `"anthropic"`, and `"google"` are valid provider values. For OpenRouter or other OpenAI-compatible APIs, use `"openai"` with a base URL override. See `references/providers.md`.

### "Missing required fields: mcpServerUrl, llmConfig, messages"
Your request body is missing one of these required fields. Check your JSON structure.

### Chat returns empty content
- The LLM might not have understood the request
- The API key might be invalid (check the error field)
- The model might not support tool-use (older models)

### Chat stream hangs
The streaming endpoint might hang if:
- The LLM is doing a long chain of tool calls (max 10 steps)
- The MCP server is slow to respond
- Network issues between inspector and LLM provider

Use the non-streaming endpoint (`/api/chat`) instead for more reliable results in scripts.

### "Tool call timeout" in stream
The MCPAgent's tool call timed out (30 second default in the widget callTool, but varies for direct tool calls). The MCP server is taking too long to respond.

### LLM calls wrong tool / no tool
This is a model quality issue, not an inspector bug. Try:
- A more capable model (gpt-4o instead of gpt-4o-mini)
- A more specific prompt
- Adding context about available tools in the system message

## RPC Stream Issues

### No events appearing
- Check the `serverIds` filter — if set, only events from those servers appear
- Check `replay` — set to `0` means no historical events
- Make sure the browser UI (or your curl calls) are actually sending traffic through the proxy

### Events stop after a while
The SSE connection might have timed out. Reconnect:
```bash
curl -sf -N "http://localhost:${PORT}/inspector/api/rpc/stream?replay=10"
```

## JSON-RPC Debugging Tips

### See raw request/response
```bash
# Verbose curl output
curl -v -X POST "${BASE}/api/proxy" \
  -H "Content-Type: application/json" \
  -H "x-mcp-url: ${MCP_URL}" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' 2>&1
```

### Validate JSON before sending
```bash
echo '{"name":"my_tool","arguments":{"key":"value"}}' | jq . > /dev/null && echo "valid JSON" || echo "INVALID JSON"
```

### Common JSON escaping issues
```bash
# BAD: Double quotes inside double quotes
-d "{"jsonrpc":"2.0"}"

# GOOD: Single quotes outer, double inner
-d '{"jsonrpc":"2.0"}'

# GOOD: Escaped inner quotes
-d "{\"jsonrpc\":\"2.0\"}"

# BEST for complex payloads: heredoc
curl -X POST "$URL" -H "Content-Type: application/json" -d @- <<'EOF'
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"my_tool","arguments":{"complex":"data with 'quotes'"}}}
EOF
```

## Cleanup

Always kill the inspector when done:
```bash
kill $INSPECTOR_PID 2>/dev/null

# If you lost the PID:
pkill -f "@mcp-use/inspector"

# Or find and kill by port:
lsof -ti :19876 | xargs kill
```
