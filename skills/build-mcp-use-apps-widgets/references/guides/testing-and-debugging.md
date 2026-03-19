# Testing and Debugging MCP Apps

Test and debug MCP Apps (widget-enabled servers) built with mcp-use across every stage of development.

---

## 1. MCP Inspector

The mcp-use SDK ships a built-in Inspector that is the primary tool for testing and debugging widget-enabled servers.

### Built-in Inspector (Dev Mode)

Run `mcp-use dev` — the Inspector auto-opens at `http://localhost:3000/inspector`. It stays open across HMR reloads.

```bash
mcp-use dev             # Starts server with HMR + Inspector
mcp-use dev --port 8080 # Custom port
```

### Inspector Features for MCP Apps

| Panel / Tab | What to test |
|---|---|
| **Tools** | All tools appear with correct names, descriptions, and JSON schemas |
| **Resources** | Static and template resources load with correct URIs and content |
| **Prompts** | Prompt argument definitions render correctly |
| **Chat** | BYOK (bring-your-own-key) live testing with an LLM |
| **Elicitation** | Renders SEP-1330 enum patterns (single-select, multi-select) |
| **Protocol toggle** | Switch between MCP Apps and ChatGPT protocol views |
| **CSP mode** | Toggle between Permissive (fast iteration) and Widget-Declared (production) |
| **Device/locale panels** | Simulate different host environments for `useWidget` context |

### Widget-Specific Testing in Inspector

1. Run `npm run dev` to start the server.
2. Open `http://localhost:3000/inspector`.
3. Toggle the protocol selector (MCP Apps ↔ ChatGPT) to verify dual-protocol rendering.
4. Switch CSP mode to **Widget-Declared** to surface CSP violations before release.
5. Use the device and locale panels to simulate `theme`, `locale`, `timeZone`, and `safeArea` values.
6. Test display modes: inline / pip / fullscreen — watch that `requestDisplayMode` is honoured.
7. Call tools that return `widget()` responses and observe the live widget in the frame.

### Add to Client (from Inspector)

The Inspector header has an **Add to Client** button that configures the connected server in:
- Cursor
- VS Code
- Claude Desktop
- Generic CLI tools

---

## 2. Development Workflow

### mcp-use Dev Server

```bash
mcp-use dev                          # HMR + Inspector + type generation
mcp-use dev --port 8080 --no-open    # Custom port, no auto-open browser
mcp-use dev --no-hmr                 # Falls back to tsx watch
```

**Hot-reloadable (no restart needed):** tools, prompts, resources, widget components, schemas.
**Requires restart:** server config (`MCPServer` constructor options), middleware, OAuth config.

Connected clients receive `list_changed` notifications automatically on HMR. The Inspector session is preserved across reloads.

### Type Generation

```bash
mcp-use generate-types                          # From tool Zod schemas
mcp-use generate-types --server src/server.ts   # Custom entry file
```

Creates `.mcp-use/tool-registry.d.ts` for type-safe `useCallTool` in widgets.

Add to `tsconfig.json`:
```json
{
  "include": ["index.ts", "src/**/*", "resources/**/*", ".mcp-use/**/*"]
}
```

Runs automatically in `mcp-use dev`. Run manually for CI or after schema changes.

### Recommended package.json Scripts

```json
{
  "scripts": {
    "dev": "mcp-use dev",
    "build": "mcp-use build",
    "start": "mcp-use start",
    "typecheck": "tsc --noEmit",
    "generate-types": "mcp-use generate-types"
  }
}
```

---

## 3. Tunneling (Test with Real Clients)

Expose a local server to ChatGPT, Claude, or any real MCP client without deploying:

```bash
# 1. Start your server
npm run dev

# 2. In a second terminal, create a public tunnel
npx @mcp-use/tunnel 3000
# Prints: https://happy-blue-cat.local.mcp-use.run/mcp
```

Use the printed URL as the MCP endpoint in ChatGPT Developer Mode, Claude Desktop, or Goose.

**Tunnel limits:**

| Limit | Value |
|---|---|
| Lifetime | 24 hours |
| Inactivity timeout | 1 hour |
| Creations per IP | 10 / hour |
| Concurrent tunnels per IP | 5 |

Alternatively, pass `--tunnel` directly to the start command:

```bash
mcp-use start --port 3000 --tunnel
```

---

## 4. Manual Testing with curl

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

# 3. Call a widget tool (observe structuredContent in response)
curl -s -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" -H "Mcp-Session-Id: <session-id>" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"get-weather","arguments":{"city":"Tokyo"}},"id":3}' | jq .
```

Widget tool responses include `structuredContent` (the `props` data) alongside `content` (the `message` text visible to the LLM).

---

## 5. Testing in Real Clients

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "my-mcp-app": {
      "url": "http://localhost:3000/mcp"
    }
  }
}
```

**Verify:** Quit Claude (Cmd+Q) → Reopen → Click the hammer icon to confirm tools appear → call a widget tool → widget should render inline.

```bash
tail -f ~/Library/Logs/Claude/mcp*.log
```

### ChatGPT

1. Enable **Developer Mode** in ChatGPT settings.
2. Go to **Connectors → Advanced** → add your MCP URL (or tunnel URL).
3. Call a tool — widget should render with ChatGPT Apps SDK protocol.

### Goose

Configure the MCP server URL in Goose settings. Widget tools appear and render with the MCP Apps Extension protocol.

| Issue | Fix |
|---|---|
| Widget not rendering | Check `ctx.client.supportsApps()` returns true in that client |
| Props not received | Verify `widget({ props: {...}, message: "..." })` not `output` |
| CSP violations | Switch Inspector to Widget-Declared mode; add domain to `metadata.csp` |
| Tools don't appear | Restart client; verify JSON-RPC initialize succeeds |

