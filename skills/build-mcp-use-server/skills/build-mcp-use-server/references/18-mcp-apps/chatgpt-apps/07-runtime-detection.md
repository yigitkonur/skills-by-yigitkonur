# Runtime Detection

`useWidget` automatically detects which host loaded the widget and picks the right transport. The bridge object is the underlying primitive; you almost never call it directly.

## How `useWidget` decides

When `useWidget` mounts, it checks two globals:

```typescript
const isChatGPT = typeof window !== "undefined" && "openai" in window;
const isMcpApps = typeof window !== "undefined" && window.parent !== window;
```

| Detection | Bridge selected | Transport |
|---|---|---|
| `window.openai` exists | `AppsSdkAdapter` | `window.openai.*` calls |
| `window.parent !== window` (and no `window.openai`) | `McpAppsAdapter` | `postMessage` JSON-RPC |
| Neither (rare — standalone preview) | None | Throws on tool calls; `isAvailable` is `false` |

The selection is made once on mount; switching hosts mid-session is not a supported scenario.

## What the bridge does

The bridge object encapsulates one transport. Both adapters implement the same interface:

```typescript
interface Bridge {
  callTool(name: string, args: unknown): Promise<CallToolResult>;
  readResource(uri: string): Promise<ReadResourceResult>;
  sendMessage(content: unknown): Promise<void>;
  openLink(href: string): Promise<void>;
  requestDisplayMode(mode: DisplayMode): Promise<{ mode: DisplayMode }>;
  setWidgetState(state: unknown): Promise<void>;
  // ... etc
}
```

`useWidget` exposes the user-facing API on top of this. You should reach for `useWidget`, not the bridge.

## Direct bridge access (advanced, rare)

For the rare case where you need a primitive call that `useWidget` doesn't surface, mcp-use exposes:

```tsx
import { getMcpAppsBridge } from "mcp-use/react";

function MyWidget() {
  const bridge = getMcpAppsBridge();

  const result = await bridge.callTool("search", { query: "hello" });
  const data = await bridge.readResource("file:///data.json");
  await bridge.sendMessage({ type: "info", text: "Processing..." });
  await bridge.openLink("https://example.com");
  await bridge.requestDisplayMode("fullscreen");

  return <div>My Widget</div>;
}
```

Most widgets do not need this. `useWidget` provides the same operations with React-friendly state management, host context, and protocol-agnostic semantics.

## When you might detect manually

Almost never. Cases where it's actually justified:

| Need | Better answer |
|---|---|
| "Different UI in ChatGPT vs Claude" | Branch on **capabilities**, not host. Use `useWidget().displayMode`, `userAgent`, etc. |
| "Different feature flag per host" | Server tells the widget via `metadata` channel based on `ctx.client`. |
| "Use ChatGPT-only API" | If you really must, gate via `useWidget().hostInfo === undefined` (ChatGPT) and call `window.openai` inside that branch. |
| "Use MCP-Apps-only feature" | Gate via `useWidget().hostInfo` truthy and use `useWidget().hostCapabilities` to test. |

`hostInfo` is `{ name, version }` in MCP Apps and `undefined` in ChatGPT — the cleanest detection signal exposed by the hook.

```tsx
const { hostInfo, hostCapabilities } = useWidget();

if (hostInfo) {
  // MCP Apps — Claude, Goose, Inspector, etc.
  // hostInfo.name, hostInfo.version available
  // hostCapabilities advertises what the host supports (SEP-1865)
} else {
  // ChatGPT
}
```

## What's NOT host-portable

A short list of features that genuinely differ:

| Feature | MCP Apps | ChatGPT |
|---|---|---|
| `partialToolInput` (streamed args) | Yes (when host supports it) | Always `null`/`false` |
| `sendFollowUpMessage` content blocks | Full SEP-1865 (text, image, resource) | Text only — image/resource silently stripped |
| `hostInfo` / `hostCapabilities` | Yes | `undefined` |
| `maxWidth` | Yes | `undefined` |

Code defensively against these — see the `widget-react/` cluster for hook-level guards and the `streaming-tool-props/` cluster for streaming.

## Don't fight the abstraction

If you find yourself writing `if (window.openai) { ... } else { ... }` more than once in your widget, reconsider. The abstraction's whole purpose is letting you write portable code; manual host branching reintroduces the bug class it was built to prevent.
