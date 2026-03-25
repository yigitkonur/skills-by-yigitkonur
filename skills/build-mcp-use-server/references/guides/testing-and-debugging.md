# Testing and Debugging MCP Servers

Test and debug MCP servers built with mcp-use across every stage of development.

---

## 1. MCP Inspector

### mcp-use Inspector (Standalone Web UI)

The mcp-use Inspector is a web-based debugging tool that runs separately from your server. Launch it with `npx @mcp-use/inspector`. It starts on port `8080` by default and opens automatically in your browser. It is also available hosted at [inspector.mcp-use.com](https://inspector.mcp-use.com).

```bash
npx @mcp-use/inspector                              # Launch inspector UI on port 8080
npx @mcp-use/inspector --url http://localhost:3000/mcp  # Auto-connect to HTTP server
npx @mcp-use/inspector --port 9000                  # Use a different port
npx @mcp-use/inspector --help                       # Show all options
```

The inspector auto-selects the next available port if `8080` is in use. The terminal shows the actual URL:

```
MCP Inspector running on http://localhost:8081
Auto-connecting to: http://localhost:3000/mcp
```

### Built-in Inspector (mcp-use Server Dev Mode)

When running `mcp-use dev`, the server exposes an inspector UI at `http://localhost:3000/inspector` (served from the same port as your MCP server). This is the mcp-use server's own built-in inspector, separate from `@mcp-use/inspector`.

### What to Test with Inspector

| Tab / Action | What to verify |
|---|---|
| **Tools tab** | All tools appear with correct names, descriptions, schemas; execute each tool and check results |
| **Resources tab** | URIs, content, MIME types are accurate; subscription testing works |
| **Prompts tab** | Argument definitions render correctly; preview generated messages |
| **Elicitation tab** | Pending elicitation requests appear; forms render from server schema |
| **Chat tab** | Configure BYOK API key; LLM invokes tools correctly; tool call JSON visible |
| **RPC Messages panel** | All JSON-RPC send/receive messages visible with direction, method, and payload |
| **Notifications pane** | Server log messages and list-change notifications appear |

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
    "inspect": "npx @mcp-use/inspector --url http://localhost:3000/mcp",
    "typecheck": "tsc --noEmit",
    "generate-types": "mcp-use generate-types"
  }
}
```

### Official Feature Examples (from mcp-use monorepo)

Run any of these from the package root (`libraries/typescript/packages/mcp-use`):

```bash
pnpm run example:server:dns-rebinding   # DNS rebinding protection; verify spoofed Host → 403
pnpm run example:server:streaming-props # Streaming tool props to widgets (partialToolInput / isStreaming)
```

| Example | What it tests |
|---|---|
| `dns-rebinding` | `allowedOrigins` config; curl commands to verify accept/reject behavior |
| `streaming-props` | `generate-code` / `generate-json` tools; widget updates live as LLM streams arguments |

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

# Per spec: after init, all requests MUST include Mcp-Session-Id and MCP-Protocol-Version
# The Accept header MUST list both application/json and text/event-stream

# 2. List tools
curl -s -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: <session-id>" \
  -H "MCP-Protocol-Version: 2025-11-25" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":2}' | jq .

# 3. Call a tool
curl -s -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: <session-id>" \
  -H "MCP-Protocol-Version: 2025-11-25" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"greet","arguments":{"name":"World"}},"id":3}' | jq .

# 4. Resources and prompts
curl -s -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: <session-id>" \
  -H "MCP-Protocol-Version: 2025-11-25" \
  -d '{"jsonrpc":"2.0","method":"resources/read","params":{"uri":"config://app"},"id":4}' | jq .

curl -s -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: <session-id>" \
  -H "MCP-Protocol-Version: 2025-11-25" \
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

## 5. Tunneling for Remote Testing

Tunneling exposes your local MCP server to external MCP clients (ChatGPT, Claude, etc.) without deploying. The tunnel forwards public HTTPS traffic to your local port. Servers must be served on the `/mcp` path.

### Quick Start

```bash
# Option A: start server with tunnel in one command
mcp-use start --port 3000 --tunnel

