# ChatGPT Apps Compatibility

How MCP Apps widgets work as ChatGPT Apps, protocol bridging, and deployment for ChatGPT compatibility.

---

## Overview

MCP Apps widgets are designed to work in both MCP Apps clients and ChatGPT simultaneously. The same widget code runs in both environments — the `useWidget` hook detects the runtime and adapts automatically.

```
┌──────────────────────────────────────┐
│  Widget Code (React + useWidget)     │
├──────────────────────────────────────┤
│  Runtime Detection Layer             │
├─────────────────┬────────────────────┤
│  MCP Apps Mode  │  ChatGPT Mode      │
│  (postMessage)  │  (window.openai)   │
└─────────────────┴────────────────────┘
```

When loaded inside ChatGPT, the widget detects `window.openai` and uses the OpenAI Apps SDK bridge. When loaded in an MCP Apps client, it uses JSON-RPC over `postMessage`.

---

## The `window.openai` API Bridge

In ChatGPT, widgets communicate through the global `window.openai` object instead of postMessage. The `useWidget` hook handles this automatically, but understanding the underlying API helps with debugging.

### ChatGPT Runtime Detection

```typescript
// How useWidget() internally detects the runtime
const isChatGPT = typeof window !== "undefined" && "openai" in window;
const isMcpApps = typeof window !== "undefined" && window.parent !== window;
```

### What `window.openai` Provides

| API | MCP Apps Equivalent | Description |
|-----|---------------------|-------------|
| `window.openai.theme` | `useWidget().theme` | Current theme (`"light"` or `"dark"`) |
| `window.openai.callTool()` | `useWidget().callTool()` | Call a server tool |
| `window.openai.sendFollowUp()` | `useWidget().sendFollowUpMessage()` | Send follow-up message to chat |
| `window.openai.openExternal()` | `useWidget().openExternal()` | Open URL in browser |
| `window.openai.requestDisplayMode()` | `useWidget().requestDisplayMode()` | Request fullscreen/PiP |

### Why You Should NOT Access `window.openai` Directly

```typescript
// ❌ BAD — breaks in MCP Apps clients where window.openai doesn't exist
const theme = window.openai.theme;
window.openai.callTool("search", { query: "test" });

// ✅ GOOD — works in both ChatGPT and MCP Apps
const { theme, callTool } = useWidget();
await callTool("search", { query: "test" });
```

---

## MIME Type Mapping

Servers return widgets with different MIME types depending on the protocol:

| Protocol | MIME Type | Used By |
|----------|-----------|---------|
| MCP Apps | `text/html;profile=mcp-app` | Claude, MCP clients |
| ChatGPT | `text/html+skybridge` | ChatGPT |

### How mcp-use Handles This

The `AppsSdkAdapter` in `mcp-use/server` automatically converts between formats:

```typescript
import { AppsSdkAdapter } from "mcp-use/server";

// When ChatGPT connects, the adapter:
// 1. Detects ChatGPT user-agent or protocol markers
// 2. Converts MIME type to "text/html+skybridge"
// 3. Transforms metadata keys to "openai/*" prefixed format
// 4. Converts CSP from camelCase to snake_case
```

You don't need to use `AppsSdkAdapter` directly — it's applied automatically when a ChatGPT client connects.

---

## CSP Mapping: camelCase ↔ snake_case

Widget metadata uses camelCase for CSP domains, but ChatGPT expects snake_case. The adapter converts automatically.

| MCP Apps (your code) | ChatGPT (auto-converted) |
|---------------------|--------------------------|
| `connectDomains` | `connect_domains` |
| `resourceDomains` | `resource_domains` |

### Example

```typescript
// Your widget metadata — always use camelCase
export const widgetMetadata: WidgetMetadata = {
  description: "Widget with external API access",
  props: z.object({ data: z.any() }),
  metadata: {
    csp: {
      connectDomains: ["https://api.example.com"],   // ← camelCase
      resourceDomains: ["https://cdn.example.com"],  // ← camelCase
    },
    prefersBorder: true,
  },
};

// ChatGPT sees:
// {
//   "connect_domains": ["https://api.example.com"],   ← snake_case
//   "resource_domains": ["https://cdn.example.com"],  ← snake_case
// }
```

---

## Apps SDK Metadata vs MCP Apps Metadata

### Tool Registration Metadata

MCP Apps uses standard `_meta` fields. ChatGPT uses `openai/*` prefixed keys. The adapter maps between them.

```typescript
// Your tool definition — standard mcp-use format
server.tool({
  name: "show-chart",
  description: "Display a chart",
  schema: z.object({ data: z.array(z.any()) }),
  widget: {
    name: "chart",
    invoking: "Generating chart...",
    invoked: "Chart generated",
  },
}, handler);

// MCP Apps sees (standard _meta):
// { widget: { name: "chart", invoking: "...", invoked: "..." } }

// ChatGPT sees (auto-converted to openai/* prefixed):
// {
//   "openai/outputTemplate": "ui://widgets/chart",
//   "openai/toolInvocation/invoking": "Generating chart...",
//   "openai/toolInvocation/invoked": "Chart generated",
//   "openai/widgetAccessible": true
// }
```

### Manual OpenAI Metadata (Advanced)

For fine-grained control, you can set `openai/*` metadata directly:

```typescript
server.tool({
  name: "show_chart",
  schema: z.object({ data: z.array(z.any()) }),
  _meta: {
    "openai/outputTemplate": "ui://widgets/chart",
    "openai/toolInvocation/invoking": "Generating chart...",
    "openai/toolInvocation/invoked": "Chart generated",
    "openai/widgetAccessible": true,
  },
}, async ({ data }) => ({
  _meta: { "openai/outputTemplate": "ui://widgets/chart" },
  content: [{ type: "text", text: "Chart displayed" }],
  structuredContent: { data },
}));
```