---

## 6. Widget-Specific Debugging

### useWidget Debug Props

Enable the built-in debugger overlay on `McpUseProvider`:

```tsx
export default function Widget() {
  return (
    <McpUseProvider autoSize debugger viewControls>
      <WidgetContent />
    </McpUseProvider>
  );
}
```

- `debugger` — shows an overlay with raw props, host context, and state.
- `viewControls` — adds display mode controls (inline / pip / fullscreen) for testing.

### Inspecting Host Context

```typescript
function WidgetContent() {
  const {
    props,
    isPending,
    isStreaming,
    partialToolInput,
    theme,
    locale,
    timeZone,
    maxWidth,
    maxHeight,
    userAgent,
    safeArea,
    displayMode,
    state,
  } = useWidget();

  console.log("Host context:", { theme, locale, timeZone, maxWidth, maxHeight });
  console.log("Device:", userAgent?.device?.type, "Touch:", userAgent?.capabilities?.touch);
  console.log("Safe area insets:", safeArea?.insets);
  // ...
}
```

### Streaming Props Preview

When the LLM streams tool arguments, `isStreaming` is `true` and `partialToolInput` contains partial data:

```tsx
function CodePreview() {
  const { props, isPending, isStreaming, partialToolInput } = useWidget<{ code: string }>();

  const displayCode = isStreaming ? (partialToolInput?.code ?? "") : (props.code ?? "");

  return (
    <pre>
      {displayCode}
      {isStreaming && <span className="animate-pulse">▌</span>}
    </pre>
  );
}
```

Test streaming in the Inspector by calling a tool with a large `code` parameter — the Inspector sends `ui/notifications/tool-input-partial` notifications as it types.

### State Persistence

```tsx
const { state, setState } = useWidget<Props, Output, Meta, { count: number }>();

// UI-only state — persists per message via the MCP Apps bridge
await setState({ count: (state?.count ?? 0) + 1 });
```

State round-trips via `ui/update-model-context` (MCP Apps) or `window.openai.setWidgetState` (ChatGPT).

---

## 7. Logging for Debugging

### Debug Modes

```bash
DEBUG=1 node dist/server.js   # Logs registrations, session lifecycle
DEBUG=2 node dist/server.js   # Full JSON-RPC request/response bodies
```

### Tool-Level Logging with ctx.log

```typescript
server.tool(
  { name: "process_data", schema: z.object({ items: z.array(z.string()) }) },
  async ({ items }, ctx) => {
    await ctx.log("info", "Starting processing");
    await ctx.log("debug", `${items.length} items`, "my-tool");
    // ...
    return text("Done");
  }
);
```

Levels: `debug`, `info`, `notice`, `warning`, `error`, `critical`, `alert`, `emergency`.

---

## 8. Common Debug Scenarios

| Scenario | Debug steps |
|---|---|
| **Widget not rendering** | Verify tool returns `widget({...})` response. Check `ctx.client.supportsApps()`. |
| **Props missing or wrong** | Inspect `structuredContent` in curl response. Verify `props` shape matches `widgetMetadata.props` schema. |
| **CSP violation** | Open Inspector → Widget-Declared CSP mode → check browser console. Add domain to `metadata.csp.connectDomains` or `resourceDomains`. |
| **Streaming not working** | Verify Inspector is sending `ui/notifications/tool-input-partial`. Check `isStreaming` and `partialToolInput` in widget. |
| **State not persisting** | Use `setState` from `useWidget`, not `localStorage`. Check bridge RPC logs in browser console. |
| **Display mode rejected** | `requestDisplayMode` is advisory — read back `displayMode` to confirm. Test in Inspector with viewControls. |
| **Tool not appearing** | Verify name/description non-empty. Run `DEBUG=1` to see registrations. |
| **Wrong response format** | Use `widget()`, `text()`, `object()` helpers. Inspect raw JSON-RPC in Inspector. |
| **Auth failures** | Verify OAuth env vars. Check redirect URI. Inspect `/oauth/callback`. |
| **CORS errors** | Set `cors` in server config. Check preflight in browser console. |
| **HMR not working** | Config changes always require full restart. Widget component changes hot-reload. |

### JSON-RPC Error Codes

| Code | Meaning | Likely cause |
|---|---|---|
| -32700 | Parse error | Malformed JSON |
| -32600 | Invalid request | Missing JSON-RPC fields |
| -32601 | Method not found | Typo or capability not advertised |
| -32602 | Invalid params | Arguments don't match schema |
| -32603 | Internal error | Unhandled exception in handler |

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
- [ ] Widget tools return `structuredContent` with correct `props` shape
- [ ] Widget renders correctly in Inspector (both CSP modes)
- [ ] Widget handles `isPending` state (loading skeleton)
- [ ] Widget handles `isStreaming` / `partialToolInput` (if applicable)
- [ ] Widget CSP validated in Widget-Declared mode — no console violations
- [ ] `setState` persists across interactions in the same session
- [ ] `requestDisplayMode("fullscreen")` works where supported
- [ ] `sendFollowUpMessage` triggers a new LLM turn correctly
- [ ] Server works in Claude Desktop (tools appear, widget renders)
- [ ] Server works via tunnel with ChatGPT or Goose
- [ ] `mcp-use generate-types` succeeds and `useCallTool` is type-safe
- [ ] `DEBUG=2` shows correct request/response logging
- [ ] No `console.log()` in stdio server code; CORS/auth tested
