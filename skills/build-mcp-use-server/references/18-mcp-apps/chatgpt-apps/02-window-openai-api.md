# `window.openai` API

Inside a ChatGPT-rendered widget, the iframe has a `window.openai` global injected by the host. This is the underlying API the ChatGPT Apps SDK exposes. **Do not access it directly** — `useWidget` from `mcp-use/react` wraps it and falls back to `postMessage` JSON-RPC for MCP Apps. Direct access breaks portability.

## What's on `window.openai`

`mcp-use@1.26.0` types the direct ChatGPT bridge as `OpenAiGlobals & API`. The host updates globals through the `openai:set_globals` event.

| Direct API | Equivalent in `useWidget` | Purpose |
|---|---|---|
| `window.openai.theme` | `useWidget().theme` | Current theme (`"light"` or `"dark"`) |
| `window.openai.userAgent` | `useWidget().userAgent` | Device and capability hints |
| `window.openai.locale` | `useWidget().locale` | Current locale (BCP-47) |
| `window.openai.maxHeight` | `useWidget().maxHeight` | Host-provided maximum height |
| `window.openai.displayMode` | `useWidget().displayMode` | Current display mode |
| `window.openai.safeArea` | `useWidget().safeArea` | Safe-area insets |
| `window.openai.toolInput` | `useWidget().toolInput` | Complete tool arguments |
| `window.openai.toolOutput` | `useWidget().output` | Last tool output / structured content |
| `window.openai.toolResponseMetadata` | `useWidget().metadata` | Tool-result `_meta` |
| `window.openai.widgetState` | `useWidget().state` | Current persisted state |
| `window.openai.callTool(name, args)` | `useWidget().callTool(name, args)` | Call a tool on the MCP server |
| `window.openai.sendFollowUpMessage({ prompt })` | `useWidget().sendFollowUpMessage(prompt)` | Send a follow-up message; mcp-use converts content blocks to text |
| `window.openai.openExternal({ href })` | `useWidget().openExternal(href)` | Open URL in browser |
| `window.openai.requestDisplayMode({ mode })` | `useWidget().requestDisplayMode(mode)` | Request fullscreen/pip/inline |
| `window.openai.setWidgetState(state)` | `useWidget().setState(state)` | Persist widget state |
| `window.openai.notifyIntrinsicHeight(height)` | `McpUseProvider autoSize` | Notify intrinsic height changes |
| `window.openai.uploadFile(file)` | `useFiles()` | Optional file upload support |

ChatGPT does **not** expose `partialToolInput` or `isStreaming` on `window.openai`; `useWidget` returns `null` / `false` for those in Apps SDK mode.

## Why you should NOT access it directly

```tsx
// BAD — breaks in MCP Apps clients where window.openai doesn't exist
const theme = window.openai.theme;
window.openai.callTool("search", { query: "test" });

// GOOD — works in both ChatGPT and MCP Apps
const { theme, callTool } = useWidget();
await callTool("search", { query: "test" });
```

Two reasons:

1. **Portability.** `window.openai` is undefined in Claude, Goose, the MCP Inspector, and any other MCP Apps client. Direct access throws.
2. **Type safety.** `useWidget` is generic over your widget's prop/state shapes; `window.openai` is loosely typed.

## Detecting ChatGPT runtime

`useWidget` already detects this internally:

```typescript
const isChatGPT = typeof window !== "undefined" && "openai" in window;
const isMcpApps = typeof window !== "undefined" && window.parent !== window;
```

If you ever genuinely need to branch on host (almost never), use `useWidget().hostInfo`:

- In MCP Apps: `hostInfo` is `{ name: string; version: string }`.
- In ChatGPT: `hostInfo` is `undefined`.

```tsx
const { hostInfo } = useWidget();
if (!hostInfo) {
  // running in ChatGPT (or another non-MCP-Apps host)
}
```

## When direct `window.openai` access is OK

There is **one** legitimate case: bridging a third-party SDK that pre-dates `useWidget` and accepts a config object. Even then, prefer wrapping it in a custom hook so the rest of your widget stays portable.

```typescript
// Last-resort interop with a legacy SDK
useEffect(() => {
  if ("openai" in window) {
    legacySdk.init({ openai: window.openai });
  }
}, []);
```

For everything else, use `useWidget`.

## See also

- The `useWidget` hook surface: `widget-react/` cluster.
- How mcp-use selects the bridge automatically: `07-runtime-detection.md`.
- The advanced bridge object for direct protocol calls: same cluster (`widget-react/`).
