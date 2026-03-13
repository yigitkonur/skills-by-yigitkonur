# Testing and Debugging MCP Servers

Test and debug MCP servers built with mcp-use across every stage of development.

---

## 1. MCP Inspector

### Built-in Inspector (Dev Mode)

In dev mode (`npx mcp-use dev`), the Inspector auto-opens at
`http://localhost:3000/inspector`. Include in production builds with
`mcp-use build --with-inspector`.

### Standalone Inspector

```bash
npx @modelcontextprotocol/inspector                                  # Launch browser UI
npx @modelcontextprotocol/inspector node dist/server.js              # Test stdio server
npx @modelcontextprotocol/inspector --url http://localhost:3000/mcp   # Test HTTP server
npx @modelcontextprotocol/inspector -e API_KEY=sk-123 node dist/server.js  # With env vars
```

### What to Test with Inspector

| Action | What to verify |
|---|---|
| **List tools** | All tools appear with correct names, descriptions, schemas |
| **Call each tool** | Responses return expected content type (text, object, image) |
| **List/read resources** | URIs, content, MIME types are accurate |
| **List/get prompts** | Argument definitions render correctly with sample args |
| **Subscribe to resource** | Updates fire when resource content changes |

---

## 2. Development Workflow

### mcp-use Dev Server

```bash
mcp-use dev                          # HMR + Inspector + type generation
mcp-use dev --port 8080 --no-open    # Custom port, no auto-open
mcp-use dev --no-hmr                 # Falls back to tsx watch
```

**Hot-reloadable (no restart):** tools, prompts, resources, handlers, schemas.
**Requires restart:** server config, middleware, OAuth config.
Connected clients receive `list_changed` notifications automatically.

### Type Generation

```bash
mcp-use generate-types                          # From tool Zod schemas
mcp-use generate-types --server src/server.ts   # Custom entry file
```

Creates `.mcp-use/tool-registry.d.ts` for type-safe `useCallTool` in widgets.
Add to `tsconfig.json`: `"include": ["index.ts", "src/**/*", "resources/**/*", ".mcp-use/**/*"]`.
Runs automatically in `mcp-use dev`; run manually for CI or after schema changes.

### Recommended package.json Scripts

```json
{
  "scripts": {
    "dev": "mcp-use dev src/server.ts",
    "build": "tsc",
    "start": "node dist/server.js",
    "inspect": "npm run build && npx @modelcontextprotocol/inspector node dist/server.js",
    "typecheck": "tsc --noEmit",
    "generate-types": "mcp-use generate-types"
  }
}
```

---

## 3. Manual Testing with curl

### Initialize → List → Call

```bash
# 1. Initialize and capture session ID
curl -s -D - -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0", "method": "initialize",
    "params": {
      "protocolVersion": "2025-11-25", "capabilities": {},
      "clientInfo": { "name": "curl-test", "version": "1.0.0" }
    }, "id": 1
  }'
# Extract Mcp-Session-Id from response headers

# 2. List tools
curl -s -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" -H "Mcp-Session-Id: <session-id>" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":2}' | jq .

# 3. Call a tool
curl -s -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" -H "Mcp-Session-Id: <session-id>" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"greet","arguments":{"name":"World"}},"id":3}' | jq .

# 4. Resources and prompts
curl -s -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" -H "Mcp-Session-Id: <session-id>" \
  -d '{"jsonrpc":"2.0","method":"resources/read","params":{"uri":"config://app"},"id":4}' | jq .

curl -s -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" -H "Mcp-Session-Id: <session-id>" \
  -d '{"jsonrpc":"2.0","method":"prompts/get","params":{"name":"summarize","arguments":{"topic":"MCP"}},"id":5}' | jq .
```

### SSE / Streaming Transport

```bash
curl -N -H "Accept: text/event-stream" http://localhost:3000/mcp/sse  # Open SSE stream
# In separate terminal:
curl -s -X POST http://localhost:3000/mcp/message \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

---

## 4. Claude Desktop Testing

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

For HTTP: `{ "mcpServers": { "my-http-server": { "url": "http://localhost:3000/mcp" } } }`

**Verify:** Quit Claude (Cmd+Q) → Reopen → Click 🔨 to confirm tools appear.

```bash
tail -f ~/Library/Logs/Claude/mcp*.log
grep -i "error\|fail\|crash" ~/Library/Logs/Claude/mcp*.log
```

| Issue | Fix |
|---|---|
| Tools don't appear | Verify JSON is valid; restart Claude Desktop |
| Server keeps restarting | Check logs for crash; ensure deps installed |
| Env vars missing | Use absolute paths; shell profile vars not inherited |

---

## 5. Logging for Debugging

### Debug Modes

```bash
DEBUG=1 node dist/server.js   # Logs registrations, session lifecycle
DEBUG=2 node dist/server.js   # Full JSON-RPC request/response bodies
```

### Logger API

```typescript
import { Logger } from "mcp-use/server";

Logger.configure({ level: "debug", format: "detailed" });
// Levels: silent | error | warn | info | http | verbose | debug | silly
// Formats: "minimal" (default) | "detailed"