# Option B: start server first, then tunnel separately
mcp-use start --port 3000
npx @mcp-use/tunnel 3000
```

The tunnel command prints a public URL:

```
Tunnel Created Successfully!

  Public URL:
     https://happy-blue-cat.local.mcp-use.run/mcp

  Subdomain: happy-blue-cat
  Local Port: 3000
```

Use that URL in your MCP client's config (e.g., ChatGPT, Claude Desktop, Inspector).

### Tunnel Limits

| Limit | Value |
|---|---|
| Tunnel lifetime | 24 hours from creation |
| Inactive cleanup | 1 hour of no activity |
| Max creations per IP/hour | 10 |
| Max active tunnels per IP | 5 |

### When to Use Tunneling

- Testing before deployment: verify your server works with real clients
- Iterating locally without redeploying after each change
- Testing OAuth callback URLs that require a public HTTPS endpoint
- Troubleshooting connection issues in a production-like environment

### Setting MCP_URL Behind a Proxy

When the public URL differs from `localhost` (ngrok, Cloudflare tunnels, E2B sandboxes), set `MCP_URL` so widget assets and HMR work correctly:

```bash
MCP_URL=https://abc123.ngrok.io npx @mcp-use/cli dev
MCP_URL=https://my-tunnel.trycloudflare.com npx @mcp-use/cli dev
```

---

## 6. Logging for Debugging

### Debug Modes

```bash
DEBUG=1 node dist/server.js   # Logs registrations, session lifecycle
DEBUG=2 node dist/server.js   # Full JSON-RPC request/response bodies
```

### Logger API

```typescript
import { Logger } from "mcp-use";

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

## 7. Observability

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

## 8. Common Debug Scenarios

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

## 9. Testing Patterns

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

## 10. Performance Debugging

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

## 11. Testing Checklist

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

---

## 12. Inspector Deep Dive

