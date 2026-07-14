# Widget Rendering Issues

Widgets sit between your MCP server and the host's iframe sandbox. Most "broken widget" symptoms have one of four causes: protocol mismatch, CSP, missing provider, or Vite cold start.

---

## 1. Widget shows as plain HTML (no React, no styling)

**Cause:** The host doesn't speak the MCP Apps protocol. It received `text/html` content from your tool and rendered it as raw HTML, not as a widget.

**Diagnose:**

- Open the Inspector (which always speaks MCP Apps) — does the widget render correctly there? If yes, the host is the problem.
- Check the host: ChatGPT (Apps SDK), MCP Inspector, and Claude Desktop with MCP Apps enabled support widgets. Standard MCP clients without Apps support don't.

**Fix:**

- Ensure your tool returns `widgetMetadata` correctly via `_meta["mcp-use/widget"]` — the widget is keyed on that.
- For dual-protocol support (works in both ChatGPT Apps SDK and MCP Apps), use `type: "mcpApps"` (default since v1.17.0).
- If the host genuinely doesn't speak widgets, your tool should still return useful `text` content as a fallback — set both `content` (text) and the widget metadata.

---

## 2. Widget loads but appears blank

**Cause:** CSP violation. The browser blocked the widget's JS, CSS, or fetch calls.

**Diagnose:**

1. Open browser DevTools console.
2. Look for messages like:
   ```
   Refused to load the script 'https://cdn.example.com/widget.js' because it
   violates the following Content Security Policy directive: ...
   ```
3. Identify the blocked origin.

**Fix:**

Configure the widget's CSP via `widgetMetadata.metadata.csp` when registering the resource. The fields are auto-generated camelCase on tool registration:

```typescript
server.resource({
  name: "my-widget",
  uri: "ui://widget/my-widget.html",
  metadata: {
    csp: {
      connectDomains: ["https://api.example.com"],
      resourceDomains: ["https://cdn.example.com"],
      baseUriDomains: ["https://app.example.com"],
    },
  },
}, ...);
```

For the full diagnostic flow, see `05-csp-violations.md`. For the Inspector's CSP mode toggle for live testing, see `../20-inspector/11-protocol-toggle-and-csp-mode.md`.

---

## 3. Hooks fire outside `McpUseProvider`

**Symptom:** `useWidget`, `useCallTool`, or other mcp-use React hooks throw "must be used within McpUseProvider" or return undefined.

**Cause:** The widget tree doesn't wrap content in `<McpUseProvider>`.

**Fix:**

```tsx
import { McpUseProvider } from "mcp-use/react";

export default function Widget() {
  return (
    <McpUseProvider autoSize>
      <MyWidgetContent />
    </McpUseProvider>
  );
}
```

The provider must wrap **everything** that uses mcp-use hooks. If you have nested components with their own provider mount paths (e.g. portals), each tree needs its own provider.

---

## 4. React Router not working (v1.20.1+)

**Cause:** Breaking change in v1.20.1. `McpUseProvider` no longer includes `BrowserRouter`. Routes inside the widget render but `useNavigate`/`useParams` throw.

**Fix:** Wrap routed widgets in `BrowserRouter` explicitly:

```tsx
import { BrowserRouter } from "react-router-dom";
import { McpUseProvider } from "mcp-use/react";

export default function Widget() {
  return (
    <McpUseProvider autoSize>
      <BrowserRouter>
        <RoutedContent />
      </BrowserRouter>
    </McpUseProvider>
  );
}
```

---

## 5. Widget first render times out (504)

**Cause:** Vite dev server cold start. Pre-v1.25.2, the dev server registered tools before pre-warming widget entries — first widget call could time out.

**Fix:** Upgrade `mcp-use@^1.25.2`. The dev server now pre-warms Vite entries before tool registration.

For production (built widgets), this isn't an issue.

---

## 6. Widget shows duplicate CSP meta tags (pre-v1.20.1)

**Cause:** Sandbox proxy injected a new CSP meta tag without stripping existing ones, causing conflicting directives. Browser merged using the most restrictive rule.

**Fix:** Upgrade `mcp-use@^1.20.1`. Sandbox proxy now strips existing tags before injecting.

---

## 7. Widget data not updating between tool calls

**Cause:** Iframe is cached by the browser; props haven't changed.

**Fix:** mcp-use auto-appends a timestamp query param when widget data changes (since v1.14.2). Confirm:

- You're on `mcp-use@^1.14.2`.
- Your tool returns updated `structuredContent` — props key off this; identical structuredContent renders the same iframe.

---

## 8. `useWidget` returns pending forever

**Cause:** Tool call didn't complete or `outputSchema` doesn't match what the widget expects.

**Fix:**

- Inspect the JSON-RPC trace in the Inspector. Did the tool return successfully?
- Verify `useWidget`'s expected props (from your widget's `propsSchema`) match `structuredContent`.
- Use the discriminated union — TypeScript will tell you when you read `.data` on a pending state.

```tsx
const result = useWidget<MyProps>();
if (result.isPending) return <Spinner />;
return <MyWidget {...result.data} />;
```

---

## 9. CSP mode in Inspector

The Inspector has a CSP mode toggle that simulates the production iframe sandbox locally. Use it to catch CSP violations during development before deploying. See `../20-inspector/11-protocol-toggle-and-csp-mode.md`.

---

For the underlying widget anti-patterns and the production deployment checklist for widgets, see `18-mcp-apps/widget-anti-patterns/`.
