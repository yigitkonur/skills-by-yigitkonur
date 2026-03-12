# Testing and Debugging MCP Servers

Test and debug MCP servers built with mcp-use across every stage of development.

---

## 1. MCP Inspector

The MCP Inspector is the primary graphical testing tool for MCP servers.

### Installation and Launch

```bash
# Launch Inspector (opens browser UI)
npx @modelcontextprotocol/inspector

# Test a stdio server directly
npx @modelcontextprotocol/inspector node dist/server.js

# Test an HTTP server by URL
npx @modelcontextprotocol/inspector --url http://localhost:3000/mcp

# Pass environment variables to the server
npx @modelcontextprotocol/inspector -e API_KEY=sk-123 node dist/server.js
```

### What to Test with Inspector

| Action | What to verify |
|---|---|
| **List tools** | All tools appear with correct names, descriptions, and input schemas |
| **Call each tool** | Responses return expected content type (text, object, image) |
| **List resources** | All static and dynamic resources appear with correct URIs |
| **Read resources** | Content loads correctly, MIME types are accurate |
| **List prompts** | All prompts appear with argument definitions |
| **Get prompt** | Template renders correctly with sample arguments |
| **Subscribe to resource** | Updates fire when resource content changes |

---

## 2. Manual Testing with curl (HTTP Servers)

### Initialize a Session

```bash
# Initialize and capture the session ID from Mcp-Session-Id response header
curl -s -D - -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": { "name": "curl-test", "version": "1.0.0" }
    },
    "id": 1
  }'
```

### List and Call Tools

```bash
# List available tools
curl -s -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: <session-id>" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":2}' | jq .

# Call a specific tool
curl -s -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: <session-id>" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": { "name": "greet", "arguments": { "name": "World" } },
    "id": 3
  }' | jq .
```

### Test Resources and Prompts

```bash
# List and read resources
curl -s -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" -H "Mcp-Session-Id: <session-id>" \
  -d '{"jsonrpc":"2.0","method":"resources/list","id":4}' | jq .

curl -s -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" -H "Mcp-Session-Id: <session-id>" \
  -d '{"jsonrpc":"2.0","method":"resources/read","params":{"uri":"config://app"},"id":5}' | jq .

# List and render prompts
curl -s -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" -H "Mcp-Session-Id: <session-id>" \
  -d '{"jsonrpc":"2.0","method":"prompts/list","id":6}' | jq .

curl -s -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" -H "Mcp-Session-Id: <session-id>" \
  -d '{"jsonrpc":"2.0","method":"prompts/get","params":{"name":"summarize","arguments":{"topic":"MCP"}},"id":7}' | jq .
```

---

## 3. Claude Desktop Testing

### Add Server to Configuration

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["/absolute/path/to/dist/server.js"],
      "env": { "API_KEY": "your-key-here" }
    }
  }
}
```

For HTTP servers: `{ "mcpServers": { "my-http-server": { "url": "http://localhost:3000/mcp" } } }`

### Restart and Verify

1. Quit Claude Desktop completely (Cmd+Q).
2. Reopen Claude Desktop.
3. Click the hammer icon (🔨) in the chat input to confirm tools appear.

### Check Logs

```bash
tail -f ~/Library/Logs/Claude/mcp*.log
grep -i "error\|fail\|crash" ~/Library/Logs/Claude/mcp*.log
```

| Issue | Fix |
|---|---|
| Tools don't appear | Verify JSON is valid; restart Claude Desktop |
| Server keeps restarting | Check logs for crash errors; ensure deps installed |
| Environment variables missing | Use absolute paths; shell profile vars not inherited |

---

## 4. Development Workflow

```bash
# Live reload during development
npx tsx watch src/server.ts

# Build and test with Inspector
npm run build && npx @modelcontextprotocol/inspector node dist/server.js

# Typecheck without emitting
npx tsc --noEmit
```

### Recommended package.json Scripts

```json
{
  "scripts": {
    "dev": "tsx watch src/server.ts",
    "build": "tsc",
    "start": "node dist/server.js",
    "inspect": "npm run build && npx @modelcontextprotocol/inspector node dist/server.js",
    "typecheck": "tsc --noEmit"
  }
}
```

---

## 5. Debugging Tips

### Use stderr for Debug Output

Stdio servers use stdout for JSON-RPC. Always log to stderr:

```typescript
// ✅ Correct — logs to stderr
console.error("[DEBUG] Tool called:", toolName);

// ❌ Wrong — corrupts the JSON-RPC stream
console.log("Debug output here");
```

### Enable Verbose Logging

```bash
LOG_LEVEL=debug node dist/server.js
npx @modelcontextprotocol/inspector -e LOG_LEVEL=debug node dist/server.js
```

### Use Node.js Debugger

```bash
node --inspect dist/server.js          # Attach Chrome DevTools or VS Code
node --inspect-brk dist/server.js      # Break on first line
```

### JSON-RPC Error Codes

| Code | Meaning | Likely cause |
|---|---|---|
| -32700 | Parse error | Malformed JSON in request |
| -32600 | Invalid request | Missing required JSON-RPC fields |
| -32601 | Method not found | Typo in method name or capability not advertised |
| -32602 | Invalid params | Arguments don't match tool's input schema |
| -32603 | Internal error | Unhandled exception in tool handler |

---

## 6. Common Debug Scenarios

| Scenario | Debug steps |
|---|---|
| **Tool not appearing** | Verify name/description are non-empty. Check startup logs for registration errors. |
| **Wrong response format** | Use Inspector to view raw JSON-RPC response. Verify you return `text()` or `object()`. |
| **Server crashes on tool call** | Wrap handler in try/catch. Log full error with `console.error(err)`. |
| **Slow responses** | Profile with `console.time()` / `console.timeEnd()`. Check for blocking I/O. |
| **Memory leaks** | Start with `node --max-old-space-size=256`. Use `--heap-prof` for snapshots. |
| **Session not persisting** | Verify `Mcp-Session-Id` header sent on every request. Check session store config. |
| **Resources not updating** | Call `server.sendResourceUpdated(uri)` after changes. Verify client subscribed. |
| **Auth failures** | Verify OAuth env vars. Check redirect URI matches. Inspect `/oauth/callback` response. |

### Debug Template

```typescript
server.tool(
  { name: "my-tool", schema: z.object({ input: z.string() }) },
  async ({ input }, ctx) => {
    console.error(`[my-tool] Called with: ${input}`);
    try {
      console.time("my-tool");
      const result = await doWork(input);
      console.timeEnd("my-tool");
      return text(JSON.stringify(result, null, 2));
    } catch (err) {
      console.error(`[my-tool] Error:`, err);
      return text(`Error: ${err instanceof Error ? err.message : String(err)}`);
    }
  }
);
```

---

## 7. Testing Checklist

Run through before every release:

- [ ] All tools listed in Inspector with correct schemas
- [ ] Each tool returns expected output for valid input
- [ ] Each tool returns meaningful error for invalid input
- [ ] Resources load with correct content and MIME types
- [ ] Prompts render correctly with sample arguments
- [ ] Server starts without errors from a clean build
- [ ] Server works in Claude Desktop (tools appear, calls succeed)
- [ ] HTTP server responds to initialize → tools/list → tools/call sequence
- [ ] Environment variables documented and validated on startup
- [ ] No `console.log()` calls remain in stdio server code