> Only use manual metadata when you need behavior that differs between ChatGPT and MCP Apps.

---

## Widget Description and `prefersBorder`

The `description` field in `widgetMetadata` serves as context for the LLM to understand when to invoke the tool. In ChatGPT, this maps to the Apps SDK widget description.

```typescript
export const widgetMetadata: WidgetMetadata = {
  // This description is shown to the LLM in both environments
  description: "Interactive product search results with filtering and sorting. Shows product cards with images, prices, and ratings.",

  props: z.object({ products: z.array(z.any()) }),

  metadata: {
    // prefersBorder: tells the host whether to draw a border/frame
    prefersBorder: true,   // true → host draws a border (good for cards/panels)
    // prefersBorder: false → no border (good for fullscreen/immersive widgets)
  },
};
```

---

## Display Modes in ChatGPT

ChatGPT supports the same display modes as MCP Apps, but with slightly different behavior:

| Mode | ChatGPT Behavior | MCP Apps Behavior |
|------|-------------------|-------------------|
| `inline` | Embedded in chat message | Embedded in chat flow |
| `pip` | Picture-in-picture overlay | Picture-in-picture window |
| `fullscreen` | Takes full ChatGPT panel | Takes full client viewport |

### Requesting Display Modes

```tsx
const { displayMode, requestDisplayMode } = useWidget();

// Works identically in both environments
await requestDisplayMode("fullscreen");
await requestDisplayMode("inline");
await requestDisplayMode("pip");
```

---

## Testing in ChatGPT

### Local Development

1. Start your MCP server:
   ```bash
   npm run dev
   ```

2. Use `ngrok` or similar tunnel to expose your local server:
   ```bash
   ngrok http 3000
   ```

3. In the ChatGPT plugin/action setup, point to your ngrok URL:
   ```
   https://abc123.ngrok.io/mcp
   ```

### Testing Checklist

| Test | What to Verify |
|------|----------------|
| Widget renders | Content appears in chat after tool call |
| Theme matches | Widget respects ChatGPT's dark/light mode |
| Tool calls work | `useCallTool` and `callTool` execute successfully |
| Display modes | Fullscreen/PiP transitions work |
| CSP compliance | External API calls and images load without errors |
| Follow-up messages | `sendFollowUpMessage` appears in chat |
| External links | `openExternal` opens in browser |

### Common ChatGPT Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Widget shows blank | CSP blocking resources | Add domains to `connectDomains`/`resourceDomains` |
| Theme doesn't match | Missing `ThemeProvider` | Use `McpUseProvider` which includes it |
| Tool calls fail | Incorrect tool name | Ensure tool name matches server registration exactly |
| "Not accessible" error | Missing widget metadata | Export `widgetMetadata` with description |

---

## Deployment for ChatGPT Compatibility

### Server Requirements

1. **HTTPS required** — ChatGPT only loads widgets from HTTPS endpoints
2. **CORS headers** — Must allow ChatGPT origin
3. **Public accessibility** — Server must be reachable from the internet

### Production Deployment

```typescript
import { MCPServer } from "mcp-use/server";

const server = new MCPServer({
  name: "my-widget-app",
  version: "1.0.0",
  allowedOrigins: [
    "https://chat.openai.com",
    "https://chatgpt.com",
    "https://myapp.example.com",
  ],
});

// Register tools with widgets...

await server.listen(process.env.PORT ? parseInt(process.env.PORT) : 3000);
```

### Docker Deployment

```dockerfile
FROM node:22-slim AS build
WORKDIR /app
COPY package*.json tsconfig.json ./
COPY src ./src
COPY resources ./resources
COPY public ./public
RUN npm ci && npx mcp-use build

FROM node:22-slim
WORKDIR /app
COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules ./node_modules
COPY package*.json ./
ENV NODE_ENV=production
EXPOSE 3000
CMD ["npx", "mcp-use", "start"]
```

### Environment Variables

```env
PORT=3000
NODE_ENV=production
# Add any API keys your tools need
OPENWEATHER_API_KEY=your-key-here
```

---

## Checking Client Support

Detect whether the connected client supports widgets before returning them:

```typescript
server.tool(
  {
    name: "show-dashboard",
    schema: z.object({}),
    widget: { name: "dashboard", invoking: "Loading...", invoked: "Ready" },
  },
  async (_params, ctx) => {
    // Falls back gracefully for text-only clients
    if (!ctx.client.supportsApps()) {
      return text("Dashboard data:\n- Visitors: 12,453\n- Page views: 45,231");
    }

    return widget({
      props: { visitors: 12453, pageViews: 45231 },
      output: text("Dashboard loaded with 12,453 visitors"),
    });
  }
);
```

This ensures your server works with:
- ChatGPT (widgets rendered)
- MCP Apps clients like Claude (widgets rendered)
- Text-only clients like CLI tools (text fallback)

---

## Quick Reference: Protocol Mapping

| Feature | MCP Apps | ChatGPT |
|---------|----------|---------|
| Widget MIME | `text/html;profile=mcp-app` | `text/html+skybridge` |
| Communication | `postMessage` JSON-RPC | `window.openai.*` |
| Theme source | postMessage event | `window.openai.theme` |
| CSP format | camelCase | snake_case |
| Meta prefix | Standard `_meta` | `openai/*` |
| Tool output | `ui://` template ref | `openai/outputTemplate` |
| Detection | `window.parent !== window` | `"openai" in window` |
