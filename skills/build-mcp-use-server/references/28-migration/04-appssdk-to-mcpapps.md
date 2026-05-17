# Widget Protocol Migration: `appsSdk` → `mcpApps`

The single home for the widget protocol migration. The widget cluster (`18-mcp-apps/`) and other clusters do **not** repeat this content; they link here.

---

## 1. The change

Since v1.17.0, the default widget `type` is `mcpApps` (dual-protocol) instead of `appsSdk` (ChatGPT Apps SDK only).

| Type        | Speaks                              | Default before    | Default since v1.17.0 |
|-------------|-------------------------------------|-------------------|-----------------------|
| `appsSdk`   | ChatGPT Apps SDK only               | Default           | Deprecated, still works |
| `mcpApps`   | MCP Apps **and** ChatGPT Apps SDK   | —                 | Default               |

`mcpApps` is a superset. Existing widgets that explicitly set `type: "appsSdk"` continue to render in ChatGPT but won't appear in MCP-Apps-aware hosts (Claude Desktop with MCP Apps, MCP Inspector).

---

## 2. What stays the same

- Widget code — your React component, props, schema.
- `useWidget()` hook usage.
- `useCallTool()` and other mcp-use React hooks.
- Tool call → widget render flow.
- Widget files in `resources/`.
- `_meta["mcp-use/widget"]` linking tools to widgets.

You're changing **how the widget is declared**, not its implementation.

---

## 3. The CSP format change

CSP fields were renamed from `snake_case` to `camelCase`, and most are now **auto-generated** at tool registration time.

### Old (`appsSdk`)

```typescript
// _meta on the tool
"openai/outputTemplate": {
  csp: {
    connect_domains: ["https://api.example.com"],
    resource_domains: ["https://cdn.example.com"],
    frame_domains: ["https://www.youtube.com"],
    base_uri_domains: ["https://app.example.com"],
  },
},
```

### New (`mcpApps`)

```typescript
// metadata.csp on the resource — camelCase
server.resource({
  name: "my-widget",
  uri: "ui://widget/my-widget.html",
  metadata: {
    csp: {
      connectDomains: ["https://api.example.com"],
      resourceDomains: ["https://cdn.example.com"],
      frameDomains: ["https://www.youtube.com"],
      baseUriDomains: ["https://app.example.com"],
    },
  },
}, ...);
```

Key change: **the server's own origin is auto-injected** into `connectDomains` and `resourceDomains` (since v1.16.1). You no longer need to declare your own server URL — only **external** origins.

---

## 4. Migration steps

### a) Drop explicit `type: "appsSdk"`

Search for `type: "appsSdk"` and remove it. The default is now `mcpApps`. If you want the previous behavior explicitly (you almost never do), leave it.

### b) Convert CSP keys

```bash
# in your codebase
grep -rE 'connect_domains|resource_domains|frame_domains|base_uri_domains' .
```

Rename:
- `connect_domains` → `connectDomains`
- `resource_domains` → `resourceDomains`
- `frame_domains` → `frameDomains`
- `base_uri_domains` → `baseUriDomains`
- `redirect_domains` → `redirectDomains`

### c) Move CSP from tool `_meta` to resource `metadata`

If you had CSP under `_meta["openai/outputTemplate"]` on the tool, move it to `metadata.csp` on the resource registration.

### d) Drop your own server origin from the lists

Auto-injected since v1.16.1. Only declare external origins.

### e) Verify in the Inspector

Open with CSP mode on. Browser console should show zero violations. If you see violations, walk back through `27-troubleshooting/05-csp-violations.md`.

---

## 5. Why the rename

ChatGPT's Apps SDK uses `snake_case`. MCP Apps follows the broader MCP convention of `camelCase`. The dual-protocol `mcpApps` widgets emit both formats internally — you write `camelCase` once, mcp-use emits whichever the host expects.

---

## 6. Compatibility window

| Server version | `appsSdk` widgets | `mcpApps` widgets |
|----------------|-------------------|-------------------|
| < v1.15.0      | Yes               | Not supported     |
| v1.15.0+       | Yes               | Yes               |
| v1.17.0+       | Deprecated, still works | Default      |

If your server is older than v1.15.0, upgrading is a prerequisite for `mcpApps`.

---

## 7. The deprecation note

`type: "appsSdk"` is **deprecated** since v1.17.0 but has not been removed. It will be removed in a future major (no date announced). Migrate now to avoid forced migration later.

This is the single home for that deprecation note. The widget cluster (`18-mcp-apps/`) links here rather than restating it.

---

## 8. Per-widget verification after migration

For each widget:

1. Tool call from Inspector → widget renders.
2. Browser console → zero CSP violations.
3. Hooks (`useWidget`, `useCallTool`) → no "outside provider" errors.
4. Test in both Inspector and ChatGPT (or whichever host you support) — `mcpApps` should render in both.

---

For widget anti-patterns: `18-mcp-apps/widget-anti-patterns/`. For CSP debugging: `27-troubleshooting/05-csp-violations.md`. For widget rendering issues beyond the protocol: `27-troubleshooting/04-widget-rendering-issues.md`.
