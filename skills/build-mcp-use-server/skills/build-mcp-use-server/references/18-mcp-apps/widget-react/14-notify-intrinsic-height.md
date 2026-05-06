# Intrinsic Height — Auto-Sizing in `mcp-use@1.26.0`

In `mcp-use@1.26.0`, widget height reporting is a provider feature, not a `useWidget()` action. Use `<McpUseProvider autoSize>` for normal widgets.

```tsx
import { McpUseProvider } from "mcp-use/react";

export default function Widget() {
  return (
    <McpUseProvider>
      <WidgetContent />
    </McpUseProvider>
  );
}
```

`autoSize` defaults to `true` at runtime. Passing it explicitly is fine for readability, but not required:

```tsx
<McpUseProvider autoSize>
  <WidgetContent />
</McpUseProvider>
```

## What the Provider Does

When `autoSize` is enabled, the provider:

1. Wraps children in a measured container.
2. Observes the container with `ResizeObserver`.
3. Debounces height changes.
4. Reports the intrinsic height to the host.

Runtime behavior differs by host:

| Host path | Package behavior |
|---|---|
| ChatGPT Apps SDK | Calls `window.openai.notifyIntrinsicHeight(height)` when available. |
| MCP Apps | Sends `ui/notifications/size-changed` with `{ height }` over the MCP Apps bridge. |

## When to Disable Auto-Size

Disable `autoSize` only when the widget intentionally owns a fixed viewport, such as an immersive fullscreen canvas or chart:

```tsx
<McpUseProvider autoSize={false}>
  <div style={{ height: "100vh", overflow: "hidden" }}>
    <FullscreenChart />
  </div>
</McpUseProvider>
```

Then use `displayMode`, `maxHeight`, and CSS overflow rules to keep content within the host slot. See `10-display-modes.md` and `11-host-context.md`.

## What Not to Document as Public Hook API

Do **not** teach a height-reporting method on the `useWidget()` return object. `notifyIntrinsicHeight` exists on the ChatGPT `window.openai` API and is used internally by `McpUseProvider`, but it is not returned by `useWidget()` in `mcp-use@1.26.0`.