The mcp-use Inspector is a standalone web-based tool (`@mcp-use/inspector`) and is also available hosted at [inspector.mcp-use.com](https://inspector.mcp-use.com). When running `mcp-use dev`, the server also exposes a built-in inspector at `http://localhost:3000/inspector`.

### Inspector Feature Matrix

| Feature | Tab / Panel | Notes |
|---|---|---|
| Tool calls | Tools tab | Execute tools; view schemas and results; saved requests |
| Resource browsing | Resources tab | Inspect content, MIME types; test subscriptions |
| Prompt preview | Prompts tab | No-argument prompts; result inserted into chat |
| Elicitation requests | Elicitation tab | Review pending elicitation requests; fill and submit forms |
| LLM chat with tools | Chat tab | BYOK API key (OpenAI, Anthropic, etc.); real-time tool-call visualization |
| JSON-RPC traffic | RPC Messages panel | All send/receive messages with direction, method, timestamp, payload |
| Notifications | Notifications pane | Server log messages and list-change notifications |
| Multi-server | Connection panel | Connect to multiple MCP servers simultaneously |
| OAuth | Connection panel | Built-in OAuth popup flow; credentials stored locally in browser |
| Add to client | Header button | One-click export config for Cursor, VS Code, Claude Desktop, CLI |
| Command palette | `Cmd/Ctrl+K` | Quick search, server connect, tool execution, navigation |
| Session persistence | Automatic | Connections saved to `localStorage`; auto-reconnect on reload |

### Inspector URLs

| Access method | URL |
|---|---|
| Hosted (always available) | `https://inspector.mcp-use.com` |
| Local CLI | `http://localhost:8080` (default) |
| mcp-use dev server built-in | `http://localhost:3000/inspector` |

### Inspector CLI Quick Reference

```bash
npx @mcp-use/inspector                              # Start on port 8080
npx @mcp-use/inspector --url http://localhost:3000/mcp  # Auto-connect
npx @mcp-use/inspector --port 9000                  # Custom port
```

### BYOK Chat Setup

1. Open the **Chat** tab in Inspector.
2. Click **Configure API Key**.
3. Select provider (OpenAI, Anthropic, etc.) and model (e.g., `gpt-4o`, `claude-3`).
4. Paste your API key — stored only in the browser, never sent to any server.
5. Send a message; tool calls will appear with their full JSON request/response.

### CSP Testing

Inspector has two CSP modes accessible from the settings panel:

| Mode | Behavior |
|---|---|
| **Permissive** | Relaxed CSP for debugging widget network calls |
| **Widget-Declared** | Enforces the CSP declared in `widgetMetadata.metadata.csp`; violations appear in browser console |

---

## 13. Manual HTTP Testing with curl

Every JSON-RPC call must include a session header after initialization. Use the same `Mcp-Session-Id` for subsequent calls.

### Parameter Table: JSON-RPC Envelope

| Field | Type | Required | Description |
|---|---|---|---|
| `jsonrpc` | `"2.0"` | Yes | Protocol version |
| `method` | `string` | Yes | MCP method (e.g., `tools/list`) |
| `params` | `object` | No | Method parameters |
| `id` | `number|string` | Yes | Request ID |

### Initialize + List Tools

```bash
BASE=http://localhost:3000/mcp
SESSION=$(curl -s -D - -X POST $BASE \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"curl","version":"1.0.0"}},"id":1}' \
  | grep -i "mcp-session-id" | awk '{print $2}' | tr -d '\r')

curl -s -X POST $BASE \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: $SESSION" \
  -H "MCP-Protocol-Version: 2025-11-25" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":2}' | jq
```

### Call a Tool

```bash
curl -s -X POST $BASE \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: $SESSION" \
  -H "MCP-Protocol-Version: 2025-11-25" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"get-weather","arguments":{"city":"Paris"}},"id":3}' | jq
```

### ❌ BAD: Missing Required Headers

```bash
curl -X POST $BASE -d '{"jsonrpc":"2.0","method":"tools/list","id":2}'
# Missing: Mcp-Session-Id, Accept, MCP-Protocol-Version
```

### ✅ GOOD: All Required Headers Present

```bash
curl -X POST $BASE \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: $SESSION" \
  -H "MCP-Protocol-Version: 2025-11-25" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":2}'
```

---

## 14. Claude Desktop Integration

Add your MCP server to Claude Desktop by editing the config JSON. Use HTTP for StreamableHTTP/SSE servers or stdio for local processes.

### HTTP Server Example

```json
{
  "mcpServers": {
    "mcp-use": {
      "command": "npx",
      "args": ["@mcp-use/cli", "start"],
      "env": { "PORT": "3000" },
      "transport": "http",
      "url": "http://localhost:3000/mcp"
    }
  }
}
```

### Stdio Server Example

```json
{
  "mcpServers": {
    "local": {
      "command": "node",
      "args": ["dist/server.js"],
      "transport": "stdio"
    }
  }
}
```

### ❌ BAD: Using HTTP Without Exposing `/mcp`

```json
{ "url": "http://localhost:3000" }
```

### ✅ GOOD: Target the MCP Endpoint

```json
{ "url": "http://localhost:3000/mcp" }
```

---

## 15. Transport Debugging

Enable verbose logs and inspect transport-specific behavior.

### Transport Debug Flags

| Flag / Env | Description |
|---|---|
| `DEBUG=mcp-use:*` | Enable verbose MCP logs |
| `NODE_DEBUG=http` | Node HTTP debugging |
| `MCP_LOG_LEVEL=debug` | CLI log level |

### SSE Debug Tips

- Check `Content-Type: text/event-stream`.
- Verify proxy does not buffer events.
- Keep connections alive with heartbeats.

---

## 16. HMR Debugging

If widgets or tools are not updating in dev mode, verify list change notifications are firing.

| Symptom | Likely Cause | Fix |
|---|---|---|
| Tools not updating | HMR stopped | Restart `mcp-use dev` |
| Widgets stale | Asset cache | Hard refresh or clear cache |
| Resources missing | HMR crash | Run with `--no-hmr` |

---

## 17. Common Test Scenarios

| Scenario | Goal | Notes |
|---|---|---|
| Invalid input | Ensure schema errors | Check tool error messages |
| Long-running tool | Verify progress | Use `ctx.reportProgress()` |
| Resource updates | Subscription works | Call `notifyResourceUpdated()` |
| Widget fallback | `supportsApps()` gating | Return text fallback |

---

## 18. Unit Testing Tools & Resources

Use your existing test runner (Vitest, Jest, or Node test) to unit-test tool handlers. Keep tests deterministic by mocking external API calls.

### Minimal Tool Unit Test

```typescript
import { MCPServer, text, object, widget } from 'mcp-use/server';

const server = new MCPServer({ name: 'test', version: '1.0.0' });

server.tool({ name: 'ping' }, async () => text('pong'));

// Call the handler directly or via your test harness.
```

### Parameter Table: Test Concerns

| Concern | Approach |
|---|---|
| External APIs | Mock responses |
| Timeouts | Use fake timers |
| Progress updates | Assert `reportProgress` calls |

---

## 19. Debug Checklist

1. Open `npx @mcp-use/inspector --url http://localhost:3000/mcp` (or the built-in `/inspector` in dev mode) and check for tool/schema mismatches.
2. Confirm `Mcp-Session-Id` is present for all HTTP calls after initialization.
3. Validate Claude Desktop config JSON (absolute paths, correct `/mcp` endpoint).
4. Run `mcp-use generate-types` after schema edits.
5. Check RPC Messages panel in Inspector for raw JSON-RPC send/receive payloads.

---

## 20. Notification & Subscription Debugging

Notifications are fire-and-forget, so visibility is critical during testing.

### Notification Debug Table

| Debug Step | Command | Outcome |
|---|---|---|
| List subscriptions | Inspector → Resources tab | Verify subscription status |
| Trigger update | `notifyResourceUpdated()` | Watch for update events |
| Observe client logs | `session.on("notification")` | Confirm payloads |

### Example Client Logger

```typescript
session.on('notification', (notification) => {
  console.log(notification.method, notification.params);
});
```

---

## 21. Load and Concurrency Testing

Simulate multiple sessions to validate broadcast and progress behavior.

### Multi-Session Script (Pseudo)

```bash
for i in {1..5}; do
  curl -s -X POST $BASE -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{}},"id":1}' \
    | grep -i "mcp-session-id" | awk '{print $2}' | tr -d '\r'
done
```

### Load Test Tips

| Tip | Why |
|---|---|
| Stagger sessions | Avoid burst overload |
| Reuse session IDs | Simulate real clients |
| Monitor memory | Detect leaks |

---

## 22. Smoke Tests for `/mcp`

Run lightweight smoke tests before deployments.

```bash
BASE=http://localhost:3000/mcp
curl -s -X POST $BASE -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"ping","id":999}' | jq
```

### ❌ BAD: Deploying Without a Smoke Test

```bash
mcp-use deploy
```

### ✅ GOOD: Smoke Test First

```bash
mcp-use build && mcp-use start --port 4000
curl -s -X POST http://localhost:4000/mcp -d '{"jsonrpc":"2.0","method":"ping","id":1}'
```

---

## 23. Debugging Widget Assets

Widgets load assets from the MCP server. Verify they are reachable.

### Asset Check

```bash
curl -I http://localhost:3000/mcp-use/public/icons/logo.png
```

### Common Failures

| Symptom | Cause | Fix |
|---|---|---|
| 404 on assets | Wrong `MCP_SERVER_URL` | Set correct public URL |
| CORS errors | Missing headers | Add `server.use()` middleware |

---

## 24. Error Snapshotting

Capture error payloads for reproducibility.

```bash
curl -s -X POST $BASE -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: $SESSION" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"bad-tool"},"id":5}' | jq
```

---

## 25. Regression Checklist

- [ ] Broadcast notifications still fire after HMR reloads.
- [ ] Inspector loads within 2 seconds on dev builds.
- [ ] Claude Desktop config still points to `/mcp`.
- [ ] Progress updates appear when `progressToken` is supplied.

---

## 26. Minimal Test Harness Structure

```text
src/
├─ server.ts
tests/
├─ tools.test.ts
└─ resources.test.ts
```

### Example Tool Test (Pseudo)

```typescript
import { describe, it, expect } from 'vitest';

it('ping tool returns pong', async () => {
  const result = await pingTool();
  expect(result).toContain('pong');
});
```

### Parameter Table: Test Data

| Data | Use |
|---|---|
| `fixtures/` | Sample payloads |
| `mocks/` | API stubs |
| `snapshots/` | Expected output |

---

## Final Tip

Keep a single curl script that runs initialize → list → call for fast regression checks.