const logger = Logger.get("my-component");
logger.info("Initialized");
logger.debug("Processing", { userId: 123 });
```

### Tool-Level Logging with ctx.log

Sends log messages directly to connected clients:

```typescript
server.tool(
  { name: "process_data", schema: z.object({ items: z.array(z.string()) }) },
  async ({ items }, ctx) => {
    await ctx.log("info", "Starting processing");
    await ctx.log("debug", `${items.length} items`, "my-tool");

    for (const item of items) {
      if (!item.trim()) { await ctx.log("warning", "Empty item, skipping"); continue; }
      try { await processItem(item); }
      catch (err) { await ctx.log("error", `Failed: ${err.message}`); }
    }
    return text("Done");
  }
);
```

Levels: `debug`, `info`, `notice`, `warning`, `error`, `critical`, `alert`, `emergency`.

**Stdio servers:** Always use `console.error()` — `console.log()` corrupts JSON-RPC.

---

## 6. Observability

### ObservabilityManager

```typescript
import { createManager, getDefaultManager } from "mcp-use/observability";

const manager = createManager({ observe: true });  // Custom instance
const defaultManager = getDefaultManager();          // Singleton
```

### Langfuse Integration

```typescript
import { langfuseClient, langfuseHandler } from "mcp-use/observability";

const client = langfuseClient();     // Trace tool calls, sessions, costs
const handler = langfuseHandler();   // Returns BaseCallbackHandler | null
```

```bash
export LANGFUSE_PUBLIC_KEY=pk-lf-...
export LANGFUSE_SECRET_KEY=sk-lf-...
export LANGFUSE_HOST=https://cloud.langfuse.com
```

---

## 7. Common Debug Scenarios

| Scenario | Debug steps |
|---|---|
| **Tool not appearing** | Verify name/description non-empty. Run `DEBUG=1` to see registrations. |
| **Wrong response format** | Inspector → view raw JSON-RPC. Use `text()`, `object()`, `binary()` helpers. |
| **Server crashes on call** | Wrap handler in try/catch. Check Zod schema matches input shape. |
| **Slow responses** | `console.time()`/`console.timeEnd()`. Check for blocking I/O. |
| **Session not persisting** | Verify `Mcp-Session-Id` header on every request. Check `.mcp-use/sessions.json`. |
| **Resources not updating** | Call `server.notifyResourceUpdated(uri)`. Verify client subscribed. |
| **Auth failures** | Verify OAuth env vars. Check redirect URI. Inspect `/oauth/callback`. |
| **CORS errors** | Set `cors` in server config. Check preflight in browser console. |
| **HMR not working** | Ensure `--no-hmr` not set. Config changes always require full restart. |

### JSON-RPC Error Codes

| Code | Meaning | Likely cause |
|---|---|---|
| -32700 | Parse error | Malformed JSON |
| -32600 | Invalid request | Missing JSON-RPC fields |
| -32601 | Method not found | Typo or capability not advertised |
| -32602 | Invalid params | Arguments don't match schema |
| -32603 | Internal error | Unhandled exception in handler |

### Debug Template

```typescript
server.tool(
  { name: "my-tool", schema: z.object({ input: z.string() }) },
  async ({ input }, ctx) => {
    await ctx.log("debug", `Called with: ${input}`, "my-tool");
    try {
      console.time("my-tool");
      const result = await doWork(input);
      console.timeEnd("my-tool");
      return text(JSON.stringify(result, null, 2));
    } catch (err) {
      await ctx.log("error", `${err instanceof Error ? err.message : String(err)}`);
      return text(`Error: ${err instanceof Error ? err.message : String(err)}`);
    }
  }
);
```

---

## 8. Testing Patterns

### Unit Testing Tool Handlers

```typescript
// Extract handler logic into testable functions
async function handleGreet(args: { name: string }) {
  return `Hello, ${args.name}!`;
}

// Test with vitest/jest
it("returns greeting", async () => {
  expect(await handleGreet({ name: "World" })).toBe("Hello, World!");
});
```

### E2E curl Script

```bash
#!/bin/bash
set -e
BASE="http://localhost:3000/mcp"

SESSION=$(curl -s -D - -X POST $BASE -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"e2e","version":"1.0.0"}},"id":1}' \
  | grep -i "mcp-session-id" | awk '{print $2}' | tr -d '\r')
echo "Session: $SESSION"

TOOLS=$(curl -s -X POST $BASE -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: $SESSION" -d '{"jsonrpc":"2.0","method":"tools/list","id":2}')
echo "Tools: $(echo $TOOLS | jq '.result.tools | length') found"
```

---

## 9. Performance Debugging

```bash
node --inspect dist/server.js      # Chrome DevTools / VS Code debugger
node --inspect-brk dist/server.js  # Break on first line
node --prof dist/server.js         # V8 profiling

# Connection timing
curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" \
  -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"ping","id":99}'
```

---

## 10. Testing Checklist

- [ ] All tools listed in Inspector with correct schemas
- [ ] Each tool returns expected output for valid input and meaningful error for invalid input
- [ ] Resources load with correct content and MIME types
- [ ] Prompts render correctly with sample arguments
- [ ] Server starts without errors from a clean build
- [ ] Server works in Claude Desktop (tools appear, calls succeed)
- [ ] HTTP: initialize → tools/list → tools/call sequence works
- [ ] `mcp-use generate-types` succeeds and types compile
- [ ] `DEBUG=2` shows correct request/response logging
- [ ] Environment variables documented and validated on startup
- [ ] No `console.log()` in stdio server code; CORS/auth tested
